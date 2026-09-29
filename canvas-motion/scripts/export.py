#!/usr/bin/env python3
"""匯出含配樂的 MP4，或 GIF：離線合成音訊 → 逐格擷取（可多行程平行）→ ffmpeg。

用法：
  python3 export.py <專案> out.mp4 [--size 1920x1080] [--fps 30] [--crf 19] [--mobile] [--no-audio]
  python3 export.py <專案> out.gif [--gif-width 640] [--fps 12]      # GIF：自動關顆粒、兩段式調色盤
  python3 export.py <專案> out.mp4 --preview                         # 快速預覽：640 寬、15fps，只看節奏
共用選項：
  --jobs N           平行渲染的瀏覽器數（預設依 CPU 自動，1 = 不平行）
  --verify 2,10,20   匯出後抽出這些秒數的畫格（存成 <輸出>_t2.jpg…），用 view 檢查
  --offline-fonts    不載入網路字型，只用系統字型（離線環境；確保整支片字型一致）
常用尺寸：16:9 → 1280x720／1920x1080；9:16 → 1080x1920；1:1 → 1080x1080
場景有錯誤時結束碼為 2；ffmpeg 失敗時為 1。
"""
import argparse, base64, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）
from build import build           # noqa: E402

GIF_WARN_MB = 5


def ffmpeg_bin():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        print("✗ 找不到 ffmpeg。安裝：apt install ffmpeg，或 pip install imageio-ffmpeg", file=sys.stderr)
        sys.exit(1)


def worker(html, start, end, fps, w, h, outdir, no_grain):
    """子行程：渲染 [start, end) 的影格到 outdir/%06d.jpg。"""
    from _browser import open_page, grab
    with open_page(Path(html)) as pg:
        if no_grain:
            pg.evaluate("STYLE.post && (STYLE.post.grain = 0)")
        for i in range(start, end):
            (Path(outdir) / f"{i:06d}.jpg").write_bytes(grab(pg, i / fps, w, h, "jpeg", 0.93))
        errs = pg.evaluate("__cm.errors")
    if errs:
        (Path(outdir) / f"errors_{start}.json").write_text(json.dumps(errs, ensure_ascii=False), "utf-8")


