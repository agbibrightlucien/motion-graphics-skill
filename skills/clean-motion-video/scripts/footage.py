"""Footage mode for clean-motion-video: turn raw talking-head clips into an edited,
motion-graphics short in the "split + face" style (references/footage.md).

Usage (python -I -u <skill>/scripts/footage.py <command> ...):

  ingest <dir> <clip> [<clip> ...] [--speed 1.0] [--max-gap 0.25] [--keep-fillers] [--keep-retakes] [--cut "words to remove" ...] [--cut-raw 12.3-12.6 ...]
        Normalise the clip(s) to 1080x1920 30 fps, transcribe, cut silences, fillers (um, uh, ehm...)
        and retakes (a phrase that is restarted: the last take wins), and render
        assets/footage/edit.mp4. The edit's voice is cleaned to assets/voice/full.wav and
        re-transcribed on the edit timeline (assets/footage/words.json). The face position
        is measured from one frame (plan.json "face"). Writes assets/footage/cuts.json and
        prints what was kept and dropped, so the cut can be checked before building.
  beats <dir> [--style A|B|fused] [--min 1.4] [--max 4.0] [--force]
        Split the edit's words into beats (one sentence or clause each) and write plan.json
        scenes (with a suggested "layout": split | face | cut) and timing.json for cmv.py assemble.
        Styles (references/footage.md): A = split + face (panel over a face window, head pop-out);
        B = cinematic + cutaways (full-frame face, full-screen cutaways with the voice running on);
        fused = B's face and cutaways + A's split panel for facts/numbers/lists. Saved as plan "style".
        Style A (the default) also picks the video's layouts (A1 classic, A2 flip, A4 big stage, A5 floating card,
        A6 half and half) and a look (window, ground, enter, caption): plan "variants", "look", a beat's "variant".
  face <dir>
        Re-measure the head over the whole edit (the range it moves in) and save it as plan "face".
  cutout <dir> [--quality balanced] [--all] [--force]
        Background-remove each split beat's slice of the edit (assets/footage/cut_<beat>.webm) for the
        head pop-out (--all: the whole edit as cutout.webm). ~1 frame/s on CPU: run it in the background,
        after `beats` and after the layouts are final.
  scaffold <dir> [--force]
        Write a starter compositions/<beat>.html for every beat that has none (split: panel +
        face window + pop-out; face: full-frame footage with punch-in zoom), and regenerate
        compositions/overlay.html (word captions + light-leak flashes) from timing.json.
        Never overwrites a designed beat unless --force.

After scaffold: design each beat's panel (cards, real photos), then `cmv.py assemble`, check,
snapshot, render, `cmv.py master`, `cmv.py package` as for any video.
"""
import importlib.util, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cmv", os.path.join(HERE, "cmv.py"))
cmv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmv)
load, save, snap, ffmpeg, duration, norm, opt = cmv.load, cmv.save, cmv.snap, cmv.ffmpeg, cmv.duration, cmv.norm, cmv.opt

W, H, FPS = 1080, 1920, 30
FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ehm", "hmm", "mm", "mmm", "ah", "eh"}
# Face window of the split layout (px, 1080x1920). The head pops POP px above the window's top edge.
WIN = {"x": 247, "y": 1262, "w": 586, "h": 700, "r": 40}
POP = 90
HEAD_MARGIN = 60    # px between the top of the head and the window edge when there is no pop-out
ZOOMS = [1.0, 1.12, 1.22]       # face-beat punch-ins, cycled so jump cuts read as deliberate


def flag(args, name):
    return name in args


def fdir(d, *p):
    return os.path.join(d, "assets", "footage", *p)


