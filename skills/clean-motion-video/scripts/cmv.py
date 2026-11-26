"""clean-motion-video pipeline helper.

Usage (run with `python -I -u <skill>/scripts/cmv.py <command> ...`; `python3` on macOS/Linux):

  setup [--test]
        Check prerequisites (Python, Node.js, ffmpeg, HyperFrames) and finish the SFX kit. Run once after install.
  hf <any hyperframes command...>
        Run the HyperFrames CLI (installed skill launcher, else npx hyperframes@pinned) in the current folder,
        e.g. `cmv.py hf check`, `cmv.py hf snapshot --at 1,3`, `cmv.py hf render -o renders/x.mp4 --workers 2`.

  new <dir> [--format vertical|landscape|square] [--theme light] [--title "..."]
        Scaffold a HyperFrames project from the skill template.
  voice <dir> [--file my_voiceover.mp3]
        Make or import the voiceover and write timing.json (scene starts/durations
        + per-word times). Sources, in order of precedence:
          --file / plan "voice_file"   a recording the user supplies (one take)
          plan "engine": "gemini"      Google Gemini TTS (needs GEMINI_API_KEY), one take
          plan "take": "full"          Kokoro, whole script in one take
          default                      Kokoro, one clip per scene (cached per line)
        One-take sources are cleaned ("voice_fx"), transcribed, and cut into scenes:
        by the scenes' "vo" text when plan.json has scenes, else automatically by
        sentence (the scenes are then written into plan.json).
  voices <outdir> [--engine kokoro|gemini] [--speed 1.1] [--text "..."] [--only a,b]
        Audition board: the same ~10 s line in every voice + index.html player.
  import <dir> <audio>   (alias of: voice <dir> --file <audio>)
  chapters <dir> [--size 75] [--at s20,s41,...]
        Long films: cut a one-take film into chapter projects (<dir>/chapters/chNN),
        each with its slice of the voice and its scenes, built and rendered on its own.
  cta <dir> [--kind subscribe|follow] [--at auto|SECONDS] [--channel NAME] [--sub TAGLINE] [--line TEXT]
      [--avatar logo.png] [--color #hex]
        Organic subscribe/follow overlay (cursor taps Subscribe, then the bell). Long films: auto = a calm
        section start ~1/3 in (routes into the right chapter); shorts: the last seconds.
  thumb <dir> --title "WORDS<br><b>ACCENT</b>" [--kicker TEXT] [--frame SECONDS|--image FILE] [--sticker "$4.12" --sticker-label TEXT]
        YouTube thumbnail 1280x720 -> publish/thumbnail-<name>.png
  tiktok <dir> --parts "s1..s19|s63..s82" --titles "T1|T2" [--captions "C1|C2"] [--landscape-only]
        Ready-to-post TikTok parts from a long film (no new render): 9:16 framed (PART N + title + handle) in
        publish/tiktok-ready/ as "Part N - <title>.mp4" + caption .txt; plain landscape cuts in publish/tiktok/
  chapterlist <dir>
        YouTube chapter timestamps for a chaptered film
  sfxboard <outdir>
        Listen to the SFX kit by role group (index.html + one MP3 with spoken group names).
  concat <dir>
        Join chapters/chNN/renders/chNN.mp4 into renders/<slug>.mp4 (then `master`).
  assemble <dir>
        Rewrite index.html's scene hosts, voice tracks and SFX tracks from
        plan.json + timing.json, and set the root duration.
  master <dir> <input.mp4> [--lufs -14]
        Loudness-normalise a render for social (video stream copied).
  breakdown <dir> <render.mp4> [--caption "Just Sfx"]
        Build a vertical "sound design breakdown" project (render on top,
        labelled SFX timeline with a moving playhead below) in <dir>-breakdown.

plan.json (written by Claude per video):
{
  "title": "Compound interest",
  "format": "vertical",            // vertical 1080x1920 | landscape 1920x1080 | square 1080x1080
  "theme": "light",
  "voice": "af_heart", "speed": 1.1,       // Kokoro id, or a Gemini voice name with "engine": "gemini"
  "engine": "kokoro",                      // kokoro | gemini
  "voice_style": "...",                    // gemini only: how to say it (tone direction)
  "voice_file": null,                      // path to the user's own recording (one take)
  "voice_fx": {"energize": true, "tighten": true, "tempo": "auto", "pitch": 0},
  "music": null,                   // or {"file": "assets/music/x.mp3", "volume": 0.12}
  "scenes": [
    {"id": "hook", "vo": "What if your money worked while you slept?", "min": 2.0, "pad": 0.25},
    {"id": "logo", "min": 1.6}       // no vo: lasts "min" seconds
  ],
  "sfx": [ {"scene": "hook", "t": 0.20, "sound": "pop"},  // t is scene-local seconds = the
           {"scene": "logo", "t": 0.00, "sound": "magic-whoosh", "volume": 0.5} ]   // visual moment
}
"""
import json, os, re, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL, "template")
KIT = os.path.join(SKILL, "assets", "sfx")
FORMATS = {"vertical": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}
FPS = 30
# HyperFrames CLI version this skill is tested with. Override with HYPERFRAMES_STANDALONE_CLI_VERSION=latest
# (or another exact version) once you've checked a newer release.
HF_PIN = "0.9.97"
# Where agents install skills (global + project). Used to find the HyperFrames launcher and media library.
SKILL_ROOTS = [os.path.dirname(SKILL)] + [os.path.join(os.path.expanduser("~"), p) for p in (
    ".claude/skills", ".agents/skills", ".codex/skills", ".gemini/config/skills", ".gemini/antigravity/skills",
    ".gemini/skills", ".cursor/skills", ".copilot/skills", ".config/opencode/skills", ".codeium/windsurf/skills")] + [
    os.path.join(os.getcwd(), p) for p in (".claude/skills", ".agents/skills", ".codex/skills", ".cursor/skills",
                                           ".gemini/skills", ".windsurf/skills")]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # every line shows up live


def find_skill_file(*rel):
    """First existing <skill-root>/<rel...> across all agents' skill folders, or None."""
    for root in SKILL_ROOTS:
        p = os.path.join(root, *rel)
        if os.path.exists(p):
            return p
    return None


def hf_command():
    """How to run HyperFrames: $HF_CLI, else an installed HyperFrames skill's launcher, else npx (pinned)."""
    if os.environ.get("HF_CLI"):
        return ["node", os.environ["HF_CLI"]]
    launcher = find_skill_file("hyperframes", "scripts", "plugin-cli.mjs")
    if launcher and not os.environ.get("CMV_FORCE_NPX"):
        return ["node", launcher]
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("HyperFrames needs Node.js 22+ (npx not found). Install Node.js, then retry.")
    ver = os.environ.get("HYPERFRAMES_STANDALONE_CLI_VERSION", HF_PIN)
    return [npx, "--yes", f"hyperframes@{ver}"]


