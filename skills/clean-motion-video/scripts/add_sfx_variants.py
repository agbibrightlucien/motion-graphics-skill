"""Add sound variants to the kit and tag every sound with a role group.

    python -I add_sfx_variants.py <staging_dir> --pick error:a1b2c3d4,e5f6a7b8 whoosh:... [--synth]
    python -I add_sfx_variants.py --groups-only        # just (re)write group tags for existing sounds

- Picked candidates (ids from <staging_dir>/candidates.json, made by fetch_sfx_variants.py) are trimmed,
  peak-normalised to -3 dBFS, faded, measured and added as <group>-v<N>.mp3 (CC0, credited anyway).
- --synth adds synthesised failure tones (made here from sine maths: no copyright of anyone's).
- Every manifest entry gets "group". `cmv.py assemble` rotates through a group's takes so the same
  file is not heard back to back (see references/sfx-kit.md).
"""
import json, os, re, shutil, subprocess, sys, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(SKILL, "assets", "sfx")
MAN = os.path.join(KIT, "manifest.json")

# existing kit sounds -> group (rotation pools)
BASE_GROUPS = {
    "error": "error", "whoosh-short": "whoosh", "swoosh-fast": "whoosh", "whoosh-low": "whoosh-big", "whoosh-pass": "whoosh-big",
    "swish": "whoosh-big", "enter": "appear", "pop": "pop", "bubble-pop": "pop", "ui-tap": "click", "click-soft": "click",
    "key-press": "key", "mech-typing": "typing", "typing": "typing", "message-ping": "notify", "notification": "notify",
    "ping": "ping", "chime": "success", "sparkle": "success", "impact-bass-1": "impact", "bass-drop": "impact",
    "glitch-1": "glitch", "glitch-3": "glitch", "granular-transition": "glitch", "magic-whoosh": "reveal", "glass-swell": "riser",
    "rise-crash": "riser", "riser": "riser", "whoosh-cinematic": "reveal", "shutter": "shutter",
}
ROLE = {"error": "problem beat: 'wrong' / failure", "whoosh": "move: small slide / whip", "appear": "appear: UI element lands",
        "pop": "appear: chip / badge pops", "click": "click: tap / toggle", "key": "typing: single keystroke",
        "success": "accent: success / done", "ping": "accent: stat lands", "notify": "notify: notification / message",
        "impact": "impact: slam"}
VOL = {"error": 0.4, "whoosh": 0.45, "appear": 0.4, "pop": 0.45, "click": 0.55, "key": 0.55, "success": 0.4, "ping": 0.45, "notify": 0.45, "impact": 0.35}

SYNTH = {  # name: (ffmpeg aevalsrc expression, duration)
    "error-synth-1": ("0.55*sin(2*PI*494*t)*exp(-14*t)*lt(t,0.15)+0.55*sin(2*PI*392*(t-0.16))*exp(-9*(t-0.16))*gte(t,0.16)", 0.7),       # two-tone down
    "error-synth-2": ("0.45*(sin(2*PI*330*t)+0.35*sin(2*PI*660*t))*exp(-18*t)*lt(t,0.09)+0.45*(sin(2*PI*330*(t-0.13))+0.35*sin(2*PI*660*(t-0.13)))*exp(-12*(t-0.13))*gte(t,0.13)", 0.55),  # double blip
    "error-synth-3": ("0.5*sin(2*PI*(520-500*t)*t)*exp(-6*t)", 0.6),                                                                        # falling glide
    "error-synth-4": ("0.32*(sin(2*PI*440*t)+sin(2*PI*466*t))*exp(-7*t)", 0.6),                                                             # dissonant pair
    "error-synth-5": ("0.6*sin(2*PI*150*t)*(0.6+0.4*sin(2*PI*28*t))*exp(-9*t)", 0.45),                                                     # low buzz
}


def ff(*a):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)


