"""Review every cut in an edit: what was said around it in the raw take and the sound right at each edge.
python -I SKILL/scripts/review_joins.py <project>   (after footage.py ingest)"""
import importlib.util, json, os, subprocess, sys
d = sys.argv[1]
sp = importlib.util.spec_from_file_location("f", os.path.join(os.path.dirname(os.path.abspath(__file__)), "footage.py"))
F = importlib.util.module_from_spec(sp); sp.loader.exec_module(F)
words = json.load(open(os.path.join(d, "assets/footage/raw_words.json")))
segs = json.load(open(os.path.join(d, "assets/footage/cuts.json")))["segments"]
wav = os.path.join(d, "assets/footage/_review.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "assets/footage/raw.mp4"), "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
env = F.envelope(wav); os.remove(wav)
thr = F.speech_threshold(env, words)


def runs(a, b):
    return " ".join(f"[{x:.2f}-{y:.2f}]" for x, y in F.voiced_runs(env, a, b, thr, 0.03))


acc = 0.0
for n, (a, b) in enumerate(segs):
    if n:
        pa, pb = segs[n - 1]
        before = [w["text"] for w in words if pa <= w["start"] < pb][-3:]
        gone = [w["text"] for w in words if pb <= w["start"] < a and w["text"]]
        after = [w["text"] for w in words if a <= w["start"] < b][:3]
        print(f"edit {acc:6.2f}s | ...{' '.join(before)} || cut {pb:.2f}->{a:.2f} [{' '.join(gone)[:60]}] || {' '.join(after)}...")
        print(f"      sound in last 0.4 s kept: {runs(pb - 0.4, pb)}   first 0.4 s kept: {runs(a, a + 0.4)}")
    acc += b - a