def hf(*args, cwd=None, check=True):
    """Run the HyperFrames CLI, streaming its output live (long jobs should be watchable)."""
    env = dict(os.environ)
    # Kokoro TTS needs a real Python (the Windows Store "python" alias fails when spawned from node).
    env.setdefault("HYPERFRAMES_PYTHON", sys.executable)
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("HYPERFRAMES_STANDALONE_CLI_VERSION", HF_PIN)   # the launcher honours this pin too
    print(f"$ hyperframes {' '.join(a if len(a) < 80 else a[:77] + '...' for a in args)}", flush=True)
    p = subprocess.Popen([*hf_command(), *args], cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", bufsize=1)
    lines = []
    for line in p.stdout:
        lines.append(line)
        print("  " + line.rstrip(), flush=True)
    p.wait()
    if check and p.returncode != 0:
        raise SystemExit(f"hyperframes {args[0]} failed (exit {p.returncode})")
    p.stdout_text = "".join(lines)
    return p


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def snap(t):
    return round(round(t * FPS) / FPS, 3)


# ---------------------------------------------------------------- new
def cmd_new(args):
    d = os.path.abspath(args[0])
    fmt = opt(args, "--format", "vertical")
    theme = opt(args, "--theme", "light")
    title = opt(args, "--title", os.path.basename(d))
    if os.path.exists(os.path.join(d, "index.html")):
        raise SystemExit(f"{d} already has index.html; not overwriting")
    parent, name = os.path.split(d)
    os.makedirs(parent, exist_ok=True)
    hf("init", name, "--skip-skills", "--skill=clean-motion-video", cwd=parent)
    w, h = FORMATS[fmt]
    for root, _, files in os.walk(TEMPLATE):
        rel = os.path.relpath(root, TEMPLATE)
        os.makedirs(os.path.join(d, rel), exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(d, rel, f))
    idx = os.path.join(d, "index.html")
    s = open(idx, encoding="utf-8").read()
    s = s.replace("__W__", str(w)).replace("__H__", str(h)).replace("__THEME__", theme).replace("__TITLE__", title)
    open(idx, "w", encoding="utf-8").write(s)
    for sub in ("compositions", "renders", os.path.join("assets", "sfx"), os.path.join("assets", "voice")):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    if not os.path.exists(os.path.join(d, "plan.json")):
        save(os.path.join(d, "plan.json"), {"title": title, "format": fmt, "theme": theme, "voice": "af_heart",
                                            "speed": 1.1, "music": None, "scenes": [], "sfx": []})
    print(f"created {d} ({fmt} {w}x{h}, theme {theme})")


# ---------------------------------------------------------------- voice helpers
# Presence/"radio" chain that lifts a flat or dull read: trim rumble, a little less
# boxiness, +3 dB presence, a touch of air, gentle compression.
ENERGIZE = ("highpass=f=75,equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=3,"
            "equalizer=f=9500:t=q:w=1:g=2,acompressor=threshold=-21dB:ratio=3:attack=5:release=80:makeup=2")
TIGHTEN = ("silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.02:"
           "stop_periods=-1:stop_duration=0.38:stop_threshold=-48dB:stop_silence=0.28")


def ffmpeg(*a):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)


_RB = None


def stretch(tempo, pitch_semitones):
    """Tempo change that keeps pitch (+ optional pitch shift): rubberband if this ffmpeg has it, else atempo."""
    global _RB
    if _RB is None:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        _RB = " rubberband " in out
    p = 2 ** (pitch_semitones / 12)
    if _RB:
        return f"rubberband=tempo={tempo:.4f}:pitch={p:.5f}:formant=preserved"
    parts = []
    if abs(p - 1) > 1e-4:
        parts += [f"asetrate=44100*{p:.5f}", "aresample=44100"]
        tempo = tempo / p
    t = tempo
    while t > 2.0:
        parts.append("atempo=2.0"); t /= 2.0
    while t < 0.5:
        parts.append("atempo=0.5"); t /= 0.5
    parts.append(f"atempo={t:.4f}")
    return ",".join(["aresample=44100"] + parts)


def voice_fx(src, dst, fx, tempo=1.0):
    """Clean a voice take. fx: {energize, tighten, pitch (semitones)}; tempo keeps pitch."""
    f = []
    if fx.get("tighten", True):
        f.append(TIGHTEN)
    pitch = float(fx.get("pitch", 0) or 0)
    if abs(tempo - 1) > 0.005 or pitch:
        f.append(stretch(tempo, pitch))
    if fx.get("energize", True):
        f.append(ENERGIZE)
    f.append("loudnorm=I=-16:TP=-1.5:LRA=9")
    ffmpeg("-i", src, "-af", ",".join(f), "-ac", "1", "-ar", "44100", dst)


