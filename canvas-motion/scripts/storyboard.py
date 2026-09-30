#!/usr/bin/env python3
"""分鏡 → 專案：一步產生 project.json 與自訂場景鷹架，並檢查節奏。

用法：
  python3 storyboard.py storyboard.json --preview        # 只印出提案用的分鏡表與檢查結果，不寫檔
  python3 storyboard.py storyboard.json <專案資料夾>      # 產生 <專案>/project.json 與 scenes/ 鷹架
  python3 storyboard.py storyboard.json <專案> --force   # 覆寫既有 project.json（已存在的場景檔不會被覆寫）

storyboard.json：
{
  "title": "片名", "aspect": "auto", "bpm": 100,            // bpm 選填，預設取風格
  "style": "minimal" 或 { "base": "minimal", ... },         // 風格參數見 styles/_schema.json
  "source": "source.txt",                                   // 選填：素材檔，build.py 用來追溯數字
  "scenes": [
    { "fn": "sHook", "bars": 2, "energy": 0.3, "trans": "zoom", "say": "這幕講的一件事",
      "hero": { "beat": 4, "what": "觀眾會記住的那一格：墨點炸開成分格" },   // 建議：高光瞬間落在本幕第幾拍（可以是爆發，也可以是一個停頓）
      "carry": "上一幕的什麼變成這幕的主角",                                   // 選填：物件延續鏈
      "sfx": [[3.5, "whoosh"], [4, "impact"]],                                  // 選填：音效綁動作（拍數, 種類, 音量）
      "rest": [7, 8] },                                                          // 選填：這段配樂靜默，高潮前留一口氣
    { "fn": "sProduct", "bars": 3, "energy": 0.7, "say": "產品如何運作", "hero": { "beat": 6, "what": "…" } }
  ]
}
音效種類：whoosh、swish、riser、impact、boom、pop、click、stamp、chime、gong、drum（見 references/craft.md）

劇本模式（30 秒以上的故事片，見 references/crew.md）：頂層加 script 與 cast，每個鏡頭加 act、beat、shot、who：
  "script": { "logline": "一句話故事", "genre": "hkcomic",
              "protagonist": { "name": "阿明", "want": "想要什麼", "obstacle": "什麼擋住他", "change": "最後他變成怎樣" } },
  "cast": { "kid": { "props": "teen", "hair": "spiky", "pal": { "top": "#e8e0c8" }, "render": "hkcomic", "note": "外型描述" } },
  鏡頭：{ …, "act": 1, "beat": "hook", "who": ["kid"],
          "shot": { "size": "LS", "angle": "low", "move": "push", "dir": "L>R" }, "lines": ["對白或旁白"] }
  dir 是角色在畫面上面向／前進的方向；同一鏡頭多個角色方向不同時寫成 { "kid": "L>R", "master": "R>L" }
  beat：hook、setup、inciting、rising、midpoint、crisis、climax、resolution
  size：ELS、LS、MS、CU、ECU；angle：eye、low、high、dutch、top；move：static、push、pull、pan、truck、crane、whip、follow、handheld、dolly-zoom
"""
import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

sys.path.insert(0, str(Path(__file__).parent))
from new_project import SCAFFOLD  # noqa: E402
from style_gen import anchor_info, anchor_src  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
TRANS = {"cut", "fade", "push", "wipe", "zoom", "iris", "flash", "glitch"}
BEATS = ["hook", "setup", "inciting", "rising", "midpoint", "crisis", "climax", "resolution"]
SIZES = ["ELS", "LS", "MS", "CU", "ECU"]
ANGLES = {"eye", "low", "high", "dutch", "top"}
MOVES = {"static", "push", "pull", "pan", "truck", "crane", "whip", "follow", "handheld", "dolly-zoom"}
SFX = {"whoosh", "swish", "riser", "impact", "boom", "pop", "click", "stamp", "chime", "gong", "drum"}


def lib_scenes():
    src = "\n".join(p.read_text("utf-8") for p in (SKILL / "library").glob("*.js"))
    return set(re.findall(r"function\s+(L_[A-Za-z0-9_]+)\s*\(", src))