# ---------------------------------------------------------------- ingest
def normalise(src, dst):
    """Any phone clip -> 1080x1920, 30 fps CFR, yuv420p, AAC 48 kHz (fills the frame, crops overflow)."""
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,setsar=1"
    ffmpeg("-i", src, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", dst)


def phrases(words, gap=0.6):
    out, cur = [], []
    for i, w in enumerate(words):
        if cur and (w["start"] - cur[-1]["end"] > gap or re.search(r"[.!?]$", cur[-1]["text"])):
            out.append(cur); cur = []
        cur.append(dict(w, i=i))
    if cur:
        out.append(cur)
    return out


def find_retakes(words):
    """A phrase restarted later (same opening words within the next 3 phrases) is a retake: drop it."""
    ph = phrases(words)
    drop = set()
    for a in range(len(ph)):
        ta = [norm(w["text"]) for w in ph[a] if norm(w["text"])]
        if not ta:
            continue
        k = min(3, len(ta))
        for b in range(a + 1, min(a + 4, len(ph))):
            tb = [norm(w["text"]) for w in ph[b] if norm(w["text"])]
            if len(tb) >= k and tb[:k] == ta[:k] and len(ta) <= len(tb) + 2:
                drop |= {w["i"] for w in ph[a]}
                break
    # restarts inside running speech: "imagine you buy pay | imagine you buy something..." or
    # "and I don't know why the school is not, | and I don't know why the school is not taking..."
    toks = [norm(w["text"]) for w in words]
    i = 0
    while i < len(words):
        hit = None
        for j in range(i + 2, min(i + 16, len(words))):
            k = 0
            while j + k < len(words) and i + k < j and toks[i + k] and toks[i + k] == toks[j + k]:
                k += 1
            # 3+ repeated words is a restart; 2 only when the abandoned bit trails off ("...on Jumia or | imagine you")
            # the transcriber often stretches the word before a pause over the silence, so also judge by onsets
            pause = max(words[j]["start"] - words[j - 1]["end"], words[j]["start"] - words[j - 1]["start"] - 0.8)
            if k >= 3 or (k == 2 and (pause >= 0.7 or (len(toks[i]) >= 5 and toks[j - 1] in ("or", "and", "so", "like", "but", "the", "a")))):
                hit = j
                break
        if hit is not None and not any(re.search(r"[.!?]$", words[x]["text"]) for x in range(i, hit - 1)):
            drop |= set(range(i, hit))
            i = hit
        else:
            i += 1
    return drop, ph


FRAME = 0.01      # audio envelope resolution (s)


def envelope(wav16k):
    """dBFS per 10 ms frame of a 16 kHz mono 16-bit wav (stdlib only)."""
    import array, math, wave
    with wave.open(wav16k, "rb") as wf:
        n, sw = wf.getnframes(), wf.getsampwidth()
        data = array.array("h", wf.readframes(n)) if sw == 2 else None
    if data is None:
        return []
    hop = int(16000 * FRAME)
    out = []
    for k in range(0, len(data) - hop + 1, hop):
        seg = data[k:k + hop]
        ms = sum(x * x for x in seg) / hop
        out.append(10 * math.log10(ms / (32768.0 ** 2) + 1e-12))
    return out


def speech_threshold(env, words):
    """Loudness that counts as 'voice': ~22 dB under the median loudness inside words, never under -45 dBFS."""
    inside = []
    for w in words:
        a, b = int(w["start"] / FRAME), int(w["end"] / FRAME)
        inside += env[a:b]
    if not inside:
        return -38.0
    inside.sort()
    return max(-45.0, inside[len(inside) // 2] - 22.0)


def voiced_runs(env, a, b, thr, min_len=0.07):
    """[(start, end)] of runs louder than thr between a and b (s)."""
    runs, cur = [], None
    for k in range(max(0, int(a / FRAME)), min(len(env), int(b / FRAME))):
        if env[k] > thr:
            cur = [k, k + 1] if cur is None else [cur[0], k + 1]
        elif cur is not None:
            runs.append(cur); cur = None
    if cur is not None:
        runs.append(cur)
    return [(r[0] * FRAME, r[1] * FRAME) for r in runs if (r[1] - r[0]) * FRAME >= min_len]


def silent_gaps(env, a, b, thr, min_len=0.03):
    """[(start, end)] of quiet stretches (below thr for >= min_len) between a and b (s)."""
    out, cur = [], None
    for k in range(max(0, int(a / FRAME)), min(len(env), int(b / FRAME) + 1)):
        if env[k] < thr:
            cur = [k, k + 1] if cur is None else [cur[0], k + 1]
        elif cur is not None:
            out.append(cur); cur = None
    if cur is not None:
        out.append(cur)
    return [(g[0] * FRAME, g[1] * FRAME) for g in out if (g[1] - g[0]) * FRAME >= min_len]


def snap_edge(env, thr, t, lo, hi, side):
    """Move a cut from a transcript timestamp t to the nearest real silence in [lo, hi].
    side='start': cut late in the gap (just before the word); 'end': early in the gap (just after it)."""
    if env is None:
        return t
    gaps = silent_gaps(env, lo, hi, thr)
    if gaps:
        g = min(gaps, key=lambda g: 0 if g[0] <= t <= g[1] else min(abs(g[0] - t), abs(g[1] - t)))
        return max(g[0], g[1] - 0.04) if side == "start" else min(g[1], g[0] + 0.04)
    ks = range(max(0, int(lo / FRAME)), min(len(env), int(hi / FRAME) + 1))
    return min(ks, key=lambda k: env[k]) * FRAME if ks else t


def end_before_removed(env, thr, w, nxt, hi):
    """End a kept span that is followed by removed words. The transcriber stretches the kept word over the
    start of the removed one, so the sound after the kept word is split into bursts at pauses (>= 60 ms) and
    short trailing bursts (<= 0.2 s: an 'or', an 'I', a half word) are stripped. A real last syllable
    ('p.m.' after its silent 'p') is longer and stays."""
    lo = w["start"] - 0.1
    runs = voiced_runs(env, lo, min(hi, nxt["start"] + 0.05), thr, min_len=0.03)
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] < 0.06:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    while len(merged) > 1 and merged[-1][1] - merged[-1][0] <= 0.2 and merged[-1][0] >= w["start"] + 0.05:
        merged.pop()
    if not merged:
        return snap_edge(env, thr, w["end"] + 0.02, w["end"] - 0.08, hi, "end")
    end = merged[-1][1]
    gaps = silent_gaps(env, end - 0.01, hi + 0.2, thr, min_len=0.02)
    return min(gaps[0][1], end + 0.05) if gaps else end + 0.02


def keep_segments(words, drop, max_gap, pre=0.06, post=0.12, total=None, env=None, thr=-38.0):
    """Spans of the raw clip to keep: kept words joined when the pause between them is short, nothing dropped
    in between. With an audio envelope each span's edges move to the nearest real silence, because the
    transcriber's timestamps run ~0.1-0.2 s late: cutting on them leaves the start of a removed word
    ('or... or I always') or clips a kept one."""
    spans, prev_k = [], None
    for i, w in enumerate(words):
        if i in drop:
            continue
        if spans and prev_k == i - 1 and (w["start"] - pre) - (words[prev_k]["end"] + post) <= max_gap:
            spans[-1][1] = i
        else:
            spans.append([i, i])
        prev_k = i
    segs = []
    for i0, i1 in spans:
        w0, w1 = words[i0], words[i1]
        pw = words[i0 - 1] if i0 > 0 else None
        nw = words[i1 + 1] if i1 + 1 < len(words) else None
        if pw is not None and pw.get("manual") and nw is not None and nw.get("manual"):
            segs.append([pw["end"], nw["start"]]); continue
        if env is not None and pw is not None and pw.get("manual"):
            st = pw["end"]              # a --cut-raw edge is exact
            hi = min(w1["end"] + 0.35, (nw["end"] - 0.08) if nw else w1["end"] + 0.35)
            en = nw["start"] if (nw is not None and nw.get("manual")) else (
                end_before_removed(env, thr, w1, nw, hi) if (nw is not None and (i1 + 1) in drop)
                else snap_edge(env, thr, w1["end"] + 0.02, w1["end"] - 0.08, hi, "end"))
        elif env is not None and nw is not None and nw.get("manual"):
            lo = max(w0["start"] - 0.35, (pw["start"] + 0.08) if pw else 0.0)
            st = snap_edge(env, thr, w0["start"] - 0.02, lo, w0["start"] + 0.08, "start")
            en = nw["start"]
        elif env is not None:
            lo = max(w0["start"] - 0.35, (pw["start"] + 0.08) if pw else 0.0)
            st = snap_edge(env, thr, w0["start"] - 0.02, lo, w0["start"] + 0.08, "start")
            hi = min(w1["end"] + 0.35, (nw["end"] - 0.08) if nw else w1["end"] + 0.35)
            if nw is not None and (i1 + 1) in drop:
                # a removed word follows: the transcriber often stretches the kept word over the start of the
                # removed one (timestamps run late): end_before_removed strips that leftover
                en = end_before_removed(env, thr, w1, nw, hi)
            else:
                en = snap_edge(env, thr, w1["end"] + 0.02, w1["end"] - 0.08, hi, "end")
        else:
            st = max(0.0, w0["start"] - pre)
            en = min(w1["end"] + post, nw["start"]) if nw and (i1 + 1) in drop else w1["end"] + post
        segs.append([max(0.0, st), en])
    if total:
        segs = [[a, min(b, total)] for a, b in segs if a < total]
    out = []
    for a, b in segs:
        if out and a < out[-1][1]:
            a = out[-1][1]
        if b - a >= 2 / FPS:
            out.append([round(a, 3), round(b, 3)])
    return out


def edit_to_raw(segs, t):
    """Map a time on the edit timeline back to the raw clip."""
    acc = 0.0
    for a, b in segs:
        if t <= acc + (b - a):
            return a + (t - acc)
        acc += b - a
    return segs[-1][1] if segs else t


def check_edit(ewav16k, ewords, segs=()):
    """The 'listen back' pass over the whole edit (re-transcribed): (1) words or phrases said twice in a row
    ('or I always or I always', 'if if'): fixed automatically; (2) a short sound right at a join that no word
    covers (a leftover piece of a removed word): reported for a listen. Returns [(start, end, kind, text)]."""
    env = envelope(ewav16k)
    thr = speech_threshold(env, ewords)
    issues = []
    toks = [norm(w["text"]) for w in ewords]
    for n in (4, 3, 2, 1):
        for i in range(len(toks) - 2 * n + 1):
            if toks[i:i + n] == toks[i + n:i + 2 * n] and all(toks[i:i + n]):
                if not any(x[0] <= ewords[i]["start"] < x[1] for x in issues):
                    issues.append((ewords[i]["start"], ewords[i + n - 1]["end"] + 0.02, "repeat",
                                   " ".join(w["text"] for w in ewords[i:i + n])))
    acc, joins = 0.0, []
    for a0, b0 in segs:
        acc += b0 - a0
        joins.append(acc)
    for j in joins[:-1]:
        for ra, rb in voiced_runs(env, j - 0.3, j + 0.3, thr, min_len=0.04):
            if rb - ra <= 0.3 and not any(w["start"] - 0.12 < rb and ra < w["end"] + 0.12 for w in ewords):
                issues.append((ra, rb, "fragment", ""))
    return sorted(issues), env


def render_edit(raw, segs, dst, speed=1.0):
    """Cut raw.mp4 down to segs (with 8 ms audio fades at every join) and optionally speed it up."""
    parts, chains = [], []
    for n, (s, e) in enumerate(segs):
        d = e - s
        chains.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{n}];"
                      f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.3f}:d=0.008[a{n}];")
        parts.append(f"[v{n}][a{n}]")
    fc = "".join(chains) + "".join(parts) + f"concat=n={len(segs)}:v=1:a=1[cv][ca]"
    if abs(speed - 1) > 0.005:
        fc += f";[cv]setpts=PTS/{speed}[ov];[ca]{cmv.stretch(speed, 0)}[oa]"
        vmap, amap = "[ov]", "[oa]"
    else:
        vmap, amap = "[cv]", "[ca]"
    script = dst + ".filter.txt"
    with open(script, "w", encoding="utf-8") as f:
        f.write(fc)
    ffmpeg("-i", raw, "-/filter_complex", script, "-map", vmap, "-map", amap, "-r", str(FPS),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", dst)
    os.remove(script)


def _alpha_box(png, crop=None):
    """Bounding box (x, y, w, h) of the opaque part of a cutout PNG, via ffmpeg cropdetect (no Pillow needed)."""
    vf = (f"crop={crop}," if crop else "") + "alphaextract,cropdetect=limit=0.3:round=1:reset=0:skip=0"
    dec = ["-c:v", "libvpx-vp9"] if png.lower().endswith(".webm") else []     # the default VP9 decoder drops alpha
    r = subprocess.run(["ffmpeg", "-hide_banner", *dec, "-i", png, "-vf", vf, "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
    if not m:
        return None
    w, h, x, y = map(int, m[-1])
    return x, y, w, h


def measure_face(d, video):
    """One frame -> background-removed PNG -> head top, centre x, head width (source px)."""
    default = {"cx": 540, "top": 420, "head_w": 420}
    t = max(0.5, duration(video) * 0.3)
    frame, cut = fdir(d, "_face.png"), fdir(d, "_face_cut.png")
    ffmpeg("-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", frame)
    cmv.hf("remove-background", frame, "-o", cut, check=False)
    face = default
    body = _alpha_box(cut) if os.path.exists(cut) else None
    if body and body[3] > 100:
        x, y, w, h = body
        band = max(40, int(h * 0.10))
        head = _alpha_box(cut, f"{W}:{band}:0:{y}") or (x, 0, w, band)
        face = {"cx": head[0] + head[2] // 2, "top": y, "head_w": max(120, int(head[2] * 1.1))}
    else:
        print("note: could not find the person in the frame; using a default face position (edit plan.json \"face\")")
    for p in (frame, cut):
        try: os.remove(p)
        except OSError: pass
    return face


def measure_face_range(d, video, n=14):
    """The head over the whole edit: n frames spread over the video -> one background-removed clip ->
    the highest the head ever gets, and the full left-right range of the upper head. Returns a face dict
    that covers all of it, so a window sized for it never cuts the head when the speaker leans or sits up."""
    one = measure_face(d, video)
    dur = duration(video)
    clip, cut = fdir(d, "_range.mp4"), fdir(d, "_range_cut.webm")
    step = max(0.5, dur / (n + 1))
    sel = "+".join(f"eq(n\\,{int(round((k + 1) * step * FPS))})" for k in range(n))
    ffmpeg("-i", video, "-vf", f"select='{sel}',setpts=N/{FPS}/TB", "-an", "-frames:v", str(n), "-c:v", "libx264", "-crf", "18", clip)
    cmv.hf("remove-background", clip, "-o", cut, check=False)
    face = dict(one)
    if os.path.exists(cut):
        body = _alpha_box(cut)                                  # cropdetect with reset=0: the union over all frames
        if body and body[3] > 100:
            x, y, w, h = body
            band = max(60, int(one.get("head_w", 420) * 0.8))  # hair to eyes: the widest the head moves
            head = _alpha_box(cut, f"{W}:{band}:0:{y}")
            if head:
                face = {"cx": head[0] + head[2] // 2, "top": y, "head_w": max(one["head_w"], int(head[2] * 1.12)),
                        "one_frame": one}
    for f_ in (clip, cut):
        try: os.remove(f_)
        except OSError: pass
    return face


def cmd_face(args):
    """Re-measure the head over the whole edit and save it as plan "face" (then rebuild the scenes)."""
    d = os.path.abspath(args[0])
    plan = load(os.path.join(d, "plan.json"), {}) or {}
    plan["face"] = measure_face_range(d, fdir(d, "edit.mp4"))
    save(os.path.join(d, "plan.json"), plan)
    print(f"face over the whole edit: {plan['face']}")


def silences(wav, noise="-38dB", dur=0.3):
    """[(start, end)] of silent stretches in a file (ffmpeg silencedetect)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", f"silencedetect=noise={noise}:d={dur}", "-f", "null", "-"],
                       capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(st, en + [1e9] * (len(st) - len(en))))


def trim_to_speech(words, quiet):
    """The transcriber often stretches a word over the pause after it (or before it). Clip words to the audio."""
    out = []
    for w in words:
        s, e = w["start"], w["end"]
        for a, b in quiet:
            if s < a < e and b > a + 0.3:        # silence starts inside the word: the word really ends there
                e = max(s + 0.12, a + 0.05)
            if s < b < e and a < s + 0.05:       # the word starts inside a silence: it really starts at its end
                s = min(e - 0.12, b - 0.03)
        out.append(dict(w, start=round(s, 3), end=round(e, 3)))
    return out


def cmd_ingest(args):
    d = os.path.abspath(args[0])
    clips = [a for a in args[1:] if not a.startswith("--") and os.path.splitext(a)[1].lower() in (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp")]
    if not clips:
        raise SystemExit("give at least one video clip")
    speed = float(opt(args, "--speed", 1.0))
    max_gap = float(opt(args, "--max-gap", 0.25))
    os.makedirs(fdir(d), exist_ok=True)
    os.makedirs(os.path.join(d, "assets", "voice"), exist_ok=True)

    print(f"normalising {len(clips)} clip(s) to {W}x{H} @ {FPS} fps")
    norm_parts = []
    for n, c in enumerate(clips):
        if not os.path.exists(c):
            raise SystemExit(f"clip not found: {c}")
        p = fdir(d, f"_raw{n}.mp4")
        normalise(c, p)
        norm_parts.append(p)
    raw = fdir(d, "raw.mp4")
    if len(norm_parts) == 1:
        shutil.move(norm_parts[0], raw)
    else:
        lst = fdir(d, "_raw.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.writelines(f"file '{os.path.basename(p)}'\n" for p in norm_parts)
        ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw)
        for p in norm_parts + [lst]:
            os.remove(p)
    rdur = duration(raw)

    print("transcribing the raw take")
    rwav = fdir(d, "_raw.wav")
    ffmpeg("-i", raw, "-vn", "-ac", "1", "-ar", "16000", rwav)
    words = cmv.transcribe(d, rwav)
    if not words:
        raise SystemExit("no speech found in the footage")
    words = trim_to_speech(words, silences(rwav))
    renv = envelope(rwav)
    rthr = speech_threshold(renv, words)
    os.remove(rwav)
    save(fdir(d, "raw_words.json"), words)
    for a_i, a in enumerate(args):     # --cut-raw a-b: a stretch of the raw take to remove by time (a stutter the transcriber folded into a word)
        if a == "--cut-raw" and a_i + 1 < len(args):
            t0, t1 = (float(x) for x in args[a_i + 1].replace(":", "-").split("-"))
            words = [w for w in words if not (w["start"] >= t0 - 0.02 and w["end"] <= t1 + 0.02)]
            words.append({"text": "", "start": t0, "end": t1, "manual": True})
    words.sort(key=lambda w: w["start"])

    drop = {i for i, w in enumerate(words) if w.get("manual")}
    fillers = []
    if not flag(args, "--keep-fillers"):
        for i, w in enumerate(words):
            if norm(w["text"]) in FILLERS:
                drop.add(i); fillers.append(w["text"])
    retake_text = []
    if not flag(args, "--keep-retakes"):
        rt, ph = find_retakes([w for w in words])
        run = []
        for i in sorted(rt):
            if run and i != run[-1] + 1:
                retake_text.append(" ".join(words[x]["text"] for x in run)); run = []
            run.append(i)
        if run:
            retake_text.append(" ".join(words[x]["text"] for x in run))
        drop |= rt
    manual = []
    for a_i, a in enumerate(args):
        if a == "--cut" and a_i + 1 < len(args):
            want = [norm(t) for t in args[a_i + 1].split() if norm(t)]
            toks = [norm(w["text"]) for w in words]
            for st in range(len(words) - len(want) + 1):
                if want and toks[st:st + len(want)] == want:
                    drop |= set(range(st, st + len(want)))
                    manual.append(" ".join(w["text"] for w in words[st:st + len(want)]))
                    break
            else:
                print(f"warning: --cut phrase not found: {args[a_i + 1]!r}")
    edit = fdir(d, "edit.mp4")
    issues = []
    for attempt in range(3):     # cut -> listen back over the whole edit -> cut out what is left -> again
        segs = keep_segments(words, drop, max_gap, total=rdur, env=renv, thr=rthr)
        print(f"cutting: {len(segs)} segments kept from {rdur:.1f} s" + (f" (pass {attempt + 1})" if attempt else ""))
        render_edit(raw, segs, edit, speed)
        cwav = fdir(d, "_check.wav")
        ffmpeg("-i", edit, "-vn", "-ac", "1", "-ar", "16000", cwav)
        cwords = trim_to_speech(cmv.transcribe(d, cwav), silences(cwav))
        issues, _ = check_edit(cwav, cwords, segs)
        os.remove(cwav)
        reps = [x for x in issues if x[2] == "repeat"]
        if not reps or speed != 1.0:
            break
        new = [(round(edit_to_raw(segs, a) - 0.02, 3), round(edit_to_raw(segs, b) + 0.02, 3)) for a, b, _, _ in issues]
        for a, b, kind, txt in reps:
            print(f"  check: said twice at {a:.2f} s {txt!r}: cutting the first one")
        # a repeated phrase: drop the raw words under its first copy
        for (a, b), (_, _, kind, _) in zip(new, issues):
            if kind == "repeat":
                drop |= {i for i, w in enumerate(words) if w["start"] >= a - 0.05 and w["end"] <= b + 0.05}
    edur = duration(edit)

    print("cleaning the voice")
    ewav = fdir(d, "_edit.wav")
    ffmpeg("-i", edit, "-vn", "-ac", "2", "-ar", "44100", ewav)
    plan = load(os.path.join(d, "plan.json"), {}) or {}
    fx = dict({"punch": True}, **(plan.get("voice_fx") or {}), tighten=False)   # pauses are already cut; phone takes get the punch chain
    cmv.voice_fx(ewav, os.path.join(d, "assets", "voice", "full.wav"), fx, 1.0)
    os.remove(ewav)

    print("transcribing the edit")
    ewords = cmv.transcribe(d, os.path.join(d, "assets", "voice", "full.wav"))
    ewords = trim_to_speech(ewords, silences(os.path.join(d, "assets", "voice", "full.wav")))
    save(fdir(d, "words.json"), ewords)
    save(fdir(d, "cuts.json"), {"source": [os.path.abspath(c) for c in clips], "speed": speed, "max_gap": max_gap,
                                "raw_duration": round(rdur, 3), "edit_duration": round(edur, 3), "segments": segs,
                                "dropped_fillers": fillers, "dropped_retakes": retake_text,
                                "check": [{"t": round(a, 2), "end": round(b, 2), "kind": k, "text": t} for a, b, k, t in issues]})
    plan["face"] = measure_face_range(d, edit)        # the whole edit, not one frame: the head moves
    plan.setdefault("mode", "footage")
    plan.setdefault("palette", "ghana")
    save(os.path.join(d, "plan.json"), plan)

    span = (ewords[-1]["end"] - ewords[0]["start"]) if len(ewords) > 1 else edur
    print(f"\nraw {rdur:.1f} s -> edit {edur:.1f} s  ({len(segs)} segments, {len(ewords)} words, {len(ewords) / span * 60:.0f} wpm)")
    if fillers:
        print(f"dropped {len(fillers)} filler(s): {' '.join(fillers[:20])}")
    for t in retake_text:
        print(f"dropped retake: \"{t}\"")
    for t in manual:
        print(f"cut on request: \"{t}\"")
    print(f"face (source px): {plan['face']}")
    if issues:
        print("\nCHECK: still to fix by hand (listen at these edit times; --cut the words or raise --max-gap):")
        for a, b, k, t in issues:
            print(f"  {k} {a:.2f}-{b:.2f} s {t}")
    else:
        print("\ncheck: the whole edit was re-transcribed and scanned: no fragments, no repeated words")
    print("\nkept transcript:\n" + " ".join(w["text"] for w in ewords))


# ---------------------------------------------------------------- beats
def suggest_layout(text, n, style="A"):
    has_fact = bool(re.search(r"\d|%|\bGH|cedi|first|second|third|number|step|list|versus|vs\b", text, re.I))
    proper = len(re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]+", text)) > 0
    if style == "B":                       # face is home; things and facts go full-screen
        return "cut" if (has_fact or proper) else "face"
    if style == "fused":                   # facts -> A's split panel, named things -> B's cutaway, else face
        return "split" if has_fact else ("cut" if proper else "face")
    if n == 0:
        return "split"
    return "split" if (has_fact or proper) else "face"


def cmd_beats(args):
    d = os.path.abspath(args[0])
    lo, hi = float(opt(args, "--min", 1.4)), float(opt(args, "--max", 4.0))
    words = load(fdir(d, "words.json"))
    style_arg = opt(args, "--style", None)
    if not words:
        raise SystemExit("run `footage.py ingest` first")
    plan = load(os.path.join(d, "plan.json"), {}) or {}
    if plan.get("scenes") and not flag(args, "--force") and any(
            os.path.exists(os.path.join(d, "compositions", f"{s['id']}.html")) for s in plan["scenes"]):
        raise SystemExit("beats already designed (compositions exist); pass --force to re-split (designs are kept on disk)")
    edur = duration(fdir(d, "edit.mp4"))
    style = (style_arg or plan.get("style") or "A").strip()
    style = {"a": "A", "b": "B", "ab": "fused", "a+b": "fused", "fusion": "fused"}.get(style.lower(), style)
    plan["style"] = style

    groups, cur = [], []
    for w in words:
        cur.append(w)
        dur = cur[-1]["end"] - cur[0]["start"]
        end_s = re.search(r"[.!?]$", w["text"])
        end_c = re.search(r"[,;:]$", w["text"])
        if (end_s and dur >= lo) or (end_c and dur >= hi * 0.7) or dur >= hi:
            groups.append(cur); cur = []
    if cur:
        if groups and cur[-1]["end"] - cur[0]["start"] < lo and cur[-1]["end"] - groups[-1][0]["start"] <= hi * 1.2:
            groups[-1] += cur
        else:
            groups.append(cur)

    bounds = [0.0]
    for a, b in zip(groups, groups[1:]):
        bounds.append(snap(max(a[-1]["end"] + 0.02, b[0]["start"] - 0.06)))
    bounds.append(snap(edur))
    scenes, tscenes = [], []
    for n, g in enumerate(groups):
        bid = f"b{n + 1}"
        st, du = bounds[n], snap(bounds[n + 1] - bounds[n])
        text = " ".join(w["text"] for w in g)
        scenes.append({"id": bid, "vo": text, "layout": suggest_layout(text, n, style)})
        tscenes.append({"id": bid, "start": st, "duration": du,
                        "words": [{"text": w["text"], "t": round(w["start"] - st, 3), "end": round(w["end"] - st, 3)} for w in g]})
    # keep the rhythm: A never has 3 face beats in a row; B/fused never 3 (the face is home, but cutaways keep it moving)
    run = 0
    for s, t in zip(scenes, tscenes):
        run = run + 1 if s["layout"] == "face" else 0
        if run >= 3:
            s["layout"] = "split" if style == "A" else "cut"; run = 0
    if style in ("B", "fused") and scenes:
        scenes[-1]["layout"] = "face"; scenes[-1]["end"] = True      # last beat ends on the face (player card only if plan "player_card")
    if style == "A":
        seed = os.path.basename(d) + f"{edur:.2f}"
        nsplit = sum(1 for x in scenes if x.get("layout") == "split")
        plan.setdefault("variants", pick_variants(seed, 4 if nsplit >= 10 else 3))
        plan.setdefault("look", pick_look(seed))
        assign_variants(scenes, plan["variants"])
    plan["scenes"] = scenes
    save(os.path.join(d, "plan.json"), plan)
    save(os.path.join(d, "timing.json"), {"scenes": tscenes, "total": snap(edur),
                                          "voice_track": {"src": "assets/voice/full.wav", "at": 0.0,
                                                          "dur": round(duration(os.path.join(d, "assets", "voice", "full.wav")), 3)}})
    for s, t in zip(scenes, tscenes):
        print(f"{s['id']:5s} {t['start']:6.2f} +{t['duration']:5.2f}  {s['layout']:5s} {s.get('variant', ''):3s} {s['vo']}")
    print(f"style {style}: total {snap(edur)} s, {len(scenes)} beats. Edit \"layout\" per beat in plan.json, then run scaffold.")
    if style == "A":
        print(f"layouts this video: {', '.join(plan['variants'])}; look: {plan['look']} (edit plan \"variants\" / \"look\" / a beat's \"variant\")")


# ---------------------------------------------------------------- cutout
def cmd_cutout(args):
    """Background-remove only what the pop-out needs: each split beat's slice of the edit (cut_<beat>.webm).
    --all removes the whole edit instead (cutout.webm). CPU runs at about 1 frame/s, so this matters."""
    d = os.path.abspath(args[0])
    edit = fdir(d, "edit.mp4")
    if not os.path.exists(edit):
        raise SystemExit("run `footage.py ingest` first")
    q = opt(args, "--quality", "balanced")
    plan, timing = load(os.path.join(d, "plan.json"), {}) or {}, load(os.path.join(d, "timing.json"))
    if flag(args, "--all") or not timing or not plan.get("scenes"):
        cmv.hf("remove-background", edit, "-o", fdir(d, "cutout.webm"), "--quality", q)
        print("wrote assets/footage/cutout.webm"); return
    by_id = {e["id"]: e for e in timing["scenes"]}
    todo = [s for s in plan["scenes"] if s.get("layout", "split") == "split" and s.get("variant", "A1") in POP_VARIANTS]
    for n, s in enumerate(todo):
        e, out = by_id[s["id"]], fdir(d, f"cut_{s['id']}.webm")
        if os.path.exists(out) and not flag(args, "--force"):
            continue
        part = fdir(d, f"_part_{s['id']}.mp4")
        ffmpeg("-ss", f"{e['start']:.3f}", "-i", edit, "-t", f"{e['duration']:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", part)
        print(f"[{n + 1}/{len(todo)}] {s['id']} ({e['duration']:.1f} s)")
        cmv.hf("remove-background", part, "-o", out, "--quality", q)
        os.remove(part)
    print(f"wrote {len(todo)} beat cutout(s). Re-run scaffold for new beats; designed beats need their fk-pop block (see references/footage.md).")


# ---------------------------------------------------------------- scaffold
def window_geometry(face, pop=True):
    """Place the source video in the face window. The full head must always show (user rule):
    pop=True  -> the head rises POP px above the window (its cutout is drawn there), never cropped;
    pop=False -> no cutout for this beat, so the whole head sits INSIDE the window with a margin."""
    s = max(0.42, min(1.0, 0.56 * WIN["w"] / max(120, face.get("head_w", 420))))
    head_top = WIN["y"] - POP if pop else WIN["y"] + HEAD_MARGIN
    # the footage must reach the bottom of the frame (no gap under the window)
    s = max(s, (H - head_top) / max(200, H - face.get("top", 420)))
    vw, vh = W * s, H * s
    left = WIN["x"] + WIN["w"] / 2 - face.get("cx", 540) * s
    top = head_top - face.get("top", 420) * s
    return {"s": round(s, 4), "left": round(left, 1), "top": round(top, 1), "w": round(vw, 1), "h": round(vh, 1),
            "show": round(WIN["y"] - top, 1)}


def face_zoom(face, zoom, margin=70):
    """Cap a face-beat punch-in so the top of the head (hair, cap) never leaves the frame."""
    top = face.get("top", 420)
    oy = top + face.get("head_w", 420) * 0.55
    limit = (oy - margin) / max(1, oy - top)
    return round(min(zoom, limit), 3)


def video_tag(vid, src, start, dur, style, cls="clip"):
    return (f'<video id="{vid}" class="{cls}" src="{src}" data-start="0" data-duration="{dur}" '
            f'data-media-start="{start}" muted playsinline data-track-index="0" style="{style}"></video>')


# ---------------------------------------------------------------- style A variants
# Six layouts of the same idea (graphics + the face, full head always visible), mixed per video so the
# edits never look like one template. A video uses 3 of them, never the same one twice in a row.
VARIANTS = {
    "A1": "classic: panel on top, face window below with the head popping out",
    "A2": "flip: face window at the top, graphics below",
    "A4": "big stage: graphics fill the screen, a wide face card at the bottom-left with the head popping out",
    "A5": "floating card: full-frame face, the graphics on a card above the head (never over it)",
    "A6": "half and half: graphics edge to edge on top, the face edge to edge below",
}
POP_VARIANTS = ("A1", "A4")                     # the variants that use the head pop-out (need cut_<beat>.webm)
CAP_TOP = {"A1": 928, "A2": 1508, "A4": 838, "A6": 666}   # caption y per variant; A3/A5 carry no captions
LOOKS = {"window": ("round", "arch", "soft"), "ground": ("glow", "grid", "dots"),
         "enter": ("cut", "slide", "wipe"), "caption": ("pop", "box", "line")}


def pick_look(seed):
    """A per-video look: window shape, background, beat entrance, caption style (deterministic per project)."""
    import random
    r = random.Random(seed)
    return {k: r.choice(v) for k, v in LOOKS.items()}


def pick_variants(seed, n=3):
    import random
    r = random.Random(seed + "v")
    pool = list(VARIANTS)
    r.shuffle(pool)
    chosen = pool[:n]
    if not any(v in POP_VARIANTS for v in chosen):     # keep one pop-out layout in every video
        chosen[-1] = r.choice(POP_VARIANTS)
    return chosen


def assign_variants(scenes, variants):
    """Rotate the video's variants over its split beats; never the same layout twice in a row."""
    k, last = 0, None
    for sc in scenes:
        if sc.get("layout", "split") != "split" or sc.get("variant"):
            last = sc.get("variant", last); continue
        v = variants[k % len(variants)]
        if v == last and len(variants) > 1:
            k += 1; v = variants[k % len(variants)]
        sc["variant"] = v; last = v; k += 1
    return scenes


def place_video(face, box, head_top, min_s=0.42, max_s=1.0, head_frac=0.56):
    """Scale and place the full frame so the whole head starts at head_top, centred in box, the frame covers
    the box below head_top, and the head is never wider than the box allows."""
    hw = max(120, face.get("head_w", 420))
    s = max(min_s, min(max_s, head_frac * box["w"] / hw))
    s = max(s, (box["y"] + box["h"] - head_top) / max(200, H - face.get("top", 420)), box["w"] / W)
    top = head_top - face.get("top", 420) * s
    left = box["x"] + box["w"] / 2 - face.get("cx", 540) * s
    left = min(box["x"], max(box["x"] + box["w"] - W * s, left))      # always cover the box sideways
    return {"s": round(s, 4), "left": round(left, 1), "top": round(top, 1), "w": round(W * s, 1), "h": round(H * s, 1)}


def win_radius(look, edge):
    """CSS border-radius for a face window; edge = the side that touches the frame (bottom/top/left/none)."""
    kind = (look or {}).get("window", "round")
    r = {"round": 40, "soft": 80, "arch": 300}[kind]
    small = 40 if kind != "soft" else 80
    return {"bottom": f"{r}px {r}px 0 0", "top": f"0 0 {small}px {small}px", "left": f"0 {r}px {small}px 0",
            "none": f"{r}px {r}px {small}px {small}px"}[edge]


def variant_layout(variant, face):
    """-> (stage css transform, face window box, edge, head_top, pop) for a variant."""
    ft = face.get("top", 420)
    if variant == "A2":
        return "translateY(580px)", {"x": 220, "y": 0, "w": 640, "h": 740}, "top", 110, False
    if variant == "A3":
        return "translate(424px, 400px) scale(0.62)", {"x": 0, "y": 0, "w": 410, "h": H}, "left", None, False
    if variant == "A4":
        return "translateY(-90px)", {"x": 30, "y": 1300, "w": 540, "h": H - 1300}, "bottom", 1300 - POP, True
    if variant == "A6":
        return "translate(0, -150px) scale(0.88)", {"x": 0, "y": 940, "w": W, "h": 980}, "none", 1050, False
    return "", dict(WIN), "bottom", WIN["y"] - POP, True        # A1


def split_variant_html(bid, st, du, text, face, variant="A1", has_cut=False, words=(), cut_src=None, look=None):
    """A split beat in any A variant. Same placeholders as split_html (KICKER, fk-head, cards, SUB LABEL), so a
    project's build script fills it the same way. The stage (kicker, headline, panel, sub) is moved by a static
    transform on #<bid>-stage; animations go on its child #<bid>-in."""
    look = look or {}
    head = " ".join(text.split()[:4]).upper().rstrip(".,!?")
    ground = f'<div class="fk-ground {look.get("ground", "glow")}"></div>'
    stage_tf, box, edge, head_top, pop = variant_layout(variant, face)
    pop = pop and has_cut
    face_part, card = "", ""
    if variant == "A5":
        ft = face.get("top", 420)
        # no sub label on this layout, so the card holds kicker -> panel (292..940) and the graphics stay big
        k = round(max(0.45, min(0.74, (ft - 240) / 648)), 3)       # card ends ~90 px above the highest the head gets
        stage_tf = f"translate(0, {round(100 - k * 292)}px) scale({k})"
        card_h = round(k * 648 + 60)
        card = (f'\n    <div class="fk-glass" style="position:absolute;left:50px;right:50px;top:70px;height:{card_h}px;border-radius:44px;'
                f'background:color-mix(in srgb, var(--fk-bg) 84%, transparent);box-shadow:0 30px 80px rgba(0,0,0,0.45), inset 0 0 0 1.5px var(--fk-line)"></div>')
        face_part = video_tag(f"{bid}-v", "assets/footage/edit.mp4", st, du, f"position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover")
        ground = ""
    else:
        if variant == "A3":
            g = place_video(face, box, 0, min_s=0.3, head_frac=0.80)
            # the head must fit the 470 px column: pick the scale from the head, then start the card where the frame starts
            hw = max(120, face.get("head_w", 420))
            s3 = min(0.74 * box["w"] / hw, 1.0)      # room either side: the head moves while talking
            top = H - H * s3
            g = {"s": round(s3, 4), "left": round(box["w"] / 2 - face.get("cx", 540) * s3, 1), "top": round(top, 1),
                 "w": round(W * s3, 1), "h": round(H * s3, 1)}
            g["left"] = min(0, max(box["w"] - g["w"], g["left"]))
            box = {"x": 0, "y": max(0, round(top)), "w": box["w"], "h": H - max(0, round(top))}
        else:
            if not pop and variant in POP_VARIANTS:
                head_top = box["y"] + HEAD_MARGIN
            g = place_video(face, box, head_top)
        vid = video_tag(f"{bid}-v", "assets/footage/edit.mp4", st, du,
                        f"position:absolute;left:{round(g['left'] - box['x'], 1)}px;top:{round(g['top'] - box['y'], 1)}px;"
                        f"width:{g['w']}px;height:{g['h']}px;max-width:none")
        face_part = (f'<div id="{bid}-win" class="fk-win" style="left:{box["x"]}px;top:{box["y"]}px;width:{box["w"]}px;height:{box["h"]}px;'
                     f'border-radius:{win_radius(look, edge)}">{vid}</div>')
        if pop:
            rtop = min(int(win_radius(look, edge).split("px")[0]), box["w"] // 2)   # also over the window's curved top corners
            # the pop-out shows only the head: above the window (and over its rounded corners), within the window's width
            face_part += (f'\n    <div class="fk-pop" style="clip-path:inset(0 {W - box["x"] - box["w"]}px {H - min(H, box["y"] + rtop)}px {box["x"]}px)">'
                          + video_tag(f"{bid}-c", cut_src or "assets/footage/cutout.webm", 0 if cut_src else st, du,
                                      f"position:absolute;left:{g['left']}px;top:{g['top']}px;width:{g['w']}px;height:{g['h']}px;max-width:none")
                          + "</div>")
    enter = look.get("enter", "cut")
    ejs = {"slide": f'tl.fromTo($("#{bid}-in"), {{ x: 70, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.3, ease: "expo.out" }}, 0);',
           "wipe": f'tl.fromTo($("#{bid}-in"), {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.35, ease: "power3.out" }}, 0);',
           "cut": ""}[enter]
    face_first = variant == "A5"
    hide_sub = f"\n    #{bid}-sub {{ display: none; }}" if variant == "A5" else ""
    stage = (f'<div id="{bid}-stage" style="position:absolute;inset:0;transform-origin:{"540px 0" if variant in ("A5", "A6") else "0 0"};'
             f'transform:{stage_tf or "none"}">\n      <div id="{bid}-in" style="position:absolute;inset:0">\n'
             f'      <div id="{bid}-kick" class="fk-kicker">KICKER</div>\n'
             f'      <h1 id="{bid}-head" class="fk-head">{head} <b>WORD</b></h1>\n'
             f'      <div id="{bid}-panel" class="fk-panel">\n      <!-- cards go here -->\n      </div>\n'
             f'      <div id="{bid}-sub" class="fk-sub">SUB LABEL</div>\n      </div>\n    </div>')
    body = (f'    {face_part}{card}\n    {stage}' if face_first else f'    {ground}\n    {stage}\n    {face_part}')
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; background: var(--fk-bg); }}{hide_sub}
  </style>
  <div id="root" data-composition-id="{bid}" data-width="{W}" data-height="{H}" data-variant="{variant}">
    <!-- STYLE {variant}: {VARIANTS.get(variant, "")}. Fill KICKER, the headline, the cards and SUB LABEL as for any split beat. -->
{body}
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="{bid}"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({{ paused: true }});
      // spoken words (scene-local s): {", ".join(f"{w['text']}@{w['t']}" for w in words)}
      {ejs}
      CM.decode(tl, $("#{bid}-head"), 0.0);
      CM.blurIn(tl, $("#{bid}-kick"), 0.0, {{ dur: 0.25 }});
      CM.blurIn(tl, $("#{bid}-sub"), 0.3, {{ dur: 0.25 }});
      tl.fromTo(root, {{ opacity: 1 }}, {{ opacity: 1, duration: {du} }}, 0);
      window.__timelines["{bid}"] = tl;
    }})();
  </script>