def transcribe(d, wav):
    tdir = os.path.join(d, ".cmv-tx")
    os.makedirs(tdir, exist_ok=True)
    hf("transcribe", wav, "-d", tdir)
    words = load(os.path.join(tdir, "transcript.json"), [])
    return [{"text": w["text"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in words if w["text"].strip()]


def norm(tok):
    return re.sub(r"[^a-z0-9]", "", tok.lower())


def gemini_tts(text, voice, out_wav, style=None, model=None):
    import base64, urllib.request, urllib.error, wave
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("Gemini voice needs the GEMINI_API_KEY environment variable (a free key from aistudio.google.com).")
    model = model or os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    prompt = f"{style.strip().rstrip(':')}:\n{text}" if style else text
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini TTS failed ({e.code}): {e.read().decode(errors='replace')[:600]}")
    part = j["candidates"][0]["content"]["parts"][0]["inlineData"]
    pcm = base64.b64decode(part["data"])
    rate = int(re.search(r"rate=(\d+)", part.get("mimeType", "")).group(1)) if "rate=" in part.get("mimeType", "") else 24000
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


def kokoro_tts(text, voice, speed, out_wav):
    hf("tts", text, "-v", voice, "-s", str(speed), "-o", out_wav)


def auto_beats(words, lo=1.6, hi=5.5):
    """Group transcript words into beats: sentence ends, merging short ones and splitting long ones."""
    sents, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r"[.?!]['\"]?$", w["text"]):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    out = []
    for s in sents:  # split long sentences at a comma, else at the widest pause
        stack = [s]
        while stack:
            g = stack.pop(0)
            if words[g[-1]]["end"] - words[g[0]]["start"] <= hi or len(g) < 4:
                out.append(g); continue
            cand = [k for k in range(1, len(g) - 1) if words[g[k - 1]]["text"].endswith((",", ";", ":"))]
            mid = len(g) // 2
            k = min(cand, key=lambda k: abs(k - mid)) if cand else max(range(2, len(g) - 1),
                key=lambda k: words[g[k]]["start"] - words[g[k - 1]]["end"] - abs(k - mid) * 0.01)
            stack[0:0] = [g[:k], g[k:]]
    dur = lambda g: words[g[-1]]["end"] - words[g[0]]["start"]
    beats = list(out)
    i = 0
    while i < len(beats):  # a too-short beat joins its shorter neighbour (forward preferred on ties)
        g = beats[i]
        if dur(g) >= lo or len(beats) == 1:
            i += 1; continue
        prev = beats[i - 1] if i > 0 else None
        nxt = beats[i + 1] if i + 1 < len(beats) else None
        fwd = nxt is not None and (prev is None or dur(nxt) <= dur(prev) or dur(prev + g) > hi)
        if fwd:
            beats[i:i + 2] = [g + nxt]
        elif prev is not None:
            beats[i - 1:i + 1] = [prev + g]; i -= 1
        else:
            i += 1
    return beats


def align_beats(words, scenes):
    """Map each scene's "vo" onto transcript word indices (fuzzy, in order)."""
    import difflib
    script, owner = [], []
    for si, sc in enumerate(scenes):
        for tok in (sc.get("vo") or "").split():
            if norm(tok):
                script.append(norm(tok)); owner.append(si)
    heard = [norm(w["text"]) for w in words]
    m = difflib.SequenceMatcher(None, script, heard, autojunk=False)
    j2i = {}
    for a, b, n in m.get_matching_blocks():
        for k in range(n):
            j2i[a + k] = b + k
    firsts = {}
    for si in range(len(scenes)):
        js = [j for j, o in enumerate(owner) if o == si]
        if not js:
            continue
        hit = next((j for j in js if j in j2i), None)
        firsts[si] = max(0, j2i[hit] - (hit - js[0])) if hit is not None else None
    voiced = [si for si in range(len(scenes)) if si in firsts]
    # fill unmatched scenes proportionally between neighbours, keep strictly increasing
    starts, prev = {}, -1
    for n, si in enumerate(voiced):
        s = firsts[si]
        if s is None:
            nxt = next((firsts[x] for x in voiced[n + 1:] if firsts[x] is not None), len(words))
            s = prev + max(1, (nxt - prev) // 2)
        s = max(s, prev + 1)
        starts[si] = min(s, len(words) - 1)
        prev = starts[si]
    groups = {}
    for n, si in enumerate(voiced):
        end = starts[voiced[n + 1]] if n + 1 < len(voiced) else len(words)
        groups[si] = list(range(starts[si], end))
    return groups


def full_take(d, plan, raw):
    """One continuous voice file -> cleaned full.wav + scenes cut from its words."""
    vdir = os.path.join(d, "assets", "voice")
    os.makedirs(vdir, exist_ok=True)
    fx = plan.get("voice_fx") or {}
    clean = os.path.join(vdir, "full.wav")
    voice_fx(raw, clean, fx)
    words = transcribe(d, clean)
    if not words:
        raise SystemExit("no speech found in the voice file")
    span = words[-1]["end"] - words[0]["start"]
    wpm = len(words) / span * 60
    tempo = fx.get("tempo", "auto")
    if tempo == "auto":   # lift slow reads toward ~160 wpm, never more than 1.2x
        tempo = min(1.2, 160 / wpm) if wpm < 148 else 1.0
    tempo = float(tempo)
    if abs(tempo - 1) > 0.005:
        tmp = os.path.join(vdir, "full_tempo.wav")
        ffmpeg("-i", clean, "-af", stretch(tempo, 0), tmp)
        os.replace(tmp, clean)
        words = [{"text": w["text"], "start": round(w["start"] / tempo, 3), "end": round(w["end"] / tempo, 3)} for w in words]
    print(f"voice take: {len(words)} words, {wpm:.0f} wpm as recorded, tempo x{tempo:.2f} -> {wpm * tempo:.0f} wpm")

    scenes = plan.get("scenes") or []
    voiced_sc = [sc for sc in scenes if (sc.get("vo") or "").strip()]
    if voiced_sc:
        idx = {sc["id"]: si for si, sc in enumerate(scenes)}
        groups = align_beats(words, scenes)
        order = [(scenes[si], g) for si, g in sorted(groups.items())]
        trailing = [sc for sc in scenes[max(groups) + 1:] if not (sc.get("vo") or "").strip()]
        stray = [sc["id"] for sc in scenes[:max(groups)] if idx[sc["id"]] not in groups]
        if stray:
            print(f"warning: scenes without vo inside a one-take voice are skipped: {stray}")
    else:
        beats = auto_beats(words)
        scenes = [{"id": f"s{n + 1}", "vo": " ".join(words[i]["text"] for i in g)} for n, g in enumerate(beats)]
        if scenes:
            scenes[-1]["min"] = 2.6
        order = list(zip(scenes, beats))
        trailing = []
        plan["scenes"] = scenes
        save(os.path.join(d, "plan.json"), plan)
        print(f"auto-split into {len(scenes)} beats and wrote them to plan.json")

    lead = snap(plan.get("lead", 0.15))   # frame-exact, so word times match the audio clip
    vdur = duration(clean)
    timing = {"scenes": [], "voice_track": {"src": "assets/voice/full.wav", "at": lead, "dur": round(vdur, 3)}}
    bounds = [0.0]
    for n in range(1, len(order)):
        prev_end = lead + words[order[n - 1][1][-1]]["end"]
        first = lead + words[order[n][1][0]]["start"]
        b = min(first, max(prev_end + 0.02, first - 0.2))
        bounds.append(round(int(b * FPS) / FPS, 3))   # floor to a frame: never after the first word
    last_sc, last_g = order[-1]
    end = lead + words[last_g[-1]]["end"] + last_sc.get("pad", 0.4)
    end = max(end, bounds[-1] + last_sc.get("min", 0))
    bounds.append(snap(end))
    for n, (sc, g) in enumerate(order):
        st = bounds[n]
        timing["scenes"].append({"id": sc["id"], "start": st, "duration": snap(bounds[n + 1] - st),
                                 "words": [{"text": words[i]["text"], "t": round(lead + words[i]["start"] - st, 3),
                                            "end": round(lead + words[i]["end"] - st, 3)} for i in g]})
    t = bounds[-1]
    for sc in trailing:
        timing["scenes"].append({"id": sc["id"], "start": snap(t), "duration": snap(sc.get("min", 1.5))})
        t += snap(sc.get("min", 1.5))
    timing["voice_track"]["dur"] = round(min(vdur, t - lead), 3)
    timing["total"] = snap(t)
    return timing


# ---------------------------------------------------------------- voice
def print_timing(timing):
    for e in timing["scenes"]:
        ws = " ".join(f"{w['text']}@{w['t']}" for w in e.get("words", []))
        print(f"{e['id']:12s} start {e['start']:6.2f}  dur {e['duration']:5.2f}  {ws}")
    print(f"total {timing['total']} s")


def cmd_voice(args):
    d = os.path.abspath(args[0])
    plan = load(os.path.join(d, "plan.json"))
    if plan.get("voice_locked"):
        raise SystemExit("this is a chapter: its voice and timing come from the parent's `chapters` step; don't re-run voice here")
    vfile = opt(args, "--file", None) or plan.get("voice_file")
    engine = plan.get("engine", "kokoro")
    if vfile or engine == "gemini" or plan.get("take") == "full":
        vdir = os.path.join(d, "assets", "voice")
        os.makedirs(vdir, exist_ok=True)
        if vfile:
            raw = os.path.abspath(vfile if os.path.isabs(vfile) or os.path.exists(vfile) else os.path.join(d, vfile))
            if not os.path.exists(raw):
                raise SystemExit(f"voice file not found: {raw}")
            keep = os.path.join(vdir, "original" + os.path.splitext(raw)[1].lower())
            if os.path.abspath(raw) != os.path.abspath(keep):
                shutil.copy2(raw, keep)
            plan["voice_file"] = os.path.relpath(keep, d).replace("\\", "/")
            save(os.path.join(d, "plan.json"), plan)
            raw = keep
        else:
            text = " ".join((sc.get("vo") or "").strip() for sc in plan.get("scenes", []) if (sc.get("vo") or "").strip())
            if not text:
                raise SystemExit("plan.json has no scene \"vo\" text to speak")
            raw = os.path.join(vdir, "take_raw.wav")
            if engine == "gemini":
                gemini_tts(text, plan.get("voice", "Kore"), raw, plan.get("voice_style"), plan.get("gemini_model"))
            else:
                kokoro_tts(text, plan.get("voice", "af_heart"), plan.get("speed", 1.1), raw)
        timing = full_take(d, plan, raw)
        save(os.path.join(d, "timing.json"), timing)
        print_timing(timing)
        return
    voice, speed = plan.get("voice", "af_heart"), str(plan.get("speed", 1.1))
    fx = plan.get("voice_fx")
    vdir = os.path.join(d, "assets", "voice")
    os.makedirs(vdir, exist_ok=True)
    cache = load(os.path.join(d, "timing.json"), {}).get("_cache", {})
    timing = {"scenes": [], "_cache": {}}
    t = 0.0
    for sc in plan["scenes"]:
        entry = {"id": sc["id"], "start": snap(t)}
        vo = (sc.get("vo") or "").strip()
        if vo:
            key = f"{voice}|{speed}|{json.dumps(fx, sort_keys=True)}|{vo}"
            wav = os.path.join(vdir, f"{sc['id']}.wav")
            words = None
            if cache.get(sc["id"], {}).get("key") == key and os.path.exists(wav):
                words = cache[sc["id"]]["words"]
            else:
                kokoro_tts(vo, voice, speed, wav)
                if fx is None or fx:   # default: energize, keep the line's own pauses
                    tmp = os.path.join(vdir, f"{sc['id']}_raw.wav")
                    os.replace(wav, tmp)
                    voice_fx(tmp, wav, dict({"tighten": False}, **(fx or {})))
                    os.remove(tmp)
                words = transcribe(d, wav)
            timing["_cache"][sc["id"]] = {"key": key, "words": words}
            vdur = duration(wav)
            lead = sc.get("lead", 0.15)   # voice starts this long after the scene starts
            entry.update({"voice": f"assets/voice/{sc['id']}.wav", "voice_at": lead, "voice_dur": round(vdur, 3),
                          "words": [{"text": w["text"], "t": round(w["start"] + lead, 3), "end": round(w["end"] + lead, 3)} for w in words]})
            dur = max(sc.get("min", 0), lead + vdur + sc.get("pad", 0.25))
        else:
            dur = sc.get("min", 1.5)
        entry["duration"] = snap(dur)
        timing["scenes"].append(entry)
        t += entry["duration"]
    timing["total"] = snap(t)
    save(os.path.join(d, "timing.json"), timing)
    print_timing(timing)


# ---------------------------------------------------------------- voices (audition board)
KOKORO_EN = ["af_heart", "af_bella", "af_nicole", "af_aoede", "af_kore", "af_sarah", "af_nova", "af_sky", "af_alloy",
             "af_jessica", "af_river", "am_michael", "am_fenrir", "am_puck", "am_echo", "am_eric", "am_liam", "am_onyx",
             "am_adam", "am_santa", "bf_emma", "bf_isabella", "bf_alice", "bf_lily", "bm_george", "bm_fable", "bm_lewis", "bm_daniel"]
GEMINI_VOICES = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus",
                 "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
                 "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia",
                 "Sadaltager", "Sulafat"]
DEMO_TEXT = ("Stop scrolling. Most people save money the slow way. But if you put away just fifty dollars a month, "
             "it quietly grows on its own. Here's exactly how it works.")


def cmd_voices(args):
    out = os.path.abspath(args[0])
    engine = opt(args, "--engine", "kokoro")
    speed = float(opt(args, "--speed", "1.1"))
    text = opt(args, "--text", DEMO_TEXT)
    style = opt(args, "--style", "Read this like an upbeat, confident social media creator, with energy and natural rhythm")
    names = opt(args, "--only", None)
    names = names.split(",") if names else (GEMINI_VOICES if engine == "gemini" else KOKORO_EN)
    os.makedirs(out, exist_ok=True)
    rows = []
    for n, v in enumerate(names, 1):
        mp3 = os.path.join(out, f"{n:02d}_{v}.mp3")
        if not os.path.exists(mp3):
            raw = os.path.join(out, "_raw.wav")
            if engine == "gemini":
                gemini_tts(text, v, raw, style)
            else:
                kokoro_tts(text, v, speed, raw)
            wav = os.path.join(out, "_fx.wav")
            voice_fx(raw, wav, {"tighten": True})
            ffmpeg("-i", wav, "-c:a", "libmp3lame", "-q:a", "3", mp3)
            for f in (raw, wav):
                os.remove(f)
        dur = duration(mp3)
        if engine == "gemini":
            desc = "Google Gemini"
        else:
            accent = "US" if v[0] == "a" else "UK"
            desc = f"{accent} {'female' if v[1] == 'f' else 'male'}"
        rows.append((n, v, desc, os.path.basename(mp3), dur))
        print(f"{n:2d} {v:14s} {desc:14s} {dur:4.1f}s")
    items = "\n".join(
        f'<li><span class="n">{n:02d}</span><b>{v}</b><i>{desc}</i><audio controls preload="none" src="{f}"></audio></li>'
        for n, v, desc, f, _ in rows)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Voice audition</title><style>
body{{font:16px/1.4 system-ui,sans-serif;margin:0;padding:24px 16px;background:#F4F4F6;color:#111}}
h1{{font-size:22px;margin:0 0 4px}} p{{color:#666;margin:0 0 18px;max-width:640px}}
ul{{list-style:none;padding:0;margin:0;display:grid;gap:8px;max-width:720px}}
li{{display:flex;align-items:center;gap:12px;background:#fff;border-radius:14px;padding:10px 14px;flex-wrap:wrap}}
.n{{color:#999;font-variant-numeric:tabular-nums}} b{{min-width:110px}} i{{color:#666;font-style:normal;min-width:90px}}
audio{{flex:1;min-width:220px;height:36px}}</style></head><body>
<h1>Voice audition ({engine})</h1><p>Same line in every voice{"" if engine == "gemini" else f", speed {speed}"}, with the skill's voice polish (presence EQ, compression, tightened pauses). Tell Claude the number or name you like.</p>
<ul>{items}</ul></body></html>''')
    print(f"board: {os.path.join(out, 'index.html')}")


# ---------------------------------------------------------------- assemble
def block(s, name, content):
    pat = re.compile(rf"(<!-- CMV:{name} -->)(.*?)(<!-- /CMV:{name} -->)", re.S)
    if not pat.search(s):
        raise SystemExit(f"index.html is missing the <!-- CMV:{name} --> markers")
    return pat.sub(lambda m: m.group(1) + "\n" + content + "\n      " + m.group(3), s)


def cmd_assemble(args):
    d = os.path.abspath(args[0])
    plan = load(os.path.join(d, "plan.json"))
    timing = load(os.path.join(d, "timing.json"))
    if not timing:
        raise SystemExit("run `voice` first (it also times scenes without voiceover)")
    w, h = FORMATS[plan.get("format", "vertical")]
    by_id = {e["id"]: e for e in timing["scenes"]}
    total = timing["total"]

    hosts, audio = [], []
    for e in timing["scenes"]:
        src = f"compositions/{e['id']}.html"
        if not os.path.exists(os.path.join(d, src)):
            print(f"warning: {src} does not exist yet")
        hosts.append(f'      <div id="{e["id"]}" data-composition-id="{e["id"]}" data-composition-src="{src}" '
                     f'data-start="{e["start"]}" data-duration="{e["duration"]}" data-track-index="1" '
                     f'data-track-kind="graphics" data-width="{w}" data-height="{h}"></div>')
        if e.get("voice") and not timing.get("voice_track"):
            audio.append(f'      <audio id="vo-{e["id"]}" class="clip" src="{e["voice"]}" data-start="{snap(e["start"] + e["voice_at"])}" '
                         f'data-duration="{e["voice_dur"]}" data-track-index="10" data-volume="1"></audio>')

    # overlays (subscribe/follow CTAs, lower thirds): drawn above the scenes on their own track
    for o in plan.get("overlays", []):
        st, du = snap(o["start"]), snap(min(o["duration"], total - o["start"]))
        if du <= 0:
            continue
        by_id[o["id"]] = {"id": o["id"], "start": st, "duration": du}
        hosts.append(f'      <div id="{o["id"]}" data-composition-id="{o["id"]}" data-composition-src="{o["src"]}" '
                     f'data-start="{st}" data-duration="{du}" data-track-index="2" data-track-kind="graphics" '
                     f'data-width="{w}" data-height="{h}" style="z-index:20"></div>')

    vt = timing.get("voice_track")
    if vt:
        audio.append(f'      <audio id="vo-full" class="clip" src="{vt["src"]}" data-start="{snap(vt["at"])}" '
                     f'data-duration="{vt["dur"]}" data-track-index="10" data-volume="1"></audio>')

    music = plan.get("music")
    if music and music.get("file"):
        md = min(duration(os.path.join(d, music["file"])) - music.get("offset", 0), total)
        audio.append(f'      <audio id="music" class="clip" src="{music["file"]}" data-start="0" data-duration="{snap(md)}" '
                     f'data-media-start="{music.get("offset", 0)}" data-track-index="11" data-volume="{music.get("volume", 0.12)}" '
                     f'data-fade-in="0.3" data-fade-out="1.0"></audio>')

    manifest = load(os.path.join(KIT, "manifest.json"), {})
    credits, lanes = set(), []  # lanes: list of end times, for Studio readability
    sfx = sorted(plan.get("sfx", []), key=lambda c: by_id[c["scene"]]["start"] + c["t"] if c.get("scene") else c["t"])
    # Variety: a cue names a sound ("error") or a role group ("@error"). Sounds in a group rotate so
    # the same file isn't heard again until the group's other takes have played (unless the cue says
    # "exact": true or plan.json has "sfx_vary": false). Deterministic: same plan -> same mix.
    manifest = {k: v for k, v in manifest.items() if os.path.exists(os.path.join(KIT, v["file"]))}  # installed only
    groups = {}
    for k in sorted(manifest):
        if manifest[k].get("group"):
            groups.setdefault(manifest[k]["group"], []).append(k)
    vary = plan.get("sfx_vary", True)
    seed = sum(map(ord, os.path.basename(d)))   # chapters start their rotation at different takes
    recent = {}
    full = load(os.path.join(KIT, "manifest.json"), {})
    def pick(name, cue):
        if not name.startswith("@") and name not in manifest and full.get(name, {}).get("group") in groups:
            name = "@" + full[name]["group"]          # e.g. a library sound that isn't installed: use its role group
        base = manifest.get(name[1:] if name.startswith("@") else name)
        g = name[1:] if name.startswith("@") else (base or {}).get("group")
        if name.startswith("@") and g not in groups:
            return None, None
        if not g or not vary or cue.get("exact") or len(groups.get(g, [])) < 2:
            return name, base
        pool = groups[g]
        used = recent.setdefault(g, [])
        # start each project/chapter at a different take (seed), so across chapters the "named" take
        # doesn't open every chapter (otherwise the named take still opens most chapters of a long film)
        start = (seed + len(used)) % len(pool)
        order = pool[start:] + pool[:start]
        avoid = set(used[-min(len(pool) - 1, 4):])
        choice = next((k for k in order if k not in avoid), order[0])
        used.append(choice)
        ref = base or manifest[choice]
        return choice, ref

    for i, c in enumerate(sfx):
        name, ref = pick(c["sound"], c)
        if name is None:
            print(f"warning: unknown sound group '{c['sound']}', skipped"); continue
        m = manifest.get(name)
        if m:
            fn = m["file"]
            srcfile = os.path.join(KIT, fn)
            shutil.copy2(srcfile, os.path.join(d, "assets", "sfx", fn))
            scale = m["volume"] / ref["volume"] if ref and ref.get("volume") else 1.0
            peak, dur, vol = m["peak"], m["duration"], round(c.get("volume", ref["volume"] if ref else m["volume"]) * scale, 3)
            if m.get("license") == "by":
                credits.add(f"- {fn}: {m['credit']}")
        else:  # a project-local file, e.g. assets/sfx/custom.mp3
            fn = os.path.basename(name)
            p = os.path.join(d, "assets", "sfx", fn)
            if not os.path.exists(p):
                print(f"warning: unknown sound '{name}', skipped"); continue
            peak, dur, vol = c.get("peak", 0.0), duration(p), c.get("volume", 0.5)
        visual = (by_id[c["scene"]]["start"] if c.get("scene") else 0) + c["t"]
        start = max(0.0, snap(visual - peak + 1 / FPS))   # hit lands one frame after the picture
        dur = round(min(dur, total - start), 3)
        if dur <= 0:
            continue
        lane = next((k for k, end in enumerate(lanes) if end <= start), None)
        if lane is None:
            lanes.append(0); lane = len(lanes) - 1
        lanes[lane] = start + dur
        audio.append(f'      <audio id="sfx-{i:02d}-{os.path.splitext(fn)[0]}" class="clip" src="assets/sfx/{fn}" data-start="{start}" '
                     f'data-duration="{dur}" data-track-index="{20 + lane}" data-volume="{vol}"></audio>')

    idx = os.path.join(d, "index.html")
    s = open(idx, encoding="utf-8").read()
    s = block(s, "SCENES", "\n".join(hosts))
    s = block(s, "AUDIO", "\n".join(audio))
    s = re.sub(r'(id="root"[^>]*?data-duration=")[\d.]+(")', rf"\g<1>{total}\g<2>", s, count=1, flags=re.S)
    open(idx, "w", encoding="utf-8").write(s)
    if credits:
        open(os.path.join(d, "CREDITS.md"), "w", encoding="utf-8").write(
            "# Credits\n\nSound effects licensed CC BY 4.0 (credit wherever the video is published):\n\n" + "\n".join(sorted(credits)) + "\n")
    save(os.path.join(d, "sfx_resolved.json"), [
        {"id": a.split('id="')[1].split('"')[0], "start": float(a.split('data-start="')[1].split('"')[0]),
         "dur": float(a.split('data-duration="')[1].split('"')[0])} for a in audio if 'id="sfx-' in a])
    print(f"assembled {len(hosts)} scenes, {len(audio)} audio clips, total {total} s")


# ---------------------------------------------------------------- master
def cmd_master(args):
    d, src = os.path.abspath(args[0]), os.path.abspath(args[1])
    target = float(opt(args, "--lufs", "-14"))
    out = os.path.splitext(src)[0] + "_master.mp4"
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={target}:TP=-1.0:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rfind("{"):meas.rfind("}") + 1])
    af = (f"loudnorm=I={target}:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-c:v", "copy", "-af", af,
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", out], check=True)
    print(f"mastered: {out}  (was {j['input_i']} LUFS, target {target})")


# ---------------------------------------------------------------- breakdown
def cmd_breakdown(args):
    d, render = os.path.abspath(args[0]), os.path.abspath(args[1])
    caption = opt(args, "--caption", "Just Sfx")
    plan = load(os.path.join(d, "plan.json"))
    timing = load(os.path.join(d, "timing.json"))
    cues = load(os.path.join(d, "sfx_resolved.json"), [])
    total = timing["total"]
    bd = d.rstrip("\\/") + "-breakdown"
    if not os.path.exists(os.path.join(bd, "index.html")):
        parent, name = os.path.split(bd)
        hf("init", name, "--skip-skills", "--skill=clean-motion-video", cwd=parent)
    os.makedirs(os.path.join(bd, "assets"), exist_ok=True)
    shutil.copy2(render, os.path.join(bd, "assets", "film.mp4"))
    vw, vh = FORMATS[plan.get("format", "vertical")]
    # film box: 1000 px wide inside 1080x1920, height by aspect (capped at 1080)
    box_w = 1000
    box_h = int(box_w * vh / vw)
    if box_h > 1080:
        box_h = 1080; box_w = int(box_h * vw / vh)
    px_per_s = 260  # timeline scale
    rows = []
    lanes = []
    for i, c in enumerate(cues):
        label = re.sub(r"^sfx-\d+-", "", c["id"]).replace("-", " ").title()
        lane = next((k for k, end in enumerate(lanes) if end <= c["start"]), None)
        if lane is None:
            lanes.append(0); lane = len(lanes) - 1
        wpx = max(c["dur"] * px_per_s, len(label) * 14 + 70)   # wide enough for its label
        lanes[lane] = c["start"] + wpx / px_per_s + 0.05
        rows.append(f'<div class="blk" style="left:{c["start"] * px_per_s:.0f}px;top:{lane * 64}px;width:{wpx:.0f}px">'
                    f'<span class="dia"></span>{label}</div>')
    tl_h = max(1, len(lanes)) * 64
    html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 1080px; height: 1920px; background: #000; font-family: "Inter", sans-serif; }}
      #cap {{ position: absolute; top: 300px; width: 100%; text-align: center; color: #fff; font-family: "EB Garamond", serif; font-size: 64px; }}
      #film {{ position: absolute; left: {(1080 - box_w) // 2}px; top: 420px; width: {box_w}px; height: {box_h}px; object-fit: cover; }}
      #tlwrap {{ position: absolute; left: 0; top: {420 + box_h + 40}px; width: 1080px; height: {tl_h + 60}px; background: #1B1B1D; overflow: hidden; }}
      #track {{ position: absolute; left: 540px; top: 30px; height: {tl_h}px; width: {total * px_per_s + 600:.0f}px; }}
      .blk {{ position: absolute; height: 50px; border-radius: 8px; background: #1E5E66; border: 1.5px solid #2FB3C0; color: #DFFBFF;
              font-size: 22px; font-weight: 600; display: flex; align-items: center; gap: 10px; padding: 0 12px; white-space: nowrap; overflow: hidden; }}
      .dia {{ width: 16px; height: 16px; background: #5CE1EE; transform: rotate(45deg); flex: none; }}
      #head {{ position: absolute; left: 539px; top: 0; width: 3px; height: 100%; background: #fff; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="cap" class="clip" data-start="0" data-duration="{total}" data-track-index="2">{caption}</div>
      <video id="film" class="clip" src="assets/film.mp4" data-start="0" data-duration="{total}" data-track-index="0" playsinline data-has-audio="true"></video>
      <div id="tlwrap" class="clip" data-layout-ignore data-layout-allow-overflow data-start="0" data-duration="{total}" data-track-index="1"><div id="track">{"".join(rows)}</div><div id="head"></div></div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#track", {{ x: 0 }}, {{ x: -{total * px_per_s:.0f}, duration: {total}, ease: "none" }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
    open(os.path.join(bd, "index.html"), "w", encoding="utf-8").write(html)
    print(f"breakdown project: {bd}")


# ---------------------------------------------------------------- subscribe / follow CTA
CTA_TIMES = {"subscribe": {"dur": 5.2, "press": [1.25, 2.3]}, "follow": {"dur": 3.8, "press": [1.2]}}


def cmd_cta(args):
    """Add an organic subscribe/follow CTA overlay. Long films: --at auto picks a calm section start
    about a third of the way in; shorts: the last seconds. Works on a chapter parent (routes to the chapter)."""
    d = os.path.abspath(args[0])
    kind = opt(args, "--kind", None)
    at = opt(args, "--at", "auto")
    chans = load(os.path.join(d, "chapters", "chapters.json"))
    plan0 = load(os.path.join(d, "plan.json")) or {}
    fmt = plan0.get("format", "vertical")
    if not kind:
        kind = "subscribe" if fmt == "landscape" else "follow"
    dur = float(opt(args, "--dur", str(CTA_TIMES[kind if fmt == "landscape" or kind == "follow" else "follow"]["dur"])))
    target, local = d, None
    if chans:
        total = chans[-1]["end"]
        if at == "auto":   # first section start at >= 30% of the film, shown over its title card
            c = next((c for c in chans if c["start"] / total >= 0.3), chans[len(chans) // 2])
            at_abs = c["start"] + 0.4
        else:
            at_abs = float(at)
        c = next(c for c in chans if c["start"] <= at_abs < c["end"])
        target, local = os.path.join(d, "chapters", c["id"]), round(at_abs - c["start"], 3)
        print(f"CTA at {at_abs:.1f}s -> {c['id']} +{local}s")
    timing = load(os.path.join(target, "timing.json"))
    plan = load(os.path.join(target, "plan.json"))
    total_t = timing["total"]
    if local is None:
        if at == "auto":
            if total_t > 90:   # long single project: nearest scene start to 35%
                local = min((e["start"] for e in timing["scenes"]), key=lambda s: abs(s - total_t * 0.35)) + 0.3
            else:              # short: last seconds
                local = max(0.0, total_t - dur - 0.15)
        else:
            local = float(at)
    w, h = FORMATS[plan.get("format", "vertical")]
    channel = opt(args, "--channel", plan.get("channel", {}).get("name", "Your Channel"))
    sub = opt(args, "--sub", plan.get("channel", {}).get("tagline", "New videos every week"))
    color = opt(args, "--color", plan.get("channel", {}).get("color", "#0A84FF"))
    avatar = opt(args, "--avatar", plan.get("channel", {}).get("avatar"))
    if kind == "subscribe" and fmt == "landscape":
        tpl = "subscribe.html"; left, top = 192, 830
        line = opt(args, "--line", "Getting value from this? Subscribe and turn on notifications")
    else:
        tpl = "follow.html"; left, top = 120, 1100   # one compact card: y 1100-1232, inside x 120-780
        line = opt(args, "--line", "Follow for more like this" if kind == "follow" else "Subscribe for more like this")
    n = 1 + sum(1 for o in plan.get("overlays", []) if o["id"].startswith("cta"))
    cid = opt(args, "--id", f"cta{n}")
    av_html = (re.sub(r"[^A-Za-z0-9]", "", channel)[:1] or "Y").upper()
    if tpl == "follow.html":       # compact card: the line becomes the card's subtitle
        sub = line
    if avatar:
        src = os.path.abspath(avatar)
        dst = os.path.join(target, "assets", "brand", os.path.basename(src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        av_html = f'<img src="assets/brand/{os.path.basename(src)}" alt="">'
    html = open(os.path.join(TEMPLATE, "cta", tpl), encoding="utf-8").read()
    rep = {"__ID__": cid, "__CHANNEL__": channel, "__SUB__": sub, "__COLOR__": color, "__LINE__": line, "__AVATAR__": av_html,
           "__LEFT__": str(left), "__TOP__": str(top), "__W__": str(w), "__H__": str(h), "__OUT__": f"{dur - 0.4:.2f}",
           "__B1__": "Follow" if kind == "follow" else "Subscribe", "__B2__": "Following" if kind == "follow" else "Subscribed"}
    for k, v in rep.items():
        html = html.replace(k, v)
    os.makedirs(os.path.join(target, "compositions"), exist_ok=True)
    open(os.path.join(target, "compositions", f"{cid}.html"), "w", encoding="utf-8").write(html)
    plan["overlays"] = [o for o in plan.get("overlays", []) if o["id"] != cid] + [
        {"id": cid, "src": f"compositions/{cid}.html", "start": round(local, 3), "duration": dur, "kind": kind}]
    plan["sfx"] = [s for s in plan.get("sfx", []) if s.get("scene") != cid]
    presses = CTA_TIMES["subscribe" if tpl == "subscribe.html" else "follow"]["press"]
    plan["sfx"] += [{"scene": cid, "t": 0.02, "sound": "@appear", "volume": 0.28},
                    {"scene": cid, "t": presses[0], "sound": "ui-tap", "volume": 0.5, "exact": True},
                    {"scene": cid, "t": presses[0] + 0.06, "sound": "@success", "volume": 0.25}]
    if len(presses) > 1:
        plan["sfx"] += [{"scene": cid, "t": presses[1], "sound": "ui-tap", "volume": 0.5, "exact": True},
                        {"scene": cid, "t": presses[1] + 0.08, "sound": "@notify", "volume": 0.28}]
    plan["sfx"].append({"scene": cid, "t": dur - 0.4, "sound": "@whoosh", "volume": 0.22})
    save(os.path.join(target, "plan.json"), plan)
    print(f"{kind} CTA '{cid}' at {local:.2f}s for {dur}s in {target} (run assemble + render)")


# ---------------------------------------------------------------- publish pack: thumbnail + TikTok parts
def render_stills(work, html, times, files=()):
    """Snapshot a one-page HyperFrames composition at the given times; returns PNG paths."""
    if not os.path.exists(os.path.join(work, "hyperframes.json")):
        parent, name = os.path.split(work)
        os.makedirs(parent, exist_ok=True)
        hf("init", name, "--skip-skills", "--skill=clean-motion-video", cwd=parent)
    os.makedirs(os.path.join(work, "assets"), exist_ok=True)
    for src in files:
        shutil.copy2(src, os.path.join(work, "assets", os.path.basename(src)))
    open(os.path.join(work, "index.html"), "w", encoding="utf-8").write(html)
    r = hf("snapshot", "--at", ",".join(f"{t:.2f}" for t in times), cwd=work)
    pngs = re.findall(r"([A-Za-z]:[^\n]*?frame-\d+-at-[\d.]+s\.png)", r.stdout_text)
    return [p.strip() for p in pngs][:len(times)]


def find_render(d):
    slug = os.path.basename(os.path.normpath(d))
    for f in (f"{slug}_master.mp4", f"{slug}.mp4"):
        p = os.path.join(d, "renders", f)
        if os.path.exists(p):
            return p
    raise SystemExit("no render found in renders/ (render + master first)")


def cmd_thumb(args):
    """thumb <dir> --title "YOU'RE<br><b>BROKE.</b>" [--kicker "Accept it"] [--frame SECONDS | --image file]
       [--sticker-label "Balance" --sticker "$4.12"] [--theme dark|light] [--accent #hex] [--name v1]"""
    d = os.path.abspath(args[0])
    title, kicker = opt(args, "--title", "TITLE"), opt(args, "--kicker", "")
    theme, accent, name = opt(args, "--theme", "dark"), opt(args, "--accent", "#0A84FF"), opt(args, "--name", "v1")
    pub = os.path.join(d, "publish"); work = os.path.join(pub, "_thumb")
    os.makedirs(pub, exist_ok=True)
    files, frame_html = [], ""
    img = opt(args, "--image", None)
    if opt(args, "--frame", None) is not None:
        img = os.path.join(pub, "_frame.jpg")
        ffmpeg("-ss", opt(args, "--frame", "0"), "-i", find_render(d), "-frames:v", "1", "-q:v", "2", img)
    if img:
        files.append(os.path.abspath(img)); frame_html = f'<img src="assets/{os.path.basename(img)}" alt="">'
    st_v = opt(args, "--sticker", None)
    sticker = f'<div class="stk"><div class="k">{opt(args, "--sticker-label", "")}</div><div class="v">{st_v}</div></div>' if st_v else ""
    bg, ink = ("radial-gradient(70% 90% at 30% 50%, #1C2336 0%, #0B0D14 70%)", "#FFFFFF") if theme == "dark" else ("#F4F4F6", "#111113")
    html = open(os.path.join(TEMPLATE, "publish", "thumbnail.html"), encoding="utf-8").read()
    for k, v in {"__BG__": bg, "__INK__": ink, "__ACCENT__": accent, "__KICKER__": kicker, "__TITLE__": title,
                 "__FRAME__": frame_html, "__STICKER__": sticker}.items():
        html = html.replace(k, v)
    if not kicker:
        html = html.replace('<div id="kick"></div>', "")
    png = render_stills(work, html, [0.1], files)
    out = os.path.join(pub, f"thumbnail-{name}.png")
    shutil.copy2(png[0], out)
    print(f"thumbnail: {out}")


def parse_parts(d, spec):
    """'s1..s19|s63..s82' (scene ids) or '0-71.1|229.6-297' (seconds) -> [(start, end)] in the film's time."""
    timing = load(os.path.join(d, "timing.json"))
    sc = {e["id"]: e for e in timing["scenes"]} if timing else {}
    out = []
    for p in spec.split("|"):
        p = p.strip()
        if ".." in p:
            a, b = p.split("..")
            out.append((sc[a]["start"], sc[b]["start"] + sc[b]["duration"]))
        else:
            a, b = p.split("-")
            out.append((float(a), float(b)))
    return out


def cmd_tiktok(args):
    """tiktok <dir> --parts "s1..s19|s63..s82" --titles "T1|T2" [--captions "C1|C2"] [--landscape-only] [--handle @x] [--avatar file]
    Framed 9:16 parts are the default (the user posts them as-is); they are also copied to publish/tiktok-ready/
    as "Part N - <title>.mp4" with "Part N - caption.txt" beside each."""
    d = os.path.abspath(args[0])
    parts = parse_parts(d, opt(args, "--parts", ""))
    titles = (opt(args, "--titles", "") or "").split("|")
    src = find_render(d)
    outd = os.path.join(d, "publish", "tiktok"); os.makedirs(outd, exist_ok=True)
    plan = load(os.path.join(d, "plan.json")) or {}
    ch = plan.get("channel", {})
    handle = opt(args, "--handle", ch.get("handle", "@yourchannel"))
    avatar = opt(args, "--avatar", ch.get("avatar"))
    if avatar and not os.path.isabs(avatar):
        avatar = os.path.normpath(os.path.join(d, avatar))
    frames = []
    captions = (opt(args, "--captions", "") or "").split("|")
    if "--landscape-only" not in args:
        pages = ""
        av = f'<img src="assets/{os.path.basename(avatar)}" alt="">' if avatar and os.path.exists(avatar) else ""
        for i in range(len(parts)):
            t = titles[i] if i < len(titles) else ""
            pages += (f'      <div class="pg clip" data-start="{i}" data-duration="1"><div class="top"><span class="part">PART {i + 1}</span>'
                      f'<div class="ttl">{t}</div></div><div class="band"></div><div class="bot"><div class="av">{av}</div>'
                      f'<div><div class="h">{handle}</div><div class="s">Full video on YouTube</div></div></div></div>\n')
        html = open(os.path.join(TEMPLATE, "publish", "tiktok_frame.html"), encoding="utf-8").read()
        html = html.replace("__N__", str(len(parts))).replace("__PAGES__", pages)
        frames = render_stills(os.path.join(d, "publish", "_tiktok_frames"), html, [i + 0.5 for i in range(len(parts))],
                               [avatar] if av else [])
    for i, (a, b) in enumerate(parts, 1):
        dur = b - a
        out = os.path.join(outd, f"part-{i:02d}.mp4")
        ffmpeg("-ss", f"{a:.3f}", "-i", src, "-t", f"{dur:.3f}", "-vf", f"fade=t=out:st={dur - 0.3:.3f}:d=0.3",
               "-af", f"afade=t=in:d=0.12,afade=t=out:st={dur - 0.35:.3f}:d=0.35",
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", out)
        line = f"part {i:02d}: {int(a // 60):02d}:{a % 60:05.2f} -> {int(b // 60):02d}:{b % 60:05.2f}  ({dur:.0f}s)  {out}"
        if frames:
            vout = os.path.join(outd, f"part-{i:02d}-vertical.mp4")
            ffmpeg("-loop", "1", "-i", frames[i - 1], "-i", out, "-filter_complex",
                   "[1:v]scale=1080:608[v];[0:v]scale=1080:1920,setsar=1[bg];[bg][v]overlay=0:656:shortest=1[o]", "-map", "[o]", "-map", "1:a",
                   "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", "-r", "30", "-shortest", vout)
            line += f"\n          vertical: {vout}"
            ready = os.path.join(d, "publish", "tiktok-ready"); os.makedirs(ready, exist_ok=True)
            t = re.sub(r'[\\/:*?"<>|]', "", titles[i - 1] if i - 1 < len(titles) else "").strip(". ") or f"part {i}"
            shutil.copy2(vout, os.path.join(ready, f"Part {i} - {t}.mp4"))
            cap = captions[i - 1] if i - 1 < len(captions) and captions[i - 1] else f"{t} (Part {i})"
            open(os.path.join(ready, f"Part {i} - caption.txt"), "w", encoding="utf-8").write(
                f"{cap}\n\nFirst comment: Full video on YouTube: {ch.get('name', '')} ({handle})\n")
        print(line)


def cmd_chapterlist(args):
    """Print YouTube chapter timestamps from chapters/chapters.json (first words of each chapter's opening scene)."""
    d = os.path.abspath(args[0])
    chans = load(os.path.join(d, "chapters", "chapters.json"))
    timing = load(os.path.join(d, "timing.json"))
    sc = {e["id"]: e for e in timing["scenes"]}
    for c in chans:
        t = int(c["start"])
        words = " ".join(w["text"] for w in sc[c["scenes"][0]].get("words", []))
        print(f"{t // 60:02d}:{t % 60:02d}  {words[:70]}")


# ---------------------------------------------------------------- hf passthrough + setup / doctor
def cmd_hf(args):
    """Run any HyperFrames CLI command (check, snapshot, render, tts, transcribe, ...) from the current folder."""
    p = hf(*args, cwd=os.getcwd(), check=False)
    sys.exit(p.returncode)


def cmd_setup(args):
    """Check prerequisites and finish the SFX kit (library sounds come from your HyperFrames media-use skill)."""
    ok = True
    def row(name, good, hint=""):
        nonlocal ok
        ok = ok and good
        print(f"  [{'ok' if good else '!!'}] {name}" + ("" if good else f"  -> {hint}"))
    print("clean-motion-video setup")
    row(f"Python {sys.version.split()[0]}", sys.version_info >= (3, 9), "install Python 3.9+")
    row("Node.js / npx", bool(shutil.which("npx") or shutil.which("npx.cmd")), "install Node.js 22+ (nodejs.org)")
    row("ffmpeg + ffprobe", bool(shutil.which("ffmpeg") and shutil.which("ffprobe")), "install ffmpeg (winget install Gyan.FFmpeg / brew install ffmpeg / apt install ffmpeg)")
    if shutil.which("ffmpeg"):
        rb = " rubberband " in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        print(f"  [{'ok' if rb else '--'}] ffmpeg rubberband filter" + ("" if rb else "  (optional: atempo fallback is used)"))
    launcher = find_skill_file("hyperframes", "scripts", "plugin-cli.mjs")
    print(f"  [{'ok' if launcher else '--'}] HyperFrames skills " + (launcher if launcher else
          "not found (videos still work via npx; for best results run: npx skills add heygen-com/hyperframes)"))
    lib = find_skill_file("media-use", "audio", "assets", "sfx")
    man = load(os.path.join(KIT, "manifest.json"), {})
    missing = [k for k, v in man.items() if not os.path.exists(os.path.join(KIT, v["file"]))]
    if missing and lib:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import add_sfx_variants as av
        got = 0
        for k in missing:
            src = os.path.join(lib, man[k]["file"])
            if os.path.exists(src):
                dur, pk = av.level_into_kit(src, k, man[k].get("duration", 2.0) + 0.05)
                man[k].update({"duration": dur, "peak": pk}); got += 1
        save(os.path.join(KIT, "manifest.json"), man)
        print(f"  [ok] library sounds installed from {lib}: {got}/{len(missing)}")
        missing = [k for k, v in man.items() if not os.path.exists(os.path.join(KIT, v["file"]))]
    present = len(man) - len(missing)
    print(f"  [{'ok' if not missing else '--'}] SFX kit: {present}/{len(man)} sounds" +
          ("" if not missing else f" (missing: {', '.join(missing)}; rotation uses the other takes in each role)"))
    if "--test" in args:
        print("  testing the HyperFrames CLI (first run downloads it)...")
        r = hf("--version", check=False)
        row("HyperFrames CLI runs", r.returncode == 0, "check Node.js and your internet connection")
    print("ready." if ok else "fix the items marked !! and run setup again.")


# ---------------------------------------------------------------- sfx audition board
def cmd_sfxboard(args):
    """Listen to the kit by role group: index.html with players + ALL_SFX_by_group.mp3."""
    out = os.path.abspath(args[0])
    os.makedirs(out, exist_ok=True)
    man = load(os.path.join(KIT, "manifest.json"), {})
    groups = {}
    for k in sorted(man):
        groups.setdefault(man[k].get("group", "other"), []).append(k)
    gap = os.path.join(out, "_gap.wav")
    ffmpeg("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.55", gap)
    parts, html = [], []
    for g, ks in sorted(groups.items(), key=lambda x: -len(x[1])):
        lbl = os.path.join(out, f"_lbl_{g}.wav")
        kokoro_tts(f"{g.replace('-', ' ')} sounds.", "bf_emma", 1.1, lbl)
        lbl2 = os.path.join(out, f"_lbl2_{g}.wav")
        ffmpeg("-i", lbl, "-af", "volume=-6dB", "-ar", "44100", "-ac", "2", lbl2)
        parts += [lbl2, gap]
        rows = []
        for k in ks:
            f = man[k]["file"]
            shutil.copy2(os.path.join(KIT, f), os.path.join(out, f))
            w = os.path.join(out, f"_{k}.wav")
            ffmpeg("-i", os.path.join(out, f), "-af", f"volume={man[k].get('volume', 0.5) / 0.5:.2f}", "-ar", "44100", "-ac", "2", w)
            parts += [w, gap]
            rows.append(f'<li><b>{k}</b><i>{man[k].get("license", "")}</i><audio controls preload="none" src="{f}"></audio></li>')
        parts.append(gap)
        html.append(f"<h2>{g} <span>{len(ks)} takes</span></h2><ul>{''.join(rows)}</ul>")
    lst = os.path.join(out, "_list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        fh.writelines(f"file '{p.replace(chr(92), '/')}'\n" for p in parts)
    ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-c:a", "libmp3lame", "-q:a", "3", os.path.join(out, "ALL_SFX_by_group.mp3"))
    for p in set(parts) | {lst, gap}:
        if os.path.basename(p).startswith("_") and os.path.exists(p):
            os.remove(p)
    for f in os.listdir(out):
        if f.startswith("_lbl_"):
            os.remove(os.path.join(out, f))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SFX kit</title><style>
body{{font:16px/1.4 system-ui,sans-serif;margin:0;padding:24px 16px;background:#F4F4F6;color:#111}}
h1{{font-size:22px;margin:0 0 6px}} h2{{font-size:18px;margin:26px 0 8px}} h2 span{{color:#888;font-weight:400;font-size:14px}}
ul{{list-style:none;padding:0;margin:0;display:grid;gap:6px;max-width:720px}}
li{{display:flex;align-items:center;gap:12px;background:#fff;border-radius:12px;padding:8px 12px;flex-wrap:wrap}}
b{{min-width:140px}} i{{color:#888;font-style:normal;min-width:60px}} audio{{flex:1;min-width:220px;height:34px}}</style></head><body>
<h1>Sound kit by role</h1><p>Takes in the same group rotate automatically in videos. Tell Claude any take to drop.</p>{"".join(html)}</body></html>''')
    print(f"board: {os.path.join(out, 'index.html')} and ALL_SFX_by_group.mp3 ({sum(len(v) for v in groups.values())} sounds)")


# ---------------------------------------------------------------- long form: chapters + concat
def cmd_chapters(args):
    """Cut a long one-take film (after `voice`) into chapter projects of ~--size seconds."""
    d = os.path.abspath(args[0])
    size = float(opt(args, "--size", "75"))
    plan, timing = load(os.path.join(d, "plan.json")), load(os.path.join(d, "timing.json"))
    vt = timing.get("voice_track") if timing else None
    if not vt:
        raise SystemExit("run `voice` with a one-take source (--file, gemini, or take:full) first")
    scenes = timing["scenes"]
    groups, cur = [], []
    at = opt(args, "--at", None)   # explicit cuts: scene ids that start a new chapter (e.g. section starts)
    if at:
        cuts = set(at.split(","))
        for e in scenes:
            if e["id"] in cuts and cur:
                groups.append(cur); cur = []
            cur.append(e)
        groups.append(cur); cur = []
        scenes = []
    for e in scenes:   # close a chapter at a scene boundary once it reaches ~size (sentence end preferred)
        cur.append(e)
        length = e["start"] + e["duration"] - cur[0]["start"]
        last = (e.get("words") or [{"text": "."}])[-1]["text"]
        if length >= size and (re.search(r"[.?!]$", last) or length >= size * 1.4):
            groups.append(cur); cur = []
    if cur:
        if groups and cur[-1]["start"] + cur[-1]["duration"] - cur[0]["start"] < size * 0.35:
            groups[-1] += cur
        else:
            groups.append(cur)
    by_id = {sc["id"]: sc for sc in plan["scenes"]}
    full = os.path.join(d, vt["src"])
    lead = vt["at"]
    index = []
    for n, g in enumerate(groups, 1):
        cid = f"ch{n:02d}"
        cd = os.path.join(d, "chapters", cid)
        S = g[0]["start"]; E = g[-1]["start"] + g[-1]["duration"]
        if not os.path.exists(os.path.join(cd, "index.html")):
            cmd_new([cd, "--format", plan.get("format", "vertical"), "--theme", plan.get("theme", "light"),
                     "--title", f"{plan.get('title', '')} {cid}"])
        a0 = max(0.0, S - lead)
        at = max(0.0, lead - S)   # noqa: shadows the --at option, which is no longer needed here
        clip = os.path.join(cd, "assets", "voice", "full.wav")
        os.makedirs(os.path.dirname(clip), exist_ok=True)
        ffmpeg("-ss", f"{a0:.3f}", "-t", f"{E - S - at:.3f}", "-i", full, clip)
        ctiming = {"scenes": [dict(e, start=snap(e["start"] - S)) for e in g],
                   "voice_track": {"src": "assets/voice/full.wav", "at": snap(at), "dur": round(duration(clip), 3)},
                   "total": snap(E - S), "chapter_of": d, "abs_start": S}
        save(os.path.join(cd, "timing.json"), ctiming)
        idx = os.path.join(cd, "index.html")   # long form: calm word entrances (no per-word scale snap)
        h = open(idx, encoding="utf-8").read()
        if 'data-word-style' not in h:
            h = h.replace('id="root"', 'id="root" data-word-style="soft"', 1)
            open(idx, "w", encoding="utf-8").write(h)
        cplan = {k: v for k, v in plan.items() if k not in ("scenes", "sfx", "voice_file", "engine", "take")}
        old = load(os.path.join(cd, "plan.json"), {}) or {}
        cplan.update({"title": f"{plan.get('title', '')} {cid}", "voice_locked": True,
                      "scenes": [by_id.get(e["id"], {"id": e["id"]}) for e in g], "sfx": old.get("sfx", [])})
        save(os.path.join(cd, "plan.json"), cplan)
        index.append({"id": cid, "start": S, "end": E, "scenes": [e["id"] for e in g]})
        print(f"{cid}: {S:7.2f}-{E:7.2f}s  ({E - S:5.1f}s, {len(g)} scenes)  {g[0]['id']} .. {g[-1]['id']}")
    save(os.path.join(d, "chapters", "chapters.json"), index)
    print(f"{len(groups)} chapters in {os.path.join(d, 'chapters')}. Build each like a normal project "
          f"(scenes + sfx in its plan.json, then assemble/check/render), then `concat`.")


def cmd_concat(args):
    """Join rendered chapters (chapters/chNN/renders/chNN.mp4) into renders/<slug>.mp4."""
    d = os.path.abspath(args[0])
    index = load(os.path.join(d, "chapters", "chapters.json"))
    if not index:
        raise SystemExit("no chapters/chapters.json; run `chapters` first")
    parts = []
    for c in index:
        p = os.path.join(d, "chapters", c["id"], "renders", f"{c['id']}.mp4")
        if not os.path.exists(p):
            raise SystemExit(f"missing render: {p}")
        parts.append(p)
    os.makedirs(os.path.join(d, "renders"), exist_ok=True)
    lst = os.path.join(d, "renders", "_concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{p.replace(chr(92), '/')}'\n" for p in parts)
    out = os.path.join(d, "renders", os.path.basename(d) + ".mp4")
    print(f"joining {len(parts)} chapters -> {out}")
    ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out)
    os.remove(lst)
    print(f"done: {out} ({duration(out):.1f}s). Next: master it.")


def opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


if __name__ == "__main__":
    if len(sys.argv) < 2 or (len(sys.argv) < 3 and sys.argv[1] not in ("setup", "hf")):
        print(__doc__); sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "import":
        cmd, rest = "voice", [rest[0], "--file", rest[1]]
    {"new": cmd_new, "voice": cmd_voice, "voices": cmd_voices, "assemble": cmd_assemble, "master": cmd_master,
     "breakdown": cmd_breakdown, "chapters": cmd_chapters, "concat": cmd_concat, "sfxboard": cmd_sfxboard, "cta": cmd_cta, "thumb": cmd_thumb, "tiktok": cmd_tiktok, "chapterlist": cmd_chapterlist, "hf": cmd_hf, "setup": cmd_setup}[cmd](rest)