def style_bpm(style):
    if isinstance(style, dict):
        b = (style.get("music") or {}).get("bpm")
        return min(140, max(70, int(b))) if b else anchor_info(anchor_src(style.get("base", "minimal")))["bpm"]
    p = SKILL / "styles" / f"{style}.js"
    return anchor_info(p.read_text("utf-8"))["bpm"] if p.exists() else 120


def check(sb):
    """回傳 (錯誤, 警告)。"""
    errs, warns = [], []
    sc = sb.get("scenes") or []
    if not sc:
        return ["沒有任何幕"], []
    for i, s in enumerate(sc, 1):
        fn = s.get("fn", "")
        if not isinstance(s.get("energy", .5), (int, float)):
            errs.append(f"第 {i} 幕 energy 要是數字"); continue
        if not re.match(r"s[A-Z0-9_]", fn):
            errs.append(f"第 {i} 幕 fn「{fn}」要是 s＋大寫字母開頭的自訂場景，例如 sHook（每幕都由自己發想構圖與動畫，不套版面零件）")
        b = s.get("bars", 2)
        if not isinstance(b, int) or b < 1:
            errs.append(f"第 {i} 幕 bars 必須是正整數（切點才會落在小節第一拍）")
        e = s.get("energy", .5)
        if not 0 <= e <= 1:
            errs.append(f"第 {i} 幕 energy 要在 0–1")
        if s.get("trans") and s["trans"] not in TRANS:
            errs.append(f"第 {i} 幕轉場 {s['trans']} 不支援（{', '.join(sorted(TRANS))}）")
        for k, v in (s.get("data") or {}).items():
            if isinstance(v, list) and isinstance(b, int) and len(v) > b * 4:
                warns.append(f"第 {i} 幕 {k} 有 {len(v)} 項，{b} 小節內每項不到一拍，考慮加小節或刪項")
        if not s.get("say"):
            warns.append(f"第 {i} 幕沒寫 say（這幕講的一件事），提案時使用者看不懂用意")
        beats = b * 4 if isinstance(b, int) else 8
        h = s.get("hero")
        if not isinstance(h, dict) or not h.get("what") or not isinstance(h.get("beat"), (int, float)):
            warns.append(f"第 {i} 幕沒寫 hero（觀眾會記住的那一格）：想一個最有力或最意外的瞬間會很有幫助；刻意平靜的幕可以不寫")
        elif not 0 <= h["beat"] <= beats:
            errs.append(f"第 {i} 幕 hero.beat {h['beat']} 超出本幕範圍（0–{beats} 拍）")
        if i > 1 and not s.get("carry"):
            warns.append(f"第 {i} 幕沒寫 carry（上一幕的什麼變成這幕的主角）：幕與幕各自獨立，看起來像換投影片")
        for e in s.get("sfx") or []:
            if not (isinstance(e, list) and len(e) >= 2 and isinstance(e[0], (int, float)) and e[1] in SFX):
                errs.append(f"第 {i} 幕 sfx {e} 格式錯誤：要寫 [拍數, 種類]，種類只能是 {', '.join(sorted(SFX))}")
        r = s.get("rest")
        if r is not None and not (isinstance(r, list) and len(r) == 2 and all(isinstance(x, (int, float)) for x in r) and 0 <= r[0] < r[1] <= beats):
            errs.append(f"第 {i} 幕 rest 要寫 [起拍, 終拍]，在 0–{beats} 拍之內")
    if isinstance(sc[-1].get("bars", 2), int) and sc[-1].get("bars", 2) < 2:
        warns.append("最後一幕只有 1 小節：收束和弦會很趕；想要戛然而止的效果就保留")
    en = [s.get("energy", .5) for s in sc]
    if len(sc) >= 3:
        if en[0] > .5:
            warns.append(f"開場 energy {en[0]} 偏高，通常從 .3 左右開始才有起伏")
        if en.index(max(en)) < len(en) / 2:
            warns.append("最高 energy 在前半段，高潮通常放在後半")
    if sb.get("script"):
        e2, w2 = check_script(sb)
        errs += e2; warns += w2
    tr = [s.get("trans") for s in sc[:-1] if s.get("trans")]
    if len(tr) >= 3 and len(set(tr)) == 1:
        warns.append(f"整支片只用 {tr[0]} 轉場，依內容關係換幾種（延續 push、揭示 wipe/iris、轉強 zoom/flash）")
    return errs, warns


