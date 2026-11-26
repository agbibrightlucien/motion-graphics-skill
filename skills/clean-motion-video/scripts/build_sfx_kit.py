"""Level, trim and index the SFX kit.

Run once (already done) or after adding new sounds to assets/sfx/raw-style names:
    python -I build_sfx_kit.py <kit_dir>

Each file is trimmed shortly after its tail, peak-normalised to -3 dBFS, and
re-measured. manifest.json records role, duration, peak time (seconds from the
file start: place the clip at  visual_time - peak + 1/30  so the hit lands one
frame after the picture), a suggested volume and the licence.
"""
import json, os, subprocess, sys, re, shutil, tempfile

KIT = sys.argv[1]

# name: (role, suggested volume, licence, credit)
SOUNDS = {
    "whoosh-short":       ("move: small card/text slide, whip (take A)", 0.55, "bundled", ""),
    "swoosh-fast":        ("move: fast whip / swipe (take B)", 0.45, "cc0", "\"swosh-08\" (Freesound, CC0)"),
    "whoosh-low":         ("move: soft low whoosh under a big scale/morph (take C)", 0.9, "cc0", "\"whoosh_short_low\" (Freesound, CC0)"),
    "whoosh-pass":        ("move: big pass-by / scene transition", 0.35, "by", "\"Whoosh.wav\" via Openverse/Freesound, CC BY 4.0"),
    "swish":              ("move: airy swish, soft scene change", 0.8, "by", "\"Swish\" via Openverse/Freesound, CC BY 4.0"),
    "magic-whoosh":       ("reveal: shimmering whoosh into a hero/logo", 0.45, "by", "\"Imperius - Wings Swing - 02\" by SoundFlakes, CC BY 4.0, https://freesound.org/people/SoundFlakes/sounds/492538"),
    "whoosh-cinematic":   ("transition: long swell that peaks on a cut", 0.35, "bundled", ""),
    "granular-transition":("transition: granular/electric texture on a morph or glitch", 0.35, "by", "\"Electrical Transition\" by qubodup, CC BY 4.0, https://freesound.org/people/qubodup/sounds/211639"),
    "glass-swell":        ("riser: short glassy inhale into a reveal", 0.4, "cc0", "\"Inhale with glass\" (Freesound, CC0)"),
    "rise-crash":         ("riser: build into the payoff (peak ~4 s in)", 0.4, "cc0", "\"rise-crash\" (Freesound, CC0)"),
    "riser":              ("riser: long cinematic build (peak ~3.5 s)", 0.3, "bundled", ""),
    "enter":              ("appear: UI element lands / confirm (the 'Enter' sound)", 0.4, "cc0", "\"Enter Button - Low Robotic\" (Freesound, CC0)"),
    "pop":                ("appear: chip, badge, word or icon pops in", 0.5, "bundled", ""),
    "bubble-pop":         ("appear: tiny bubble pop (rotate with pop)", 0.45, "by", "\"BUBBLE POP\" via Openverse/Freesound, CC BY 4.0"),
    "ui-tap":             ("click: cursor tap on a button", 0.6, "cc0", "\"UI Button Click\" (Freesound, CC0)"),
    "click-soft":         ("click: quiet selection / toggle", 0.6, "bundled", ""),
    "key-press":          ("typing: single keystroke", 0.6, "bundled", ""),
    "mech-typing":        ("typing: short mechanical burst", 0.4, "cc0", "\"MECH-KEYBOARD-01\" (Freesound, CC0)"),
    "typing":             ("typing: 1.5 s burst of keys", 0.6, "bundled", ""),
    "message-ping":       ("notify: message / chat bubble arrives", 0.6, "cc0", "\"Quiz Gameshow Correct Ping 14\" (Freesound, CC0)"),
    "notification":       ("notify: toast / notification card", 0.45, "bundled", ""),
    "ping":               ("accent: data point / stat lands", 0.5, "bundled", ""),
    "chime":              ("accent: success / done", 0.5, "bundled", ""),
    "sparkle":            ("accent: shine on a hero element", 0.35, "bundled", ""),
    "shutter":            ("accent: snapshot / frame freeze", 0.5, "cc0", "\"Camera Shutter\" (Freesound, CC0)"),
    "impact-bass-1":      ("impact: logo/headline slam", 0.4, "bundled", ""),
    "bass-drop":          ("impact: drop on the payoff (use once)", 0.3, "cc0", "\"bass drop\" (Freesound, CC0)"),
    "glitch-1":           ("glitch: barcode/streak transition", 0.3, "bundled", ""),
    "glitch-3":           ("glitch: subtle digital shift", 0.45, "bundled", ""),
    "error":              ("problem beat: 'wrong' / failure", 0.5, "bundled", ""),
}
DROP = ["click.mp3", "whoosh.mp3", "glitch-2.mp3", "impact-bass-2.mp3"]  # duplicates / heavy clipping


def measure(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def peak_time_and_tail(path):
    # RMS envelope via ffmpeg astats per 10 ms
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af",
                          "aresample=44100,asetnsamples=441,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Peak_level",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    vals = [float(v) if v not in ("-inf", "inf") else -120.0
            for v in re.findall(r"Peak_level=(-?[\w.]+)", out)]
    if not vals:
        return 0.0, None
    pk = max(range(len(vals)), key=lambda i: vals[i])
    top = vals[pk]
    tail = len(vals)
    for i in range(len(vals) - 1, pk, -1):
        if vals[i] > top - 45:
            tail = i + 1
            break
    return round(pk * 0.01, 3), round(tail * 0.01 + 0.12, 3)


for f in DROP:
    p = os.path.join(KIT, f)
    if os.path.exists(p):
        os.remove(p)

manifest = {}
credits = ["# SFX credits", "", "CC BY sounds must be credited where the video is published. CC0 and bundled sounds need no credit.", ""]
for name, (role, vol, lic, credit) in SOUNDS.items():
    src = os.path.join(KIT, name + ".mp3")
    if not os.path.exists(src):
        print("missing", name); continue
    _, tail = peak_time_and_tail(src)
    gain = -3.0 - measure(src)
    tmp = os.path.join(tempfile.gettempdir(), "kit_" + name + ".mp3")
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src]
    if tail:
        args += ["-t", str(tail)]
    args += ["-af", f"volume={gain:.2f}dB,afade=t=out:st={max((tail or 1) - 0.06, 0):.3f}:d=0.06",
             "-ar", "44100", "-b:a", "192k", tmp]
    subprocess.run(args, check=True)
    shutil.move(tmp, src)
    pk, _ = peak_time_and_tail(src)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True).stdout.strip())
    manifest[name] = {"file": name + ".mp3", "role": role, "duration": round(dur, 3), "peak": pk,
                      "volume": vol, "license": lic, "credit": credit}
    if lic == "by":
        credits.append(f"- `{name}.mp3`: {credit}")
    print(f"{name:20s} dur {dur:5.2f}  peak {pk:5.2f}  gain {gain:+.1f} dB")

json.dump(manifest, open(os.path.join(KIT, "manifest.json"), "w"), indent=1)
open(os.path.join(KIT, "CREDITS.md"), "w").write("\n".join(credits) + "\n")
