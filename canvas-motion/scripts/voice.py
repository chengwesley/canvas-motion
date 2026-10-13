#!/usr/bin/env python3
"""旁白配音：把每幕的 vo 念成音檔，量出實際長度，檢查放不放得進那一幕。

用法：
  python3 voice.py <專案>                    # 產生（或沿用沒改過的）旁白，印出每幕旁白長度與是否放得下
  python3 voice.py <專案> --fit              # 放不下的幕自動加小節（改 project.json 的 bars，維持整數小節）
  python3 voice.py <專案> --engine edge      # 改用 Edge 線上語音（需要 pip install edge-tts 與網路）
  python3 voice.py --list                    # 列出可用的語音

語音引擎（project.json 的 voice.engine，或 --engine）：
  winrt   Windows 內建離線語音（預設，台灣中文：Yating、Hanhan 女聲，Zhiwei 男聲）。
          每句產 3 個語速版本，用 Windows 內建辨識器聽回文字算 CER、檢查語速（每秒 3.3–5.4 字），挑最好的一版
  edge    Microsoft Edge 線上語音（跨平台、較自然；zh-TW-HsiaoChenNeural、zh-TW-YunJheNeural…）。文字會送到微軟的服務
  say     macOS 內建（Meijia）
  某句寫了 file（使用者自己錄的音檔）就直接用那個檔案

產出：<專案>/voice/<幕序>_<句序>.mp3、voice/voice.json（每句長度、語速、CER、快取鍵）、voice/subs.srt
build.py 會內嵌音檔並排好時間；引擎播放時自動壓低配樂、畫出字幕；export.py 一起混進 MP4，另存 .srt。
只有文字、語音或語速改過的句子會重產。
"""
import argparse, json, math, platform, re, shutil, subprocess, sys, tempfile, time, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）
import _vo  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
SR = 48000
CPS_T, CPS_LO, CPS_HI = 4.5, 3.3, 5.4           # 中文每秒字數：目標、下限、上限
DEFAULT_VOICE = {"winrt": "Yating", "edge": "zh-TW-HsiaoChenNeural", "say": "Meijia"}
CN = "零一二三四五六七八九"


def ffmpeg():
    f = shutil.which("ffmpeg")
    if f:
        return f
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("✗ 需要 ffmpeg：pip install imageio-ffmpeg")


def ps(script, *args):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SKILL / "scripts" / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[:300])
    return r.stdout


def list_voices():
    if platform.system() == "Windows":
        print("winrt（離線）：")
        for ln in ps("tts_winrt.ps1", "-list").splitlines():
            print("  " + ln)
    try:
        import edge_tts  # noqa: F401
        print("edge（線上）：python -m edge_tts --list-voices | findstr zh-TW")
    except ImportError:
        print("edge（線上）：未安裝，pip install edge-tts")
    if platform.system() == "Darwin":
        print("say：say -v '?' | grep zh_TW")


# ---------- 音訊處理 ----------
def to_pcm(src: Path, ff):
    """任何格式 → 48kHz 單聲道 float（numpy）。"""
    import numpy as np
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "a.wav"
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], check=True)
        with wave.open(str(out)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x


def clean(x):
    """去 DC、高通、頭尾去靜音、淡入淡出、音量標準化（沿用 anding-ep1 的處理）。"""
    import numpy as np
    x = x - x.mean()
    try:
        from scipy.signal import butter, sosfilt
        x = sosfilt(butter(2, 70, "hp", fs=SR, output="sos"), x)
    except ImportError:
        pass
    win = int(SR * .01)
    rms = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same"))
    voiced = np.where(rms > max(rms.max() * .04, 1e-4))[0]
    if len(voiced):
        x = x[max(0, voiced[0] - int(SR * .03)):min(len(x), voiced[-1] + int(SR * .06))]
    fi, fo = int(SR * .008), min(int(SR * .09), len(x) // 3)
    x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    peak = np.abs(x).max()
    return x / peak * .89 if peak > 0 else x


def save(x, out: Path, ff):
    """存成 mp3（內嵌進 HTML 才不會太大）；回傳秒數。"""
    import numpy as np
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wv = Path(td) / "a.wav"
        with wave.open(str(wv), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(wv), "-ac", "1", "-b:a", "80k", str(out)], check=True)
    return len(x) / SR


# ---------- 語音引擎 ----------
def norm(s):
    return _vo.spoken(re.sub(r"\d", lambda m: CN[int(m.group())], s).replace("〇", "零"))


def cer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))


def ssml(text, rate, lang="zh-TW"):
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}"><prosody rate="{rate:.2f}">{t}</prosody></speak>'