def check_script(sb):
    """編劇、導演、剪輯、場記的檢查（references/crew.md）。"""
    errs, warns = [], []
    sc, S, cast = sb["scenes"], sb["script"], sb.get("cast") or {}
    bar = 240 / int(sb.get("bpm") or style_bpm(sb.get("style", "minimal")))
    dur = [s.get("bars", 2) * bar for s in sc]; total = sum(dur)
    # 編劇：一句話故事與主角弧線
    if not S.get("logline"):
        warns.append("編劇：沒寫 logline；試著用一句話講完這支片，常常會冒出更好的點子")
    pr = S.get("protagonist") or {}
    for k, zh in (("want", "想要什麼"), ("obstacle", "阻礙"), ("change", "最後的轉變")):
        if not pr.get(k):
            warns.append(f"編劇：沒寫 protagonist.{k}（{zh}）；想清楚會讓故事更有張力，詩意、氛圍、實驗類的片子可以不需要")
    # 結構：三幕只是其中一種。structure 可寫 three-act（預設）、kishotenketsu（起承轉合）、nonlinear（倒敘、插敘）、loop（循環）、oneshot（一鏡到底）、free（自由）
    structure = S.get("structure", "three-act")
    acts = [s.get("act") for s in sc]
    if structure != "three-act":
        pass
    elif any(a not in (1, 2, 3) for a in acts):
        warns.append("編劇：有鏡頭沒標 act；不走三幕就在 script 寫 structure（kishotenketsu、nonlinear、loop、oneshot、free）")
    else:
        share = {a: sum(d for d, x in zip(dur, acts) if x == a) / total for a in (1, 2, 3)}
        for a, lo, hi in ((1, .15, .35), (2, .38, .65), (3, .15, .35)):
            if not lo <= share[a] <= hi:
                warns.append(f"編劇：第 {a} 幕佔 {share[a]:.0%}（建議 {lo:.0%}–{hi:.0%}；常見比例 25／50／25）")
        if acts != sorted(acts):
            warns.append("編劇：act 跳回前面了；如果是倒敘或插敘，在 script 寫 structure: nonlinear")
    # 關鍵節拍
    bs = [s.get("beat") for s in sc]
    for b in bs:
        if b and b not in BEATS:
            errs.append(f"編劇：beat「{b}」不認得（可用：{'、'.join(BEATS)}）")
    need = {"hook": "開場鉤子", "inciting": "觸發事件", "midpoint": "中點轉折", "climax": "高潮", "resolution": "結局"}
    for b, zh in (need.items() if structure == "three-act" else []):
        if b not in bs:
            warns.append(f"編劇：沒有 {b}（{zh}）節拍；三幕結構常見，但不是必要")
    if bs and bs[0] != "hook":
        warns.append("編劇：第一個鏡頭應該是 hook（前 5 秒抓住人）")
    if "climax" in bs:
        ci = bs.index("climax")
        if acts[ci] != 3:
            warns.append("編劇：climax 應該在第 3 幕")
        if sc[ci].get("energy", .5) < .85:
            warns.append("編劇：climax 那個鏡頭的 energy 應該 ≥ .85")
    # 美術：演員都有設定
    for i, s in enumerate(sc, 1):
        for w in s.get("who") or []:
            if w not in cast:
                errs.append(f"美術：第 {i} 個鏡頭的角色「{w}」不在 cast 裡（先做角色設定）")
    # 導演：鏡頭語言
    shots = [s.get("shot") or {} for s in sc]
    for i, sh in enumerate(shots, 1):
        if not sh.get("size"):
            warns.append(f"導演：第 {i} 個鏡頭沒寫 shot.size（{'／'.join(SIZES)}），寫下來有助於規劃景別變化")
        elif sh["size"] not in SIZES:
            errs.append(f"導演：第 {i} 個鏡頭 size「{sh['size']}」不認得")
        if sh.get("angle") and sh["angle"] not in ANGLES:
            errs.append(f"導演：第 {i} 個鏡頭 angle「{sh['angle']}」不認得")
        if sh.get("move") and sh["move"] not in MOVES:
            errs.append(f"導演：第 {i} 個鏡頭 move「{sh['move']}」不認得")
    sizes = [sh.get("size") for sh in shots]
    if len(sc) >= 6 and len(set(x for x in sizes if x)) < 3:
        warns.append("導演：景別少於 3 種，觀眾會覺得距離一直沒變（遠景交代、中景看動作、特寫看情緒）")
    run = 1
    for i in range(1, len(sizes)):
        run = run + 1 if sizes[i] and sizes[i] == sizes[i - 1] else 1
        if run == 4:
            warns.append(f"導演：第 {i - 2}–{i + 1} 個鏡頭連續 4 個都是 {sizes[i]}")
    if sizes and sizes[0] not in ("ELS", "LS") and not any(x in ("ELS", "LS") for x in sizes[:2]):
        warns.append("導演：開頭沒有遠景（ELS／LS）交代場景，觀眾不知道在哪裡")
    if "climax" in bs and sizes[bs.index("climax")] in ("ELS",):
        warns.append("導演：高潮用大遠景會失去力量，考慮中景或特寫")
    moves = [sh.get("move") for sh in shots if sh.get("move")]
    if len(moves) >= 6 and len(set(moves)) < 3:
        warns.append("導演：運鏡少於 3 種")
    # 場記：畫面方向（180° 軸線）
    last = {}
    for i, (s, sh) in enumerate(zip(sc, shots), 1):
        d0 = sh.get("dir")
        if not d0:
            continue
        for w in s.get("who") or []:
            d = d0.get(w) if isinstance(d0, dict) else d0   # dir 可以整個鏡頭一個方向，或每個角色各自 {"kid": "L>R", "master": "R>L"}
            if not d:
                continue
            if w in last and last[w][1] != d and not sh.get("cross"):
                warns.append(f"場記：{w} 在第 {last[w][0]} 個鏡頭是 {last[w][1]}、第 {i} 個鏡頭變成 {d}（跳軸）；刻意轉向就在 shot 加 \"cross\": true 並讓觀眾看到他轉身")
            last[w] = (i, d)
    # 剪輯：節奏
    if len(sc) >= 6 and len(set(dur)) == 1:
        warns.append("剪輯：每個鏡頭一樣長，節奏會平；鋪陳放長、高潮前後剪短")
    a1 = [d for d, a in zip(dur, acts) if a == 1]; a3 = [d for d, a in zip(dur, acts) if a == 3]
    if a1 and a3 and sum(a3) / len(a3) > sum(a1) / len(a1) * 1.25:
        warns.append("剪輯：第 3 幕的平均鏡頭比第 1 幕還長，高潮段通常要剪得更快")
    tgt = S.get("length")
    if tgt and abs(total - tgt) > max(3, tgt * .1):
        warns.append(f"製片：總長 {total:.0f} 秒，目標 {tgt} 秒")
    return errs, warns