def probe(ff, out):
    """回傳 (秒數, 寬, 高, 串流種類清單, MB)。有 ffprobe 用 ffprobe，沒有就解析 ffmpeg -i 的輸出。"""
    size = out.stat().st_size / 1e6
    pr = shutil.which("ffprobe")
    if pr:
        r = subprocess.run([pr, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(out)],
                           capture_output=True, text=True)
        j = json.loads(r.stdout or "{}"); st = j.get("streams", [])
        v = next((s for s in st if s["codec_type"] == "video"), {})
        return float(j.get("format", {}).get("duration", 0)), v.get("width"), v.get("height"), [s["codec_type"] for s in st], size
    r = subprocess.run([ff, "-hide_banner", "-i", str(out), "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    t = r.stderr
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", t)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0
    wh = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", t)
    kinds = (["video"] if "Video:" in t else []) + (["audio"] if "Audio:" in t else [])
    return dur, int(wh.group(1)) if wh else None, int(wh.group(2)) if wh else None, kinds, size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("out")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--gif-width", type=int, default=640)
    ap.add_argument("--gif-dither", default="bayer:bayer_scale=5", help="none 會更小但漸層有色帶")
    ap.add_argument("--jobs", type=int, default=0)
    ap.add_argument("--verify", default="")
    ap.add_argument("--offline-fonts", action="store_true")
    ap.add_argument("--worker", nargs=7, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.worker:   # 內部：平行渲染的子行程
        html, s0, s1, fps, w, h, rest = a.worker
        outdir, ng = rest.split("|")
        return worker(html, int(s0), int(s1), float(fps), int(w), int(h), outdir, ng == "1")

    out = Path(a.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    gif = out.suffix.lower() == ".gif"
    w, h = map(int, a.size.lower().split("x"))
    if gif or a.preview:   # 依比例縮到指定寬度，寬高保持偶數
        tw_ = a.gif_width if gif else 640
        w, h = tw_, int(round(h * tw_ / w / 2)) * 2
    if w % 2 or h % 2:
        sys.exit("✗ 寬高需為偶數（libx264 / yuv420p 限制）")
    fps = a.fps or (12 if gif else 15 if a.preview else 30)
    crf = 28 if a.preview else a.crf
    proj = Path(a.project).resolve()
    ff = ffmpeg_bin(); tmp = Path(tempfile.mkdtemp(prefix="cm-export-"))
    jobs = a.jobs or max(1, min(4, (os.cpu_count() or 2) // 2))

    from _browser import open_page
    webfonts = not a.offline_fonts
    for attempt in range(2):
        html = build(proj, tmp / "export.html", quiet=True, webfonts=webfonts)   # 寫到暫存，不覆蓋 dist/
        with open_page(html) as pg:
            missing = pg.fonts_missing if webfonts else []
            if missing and attempt == 0:
                print(f"! 網路字型沒有載入（{', '.join(missing)}），改用系統字型重建，避免影片中途換字型")
                webfonts = False; continue
            total = pg.evaluate("__cm.TOTAL")
            music = pg.evaluate("PROJECT.music !== false")
            audio = None
            if music and not a.no_audio and not gif:
                print("♪ 離線合成配樂…")
                audio = tmp / "music.wav"
                audio.write_bytes(base64.b64decode(pg.evaluate("__cm.renderWav(44100)")))
        break

    n = int(round(total * fps)); hold = int(0.8 * fps)   # 結尾多留 0.8 秒讓收束和弦落完
    frames = tmp / "f"; frames.mkdir()
    t0 = time.time()
    chunk = -(-n // jobs); procs = []
    for j in range(jobs):
        s0, s1 = j * chunk, min(n, (j + 1) * chunk)
        if s0 >= s1:
            continue
        procs.append(subprocess.Popen([sys.executable, __file__, "x", "x", "--worker", str(html), str(s0), str(s1), str(fps), str(w), str(h),
                                       f"{frames}|{1 if gif else 0}"]))
    print(f"🎞  {n} 格 × {jobs} 個瀏覽器平行渲染（{w}×{h} @ {fps}fps）…", flush=True)
    while any(p.poll() is None for p in procs):
        done = len(list(frames.glob("*.jpg")))
        print(f"\r🎞  {done}/{n} 格  {time.time() - t0:.0f}s", end="", flush=True); time.sleep(1)
    if any(p.returncode for p in procs):
        sys.exit("\n✗ 渲染子行程失敗（見上方錯誤）")
    print(f"\r🎞  {n}/{n} 格  {time.time() - t0:.0f}s")
    last = frames / f"{n - 1:06d}.jpg"
    for k in range(hold):
        shutil.copy(last, frames / f"{n + k:06d}.jpg")
    errs = []
    for f in frames.glob("errors_*.json"):
        errs += json.loads(f.read_text("utf-8"))

    seq = ["-framerate", str(fps), "-i", str(frames / "%06d.jpg")]
    if gif:
        pal = tmp / "pal.png"
        r1 = subprocess.run([ff, "-y", "-loglevel", "error", *seq, "-vf", "palettegen=stats_mode=full", str(pal)], capture_output=True, text=True)
        r2 = subprocess.run([ff, "-y", "-loglevel", "error", *seq, "-i", str(pal), "-lavfi", f"[0:v][1:v]paletteuse=dither={a.gif_dither}:diff_mode=rectangle",
                             "-loop", "0", str(out)], capture_output=True, text=True) if not r1.returncode else r1
        if r2.returncode:
            sys.exit(f"✗ ffmpeg 失敗：{(r2.stderr or '').strip()[-400:]}")
    else:
        cmd = [ff, "-y", "-loglevel", "error", *seq]
        if audio:
            cmd += ["-i", str(audio)]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        if a.mobile or a.preview:
            cmd += ["-maxrate", "3600k", "-bufsize", "7200k"]
        if audio:
            cmd += ["-c:a", "aac", "-b:a", "160k", "-t", f"{total + 0.8:.3f}"]
        r = subprocess.run(cmd + [str(out)], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"✗ ffmpeg 失敗：{(r.stderr or '').strip()[-400:]}")

    dur, vw, vh, kinds, mb = probe(ff, out)
    print(f"✓ {out}  {dur:.1f}s  {vw}×{vh}  {mb:.1f}MB  串流：{'+'.join(kinds) or '?'}")
    if audio and "audio" not in kinds:
        print("✗ 輸出沒有音軌")
    if gif and mb > GIF_WARN_MB:
        print(f"! GIF {mb:.1f}MB 超過 {GIF_WARN_MB}MB：試 --gif-width 480、--fps 10、--gif-dither none，或改給 MP4")
    for t in [x for x in a.verify.split(",") if x.strip()]:   # 抽格檢查
        fp = out.with_name(f"{out.stem}_t{t.strip()}.jpg")
        subprocess.run([ff, "-y", "-loglevel", "error", "-ss", t.strip(), "-i", str(out), "-frames:v", "1", str(fp)])
        print(f"  抽格 {fp}")
    for e in errs:
        print(f"✗ 場景錯誤 {e['fn']} @ {e['t']}s：{e['msg']}")
    shutil.rmtree(tmp, ignore_errors=True)
    if errs:
        sys.exit(2)   # 影片裡有錯誤畫面，不能當成成功


if __name__ == "__main__":
    main()