def gen_winrt(todo, voice, rate, tmp, ff):
    """每句 3 個語速版本 → 辨識回文字算 CER＋語速 → 挑最好的；語速不合格的調整後重產（最多 3 輪）。"""
    rates = {it["id"]: [round(rate * k, 3) for k in (.92, 1, 1.08)] for it in todo}
    done, has_asr = {}, True
    for rnd in range(3):
        left = [it for it in todo if it["id"] not in done]
        if not left:
            break
        jobs = [{"id": f"{it['id']}_v{v}", "ssml": ssml(it["say"], r), "out": str(tmp / f"{it['id']}_r{rnd}_v{v}.wav")}
                for it in left for v, r in enumerate(rates[it["id"]])]
        jf = tmp / "jobs.json"; jf.write_text(json.dumps(jobs, ensure_ascii=False), "utf-8")
        print(f"  第 {rnd + 1} 輪：合成 {len(jobs)} 個版本（{voice}）…", flush=True)
        ps("tts_winrt.ps1", "-jobs", str(jf), "-voice", voice)
        texts = {}
        if has_asr:
            lf, of = tmp / "asr.txt", tmp / "asr.json"
            lf.write_text("\n".join(j["out"] for j in jobs), "utf-8-sig")
            try:
                ps("asr_sapi.ps1", "-list", str(lf), "-out", str(of))
                texts = {Path(r["wav"]).name: r["text"] for r in json.loads(of.read_text("utf-8-sig"))}
            except Exception as e:  # noqa: BLE001
                has_asr = False; print(f"  ! 沒有 zh-TW 語音辨識，略過 CER（{str(e)[:80]}）")
        for it in left:
            n, zh = len(_vo.spoken(it["say"])), bool(_vo.CJK.search(it["say"]))
            cands = []
            for v, r in enumerate(rates[it["id"]]):
                p = tmp / f"{it['id']}_r{rnd}_v{v}.wav"
                x = clean(to_pcm(p, ff)); d = len(x) / SR; cps = n / d
                c = cer(it["say"], texts[p.name]) if p.name in texts else None
                ok = (CPS_LO <= cps <= CPS_HI) if zh else True
                score = (c or 0) + (abs(cps - CPS_T) / CPS_T * .5 if zh else 0) + (0 if ok else 1)
                cands.append(dict(rate=r, dur=d, cps=cps, cer=c, ok=ok, score=score, asr=texts.get(p.name), x=x))
            best = min(cands, key=lambda c: c["score"])
            if best["ok"] or rnd == 2:
                done[it["id"]] = best
            else:
                f = CPS_T / best["cps"]
                rates[it["id"]] = [round(min(1.3, max(.8, best["rate"] * f * k)), 3) for k in (.95, 1, 1.05)]
                print(f"  ↻ {it['id']} 語速 {best['cps']:.1f} 字/秒，調整後重產")
    return done


def gen_edge(todo, voice, rate, tmp, ff):
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        sys.exit("✗ edge 引擎需要：pip install edge-tts（也需要網路）；或改用 --engine winrt")
    out = {}
    for it in todo:
        p = tmp / f"{it['id']}.mp3"
        pct = f"{round((rate - 1) * 100):+d}%"
        r = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", pct, "--text", it["say"], "--write-media", str(p)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode or not p.exists():
            sys.exit(f"✗ edge-tts 失敗（{it['id']}）：{(r.stderr or '').strip()[:200]}")
        x = clean(to_pcm(p, ff)); d = len(x) / SR
        out[it["id"]] = dict(rate=rate, dur=d, cps=len(_vo.spoken(it["say"])) / d, cer=None, ok=True, x=x)
    return out


def gen_say(todo, voice, rate, tmp, ff):
    out = {}
    for it in todo:
        p = tmp / f"{it['id']}.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(round(180 * rate)), "-o", str(p), it["say"]], check=True)
        x = clean(to_pcm(p, ff)); d = len(x) / SR
        out[it["id"]] = dict(rate=rate, dur=d, cps=len(_vo.spoken(it["say"])) / d, cer=None, ok=True, x=x)
    return out