def script_page(sb):
    S, pr = sb["script"], sb["script"].get("protagonist") or {}
    out = [f"**一句話故事**：{S.get('logline', '')}",
           f"**主角**：{pr.get('name', '')}｜想要：{pr.get('want', '')}｜阻礙：{pr.get('obstacle', '')}｜轉變：{pr.get('change', '')}"]
    if S.get("theme"):
        out.append(f"**主題**：{S['theme']}")
    cast = sb.get("cast") or {}
    if cast:
        out.append("**角色**：" + "；".join(f"{k}（{v.get('note', v.get('props', ''))}）" for k, v in cast.items()))
    return "\n".join(out) + "\n"


def table(sb):
    bpm = int(sb.get("bpm") or style_bpm(sb.get("style", "minimal")))
    bar = 240 / bpm
    if sb.get("script"):
        rows = ["| # | 秒數 | 幕 · 節拍 | 鏡頭 | 角色 | 這個鏡頭講的事 | 高光 | energy |", "|---|---|---|---|---|---|---|---|"]
        t = 0
        for i, s in enumerate(sb["scenes"], 1):
            d = s.get("bars", 2) * bar; sh = s.get("shot") or {}
            h = s.get("hero") if isinstance(s.get("hero"), dict) else {}
            dd = sh.get("dir"); dd = " ".join(f"{k}{v}" for k, v in dd.items()) if isinstance(dd, dict) else dd
            cam = " ".join(x for x in (sh.get("size"), sh.get("angle"), sh.get("move"), dd) if x)
            rows.append(f"| {i} | {t:.0f}–{t + d:.0f} | {s.get('act', '?')} · {s.get('beat', '')} | {cam} | {'、'.join(s.get('who') or [])} | {s.get('say', '')} | {h.get('what', '')} | {s.get('energy', .5)} |")
            t += d
        return script_page(sb) + "\n" + "\n".join(rows) + f"\n\n總長約 {t:.0f} 秒（{bpm} BPM）"
    rows = ["| # | 小節 | 秒數 | energy | 這幕講的一件事 | 高光（第幾拍） | 延續 | 轉場 |", "|---|---|---|---|---|---|---|---|"]
    t = 0
    for i, s in enumerate(sb["scenes"], 1):
        d = s.get("bars", 2) * bar
        h = s.get("hero") if isinstance(s.get("hero"), dict) else {}
        hero = f"{h.get('what', '')}（{t + h['beat'] * bar / 4:.1f}s）" if isinstance(h.get("beat"), (int, float)) else h.get("what", "")
        rows.append(f"| {i} | {s.get('bars', 2)} | {t:.0f}–{t + d:.0f} | {s.get('energy', .5)} | {s.get('say', '')} | {hero} | {s.get('carry', '—')} | {s.get('trans', '—')} |")
        t += d
    return "\n".join(rows) + f"\n\n總長約 {t:.0f} 秒（{bpm} BPM）"