def max_vol(p):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def envelope(p):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "aresample=44100,asetnsamples=441,astats=metadata=1:reset=1,"
                          "ametadata=print:key=lavfi.astats.Overall.Peak_level", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = [float(x) if x not in ("-inf", "inf") else -120.0 for x in re.findall(r"Peak_level=(-?[\w.]+)", out)]
    if not v:
        return 0.0, None, None
    pk = max(range(len(v)), key=lambda i: v[i])
    start = next((i for i in range(len(v)) if v[i] > v[pk] - 40), 0)
    tail = next((i + 1 for i in range(len(v) - 1, pk, -1) if v[i] > v[pk] - 42), len(v))
    return pk * 0.01, start * 0.01, tail * 0.01


def level_into_kit(src, name, max_len):
    pk, start, tail = envelope(src)
    start = max(0.0, (start or 0) - 0.01)
    end = min(tail + 0.1 if tail else max_len, start + max_len)
    tmp = os.path.join(tempfile.gettempdir(), "kitv_" + name + ".wav")
    ff("-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", src, "-ac", "2", "-ar", "44100", tmp)
    gain = -3.0 - max_vol(tmp)
    dst = os.path.join(KIT, name + ".mp3")
    d = end - start
    ff("-i", tmp, "-af", f"volume={gain:.2f}dB,afade=t=in:d=0.004,afade=t=out:st={max(d - 0.06, 0):.3f}:d=0.06", "-b:a", "192k", dst)
    os.remove(tmp)
    pk2, _, _ = envelope(dst)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout)
    return round(dur, 3), round(pk2, 3)


def main():
    man = json.load(open(MAN, encoding="utf-8"))
    for k, g in BASE_GROUPS.items():
        if k in man:
            man[k]["group"] = g
    args = sys.argv[1:]
    if args and args[0] != "--groups-only":
        stage = os.path.abspath(args[0])
        cands = json.load(open(os.path.join(stage, "candidates.json"), encoding="utf-8"))
        picks = []
        if "--pick" in args:
            i = args.index("--pick") + 1
            while i < len(args) and not args[i].startswith("--"):
                picks.append(args[i]); i += 1
        for p in picks:
            g, ids = p.split(":")
            n = sum(1 for v in man.values() if v.get("group") == g and "-v" in v["file"]) + 1
            for cid in ids.split(","):
                c = next((x for x in cands.get(g, []) if x["id"].startswith(cid)), None)
                if not c:
                    print("not found:", g, cid); continue
                name = f"{g}-v{n}"; n += 1
                dur, pk = level_into_kit(os.path.join(stage, c["file"]), name, 1.6 if g not in ("success", "impact", "notify") else 2.4)
                man[name] = {"file": name + ".mp3", "role": ROLE.get(g, g), "duration": dur, "peak": pk, "volume": VOL.get(g, 0.45),
                             "license": "cc0", "credit": f"\"{c['title']}\" by {c['creator']} (CC0) {c['source']}", "group": g}
                print(f"added {name:14s} dur {dur:4.2f} peak {pk:4.2f}  <- {c['title'][:40]}")
    if "--synth" in args:
        for name, (expr, d) in SYNTH.items():
            raw = os.path.join(tempfile.gettempdir(), name + "_raw.wav")
            ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={d}", "-af", "lowpass=f=5000,aecho=0.6:0.4:40:0.18", raw)
            dur, pk = level_into_kit(raw, name, d)
            os.remove(raw)
            man[name] = {"file": name + ".mp3", "role": "problem beat: 'wrong' / failure (synthesised)", "duration": dur, "peak": pk,
                         "volume": 0.38, "license": "cc0", "credit": "synthesised for this kit", "group": "error"}
            print(f"synth {name:14s} dur {dur:4.2f} peak {pk:4.2f}")
    json.dump(man, open(MAN, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    groups = {}
    for k, v in man.items():
        groups.setdefault(v.get("group", "-"), []).append(k)
    for g, ks in sorted(groups.items()):
        print(f"{g:11s} {len(ks)}: {', '.join(ks)}")


if __name__ == "__main__":
    main()