</template>
'''


def split_html(bid, st, du, text, g, has_cut, words=(), cut_src=None, variant=None, face=None, look=None):
    if face is not None and (variant or look):
        return split_variant_html(bid, st, du, text, face, variant or "A1", has_cut, words, cut_src, look)
    head = " ".join(text.split()[:4]).upper().rstrip(".,!?")
    win_vid = video_tag(f"{bid}-v", "assets/footage/edit.mp4", st, du,
                        f"position:absolute;left:{g['left'] - WIN['x']}px;top:{g['top'] - WIN['y']}px;width:{g['w']}px;height:{g['h']}px;max-width:none")
    pop = ""
    if has_cut:
        pop = (f'\n    <!-- head pop-out: the cutout, same placement, shown only above the window\'s top edge -->\n'
               f'    <div class="fk-pop" style="clip-path:inset(0 0 {H - WIN["y"]}px 0)">'
               + video_tag(f"{bid}-c", cut_src or "assets/footage/cutout.webm", 0 if cut_src else st, du,
                           f"position:absolute;left:{g['left']}px;top:{g['top']}px;width:{g['w']}px;height:{g['h']}px;max-width:none")
               + "</div>")
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
  </style>
  <div id="root" data-composition-id="{bid}" data-width="{W}" data-height="{H}">
    <div class="fk-ground"></div>
    <!-- PANEL: say what the line says. Kicker + headline (one accent word), then cards from
         references/footage.md: fk-stat, fk-check, fk-photo (real images of what is named), fk-node. -->
    <div id="{bid}-kick" class="fk-kicker">KICKER</div>
    <h1 id="{bid}-head" class="fk-head">{head} <b>WORD</b></h1>
    <div id="{bid}-panel" class="fk-panel">
      <!-- cards go here -->
    </div>
    <div id="{bid}-sub" class="fk-sub">SUB LABEL</div>
    <!-- FACE WINDOW (do not move: the overlay's captions and the pop-out assume it) -->
    <div id="{bid}-win" class="fk-win">{win_vid}</div>{pop}
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="{bid}"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({{ paused: true }});
      // spoken words (scene-local s): {", ".join(f"{w['text']}@{w['t']}" for w in words)}
      CM.decode(tl, $("#{bid}-head"), 0.0);
      CM.blurIn(tl, $("#{bid}-kick"), 0.0, {{ dur: 0.25 }});
      CM.blurIn(tl, $("#{bid}-sub"), 0.3, {{ dur: 0.25 }});
      window.__timelines["{bid}"] = tl;
    }})();
  </script>
</template>
'''