def write(sb, d: Path, force=False, sb_dir: Path = Path(".")):
    if (d / "project.json").exists() and not force:
        sys.exit(f"✗ {d}/project.json 已存在（要覆寫加 --force）")
    (d / "scenes").mkdir(parents=True, exist_ok=True)
    cfg = {k: sb[k] for k in ("title", "style", "aspect", "bpm", "anchors", "cast", "script") if k in sb}
    cfg.setdefault("aspect", "auto")
    cfg.setdefault("style", "minimal")
    if sb.get("source"):
        src = (sb_dir / sb["source"]).resolve()
        if src.exists() and src != (d / "source.txt").resolve():
            shutil.copy(src, d / "source.txt")
    cfg["scenes"] = []
    existing = "\n".join(p.read_text("utf-8") for p in (d / "scenes").glob("*.js"))
    for k, s in enumerate(sb["scenes"]):
        row = {"fn": s["fn"], "bars": s.get("bars", 2), "energy": s.get("energy", .5)}
        for key in ("trans", "data", "hero", "carry", "sfx", "rest", "act", "beat", "shot", "who", "lines"):
            if key in s:
                row[key] = s[key]
        if s.get("say"):
            row["_say"] = s["say"]
        cfg["scenes"].append(row)
        if s["fn"].startswith("s") and not re.search(rf"function\s+{s['fn']}\s*\(", existing):
            f = d / "scenes" / f"{k:02d}_{s['fn'][1:].lower()}.js"
            f.write_text(SCAFFOLD.format(fn=s["fn"], note=s.get("say", "描述這幕要講的一件事")), "utf-8")
            print(f"  + 鷹架 {f.name}")
    (d / "project.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"✓ 已寫入 {d / 'project.json'}（{len(cfg['scenes'])} 幕）  下一步：寫自訂場景 → build.py → sheet.py --trans")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sp = Path(a.storyboard)
    try:
        sb = json.loads(sp.read_text("utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"✗ {sp} 不是合法 JSON：第 {e.lineno} 行第 {e.colno} 欄 {e.msg}（小數要寫 0.5，不能寫 .5；不能有註解或結尾逗號）")
    errs, warns = check(sb)
    if not errs:
        print(table(sb) + "\n")
    for w in warns:
        print(f"! {w}")
    if warns:
        print("  （以上是給構思用的建議，不是規則；刻意打破就保留，交付時說一句為什麼）")
    for e in errs:
        print(f"✗ {e}")
    if errs:
        sys.exit(1)
    if a.dir and not a.preview:
        write(sb, Path(a.dir), a.force, sp.parent)


if __name__ == "__main__":
    main()
