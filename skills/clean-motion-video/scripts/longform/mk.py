"""Scene builder for long-form chapters: word times come from the chapter's timing.json by phrase.

    from mk import Chapter
    c = Chapter("ch02")
    c.scene("s20", css="...", html="...", js=f"CM.speak(tl, $('#s20-t'), {c.T('s20', 'stop confusing')});")
    c.sfx("s20", 0.3, "enter", 0.3)
    c.done()
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(os.path.dirname(HERE), "chapters")

HEAD = """<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    {ground}
{html}
  </div>
  <script>
    (function () {{
      const root = document.querySelector('[data-composition-id="{sid}"]');
      const $ = (s) => root.querySelector(s);
      const $$ = (s) => Array.from(root.querySelectorAll(s));
      const tl = gsap.timeline({{ paused: true }});
      const money = (n, sym = "$") => sym + n.toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
      const whole = (n, sym = "$") => sym + Math.round(n).toLocaleString("en-US");
      const row = (el, t) => tl.fromTo(el, {{ opacity: 0, y: -10, filter: "blur(4px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.24, ease: "power3.out" }}, t);
      const slide = (el, t, dx = -30) => tl.fromTo(el, {{ opacity: 0, x: dx, filter: "blur(4px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }}, t);
      const shake = (el, t) => [[0, -14], [-14, 12], [12, -6], [-6, 0]].forEach(([a, b], i) =>
        tl.fromTo(el, {{ x: a }}, {{ x: b, duration: 0.05, ease: "none", immediateRender: false }}, t + i * 0.05));
      const draw = (el, t, d = 0.5) => {{ const L = Math.ceil(el.getTotalLength()); el.setAttribute("stroke-dasharray", L);
        tl.fromTo(el, {{ attr: {{ "stroke-dashoffset": L }} }}, {{ attr: {{ "stroke-dashoffset": 0 }}, duration: d, ease: "power2.out" }}, t); }};
      const grow = (el, t, d = 0.6, axis = "X") => tl.fromTo(el, {{ ["scale" + axis]: 0 }}, {{ ["scale" + axis]: 1, duration: d, ease: "expo.out" }}, t);
      const tint = (el, t, from, to, d = 0.25) => tl.fromTo(el, {{ color: from }}, {{ color: to, duration: d, immediateRender: false }}, t);
      const dim = (el, t) => tl.fromTo(el, {{ opacity: 1, filter: "grayscale(0)" }}, {{ opacity: 0.35, filter: "grayscale(1)", duration: 0.35, immediateRender: false }}, t);
{js}
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
"""


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


class Chapter:
    def __init__(self, cid):
        self.cid = cid
        self.dir = os.path.join(CH, cid)
        self.timing = json.load(open(os.path.join(self.dir, "timing.json"), encoding="utf-8"))
        self.sc = {e["id"]: e for e in self.timing["scenes"]}
        self.cues = []
        os.makedirs(os.path.join(self.dir, "compositions"), exist_ok=True)

    def D(self, sid):
        return self.sc[sid]["duration"]

    def words(self, sid):
        return self.sc[sid].get("words", [])

    def T(self, sid, phrase, nth=0):
        """Times of the consecutive words of `phrase` in scene sid (as a JS array literal)."""
        return json.dumps(self.times(sid, phrase, nth))

    def times(self, sid, phrase, nth=0):
        ws = [norm(w["text"]) for w in self.words(sid)]
        ps = [norm(p) for p in phrase.split() if norm(p)]
        hits = [i for i in range(len(ws) - len(ps) + 1) if ws[i:i + len(ps)] == ps]
        if len(hits) <= nth:
            raise SystemExit(f"{sid}: phrase not found: {phrase!r}\n  words: {' '.join(w['text'] for w in self.words(sid))}")
        i = hits[nth]
        return [round(self.words(sid)[k]["t"], 3) for k in range(i, i + len(ps))]

    def at(self, sid, word, nth=0):
        return self.times(sid, word, nth)[0]

    def end(self, sid, back=0.18):
        """A good exit time: just before the scene ends."""
        return round(self.D(sid) - back, 3)

    def fill(self, sid, text):
        """Tokens: $ID -> scene id; {{T:phrase}} / {{T:phrase#2}} -> word times; {{t:word}} -> first time;
        {{END}} -> exit time; {{D}} -> duration."""
        def rep(m):
            kind, body, nth = m.group(1), m.group(2).strip(), int(m.group(3) or 1) - 1
            if kind == "T":
                return self.T(sid, body, nth)
            return str(self.at(sid, body, nth))
        text = re.sub(r"\{\{(T|t):([^}#]+)(?:#(\d+))?\}\}", rep, text)
        text = text.replace("{{END}}", str(self.end(sid))).replace("{{D}}", str(self.D(sid)))
        return text.replace("$ID", sid)

    def scene(self, sid, css="", html="", js="", ground='<div class="cm-ground"></div>'):
        css, html, js = (self.fill(sid, x) for x in (css, html, js))
        out = HEAD.format(sid=sid, css=css, html=html, js=js, ground=ground)
        open(os.path.join(self.dir, "compositions", f"{sid}.html"), "w", encoding="utf-8").write(out)

    def sfx(self, sid, t, sound, vol):
        self.cues.append({"scene": sid, "t": round(t, 3), "sound": sound, "volume": vol})

    def done(self):
        p = os.path.join(self.dir, "plan.json")
        plan = json.load(open(p, encoding="utf-8"))
        plan["sfx"] = self.cues
        json.dump(plan, open(p, "w", encoding="utf-8"), indent=1)
        print(f"{self.cid}: wrote {len(self.sc)} scenes' cues ({len(self.cues)} sfx)")


if __name__ == "__main__":   # print a chapter's beats + word times
    c = Chapter(sys.argv[1])
    for e in c.timing["scenes"]:
        print(e["id"], e["start"], e["duration"], " ".join(f"{w['text']}@{w['t']}" for w in e.get("words", [])))
