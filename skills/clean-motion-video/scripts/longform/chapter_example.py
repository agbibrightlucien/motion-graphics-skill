# Example: one real chapter (20 beats) built with mk.py + parts.py. Copy the pattern, not the content.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mk import Chapter
from parts import section, person_html, panel_html, receipt_html, PANEL_ROWS

c = Chapter("ch02")
S = c.sfx

# s20 section title
section(c, "s20", 1, "First", "Stop confusing <b>expensive things</b> with wealth.", "stop confusing expensive things with wealth")

# s21 the illusion: premium card flips to reveal what it hides
c.scene("s21", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-l { top: 150px; }
    #$ID-card { position: absolute; left: 650px; top: 330px; width: 620px; height: 390px; perspective: 1600px; }
    #$ID-card .f { position: absolute; inset: 0; border-radius: 34px; padding: 40px 44px; font-family: var(--font); backface-visibility: hidden; box-shadow: 0 30px 70px rgba(0,0,0,0.25); }
    #$ID-front { background: linear-gradient(135deg, #2B2B30 0%, #0E0E10 60%, #3A3427 100%); color: #E9D9A8; }
    #$ID-front .chip { width: 90px; height: 68px; border-radius: 12px; background: linear-gradient(135deg, #E9D9A8, #B39B5B); margin-top: 40px; }
    #$ID-front .nm { position: absolute; left: 44px; bottom: 40px; font-size: 34px; letter-spacing: 0.12em; }
    #$ID-front .tier { position: absolute; right: 44px; top: 40px; font-size: 32px; font-weight: 700; letter-spacing: 0.2em; }
    #$ID-back { background: #fff; color: #111113; }
    #$ID-back .lb { font-size: 32px; color: #6E6E73; margin-top: 70px; }
    #$ID-back .am { font-size: 120px; font-weight: 700; letter-spacing: -0.045em; color: #E5484D; }
""", html="""
    <div id="$ID-all">
      <p id="$ID-l" class="ep-line ep-sub">one of the biggest financial <b>illusions</b></p>
      <div id="$ID-card">
        <div id="$ID-back" class="f"><div class="lb">Balance owed</div><div class="am">$8,940.00</div></div>
        <div id="$ID-front" class="f"><div class="tier">PLATINUM</div><div class="chip"></div><div class="nm">LOOKS RICH</div></div>
      </div>
    </div>""", js="""
      CM.speak(tl, $("#$ID-l"), {{T:one of the biggest financial illusions}});
      tl.fromTo($("#$ID-card"), { opacity: 0, y: 60, rotation: -6, filter: "blur(10px)" }, { opacity: 1, y: 0, rotation: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }, 0.1);
      tl.fromTo($("#$ID-front"), { rotationY: 0 }, { rotationY: 90, duration: 0.22, ease: "power2.in" }, {{t:illusions}});
      tl.fromTo($("#$ID-back"), { rotationY: -90 }, { rotationY: 0, duration: 0.3, ease: "expo.out" }, {{t:illusions}} + 0.22);
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s21", 0.1, "whoosh-short", 0.35); S("s21", c.at("s21", "illusions") + 0.22, "swish", 0.35); S("s21", c.at("s21", "people"), "error", 0.25); S("s21", c.end("s21"), "swoosh-fast", 0.3)

# s22-s24: someone, tagged as they're described
c.scene("s22", css="#$ID-l { top: 120px; }", html=person_html({"clothes", "phone"}) + """
    <p id="$ID-l" class="ep-line ep-sub">You see someone</p>""", js="""
      CM.speak(tl, $("#$ID-l"), {{T:you see someone}});
      CM.pop(tl, $("#$ID-person"), {{t:someone}}, { from: 0.85, ease: "expo.out", dur: 0.45 });
      slide($("#$ID-clothes"), {{t:clothes}}, 30);
      slide($("#$ID-phone"), {{t:phone}}, -30);""")
S("s22", c.at("s22", "someone"), "enter", 0.3); S("s22", c.at("s22", "clothes"), "pop", 0.3); S("s22", c.at("s22", "phone"), "bubble-pop", 0.3)

c.scene("s23", css="#$ID-l { top: 120px; }", html=person_html({"clothes", "phone", "food", "travel"}) + """
    <p id="$ID-l" class="ep-line ep-sub">You see someone</p>""", js="""
      slide($("#$ID-food"), {{t:restaurants}}, 30);
      slide($("#$ID-travel"), {{t:frequently}}, -30);""")
S("s23", c.at("s23", "restaurants"), "pop", 0.3); S("s23", c.at("s23", "frequently"), "bubble-pop", 0.3)

c.scene("s24", css="#$ID-l { top: 120px; }", html=person_html({"clothes", "phone", "food", "travel"}, stamp=True) + """
    <p id="$ID-l" class="ep-line ep-sub">and you immediately assume</p>""", js="""
      CM.speak(tl, $("#$ID-l"), {{T:and you immediately assume}});
      CM.pop(tl, $("#$ID-ok"), {{t:well}}, { from: 0.7 });""")
S("s24", c.at("s24", "well"), "chime", 0.3)

# s25-s28: but how do you actually know? (person slides left, hidden facts panel)
def hide_rows(keep):
    return "".join(f'tl.fromTo($("#$ID-{k}"), {{ opacity: 0 }}, {{ opacity: 0, duration: 0.01 }}, 0);\n' for k, _ in PANEL_ROWS if k not in keep)

c.scene("s25", css="#$ID-l { top: 120px; } #$ID-pg { transform-origin: 50% 50%; }",
        html=person_html({"clothes", "phone", "food", "travel"}, stamp=True, really=True) + panel_html(set()) + """
    <p id="$ID-l" class="ep-line ep-sub">But how do you <b>actually know?</b></p>""", js=hide_rows(set()) + """
      CM.speak(tl, $("#$ID-l"), {{T:but how do you actually know}});
      tl.fromTo($("#$ID-ok"), { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, {{t:know}});
      tl.fromTo($("#$ID-really"), { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.6)" }, {{t:know}} + 0.05);
      tl.fromTo($("#$ID-pg"), { x: 0, scale: 1 }, { x: -330, scale: 0.82, duration: 0.55, ease: "expo.inOut", immediateRender: false }, {{t:you#2}} - 0.25);
      tl.fromTo($("#$ID-panel"), { opacity: 0, x: 80, filter: "blur(8px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }, {{t:you#2}});
      row($("#$ID-debt"), {{t:debt}});""")
S("s25", c.at("s25", "know"), "pop", 0.3); S("s25", c.at("s25", "you", 1) - 0.25, "whoosh-low", 0.4); S("s25", c.at("s25", "debt"), "key-press", 0.35)

SHIFT = '<style>#$ID-pg { transform: translateX(-330px) scale(0.82); transform-origin: 50% 50%; }</style>'
for sid, keep, new, word in [("s26", {"debt"}, "sav", "savings"), ("s27", {"debt", "sav"}, "m3", "survive"), ("s28", {"debt", "sav", "m3"}, "paid", "possessions")]:
    extra = ""
    if sid == "s28":
        extra = """
      $$(".ep-tag:not(#$ID-really)").forEach((g, i) => tint(g, {{t:borrowed}} + i * 0.05, "#111113", "#E5484D"));
      CM.pop(tl, $("#$ID-st"), {{t:borrowed}} + 0.1, { from: 1.6, ease: "expo.out", dur: 0.35 });
      tl.fromTo($("#$ID-q"), { color: "#6E6E73" }, { color: "#E5484D", duration: 0.2, immediateRender: false }, {{t:borrowed}});
      CM.blurOut(tl, $("#$ID-all"), {{END}});"""
    c.scene(sid, css="#$ID-l { top: 120px; } #$ID-st { left: 360px; top: 470px; transform: rotate(-8deg); }",
            html='    <div id="$ID-all" style="position:absolute;inset:0">' + SHIFT + person_html({"clothes", "phone", "food", "travel"}, really=True) + panel_html(set()) + """
    <p id="$ID-l" class="ep-line ep-sub">You don't know.</p>""" + ('<div id="$ID-st" class="ep-stamp">Borrowed?</div>' if sid == "s28" else '') + "</div>",
            js=hide_rows(keep | {new}) + f"""
      tl.fromTo($("#$ID-{new}"), {{ opacity: 0 }}, {{ opacity: 0, duration: 0.01 }}, 0);
      row($("#$ID-{new}"), {{{{t:{word}}}}});
      tl.fromTo($("#$ID-{new} .ep-q"), {{ scale: 1 }}, {{ scale: 1.15, duration: 0.12, yoyo: true, repeat: 1, immediateRender: false }}, {{{{t:{word}}}}} + 0.25);""" + extra)
    S(sid, c.at(sid, word), "key-press", 0.35)
# s28: mark its last row's "?" to colour on 'borrowed'
p = os.path.join(c.dir, "compositions", "s28.html")
h = open(p, encoding="utf-8").read().replace('<div id="s28-paid" class="pr"><span>Paid for, or borrowed?</span><span class="ep-q">?</span>',
                                               '<div id="s28-paid" class="pr"><span>Paid for, or borrowed?</span><span id="s28-q" class="ep-q">?</span>')
open(p, "w", encoding="utf-8").write(h)
S("s28", c.at("s28", "borrowed"), "error", 0.3); S("s28", c.at("s28", "borrowed") + 0.1, "impact-bass-1", 0.2); S("s28", c.end("s28"), "swish", 0.35)

# s29 a culture of looking successful: a feed scrolls
posts = "".join(f'<div class="ep-post $ID-p" style="position:relative;margin-bottom:34px"><div class="hd"><div class="av" style="background:{g}"></div>{n}<span style="margin-left:auto;color:#6E6E73">· {h}</span></div><div class="ph" style="height:250px;background:{bg}"><i></i></div></div>'
                for n, h, g, bg in [("ama.style", "1h", "linear-gradient(135deg,#FFB86B,#F25F9A)", "linear-gradient(160deg,#FFD7A8,#F79C7A 45%,#6B4E9B)"),
                                    ("k.wins", "3h", "linear-gradient(135deg,#56CCF2,#2F80ED)", "linear-gradient(160deg,#B8E1FF,#5B8DEF 50%,#1C2E6B)"),
                                    ("dee.lux", "5h", "linear-gradient(135deg,#F2C94C,#F2994A)", "linear-gradient(160deg,#FFF1B8,#F2C94C 45%,#8C5A1E)"),
                                    ("nana.vibes", "7h", "linear-gradient(135deg,#BB6BD9,#6FCF97)", "linear-gradient(160deg,#E3D1FF,#9B6BD9 50%,#3A1E6B)")])
c.scene("s29", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-a { top: 470px; }
    #$ID-win { position: absolute; left: 230px; top: 120px; width: 500px; height: 840px; overflow: hidden; border-radius: 40px; }
    #$ID-feed { position: absolute; left: 20px; top: 20px; width: 460px; }
    #$ID-l { left: 820px; right: 192px; top: 400px; }
""", html=f"""
    <div id="$ID-all">
      <h1 id="$ID-a" class="ep-line ep-big">And that's the <b>problem.</b></h1>
      <div id="$ID-win" data-layout-allow-overflow><div id="$ID-feed">{posts}</div></div>
      <p id="$ID-l" class="ep-line ep-left ep-mid">We've created a culture where <b>looking successful</b></p>
    </div>""", js="""
      CM.speak(tl, $("#$ID-a"), {{T:and that's the problem}});
      CM.blurOut(tl, $("#$ID-a"), {{t:we've}} - 0.2);
      tl.fromTo($("#$ID-win"), { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, {{t:we've}});
      tl.fromTo($("#$ID-feed"), { y: 0 }, { y: -980, duration: 2.6, ease: "power2.inOut" }, {{t:culture}} - 0.4);
      CM.speak(tl, $("#$ID-l"), {{T:we've created a culture where looking successful}});
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s29", c.at("s29", "problem"), "pop", 0.25); S("s29", c.at("s29", "we've"), "whoosh-short", 0.35); S("s29", c.at("s29", "culture") - 0.4, "swish", 0.35); S("s29", c.end("s29"), "swoosh-fast", 0.25)

# s30 seesaw: looking successful outweighs being secure
c.scene("s30", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-beam { position: absolute; left: 460px; top: 520px; width: 1000px; height: 16px; border-radius: 8px; background: #111113; transform-origin: 50% 50%; }
    #$ID-piv { position: absolute; left: 910px; top: 536px; width: 0; height: 0; border-left: 50px solid transparent; border-right: 50px solid transparent; border-bottom: 90px solid #D6D6DB; }
    .$ID-pan { position: absolute; top: -118px; }
    #$ID-lp { left: -40px; } #$ID-rp { right: -40px; }
    #$ID-l { top: 760px; }
""", html="""
    <div id="$ID-all">
      <div id="$ID-piv"></div>
      <div id="$ID-beam"><div id="$ID-lp" class="ep-tag $ID-pan">Looking successful</div><div id="$ID-rp" class="ep-tag $ID-pan" style="color:#1F9D4C">Financially secure</div></div>
      <p id="$ID-l" class="ep-line ep-mid">sometimes matters more than actually <b>becoming financially secure.</b></p>
    </div>""", js="""
      CM.blurIn(tl, $("#$ID-piv"), 0.05);
      tl.fromTo($("#$ID-beam"), { opacity: 0, scaleX: 0.2 }, { opacity: 1, scaleX: 1, duration: 0.5, ease: "expo.out" }, 0.1);
      CM.pop(tl, $("#$ID-lp"), 0.3); CM.pop(tl, $("#$ID-rp"), 0.45);
      tl.fromTo($("#$ID-beam"), { rotation: 0 }, { rotation: -9, duration: 0.6, ease: "back.out(1.4)", immediateRender: false }, {{t:more}});
      $$(".$ID-pan").forEach((p) => tl.fromTo(p, { rotation: 0 }, { rotation: 9, duration: 0.6, ease: "back.out(1.4)", immediateRender: false }, {{t:more}}));
      CM.speak(tl, $("#$ID-l"), {{T:sometimes matters more than actually becoming financially secure}});
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s30", 0.3, "pop", 0.25); S("s30", 0.45, "bubble-pop", 0.25); S("s30", c.at("s30", "more"), "whoosh-low", 0.45); S("s30", c.end("s30"), "swoosh-fast", 0.25)

# s31 checklist: appearance ticked, the work skipped
c.scene("s31", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-l { top: 150px; }
    #$ID-list { left: 410px; top: 330px; width: 1100px; }
    #$ID-list .pr { height: 120px; font-size: 44px; white-space: nowrap; font-weight: 600; justify-content: flex-start; gap: 30px; }
    .$ID-bx { width: 64px; height: 64px; border-radius: 18px; border: 4px solid #D6D6DB; position: relative; flex: none; }
    #$ID-tick { position: absolute; left: 6px; top: 4px; }
    #$ID-strike { position: absolute; left: 94px; top: 58px; width: 660px; height: 6px; background: #E5484D; border-radius: 3px; transform-origin: 0 50%; }
    #$ID-r2 { position: relative; color: #6E6E73; }
""", html="""
    <div id="$ID-all">
      <p id="$ID-l" class="ep-line ep-sub">People want the appearance of wealth without doing the work</p>
      <div id="$ID-list" class="ep-panel">
        <div id="$ID-r1" class="pr" style="border-top:0"><div class="$ID-bx" id="$ID-b1"><svg id="$ID-tick" width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#1F9D4C" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path id="$ID-tp" d="M4 12.5l5 5L20 6"/></svg></div>Appearance of wealth</div>
        <div id="$ID-r2" class="pr"><div class="$ID-bx"></div>The difficult work of building it<div id="$ID-strike"></div></div>
      </div>
    </div>""", js="""
      CM.speak(tl, $("#$ID-l"), [ ...{{T:people want the appearance of wealth without doing the}}, {{t:work}} ]);
      CM.morph(tl, $("#$ID-list"), 0.2, { from: [0, 300, 0, 300], toRadius: 34, dur: 0.55 });
      row($("#$ID-r1"), 0.3); row($("#$ID-r2"), 0.45);
      draw($("#$ID-tp"), {{t:wealth}}, 0.3);
      tl.fromTo($("#$ID-b1"), { borderColor: "#D6D6DB" }, { borderColor: "#1F9D4C", duration: 0.2 }, {{t:wealth}});
      grow($("#$ID-strike"), {{t:without}}, 0.45);
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s31", 0.2, "enter", 0.3); S("s31", c.at("s31", "wealth"), "chime", 0.25); S("s31", c.at("s31", "without"), "whoosh-short", 0.3); S("s31", c.end("s31"), "swoosh-fast", 0.25)

# s32 buy now / remind me later
c.scene("s32", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-shop { left: 260px; top: 230px; width: 620px; }
    #$ID-shop .ph { height: 300px; border-radius: 24px; background: linear-gradient(160deg,#FFF1B8,#F2C94C 45%,#8C5A1E); margin-bottom: 26px; }
    #$ID-shop .nm { font-size: 40px; font-weight: 700; } #$ID-shop .pr2 { font-size: 34px; color: #6E6E73; margin-top: 6px; }
    #$ID-buy { margin-top: 26px; width: 100%; font-size: 36px; }
    #$ID-nt { left: 1010px; top: 330px; width: 700px; }
    #$ID-later { position: absolute; left: 1290px; top: 520px; }
    #$ID-l { top: 860px; }
""", html="""
    <div id="$ID-all">
      <div id="$ID-shop" class="ep-panel"><div class="ph"></div><div class="nm">The expensive lifestyle</div><div class="pr2">$4,200 · ships today</div><div id="$ID-buy" class="cm-btn">Buy now</div></div>
      <div id="$ID-nt" class="ep-nt"><div class="ic" style="background:#E5484D"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"><path d="M12 6v8M12 18.5v.5"/></svg></div><div><div class="tt">Financial consequences</div><div class="bd">$4,200 due · 22% interest</div></div></div>
      <div id="$ID-later" class="ep-chip">Remind me later</div>
      <p id="$ID-l" class="ep-line ep-sub">but they don't want to think about the <b>financial consequences.</b></p>
      <img id="$ID-cur" class="cm-cursor" src="assets/cursor.svg" alt="" />
    </div>""", js="""
      CM.pop(tl, $("#$ID-shop"), 0.1, { from: 0.85, ease: "expo.out", dur: 0.45 });
      const p1 = CM.tap(tl, $("#$ID-cur"), $("#$ID-buy"), root, {{t:expensive}} - 0.2, { leave: false });
      tl.fromTo($("#$ID-nt"), { opacity: 0, y: -100 }, { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, {{t:but}});
      CM.pop(tl, $("#$ID-later"), {{t:but}} + 0.3);
      const p2 = CM.tap(tl, $("#$ID-cur"), $("#$ID-later"), root, {{t:think}} - 0.35, { from: { x: CM.pos($("#$ID-buy"), root).cx, y: CM.pos($("#$ID-buy"), root).cy + 6 } });
      tl.fromTo([$("#$ID-nt"), $("#$ID-later")], { opacity: 1, x: 0 }, { opacity: 0, x: 220, duration: 0.3, ease: "power3.in", immediateRender: false }, p2 + 0.12);
      CM.speak(tl, $("#$ID-l"), {{T:but they don't want to think about the financial consequences}});
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s32", 0.1, "enter", 0.3)
_p1 = c.at("s32", "expensive") - 0.2 + 0.6; _p2 = c.at("s32", "think") - 0.35 + 0.6
S("s32", _p1, "ui-tap", 0.5); S("s32", c.at("s32", "but"), "notification", 0.3); S("s32", _p2, "ui-tap", 0.5); S("s32", _p2 + 0.12, "swoosh-fast", 0.3); S("s32", c.end("s32"), "whoosh-short", 0.25)

# s33 last money -> looking rich
c.scene("s33", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-bal { left: 560px; top: 200px; width: 800px; text-align: center; }
    #$ID-tx { left: 610px; top: 560px; width: 700px; }
    #$ID-l { top: 800px; }
""", html="""
    <div id="$ID-all">
      <div id="$ID-bal" class="ep-bal"><div class="lb">Last money this month</div><div id="$ID-amt" class="am">$50.00</div></div>
      <div id="$ID-tx" class="ep-nt"><div class="ic" style="background:#111113"></div><div><div class="tt">Designer sunglasses</div><div class="bd">Paid · −$50.00</div></div></div>
      <p id="$ID-l" class="ep-line ep-mid">would rather spend their last money <b>looking rich</b></p>
    </div>""", js="""
      CM.pop(tl, $("#$ID-bal"), 0.1, { from: 0.85, ease: "expo.out", dur: 0.45 });
      CM.speak(tl, $("#$ID-l"), {{T:would rather spend their last money looking rich}});
      tl.fromTo($("#$ID-tx"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }, {{t:last}});
      CM.count(tl, $("#$ID-amt"), {{t:money}}, 50, 0, { dur: 0.45, fmt: (n) => money(n) });
      tint($("#$ID-amt"), {{t:money}} + 0.45, "#111113", "#E5484D");
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s33", 0.1, "enter", 0.3); S("s33", c.at("s33", "last"), "message-ping", 0.3); S("s33", c.at("s33", "money") + 0.45, "error", 0.3); S("s33", c.end("s33"), "swoosh-fast", 0.25)

# s34 building a foundation, block by block, then a house
blocks = [("Emergency fund", "#DDF3E4"), ("No bad debt", "#E3EEFF"), ("Savings", "#DDF3E4"), ("Investments", "#E3EEFF")]
bh = "".join(f'<div class="$ID-b" style="background:{bg}">{t}</div>' for t, bg in blocks[::-1])
c.scene("s34", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-stack { position: absolute; left: 1060px; top: 330px; width: 560px; display: flex; flex-direction: column; gap: 12px; }
    .$ID-b { height: 100px; border-radius: 22px; display: flex; align-items: center; justify-content: center; font-family: var(--font); font-size: 38px; font-weight: 700; color: #111113; box-shadow: var(--shadow); }
    #$ID-roof { position: absolute; left: 1070px; top: 160px; width: 0; height: 0; border-left: 270px solid transparent; border-right: 270px solid transparent; border-bottom: 150px solid #111113; }
    #$ID-ok { position: absolute; left: 1195px; top: 860px; color: #1F9D4C; }
    #$ID-l { left: 192px; width: 800px; top: 360px; }
""", html=f"""
    <div id="$ID-all">
      <div id="$ID-roof"></div>
      <div id="$ID-stack">{bh}</div>
      <div id="$ID-ok" class="ep-chip">Comfortable</div>
      <p id="$ID-l" class="ep-line ep-left ep-mid">than spend a few years building the <b>financial foundation</b> that could make them <em>comfortable.</em></p>
    </div>""", js="""
      CM.speak(tl, $("#$ID-l"), [ ...{{T:than spend a few years building the financial foundation that could}}, ...{{T:make them comfortable}} ]);
      const bs = $$(".$ID-b").reverse();
      bs.forEach((b, i) => tl.fromTo(b, { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.4, ease: "bounce.out" }, {{t:years}} + i * 0.38));
      tl.fromTo($("#$ID-roof"), { opacity: 0, y: -80 }, { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, {{t:eventually}});
      CM.pop(tl, $("#$ID-ok"), {{t:comfortable}});
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
for i in range(4):
    S("s34", c.at("s34", "years") + i * 0.38 + 0.2, "key-press" if i % 2 else "click-soft", 0.4)
S("s34", c.at("s34", "eventually"), "whoosh-short", 0.3); S("s34", c.at("s34", "comfortable"), "chime", 0.3); S("s34", c.end("s34"), "swoosh-fast", 0.25)

# s35-s37: "you can ... and still ..." pairs
def pair(sid, intro, intro_phrase, left_title, left_body, left_phrase, right_title, right_body, right_phrase, flip_word, left_card_word):
    c.scene(sid, css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-in { top: 470px; }
    .$ID-c { position: absolute; top: 300px; width: 600px; height: 300px; padding: 44px 48px; }
    #$ID-L { left: 230px; } #$ID-R { left: 1090px; }
    .$ID-c .k { font-size: 30px; color: #6E6E73; font-weight: 600; }
    .$ID-c .v { font-size: 64px; font-weight: 700; letter-spacing: -0.035em; margin-top: 18px; line-height: 1.05; }
    #$ID-and { position: absolute; left: 872px; top: 420px; }
    #$ID-tl { left: 230px; right: auto; width: 600px; top: 650px; text-align: left; }
    #$ID-tr { left: 1090px; right: auto; width: 600px; top: 650px; text-align: left; }
""", html=f"""
    <div id="$ID-all">
      {('<h1 id="$ID-in" class="ep-line ep-big">' + intro + '</h1>') if intro else ''}
      <div id="$ID-L" class="ep-panel $ID-c"><div class="k">{left_title}</div><div class="v">{left_body}</div></div>
      <div id="$ID-and" class="ep-chip">and still</div>
      <div id="$ID-R" class="ep-panel $ID-c"><div class="k">{right_title}</div><div class="v ep-red">{right_body}</div></div>
      <p id="$ID-tl" class="ep-line ep-sub">{left_phrase}</p>
      <p id="$ID-tr" class="ep-line ep-sub">{right_phrase}</p>
    </div>""", js=(f"""
      CM.speak(tl, $("#$ID-in"), {{{{T:{intro_phrase}}}}});
      CM.blurOut(tl, $("#$ID-in"), {{{{t:you}}}} + 0.9);""" if intro else "") + f"""
      tl.fromTo($("#$ID-L"), {{ opacity: 0, x: -60, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, {{{{t:{left_card_word}}}}});
      CM.speak(tl, $("#$ID-tl"), {{{{T:{left_phrase.lower().replace('<b>','').replace('</b>','')}}}}});
      CM.pop(tl, $("#$ID-and"), {{{{t:{flip_word}}}}});
      tl.fromTo($("#$ID-R"), {{ opacity: 0, x: 60, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, {{{{t:{flip_word}}}}} + 0.15);
      CM.speak(tl, $("#$ID-tr"), {{{{T:{right_phrase.lower().replace('<b>','').replace('</b>','')}}}}});
      CM.blurOut(tl, $("#$ID-all"), {{{{END}}}});""")
    S(sid, c.at(sid, left_card_word), "whoosh-short", 0.3); S(sid, c.at(sid, flip_word), "pop", 0.3); S(sid, c.at(sid, flip_word) + 0.15, "whoosh-short", 0.3)
    S(sid, c.end(sid), "swoosh-fast", 0.25)

pair("s35", "Think about <b>that.</b>", "think about that", "You own", "Designer bag<br>Latest phone<br>Nice car", "You can own expensive things",
     "Emergency fund", "$0.00", "be financially vulnerable", "still", "own")
pair("s36", None, None, "Monthly income", "$8,500", "You can have a high income",
     "Day 20 balance", "$37.10", "still struggle financially", "still", "high")
S("s35", c.at("s35", "that"), "pop", 0.25)

# s37 earn more, have less (two bars)
c.scene("s37", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-l { top: 130px; }
    #$ID-g { position: absolute; left: 330px; top: 300px; width: 1260px; height: 470px; }
    .$ID-row { position: absolute; left: 0; width: 1260px; height: 96px; display: flex; align-items: center; font-family: var(--font); font-size: 36px; font-weight: 600; color: #111113; }
    .$ID-row .nm { width: 200px; }
    .$ID-row .bar { height: 64px; border-radius: 18px; transform-origin: 0 50%; display: flex; align-items: center; padding-left: 24px; color: #fff; font-size: 32px; }
    .$ID-h { position: absolute; left: 200px; font-size: 30px; color: #6E6E73; font-family: var(--font); font-weight: 600; }
    #$ID-l2 { top: 830px; }
""", html="""
    <div id="$ID-all">
      <p id="$ID-l" class="ep-line ep-sub">You can earn more money than someone else</p>
      <div id="$ID-g">
        <div class="$ID-h" style="top:0">Income</div>
        <div class="$ID-row" style="top:40px"><span class="nm">You</span><div id="$ID-i1" class="bar" style="width:900px;background:#0A84FF">$6,000</div></div>
        <div class="$ID-row" style="top:140px"><span class="nm">Them</span><div id="$ID-i2" class="bar" style="width:520px;background:#86868B">$3,500</div></div>
        <div id="$ID-h2" class="$ID-h" style="top:260px">Savings</div>
        <div class="$ID-row" style="top:300px"><span class="nm">You</span><div id="$ID-s1" class="bar" style="width:60px;background:#E5484D"></div><span id="$ID-s1v" style="margin-left:20px;color:#E5484D">$120</span></div>
        <div class="$ID-row" style="top:400px"><span class="nm">Them</span><div id="$ID-s2" class="bar" style="width:760px;background:#1F9D4C">$9,000</div></div>
      </div>
      <p id="$ID-l2" class="ep-line ep-mid">and have less financial security, because you <b>spend everything.</b></p>
    </div>""", js="""
      CM.speak(tl, $("#$ID-l"), {{T:you can earn more money than someone else}});
      grow($("#$ID-i1"), {{t:more}}, 0.6); grow($("#$ID-i2"), {{t:someone}}, 0.6);
      CM.blurIn(tl, $("#$ID-h2"), {{t:less}} - 0.2);
      grow($("#$ID-s1"), {{t:less}}, 0.5); CM.blurIn(tl, $("#$ID-s1v"), {{t:less}} + 0.3);
      grow($("#$ID-s2"), {{t:security}}, 0.6);
      CM.speak(tl, $("#$ID-l2"), [ ...{{T:and have less financial security because you}}, {{t:spend}}, {{t:everything}} ]);
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s37", c.at("s37", "more"), "whoosh-short", 0.3); S("s37", c.at("s37", "someone"), "click-soft", 0.3); S("s37", c.at("s37", "less"), "error", 0.25); S("s37", c.at("s37", "security"), "ping", 0.3); S("s37", c.end("s37"), "swoosh-fast", 0.25)

# s38 not proof of wealth
c.scene("s38", css="""
    #$ID-all { position: absolute; inset: 0; }
    #$ID-l { top: 140px; }
    #$ID-item { left: 640px; top: 300px; width: 640px; }
    #$ID-item .ph { height: 330px; border-radius: 24px; background: linear-gradient(160deg,#F6E7D7,#D9A56B 50%,#6B3F1E); }
    #$ID-item .nm { font-size: 40px; font-weight: 700; margin-top: 22px; }
    #$ID-st { left: 760px; top: 470px; transform: rotate(-10deg); }
""", html="""
    <div id="$ID-all">
      <p id="$ID-l" class="ep-line ep-sub">Your possessions are <b>not automatically</b> proof of your wealth.</p>
      <div id="$ID-item" class="ep-panel"><div class="ph"></div><div class="nm">Designer bag · $2,300</div></div>
      <div id="$ID-st" class="ep-stamp">Not proof</div>
    </div>""", js="""
      CM.speak(tl, $("#$ID-l"), {{T:your possessions are not automatically proof of your wealth}});
      CM.pop(tl, $("#$ID-item"), {{t:possessions}}, { from: 0.85, ease: "expo.out", dur: 0.45 });
      CM.pop(tl, $("#$ID-st"), {{t:proof}}, { from: 1.8, ease: "expo.out", dur: 0.3 });
      CM.blurOut(tl, $("#$ID-all"), {{END}});""")
S("s38", c.at("s38", "possessions"), "enter", 0.3); S("s38", c.at("s38", "proof"), "impact-bass-1", 0.25); S("s38", c.end("s38"), "swoosh-fast", 0.25)

# s39 proof that you know how to spend money (receipt callback); chapter end holds
c.scene("s39", css="""
    #$ID-l { left: 192px; width: 760px; top: 380px; }
    #$ID-st { left: 1090px; top: 520px; transform: rotate(-8deg); border-color: #0A84FF; color: #0A84FF; font-size: 50px; }
""", html=receipt_html(1030, 120) + """
    <p id="$ID-l" class="ep-line ep-left ep-mid">Sometimes they're simply proof that you know how to <b>spend money.</b></p>
    <div id="$ID-st" class="ep-stamp" data-layout-allow-overlap>Proof of spending</div>""", js="""
      tl.fromTo($("#$ID-rc"), { opacity: 0, y: -120 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }, 0.05);
      $$(".$ID-ri").forEach((r, i) => row(r, 0.35 + i * 0.12));
      CM.speak(tl, $("#$ID-l"), {{T:sometimes they're simply proof that you know how to spend money}});
      CM.pop(tl, $("#$ID-st"), {{t:spend}}, { from: 1.8, ease: "expo.out", dur: 0.3 });""")
S("s39", 0.05, "whoosh-short", 0.3); S("s39", 0.35, "typing", 0.3); S("s39", c.at("s39", "spend"), "impact-bass-1", 0.25)

c.done()