def face_html(bid, st, du, zoom, face):
    zoom = face_zoom(face, zoom)
    ox, oy = face.get("cx", 540), face.get("top", 420) + face.get("head_w", 420) * 0.55
    vid = video_tag(f"{bid}-v", "assets/footage/edit.mp4", st, du, f"position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover")
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; background: #000; }}
    /* punch-in: a static zoom on the untimed wrapper (never on the timed video) */
    #{bid}-zoom {{ position: absolute; inset: 0; transform-origin: {ox}px {round(oy)}px; transform: scale({zoom}); }}
  </style>
  <div id="root" data-composition-id="{bid}" data-width="{W}" data-height="{H}">
    <div id="{bid}-zoom">{vid}</div>
    <!-- optional: one quoted word or a real photo popping in beside the face (references/footage.md) -->
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="{bid}"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo($("#{bid}-zoom"), {{ opacity: 1 }}, {{ opacity: 1, duration: {du} }}, 0);
      window.__timelines["{bid}"] = tl;
    }})();
  </script>
</template>
'''


def bubble_geometry(face, size=300):
    """Round face bubble (style B, over cutaways): the whole head inside the circle, face a little below centre."""
    s = max(0.2, min(0.9, 0.62 * size / max(120, face.get("head_w", 420))))
    head_top = size * 0.12
    return {"s": round(s, 4), "left": round(size / 2 - face.get("cx", 540) * s, 1), "top": round(head_top - face.get("top", 420) * s, 1),
            "w": round(W * s, 1), "h": round(H * s, 1)}


def cut_html(bid, st, du, text, face, words=(), kind="photo", bubble=False):
    """Full-screen cutaway (style B / fused): the face is hidden, the voice runs on. kind: photo | board."""
    head = " ".join(text.split()[:3]).upper().rstrip(".,!?")
    if kind == "board":
        body = (f'<div class="fk-board"></div>\n'
                f'    <div id="{bid}-title" class="fk-btitle">{head}</div>\n'
                f'    <div id="{bid}-list" class="fk-blist">\n'
                f'      <!-- fk-bpill labels, fk-bline text lines, fk-chip stacks: one per spoken item -->\n'
                f'    </div>')
        js = f'CM.blurIn(tl, $("#{bid}-title"), 0.0, {{ dur: 0.3 }});'
    else:
        body = (f'<div class="fk-cutbg"></div>\n'
                f'    <div id="{bid}-media" class="fk-full"><img src="assets/images/REPLACE.jpg" alt="" /></div>\n'
                f'    <div class="fk-shade"></div>\n'
                f'    <div id="{bid}-spec" class="fk-spec">{head}</div>')
        js = (f'CM.push(tl, $("#{bid}-media"), 0, {du});   // slow push-in on the real photo\n'
              f'      CM.blurIn(tl, $("#{bid}-spec"), 0.3, {{ dur: 0.35, y: 30 }});')
    bub = ""
    if bubble:
        g = bubble_geometry(face)
        bub = (f'\n    <div id="{bid}-bub" class="fk-bubble">'
               + video_tag(f"{bid}-v", "assets/footage/edit.mp4", st, du,
                           f"position:absolute;left:{g['left']}px;top:{g['top']}px;width:{g['w']}px;height:{g['h']}px;max-width:none")
               + "</div>")
        js += f'\n      CM.pop(tl, $("#{bid}-bub"), 0.15, {{ from: 0.5 }});'
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
  </style>
  <div id="root" data-composition-id="{bid}" data-width="{W}" data-height="{H}">
    <!-- CUTAWAY: show the real thing this line names, full screen (the voice carries on). -->
    {body}{bub}
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="{bid}"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({{ paused: true }});
      // spoken words (scene-local s): {", ".join(f"{w['text']}@{w['t']}" for w in words)}
      {js}
      tl.fromTo(root, {{ opacity: 1 }}, {{ opacity: 1, duration: {du} }}, 0);
      window.__timelines["{bid}"] = tl;
    }})();
  </script>
</template>
'''


