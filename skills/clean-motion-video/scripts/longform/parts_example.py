"""Example recurring layouts for a long-form film (section title, person + tags, receipt, info panel)."""


def section(c, sid, n, label, title_html, title_phrase, total=6, sub_html=None, sub_phrase=None):
    """Point n of 6: segment bar fills, black pill ("First"), title speaks. Exits before the next beat."""
    segs = "".join(f'<i><b class="$ID-sg{k}"></b></i>' for k in range(1, total + 1))
    css = """    #$ID-pw { position: absolute; left: 0; right: 0; top: 330px; text-align: center; }
    #$ID-t { top: 470px; }
    #$ID-all { position: absolute; inset: 0; }"""
    html = f"""    <div id="$ID-all">
      <div class="ep-segs">{segs}</div>
      <div id="$ID-pw"><span id="$ID-pill" class="ep-pill"><span class="ep-num">{n:02d}</span>{label}</span></div>
      <h1 id="$ID-t" class="ep-line ep-big">{title_html}</h1>
      {('<p id="$ID-s" class="ep-line ep-sub" style="top:760px">' + sub_html + '</p>') if sub_html else ''}
    </div>"""
    pre = "".join(f'tl.fromTo($(".$ID-sg{k}"), {{ scaleX: 1 }}, {{ scaleX: 1, duration: 0.01 }}, 0);\n' for k in range(1, n))
    rest = "".join(f'tl.fromTo($(".$ID-sg{k}"), {{ scaleX: 0 }}, {{ scaleX: 0, duration: 0.01 }}, 0);\n' for k in range(n + 1, total + 1))
    js = pre + rest + f"""
      CM.morph(tl, $("#$ID-pill"), 0.0, {{ from: [0, 90, 0, 90], toRadius: 999, dur: 0.45 }});
      grow($(".$ID-sg{n}"), {{{{t:{label.split()[0]}}}}}, 0.6);
      CM.speak(tl, $("#$ID-t"), {{{{T:{title_phrase}}}}});
      CM.blurOut(tl, $("#$ID-all"), {{{{END}}}});"""
    if sub_html:
        js += f"""
      CM.speak(tl, $("#$ID-s"), {{{{T:{sub_phrase}}}}});"""
    c.scene(sid, css, html, js)
    c.sfx(sid, 0.0, "whoosh-low", 0.45)
    c.sfx(sid, c.at(sid, label.split()[0]), "enter", 0.35)
    c.sfx(sid, c.end(sid), "swoosh-fast", 0.3)


PERSON_TAGS = [  # (key, text, left, top)
    ("clothes", "Designer clothes", 470, 560),
    ("phone", "Latest phone", 1240, 600),
    ("food", "Fancy restaurants", 430, 380),
    ("travel", "Travels often", 1250, 330),
]


def person_html(shown, stamp=False, red=False, really=False):
    """Person figure + the tags in `shown` (static). Wrapped in #$ID-pg."""
    tags = "".join(
        f'<div id="$ID-{k}" class="ep-tag{" red" if red else ""}" style="left:{x}px;top:{y}px">{txt}</div>'
        for k, txt, x, y in PERSON_TAGS if k in shown)
    st = ('<div id="$ID-ok" class="ep-tag" style="left:735px;top:790px;color:#1F9D4C">Doing well financially</div>'
          if stamp else "")
    if really:
        st += '<div id="$ID-really" class="ep-tag" style="left:860px;top:790px;color:#6E6E73">Really?</div>'
    return f"""    <div id="$ID-pg" style="position:absolute;inset:0">
      <div id="$ID-person" class="ep-person" style="left:800px;top:290px"><div class="hd"></div><div class="bd"></div></div>
      {tags}{st}
    </div>"""


PANEL_ROWS = [("debt", "Debt"), ("sav", "Savings"), ("m3", "3 months without income"), ("paid", "Paid for, or borrowed?")]


def panel_html(shown):
    rows = "".join(f'<div id="$ID-{k}" class="pr"><span>{txt}</span><span class="ep-q">?</span></div>'
                   for k, txt in PANEL_ROWS if k in shown or True)
    return f"""    <div id="$ID-panel" class="ep-panel" style="left:1170px;top:250px;width:560px">
      <h5>What you can't see</h5>{rows}
    </div>"""


RECEIPT_ITEMS = [("iPhone 16 Pro", "1,199.00"), ("Sneakers", "240.00"), ("Designer clothes", "680.00"),
                 ("Fancy dinner", "310.00"), ("Weekend getaway", "900.00"), ("Car payment", "520.00")]


def receipt_html(left, top, total="3,849.00", rid="$ID-rc"):
    rows = "".join(f'<div class="ri $ID-ri"><span>{a}</span><span>{b}</span></div>' for a, b in RECEIPT_ITEMS)
    return f"""    <div id="{rid}" class="ep-rc" style="left:{left}px;top:{top}px">
      <h4>LIFESTYLE CO.</h4><div class="meta">ORDER #0047 · PAID IN FULL?</div><hr />{rows}
      <hr /><div class="tot"><span>TOTAL</span><span class="ep-red">{total}</span></div>
    </div>"""
