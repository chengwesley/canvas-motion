"""旁白與字幕的共用邏輯（voice.py、build.py、storyboard.py 都用這份，排出來的時間才會一致）。

每幕的 vo 可以寫成：
  "vo": "一句旁白"
  "vo": ["第一句", "第二句"]
  "vo": [{ "say": "念法（數字、英文怎麼念）", "sub": "字幕（預設同 say）", "at": 2, "file": "voice/我錄的.wav" }]
at 是這句從本幕第幾拍開始（選填；沒寫就接在上一句後面）。file 是使用者自己錄的音檔（選填）。
project.json 頂層 voice 設定排程：{ "lead": .35, "gap": .35, "tail": .45, "subs": true, "duck": .28 }
"""
import hashlib, math, re

LEAD, GAP, TAIL = .35, .35, .45
SUB_MAX = 16                                  # 一條字幕最多幾個字（CJK）；英文約 2 倍字元
SPLIT = re.compile(r"(?<=[，。！？；：、,.!?;:])")
CJK = re.compile(r"[⺀-鿿豈-﫿]")
PUNCT = re.compile(r"[，。、：；！？「」『』《》（）\s,.!?:;\"'…—\-]")


def items(scene):
    """把一幕的 vo 正規化成 [{say, sub, at, file}]。"""
    vo = scene.get("vo")
    if not vo:
        return []
    out = []
    for v in (vo if isinstance(vo, list) else [vo]):
        v = {"say": v} if isinstance(v, str) else dict(v)
        if not v.get("say") and not v.get("file"):
            continue
        v.setdefault("say", v.get("sub", ""))
        v.setdefault("sub", v["say"])
        out.append(v)
    return out


def line_id(si, k):
    return f"{si:02d}_{k}"


def key(engine, voice, rate, it):
    raw = "|".join(str(x) for x in (engine, voice, rate, it.get("say", ""), it.get("file", "")))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def spoken(s):
    return PUNCT.sub("", s)


def estimate(s, cps=4.5):
    """沒產生音檔前估計念多久：中文每秒約 4.5 字，英文每秒約 2.6 個字。"""
    cjk = len(CJK.findall(s)); words = len(re.findall(r"[A-Za-z0-9]+", s))
    return cjk / cps + words / 2.6 + .3


def layout(cfg, bar, beat, durs):
    """排出每句的時間。durs[(si, k)] = 秒數（沒有就用估計值）。
    回傳 (lines, overflow)：lines 是 [{id, s, k, t0, t1, sub}]（t0/t1 為整支片的絕對秒數），
    overflow 是 {幕序: 需要的小節數}（旁白放不下時）。"""
    V = cfg.get("voice") or {}
    lead, gap, tail = V.get("lead", LEAD), V.get("gap", GAP), V.get("tail", TAIL)
    lines, overflow, start = [], {}, 0.0
    for si, sc in enumerate(cfg["scenes"]):
        dur = sc.get("bars", 2) * bar
        t = lead
        for k, it in enumerate(items(sc)):
            d = durs.get((si, k)) or estimate(it["say"])
            t0 = it["at"] * beat if isinstance(it.get("at"), (int, float)) else t
            lines.append({"id": line_id(si, k), "s": si, "k": k, "t0": round(start + t0, 3), "t1": round(start + t0 + d, 3), "sub": it["sub"]})
            t = t0 + d + gap
        if items(sc) and t - gap + tail > dur + 1e-6:
            overflow[si] = math.ceil((t - gap + tail) / bar - 1e-6)
        start += dur
    return lines, overflow


def chunks(sub, t0, t1):
    """把一句字幕切成幾條（先依標點，太長再依空白；每條不超過 SUB_MAX 字），時間依字數比例分配。句末的，。不顯示。
    原文的空白（例如「上傳 PDF 文件」）原樣保留。"""
    segs = []
    for seg in [x for x in SPLIT.split(sub) if x]:
        lim = SUB_MAX if CJK.search(seg) else SUB_MAX * 2
        if len(seg) <= lim:
            segs.append(seg); continue
        piece = ""
        for w in re.split(r"(?<=\s)", seg):          # 依空白再切，保留空白本身
            if piece and len(piece) + len(w) > lim:
                segs.append(piece); piece = w
            else:
                piece += w
        if piece:
            segs.append(piece)
    hard = []
    for seg in segs:                                 # 沒有標點也沒有空白的長句：平均切成幾段
        lim = SUB_MAX if CJK.search(seg) else SUB_MAX * 2
        k = math.ceil(len(seg.strip()) / lim)
        hard += [seg] if k <= 1 else [seg[round(i * len(seg) / k):round((i + 1) * len(seg) / k)] for i in range(k)]
    segs = hard
    parts, cur = [], ""
    for seg in segs:
        lim = SUB_MAX if CJK.search(cur + seg) else SUB_MAX * 2
        if cur and len(cur.strip()) + len(seg.strip()) > lim:
            parts.append(cur); cur = seg
        else:
            cur += seg
    if cur.strip():
        parts.append(cur)
    out, n, acc = [], sum(max(1, len(spoken(p))) for p in parts) or 1, 0
    for p in parts:
        w = max(1, len(spoken(p)))
        a = t0 + (t1 - t0) * acc / n; acc += w; b = t0 + (t1 - t0) * acc / n
        out.append([round(a, 3), round(b, 3), re.sub(r"[，。,、；;]+$", "", p.strip())])
    return out


def srt(lines):
    """layout() 排好的句子 → .srt 文字。"""
    return srt_text([c for ln in lines for c in chunks(ln["sub"], ln["t0"], ln["t1"])])


def srt_text(rows):
    """[[起, 訖, 字幕], …] → .srt 文字。"""
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    ends = [min(b + .15, rows[i + 1][0]) if i + 1 < len(rows) else b + .15 for i, (_, b, _) in enumerate(rows)]   # 不跟下一條重疊
    return "\n".join(f"{i + 1}\n{ts(a)} --> {ts(e)}\n{s}\n" for i, ((a, _, s), e) in enumerate(zip(rows, ends)))