# ---------- 主流程 ----------
def bpm_of(cfg):
    from storyboard import style_bpm
    return int(cfg.get("bpm") or style_bpm(cfg.get("style", "minimal")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--engine", choices=["winrt", "edge", "say"])
    ap.add_argument("--voice", help="語音名稱（winrt：Yating／Hanhan／Zhiwei；edge：zh-TW-HsiaoChenNeural…）")
    ap.add_argument("--rate", type=float, help="語速倍率，預設 1")
    ap.add_argument("--fit", action="store_true", help="旁白放不下的幕自動加小節")
    ap.add_argument("--force", action="store_true", help="全部重產")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        return list_voices()
    if not a.project:
        ap.error("需要專案資料夾")
    proj = Path(a.project).resolve()
    cfg_p = proj / "project.json"; cfg = json.loads(cfg_p.read_text("utf-8"))
    V = cfg.get("voice") or {}
    engine = a.engine or V.get("engine") or ("winrt" if platform.system() == "Windows" else "say" if platform.system() == "Darwin" else "edge")
    voice = a.voice or V.get("voice") or DEFAULT_VOICE[engine]
    rate = a.rate or V.get("rate") or 1.0
    vdir = proj / "voice"; meta_p = vdir / "voice.json"
    meta = json.loads(meta_p.read_text("utf-8")) if meta_p.exists() else {"lines": {}}
    ff = ffmpeg()

    its = [dict(it, id=_vo.line_id(si, k), s=si, k=k) for si, sc in enumerate(cfg["scenes"]) for k, it in enumerate(_vo.items(sc))]
    if not its:
        sys.exit("✗ 沒有任何幕寫了 vo（旁白）。在 storyboard／project.json 的幕加上 \"vo\": \"旁白文字\"")
    for it in its:
        it["key"] = _vo.key("file" if it.get("file") else engine, voice, rate, it)
    todo = [it for it in its if a.force or meta["lines"].get(it["id"], {}).get("key") != it["key"] or not (vdir / f"{it['id']}.mp3").exists()]
    print(f"旁白 {len(its)} 句，需要產生 {len(todo)} 句（引擎 {engine}／{voice}／語速 {rate}）")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rec = [it for it in todo if it.get("file")]
        tts = [it for it in todo if not it.get("file")]
        res = {}
        for it in rec:
            src = (proj / it["file"]).resolve()
            if not src.exists():
                sys.exit(f"✗ 找不到錄音檔 {src}")
            x = clean(to_pcm(src, ff)); d = len(x) / SR
            res[it["id"]] = dict(rate=1, dur=d, cps=len(_vo.spoken(it["say"])) / d if it["say"] else 0, cer=None, ok=True, x=x, src=str(it["file"]))
        if tts:
            if engine == "winrt" and platform.system() != "Windows":
                sys.exit("✗ winrt 只能在 Windows 用；改用 --engine edge 或 say")
            res.update({"winrt": gen_winrt, "edge": gen_edge, "say": gen_say}[engine](tts, voice, rate, tmp, ff))
        for it in todo:
            r = res[it["id"]]
            d = save(r["x"], vdir / f"{it['id']}.mp3", ff)
            meta["lines"][it["id"]] = {"say": it["say"], "sub": it["sub"], "dur": round(d, 3), "key": it["key"],
                                       "engine": "file" if it.get("file") else engine, "voice": None if it.get("file") else voice,
                                       "rate": r["rate"], "cps": round(r["cps"], 2), "cer": None if r["cer"] is None else round(r["cer"], 3),
                                       "asr": r.get("asr"), "ok": r["ok"]}
            c = f"CER {r['cer']:.2f}" if r["cer"] is not None else ""
            print(f"  ✓ {it['id']}  {d:4.1f}s  {r['cps']:.1f} 字/秒  {c}  {it['say'][:24]}")
    keep = {it["id"] for it in its}
    for k in list(meta["lines"]):
        if k not in keep:
            meta["lines"].pop(k); (vdir / f"{k}.mp3").unlink(missing_ok=True)
    meta.update(engine=engine, voice=voice, rate=rate, updated=time.strftime("%Y-%m-%d %H:%M"))
    vdir.mkdir(exist_ok=True)
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")

    bpm = bpm_of(cfg); bar = 240 / bpm
    durs = {(it["s"], it["k"]): meta["lines"][it["id"]]["dur"] for it in its}
    lines, over = _vo.layout(cfg, bar, 60 / bpm, durs)
    if over and a.fit:
        for si, nb in over.items():
            print(f"  ↑ 第 {si + 1} 幕 {cfg['scenes'][si]['fn']}：{cfg['scenes'][si].get('bars', 2)} → {nb} 小節（放得下旁白）")
            cfg["scenes"][si]["bars"] = nb
        cfg_p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf-8")
        lines, over = _vo.layout(cfg, bar, 60 / bpm, durs)
    start = 0
    print("\n| # | 幕 | 幕長 | 旁白 | 放得下 |\n|---|---|---|---|---|")
    for si, sc in enumerate(cfg["scenes"]):
        d = sc.get("bars", 2) * bar
        mine = [ln for ln in lines if ln["s"] == si]
        used = (mine[-1]["t1"] - start) if mine else 0
        print(f"| {si + 1} | {sc['fn']} | {d:.1f}s | {used:.1f}s | {'✗ 需要 ' + str(over[si]) + ' 小節' if si in over else '✓'} |")
        start += d
    (vdir / "subs.srt").write_text(_vo.srt(lines), "utf-8-sig")
    bad = [k for k, v in meta["lines"].items() if not v.get("ok")]
    if bad:
        print(f"! 語速不在每秒 {CPS_LO}–{CPS_HI} 字：{', '.join(bad)}（句子太長或太短，考慮改寫）")
    if any(v.get("cer") and v["cer"] > .35 for v in meta["lines"].values()):
        print("! 有句子辨識差異大（CER > .35）：用耳朵聽一次；多音字、英文、數字可在 say 改寫成念法，sub 保留原字")
    if over:
        print(f"✗ {len(over)} 幕放不下旁白：加 --fit 自動加小節，或縮短旁白")
        sys.exit(3)
    print(f"✓ 旁白總長 {sum(v['dur'] for v in meta['lines'].values()):.1f}s，字幕 {vdir / 'subs.srt'}")


if __name__ == "__main__":
    main()
