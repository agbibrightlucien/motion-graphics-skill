"""Grow the SFX kit with several takes per role, so long videos don't repeat one sound.

    python -I fetch_sfx_variants.py <staging_dir> [--groups error,whoosh,...] [--per 6]

1. Searches Openverse (free API, no key; CC0 only, so no credit is ever needed) with several
   queries per group and downloads short candidates into <staging_dir>/<group>/ (untrusted
   downloads: own folder, never executed).
2. Rejects: too long/short for the role, clipped or silent files, and anything with speech in it
   (Parakeet transcription finds words -> reject; Openverse "pop" results once held spoken words).
3. Writes <staging_dir>/candidates.json. Then `add_sfx_variants.py` levels the picks into the kit.
Anonymous Openverse allows ~20 searches/minute and 200/day; the script paces itself.
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmv  # noqa: E402  (shares the HyperFrames resolver)
UA = "clean-motion-video-sfx-kit/1.0"

# group: (queries, min_ms, max_ms)
GROUPS = {
    "error":    (["error beep", "wrong answer buzzer", "negative ui sound", "fail sound short", "denied beep", "incorrect buzzer", "ui error", "negative beep"], 150, 1800),
    "whoosh":   (["whoosh short", "swoosh", "swish fast", "whoosh transition", "air whoosh", "swipe whoosh"], 150, 1400),
    "appear":   (["ui appear", "interface pop up", "soft notification appear", "ui confirm", "menu open sound", "ui select"], 100, 1200),
    "pop":      (["pop sound", "bubble pop", "cork pop short", "mouth pop", "plop"], 60, 700),
    "click":    (["ui click", "button click", "mouse click", "switch click", "toggle click"], 30, 500),
    "key":      (["keyboard key press", "single keystroke", "typewriter key", "mechanical key"], 30, 450),
    "success":  (["success chime", "positive ui", "achievement sound", "correct answer ding", "level up short"], 200, 2200),
    "ping":     (["ding", "bell ding short", "glass ding", "notification ding", "coin"], 150, 1800),
    "notify":   (["notification sound", "message received", "phone notification", "chat message sound"], 150, 1800),
    "impact":   (["impact hit", "boom hit short", "low thud", "drum hit impact"], 150, 2200),
}


def api(q):
    url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": q, "license": "cc0", "page_size": 20})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("results", [])


def probe(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    mx = re.search(r"max_volume: (-?[\d.]+) dB", out)
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", out)
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    d = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0
    return float(mx.group(1)) if mx else -99, float(mean.group(1)) if mean else -99, d


def has_speech(path, tmp):
    wav = os.path.join(tmp, "_probe.wav")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", wav], check=True)
    env = dict(os.environ); env.setdefault("HYPERFRAMES_PYTHON", sys.executable); env.setdefault("HYPERFRAMES_STANDALONE_CLI_VERSION", cmv.HF_PIN)
    r = subprocess.run([*cmv.hf_command(), "transcribe", wav, "-d", tmp], capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
    try:
        words = json.load(open(os.path.join(tmp, "transcript.json"), encoding="utf-8"))
    except Exception:
        return False
    real = [w for w in words if len(re.sub(r"[^a-z]", "", w.get("text", "").lower())) >= 2]
    return len(real) >= 1


def main():
    out = os.path.abspath(sys.argv[1])
    args = sys.argv[2:]
    groups = args[args.index("--groups") + 1].split(",") if "--groups" in args else list(GROUPS)
    per = int(args[args.index("--per") + 1]) if "--per" in args else 6
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_tmp"); os.makedirs(tmp, exist_ok=True)
    cands = json.load(open(os.path.join(out, "candidates.json"), encoding="utf-8")) if os.path.exists(os.path.join(out, "candidates.json")) else {}
    for g in groups:
        queries, lo, hi = GROUPS[g]
        gdir = os.path.join(out, g); os.makedirs(gdir, exist_ok=True)
        seen, keep = set(), [c for c in cands.get(g, [])]
        seen.update(c["id"] for c in keep)
        print(f"== {g}: have {len(keep)}", flush=True)
        for q in queries:
            if len(keep) >= per * 2:
                break
            try:
                res = api(q)
            except Exception as e:
                print(f"   search failed ({q}): {e}", flush=True); time.sleep(5); continue
            time.sleep(3.2)   # stay under 20 searches/minute
            for r in res:
                if len(keep) >= per * 2:
                    break
                if r["id"] in seen or r.get("license") != "cc0":
                    continue
                seen.add(r["id"])
                ms = r.get("duration") or 0
                if ms and not (lo <= ms <= hi * 3):   # previews are trimmed later; allow some tail
                    continue
                url = r.get("url") or ""
                if not url.startswith("https://"):
                    continue
                dst = os.path.join(gdir, f"{r['id'][:8]}.mp3")
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=30) as resp, open(dst, "wb") as f:
                        f.write(resp.read(4_000_000))
                except Exception as e:
                    print(f"   download failed: {e}", flush=True); continue
                mx, mean, d = probe(dst)
                why = None
                if d < lo / 1000 or d > hi / 1000 * 3:
                    why = f"length {d:.2f}s"
                elif mx < -30 or mean < -60:
                    why = "too quiet/empty"
                elif has_speech(dst, tmp):
                    why = "contains speech"
                if why:
                    print(f"   reject {r['title'][:40]!r}: {why}", flush=True); os.remove(dst); continue
                keep.append({"id": r["id"], "file": os.path.relpath(dst, out).replace("\\", "/"), "title": r["title"],
                             "creator": r.get("creator") or "", "source": r.get("foreign_landing_url") or "", "license": "cc0",
                             "duration": round(d, 2), "query": q})
                print(f"   keep   {r['title'][:40]!r} ({d:.2f}s) by {r.get('creator')}", flush=True)
        cands[g] = keep
        json.dump(cands, open(os.path.join(out, "candidates.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("done:", {g: len(v) for g, v in cands.items()})


if __name__ == "__main__":
    main()
