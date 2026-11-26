"""qc.py chNN [t1,t2,...] : assemble, check (full log -> chNN/qc.log), summarize, optional snapshots."""
import glob, json, os, subprocess, sys, collections
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

cid = sys.argv[1]
d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chapters", cid)
def _find_cmv():
    """The skill's cmv.py: $CMV_PY, else the first agent skills folder that has clean-motion-video."""
    if os.environ.get("CMV_PY"):
        return os.environ["CMV_PY"]
    home = os.path.expanduser("~")
    for root in [os.path.join(home, p) for p in (".claude/skills", ".agents/skills", ".codex/skills", ".gemini/config/skills",
                 ".gemini/antigravity/skills", ".gemini/skills", ".cursor/skills", ".copilot/skills", ".config/opencode/skills",
                 ".codeium/windsurf/skills")] + [os.path.join(os.getcwd(), p) for p in (".claude/skills", ".agents/skills",
                 ".codex/skills", ".cursor/skills", ".windsurf/skills")]:
        p = os.path.join(root, "clean-motion-video", "scripts", "cmv.py")
        if os.path.exists(p):
            return p
    raise SystemExit("cmv.py not found: set CMV_PY to <skill>/scripts/cmv.py")


CMV = [sys.executable, "-I", "-u", _find_cmv()]
HF = CMV + ["hf"]
log = open(os.path.join(d, "qc.log"), "w", encoding="utf-8")
subprocess.run(CMV + ["assemble", "."], cwd=d, check=True)
subprocess.run(HF + ["check", "--no-cache"], cwd=d, stdout=log, stderr=subprocess.STDOUT)
rep = max(glob.glob(os.path.join(d, ".hyperframes/artifacts/checks/*.json")), key=os.path.getmtime)
r = json.load(open(rep, encoding="utf-8"))


def walk(o):
    if isinstance(o, dict):
        if "code" in o and ("severity" in o or "level" in o):
            yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


items = list(walk(r))
print(cid, dict(collections.Counter(f"{i.get('severity') or i.get('level')}:{i['code']}" for i in items)))
quiet = {"line_unread"}
for i in items:
    sev = i.get("severity") or i.get("level")
    if sev == "info" or i["code"] in quiet:
        continue
    print(f"  {sev} {i['code']} | {(i.get('message') or '')[:150]} | {i.get('selector') or ''} t={i.get('time') or i.get('t') or ''}")
if len(sys.argv) > 2:
    out = subprocess.run(HF + ["snapshot", "--at", sys.argv[2]], cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    print("\n".join(l.strip() for l in out.splitlines() if "contact-sheet" in l))