def player_card(channel):
    """Style B end card: a music-player style 'What's next?' card (top half), the face stays below."""
    return ('<div id="end-card" class="fk-player"><div class="fk-ptitle">What\'s next?</div>'
            f'<div class="fk-pname">{channel}</div>'
            '<div class="fk-pctrl"><span class="fk-pskip">&#9664;</span><span class="fk-pbtn"><i></i><i></i></span><span class="fk-pskip">&#9654;</span></div>'
            '<div class="fk-pfollow">Follow for the next one</div></div>')


def overlay_html(timing, plan):
    """Word captions (n words at a time) placed per layout, plus light-leak flashes on flagged beats."""
    layouts = {s["id"]: s.get("layout", "split") for s in plan.get("scenes", [])}
    variants = {s["id"]: s.get("variant", "A1") for s in plan.get("scenes", [])}
    capstyle = (plan.get("look") or {}).get("caption", "pop")
    cap = plan.get("captions", {}) if isinstance(plan.get("captions"), dict) else {}
    style = plan.get("style", "A")
    gold = style in ("B", "fused")
    nwords, off = int(cap.get("words", 3 if gold else 1)), cap.get("off", False)
    on_face = cap.get("face", False)      # full-face beats stay clean by default (the face carries them)
    chunks = []
    for e in timing["scenes"]:
        if layouts.get(e["id"], "split") == "face" and not on_face:
            continue
        if layouts.get(e["id"], "split") == "split" and variants.get(e["id"]) in ("A3", "A5"):
            continue                      # side-by-side and floating-card layouts carry no captions (no clear spot)
        ws = e.get("words", [])
        groups_, cur_ = [], []
        for w in ws:                      # n words per caption, but break early at punctuation
            cur_.append(w)
            if len(cur_) >= nwords or re.search(r"[.,!?;:]$", w["text"]):
                groups_.append(cur_); cur_ = []
        if cur_:
            groups_.append(cur_)
        for grp in groups_:
            chunks.append({"text": " ".join(w["text"] for w in grp).strip(".,"), "t": round(e["start"] + grp[0]["t"], 3),
                           "end": round(e["start"] + grp[-1]["end"], 3), "layout": layouts.get(e["id"], "split"),
                           "send": round(e["start"] + e["duration"], 3), "variant": variants.get(e["id"], "A1")})
    spans, tweens = [], []
    for n, c in enumerate(chunks):
        nxt = chunks[n + 1]["t"] if n + 1 < len(chunks) else c["end"] + 0.4
        off_t = round(min(nxt, c["end"] + 0.6, c["send"]), 3)     # never spill into the next beat (it may be a face shot)
        top = {"split": CAP_TOP.get(c.get("variant", "A1"), 928), "cut": 1380}.get(c["layout"], 1330)
        txt = re.sub(r"[<>&]", "", c["text"])
        cls = "fk-cap fk-gold" if gold else ("fk-cap" if capstyle == "pop" else f"fk-cap fk-cap-{capstyle}")
        spans.append(f'    <div id="cap{n}" class="{cls}" style="top:{top}px"><span class="fk-capbox">{txt}</span></div>')
        tweens.append(f'      tl.fromTo($("#cap{n}"), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.01 }}, {max(0, c["t"] - 0.03):.3f});\n'
                      f'      tl.fromTo($("#cap{n}"), {{ opacity: 1 }}, {{ opacity: 0, duration: 0.01, immediateRender: false }}, {max(c["t"], off_t - 0.02):.3f});')
    leaks = []
    for e, s in zip(timing["scenes"], plan.get("scenes", [])):
        if s.get("flash"):
            leaks.append(e["start"])
    lspans = [f'    <div id="leak{n}" class="fk-leak"></div>' for n in range(len(leaks))]
    ltweens = [f'      tl.fromTo($("#leak{n}"), {{ opacity: 0, scale: 1.1 }}, {{ opacity: 0.9, scale: 1, duration: 0.12, ease: "power2.out" }}, {max(0, t - 0.08):.3f});\n'
               f'      tl.fromTo($("#leak{n}"), {{ opacity: 0.9 }}, {{ opacity: 0, duration: 0.3, ease: "power2.in", immediateRender: false }}, {t + 0.06:.3f});'
               for n, t in enumerate(leaks)]
    body = "\n".join(([] if off else spans) + lspans)
    tw = "\n".join(([] if off else tweens) + ltweens)
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; pointer-events: none; }}
  </style>
  <!-- generated by footage.py scaffold from timing.json: captions + flashes. Re-run scaffold to refresh; don't hand-edit. -->
  <div id="root" data-composition-id="overlay" data-width="{W}" data-height="{H}">
{body}
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="overlay"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({{ paused: true }});
{tw}
      tl.fromTo(root, {{ opacity: 1 }}, {{ opacity: 1, duration: {timing["total"]} }}, 0);
      window.__timelines["overlay"] = tl;
    }})();
  </script>
