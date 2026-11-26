/* cm-kit.js: clean-motion-video helper library for HyperFrames scenes.
 *
 * Every helper ADDS tweens to a paused GSAP timeline you pass in, at an absolute
 * time t (seconds, local to the scene), and returns the time its motion ends so
 * beats can be chained:  let t = CM.blurWords(tl, el, 0.2);  t = CM.pop(tl, card, t + 0.1);
 *
 * Rules it follows (HyperFrames contract): fromTo only, no timers, no unseeded
 * randomness, layout measured once at build time, transforms instead of
 * width/height, never tweens display/visibility on a .clip (animate children).
 */
(function () {
  const CM = {};

  // ---------- utilities ----------
  CM.$ = (root, sel) => (typeof sel === "string" ? root.querySelector(sel) : sel);

  // Seeded PRNG (mulberry32) so "random" layouts render identically every time.
  CM.rng = function (seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  // Position of el relative to an ancestor, ignoring transforms (safe in a scaled preview).
  CM.pos = function (el, ancestor) {
    let x = 0, y = 0, n = el;
    while (n && n !== ancestor) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight, cx: x + el.offsetWidth / 2, cy: y + el.offsetHeight / 2 };
  };

  // Wrap each word of el in <span class="cm-w">; keeps <em>/<b> accent spans as one word group.
  CM.splitWords = function (el) {
    if (el.dataset.cmSplit) return Array.from(el.querySelectorAll(".cm-w"));
    const out = [];
    const walk = (node, parent) => {
      Array.from(node.childNodes).forEach((c) => {
        if (c.nodeType === 3) {
          c.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) { parent.appendChild(document.createTextNode(" ")); return; }
            const s = document.createElement("span"); s.className = "cm-w"; s.textContent = part;
            parent.appendChild(s); out.push(s);
          });
        } else if (c.nodeType === 1) {
          const clone = c.cloneNode(false); parent.appendChild(clone); walk(c, clone);
        }
      });
    };
    const frag = document.createElement(el.tagName); walk(el, frag);
    el.innerHTML = frag.innerHTML; el.dataset.cmSplit = "1";
    return Array.from(el.querySelectorAll(".cm-w"));
  };

  // Word-entrance style. "soft" (fade + light blur, no size change) is calmer for long or fast
  // narration, where the default scale-snap on every word reads as jitter. Set it with
  // data-word-style="soft" on the root (index.html #root); the default is the short-form "pop".
  CM.wordStyle = function () {
    const soft = !!document.querySelector('[data-word-style="soft"]');
    return soft ? { blur: 6, scale: 1, dur: 0.28, ease: "power2.out" } : { blur: 10, scale: 1.08, dur: 0.18, ease: "power3.out" };
  };

  // ---------- text ----------
  // Signature move: each word arrives blurred + slightly scaled and sharpens. No translate.
  CM.blurWords = function (tl, el, t, o = {}) {
    const words = CM.splitWords(el), ws = CM.wordStyle();
    const st = o.stagger ?? 0.08, d = o.dur ?? ws.dur, b = o.blur ?? ws.blur;
    words.forEach((w, i) => {
      tl.fromTo(w, { opacity: 0, filter: `blur(${b}px)`, scale: o.scale ?? ws.scale },
        { opacity: 1, filter: "blur(0px)", scale: 1, duration: d, ease: ws.ease }, t + i * st);
    });
    return t + (words.length - 1) * st + d;
  };

  // Voice-synced blur-in: word i appears at times[i] (scene-local seconds, copy them from
  // timing.json "words[].t"). Extra words without a time follow 0.08 s after the previous one.
  CM.speak = function (tl, el, times, o = {}) {
    const words = CM.splitWords(el), ws = CM.wordStyle();
    const d = o.dur ?? ws.dur, b = o.blur ?? ws.blur;
    let last = times[0] ?? 0;
    // mode "ink": the whole line is visible from frame 0 in light grey (a real thumbnail),
    // and each word turns to its own colour as it is spoken. Use it for the hook line.
    const ink = o.mode === "ink";
    words.forEach((w, i) => {
      const at = times[i] != null ? times[i] - (o.early ?? 0.05) : last + 0.08;
      last = at;
      if (ink) {
        const target = getComputedStyle(w).color;
        tl.fromTo(w, { color: o.from ?? "#C9C9CE" }, { color: target, duration: 0.16, ease: "power2.out" }, Math.max(0, at));
      } else {
        tl.fromTo(w, { opacity: 0, filter: `blur(${b}px)`, scale: o.scale ?? ws.scale },
          { opacity: 1, filter: "blur(0px)", scale: 1, duration: d, ease: ws.ease }, Math.max(0, at));
      }
    });
    return last + d;
  };

  // Words go from light grey to ink, no movement (quiet emphasis build).
  CM.greyToInk = function (tl, el, t, o = {}) {
    const words = CM.splitWords(el);
    const st = o.stagger ?? 0.09;
    words.forEach((w, i) => tl.fromTo(w, { color: o.from ?? "#C7C7CC" }, { color: o.to ?? "currentColor", duration: 0.2, ease: "power2.out" }, t + i * st));
    return t + words.length * st + 0.2;
  };

  // Typewriter into el (an input, a search bar...). cps = characters per second.
  // Deterministic: text is a pure function of tween progress.
  CM.type = function (tl, el, text, t, o = {}) {
    const cps = o.cps ?? 20, d = Math.max(0.2, text.length / cps);
    const caret = o.caret !== false;
    const proxy = { p: 0 };
    tl.fromTo(proxy, { p: 0 }, {
      p: 1, duration: d, ease: "none",
      onUpdate: () => {
        const n = Math.round(proxy.p * text.length);
        el.textContent = text.slice(0, n);
        if (caret) el.dataset.caret = proxy.p < 1 ? "on" : "off";
      },
    }, t);
    return t + d;
  };

  // Whole element blurs in / out (lines, cards, logos).
  CM.blurIn = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.22;
    tl.fromTo(el, { opacity: 0, filter: `blur(${o.blur ?? 12}px)`, scale: o.scale ?? 1.04, y: o.y ?? 0 },
      { opacity: 1, filter: "blur(0px)", scale: 1, y: 0, duration: d, ease: o.ease ?? "power3.out" }, t);
    return t + d;
  };
  CM.blurOut = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.16;
    tl.fromTo(el, { opacity: 1, filter: "blur(0px)", scale: 1 },
      { opacity: 0, filter: `blur(${o.blur ?? 10}px)`, scale: o.scale ?? 0.98, duration: d, ease: "power2.in", immediateRender: false }, t);
    return t + d;
  };

  // Pop: element scales in with a small overshoot (chips, icons, badges, bubbles).
  CM.pop = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.35;
    tl.fromTo(el, { opacity: 0, scale: o.from ?? 0.6, filter: "blur(6px)" },
      { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: o.ease ?? "back.out(1.6)" }, t);
    return t + d;
  };

  // Slot roll: show each child of `stack` in turn like a picker; lands on the last.
  CM.roll = function (tl, stack, t, o = {}) {
    const items = Array.from(stack.children);
    const step = o.step ?? 0.12;
    const h = items[0].offsetHeight;
    items.forEach((it, i) => tl.fromTo(it, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t));
    tl.fromTo(stack, { y: 0, filter: "blur(0px)" }, {
      y: -h * (items.length - 1), duration: step * (items.length - 1), ease: o.ease ?? "power2.inOut",
    }, t);
    tl.fromTo(stack, { filter: "blur(3px)" }, { filter: "blur(0px)", duration: 0.15, ease: "power2.out", immediateRender: false }, t + step * (items.length - 1));
    return t + step * (items.length - 1) + 0.15;
  };

  // Count a number up/down inside el. fmt(n) formats the display.
  CM.count = function (tl, el, t, from, to, o = {}) {
    const d = o.dur ?? 0.9, fmt = o.fmt ?? ((n) => Math.round(n).toLocaleString("en-US"));
    const proxy = { v: from };
    tl.fromTo(proxy, { v: from }, { v: to, duration: d, ease: o.ease ?? "power3.out", onUpdate: () => (el.textContent = fmt(proxy.v)) }, t);
    return t + d;
  };

  // Words fly in from a seeded scatter and settle into the sentence.
  CM.assemble = function (tl, el, t, o = {}) {
    const words = CM.splitWords(el), r = CM.rng(o.seed ?? 7);
    const spread = o.spread ?? 420, d = o.dur ?? 0.7;
    words.forEach((w, i) => {
      tl.fromTo(w, { x: (r() - 0.5) * spread * 2, y: (r() - 0.5) * spread, opacity: 0, filter: "blur(8px)", rotation: (r() - 0.5) * 20 },
        { x: 0, y: 0, opacity: 1, filter: "blur(0px)", rotation: 0, duration: d, ease: "expo.out" }, t + i * 0.03);
    });
    return t + words.length * 0.03 + d;
  };
  CM.scatter = function (tl, el, t, o = {}) {
    const words = CM.splitWords(el), r = CM.rng(o.seed ?? 11);
    const spread = o.spread ?? 420, d = o.dur ?? 0.5;
    words.forEach((w) => {
      tl.fromTo(w, { x: 0, y: 0, opacity: 1, filter: "blur(0px)" },
        { x: (r() - 0.5) * spread * 2, y: (r() - 0.5) * spread, opacity: 0, filter: "blur(8px)", duration: d, ease: "power3.in", immediateRender: false }, t);
    });
    return t + d;
  };

  // ---------- UI ----------
  // Morph a container by clip-path (no width/height tweens): from a small pill to its full box.
  // fromInset/toInset are [top,right,bottom,left] in px; radius in px.
  CM.morph = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.45;
    const f = o.from ?? [0, el.offsetWidth * 0.4, 0, el.offsetWidth * 0.4];
    const to = o.to ?? [0, 0, 0, 0];
    const ins = (a, r) => `inset(${a[0]}px ${a[1]}px ${a[2]}px ${a[3]}px round ${r}px)`;
    tl.fromTo(el, { clipPath: ins(f, o.fromRadius ?? 999), opacity: o.fade === false ? 1 : 0.0 },
      { clipPath: ins(to, o.toRadius ?? 28), opacity: 1, duration: d, ease: o.ease ?? "expo.out" }, t);
    return t + d;
  };

  // Fake cursor glides to target, presses, target dips. Returns the press time (put the tap sfx there).
  CM.tap = function (tl, cursor, target, root, t, o = {}) {
    const p = CM.pos(target, root);
    const from = o.from ?? { x: p.cx + 260, y: p.cy + 220 };
    const tx = p.cx + (o.dx ?? 0), ty = p.cy + (o.dy ?? 6);
    const travel = o.travel ?? 0.55;
    tl.fromTo(cursor, { x: from.x, y: from.y, opacity: 0, scale: 1 },
      { x: tx, y: ty, opacity: 1, duration: travel, ease: "power3.inOut" }, t);
    const press = t + travel + 0.05;
    tl.fromTo(cursor, { scale: 1 }, { scale: 0.82, duration: 0.08, ease: "power2.in", yoyo: true, repeat: 1, immediateRender: false }, press - 0.08);
    tl.fromTo(target, { scale: 1 }, { scale: 0.95, duration: 0.08, ease: "power2.in", yoyo: true, repeat: 1, immediateRender: false }, press - 0.08);
    if (o.leave !== false) tl.fromTo(cursor, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, press + 0.35);
    return press;
  };

  // Camera push: scale/translate a stage wrapper so a point fills the frame (e.g. an input being typed).
  CM.camera = function (tl, stage, t, o = {}) {
    const d = o.dur ?? 0.8;
    tl.fromTo(stage, { scale: o.fromScale ?? 1, x: o.fromX ?? 0, y: o.fromY ?? 0 },
      { scale: o.scale ?? 1.6, x: o.x ?? 0, y: o.y ?? 0, duration: d, ease: o.ease ?? "power2.inOut", immediateRender: false }, t);
    return t + d;
  };

  // ---------- transitions ----------
  // Whip: out-element leaves fast one way, in-element arrives blurred from the other and sharpens.
  // Pair with data-motion-blur="on" on the root for a real smear.
  CM.whip = function (tl, outEl, inEl, t, o = {}) {
    const dist = o.dist ?? 900, dir = o.dir === "right" ? 1 : -1, d = o.dur ?? 0.28;
    if (outEl) tl.fromTo(outEl, { x: 0, opacity: 1 }, { x: dist * dir, opacity: 0, duration: d, ease: "power3.in", immediateRender: false }, t);
    if (inEl) tl.fromTo(inEl, { x: -dist * dir, opacity: 0, filter: "blur(10px)" }, { x: 0, opacity: 1, filter: "blur(0px)", duration: d + 0.12, ease: "expo.out" }, t + d * 0.7);
    return t + d * 0.7 + d + 0.12;
  };

  // "Barcode" glitch: vertical streak smear for ~4 frames (the account's signature cut accent).
  CM.barcode = function (tl, el, t, o = {}) {
    const id = "cm-vs-" + Math.floor(CM.rng(o.seed ?? (t * 1000) | 0)() * 1e9);
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "0"); svg.setAttribute("height", "0"); svg.style.position = "absolute";
    svg.innerHTML = `<filter id="${id}" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="0 0"/></filter>`;
    el.parentNode.insertBefore(svg, el);
    const blur = svg.querySelector("feGaussianBlur");
    const d = o.dur ?? 0.16;
    tl.fromTo(el, { filter: `url(#${id})` }, { filter: `url(#${id})`, duration: 0.01 }, t);
    tl.fromTo(blur, { attr: { stdDeviation: "0 0" } }, { attr: { stdDeviation: `0 ${o.amount ?? 60}` }, duration: d / 2, ease: "power2.in" }, t);
    tl.fromTo(blur, { attr: { stdDeviation: `0 ${o.amount ?? 60}` } }, { attr: { stdDeviation: "0 0" }, duration: d / 2, ease: "power2.out", immediateRender: false }, t + d / 2);
    tl.fromTo(el, { scaleY: 1 }, { scaleY: 1.25, duration: d / 2, yoyo: true, repeat: 1, ease: "power2.inOut", immediateRender: false }, t);
    tl.fromTo(el, { filter: `url(#${id})` }, { filter: "none", duration: 0.01, immediateRender: false }, t + d);
    return t + d;
  };

  // Iris: next layer opens as a circle from a point (default centre).
  CM.iris = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.5, x = o.x ?? "50%", y = o.y ?? "50%";
    tl.fromTo(el, { clipPath: `circle(0% at ${x} ${y})` }, { clipPath: `circle(150% at ${x} ${y})`, duration: d, ease: o.ease ?? "power3.inOut" }, t);
    return t + d;
  };

  // Lens reveal: soft white vignette clears onto the next layer (the "See who's around you" move).
  CM.lens = function (tl, el, t, o = {}) {
    const d = o.dur ?? 0.6;
    tl.fromTo(el, { opacity: 0, scale: 1.25, filter: "blur(16px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: "expo.out" }, t);
    return t + d;
  };

  // Colour flood: background colour/gradient change while the hero stays (problem -> solution).
  CM.flood = function (tl, bg, t, toBackground, o = {}) {
    const d = o.dur ?? 0.45;
    tl.fromTo(bg, { opacity: 0 }, { opacity: 1, duration: d, ease: "power2.inOut" }, t);
    if (toBackground) bg.style.background = toBackground;
    return t + d;
  };

  window.CM = CM;
})();