</template>
'''


def ensure_kit(d, plan):
    """Footage CSS + kit helpers in the project, palette on the root."""
    tpl = os.path.join(cmv.SKILL, "template", "assets")
    shutil.copy2(os.path.join(tpl, "footage-kit.css"), os.path.join(d, "assets", "footage-kit.css"))
    kit = os.path.join(d, "assets", "cm-kit.js")
    if not os.path.exists(kit) or "CM.decode" not in open(kit, encoding="utf-8").read():
        shutil.copy2(os.path.join(tpl, "cm-kit.js"), kit)
    idx = os.path.join(d, "index.html")
    s = open(idx, encoding="utf-8").read()
    if "footage-kit.css" not in s:
        s = s.replace('<link rel="stylesheet" href="assets/cm-kit.css" />',
                      '<link rel="stylesheet" href="assets/cm-kit.css" />\n    <link rel="stylesheet" href="assets/footage-kit.css" />')
    pal = plan.get("palette", "ghana")
    if "data-palette=" in s:
        s = re.sub(r'data-palette="[^"]*"', f'data-palette="{pal}"', s, count=1)
    else:
        s = s.replace('data-composition-id="main"', f'data-composition-id="main"\n      data-palette="{pal}"', 1)
    open(idx, "w", encoding="utf-8").write(s)


def cmd_scaffold(args):
    d = os.path.abspath(args[0])
    plan, timing = load(os.path.join(d, "plan.json")), load(os.path.join(d, "timing.json"))
    if not timing or not plan.get("scenes"):
        raise SystemExit("run `footage.py beats` first")
    ensure_kit(d, plan)
    face = plan.get("face") or {"cx": 540, "top": 420, "head_w": 420}
    g = window_geometry(face)
    has_cut = os.path.exists(fdir(d, "cutout.webm"))
    if not has_cut and not any(f.startswith("cut_") for f in os.listdir(fdir(d))):
        print("note: no cutouts yet (footage.py cutout), so split beats get no head pop-out")
    by_id = {e["id"]: e for e in timing["scenes"]}
    os.makedirs(os.path.join(d, "compositions"), exist_ok=True)
    nz, wrote = 0, 0
    for s in plan["scenes"]:
        e = by_id[s["id"]]
        p = os.path.join(d, "compositions", f"{s['id']}.html")
        if os.path.exists(p) and not flag(args, "--force"):
            continue
        if s.get("layout") == "cut":
            html = cut_html(s["id"], e["start"], e["duration"], s["vo"], face, e.get("words", []), s.get("cut", "photo"), s.get("bubble", False))
        elif s.get("layout") == "face":
            html = face_html(s["id"], e["start"], e["duration"], s.get("zoom", ZOOMS[nz % len(ZOOMS)]), face); nz += 1
            if s.get("end") and plan.get("player_card"):     # off by default: the user disliked the "What's next?" card
                html = html.replace("<!-- optional: one quoted word or a real photo popping in beside the face (references/footage.md) -->",
                                    player_card(plan.get("player_line") or (plan.get("channel") or {}).get("name", "Follow me")))
                html = html.replace("      window.__timelines", '      CM.pop(tl, $("#end-card"), 0.3, { from: 0.85, ease: "expo.out", dur: 0.45 });\n      window.__timelines')
        else:
            beat_cut = os.path.exists(fdir(d, f"cut_{s['id']}.webm"))
            gg = window_geometry(face, pop=bool(has_cut or beat_cut))
            html = split_html(s["id"], e["start"], e["duration"], s["vo"], gg, has_cut or beat_cut, e.get("words", []),
                              f"assets/footage/cut_{s['id']}.webm" if beat_cut else None,
                              s.get("variant"), face, plan.get("look"))
        open(p, "w", encoding="utf-8").write(html); wrote += 1
    open(os.path.join(d, "compositions", "overlay.html"), "w", encoding="utf-8").write(overlay_html(timing, plan))
    ov = [o for o in plan.get("overlays", []) if o.get("id") != "overlay"]
    ov.append({"id": "overlay", "src": "compositions/overlay.html", "start": 0, "duration": timing["total"]})
    plan["overlays"] = ov
    save(os.path.join(d, "plan.json"), plan)
    print(f"wrote {wrote} beat file(s) + compositions/overlay.html (captions{' + flashes' if any(x.get('flash') for x in plan['scenes']) else ''}).")
    print(f"face window geometry: {g}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"ingest": cmd_ingest, "beats": cmd_beats, "cutout": cmd_cutout, "scaffold": cmd_scaffold, "face": cmd_face}[cmd](rest)
