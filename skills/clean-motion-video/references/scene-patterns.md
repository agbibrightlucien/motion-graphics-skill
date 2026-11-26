# Scene patterns

Copy-ready scene files. Replace ids (prefix every id with the scene id), copy, and times.
Positions assume vertical 1080×1920; for landscape, centre with `.cm-stage` and scale sizes ~0.8.
A complete, rendered example lives in `examples/compound-interest/compositions/`.

## Skeleton (every scene)
```html
<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; }
    #s1-line { position: absolute; left: 120px; right: 192px; top: 600px; font-size: 88px; } /* group centred ~y 800 */
  </style>
  <div id="root" data-composition-id="s1" data-width="1080" data-height="1920">
    <div class="cm-ground"></div>
    <h1 id="s1-line" class="cm-line">Words with one <b>accent</b> word.</h1>
  </div>
  <script>
    (function () {
      const root = document.querySelector('[data-composition-id="s1"]');
      const $ = (s) => root.querySelector(s);
      const tl = gsap.timeline({ paused: true });
      CM.speak(tl, $("#s1-line"), [0.15, 0.4, 0.62, 0.9, 1.2]);   // from timing.json
      CM.blurOut(tl, $("#s1-line"), 2.8);                          // exit near the scene end
      window.__timelines["s1"] = tl;
    })();
  </script>
</template>
```
The scene id must match its file name, the `data-composition-id`, and the timeline key.

## 1. Hook: search bar types the question (frame 0 = thumbnail)
```html
<h1 id="h-line" class="cm-line">What if your money <b>grew</b> while you slept?</h1>
<div id="h-bar" class="cm-search" data-layout-allow-overflow>
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#86868B" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
  <span id="h-q" style="flex:1;white-space:nowrap"></span>
  <div id="h-go" style="width:76px;height:76px;border-radius:50%;background:#111113"></div>
</div>
<img id="h-cursor" class="cm-cursor" src="assets/cursor.svg" alt="" />
```
```js
CM.speak(tl, $("#h-line"), times, { mode: "ink" });
CM.morph(tl, $("#h-bar"), 0, { from: [0, 262, 0, 262], toRadius: 999, dur: 0.6, fade: false }); // inset < half width
CM.type(tl, $("#h-q"), "grow my money", 0.75, { cps: 22 });
const press = CM.tap(tl, $("#h-cursor"), $("#h-go"), root, 1.25);            // ui-tap at `press`
tl.fromTo($("#h-bar"), { scale: 1, opacity: 1, filter: "blur(0px)" },
  { scale: 1.6, opacity: 0, filter: "blur(14px)", duration: 0.3, ease: "power3.in", immediateRender: false }, 2.6); // scale-through exit
```
SFX: `enter` 0.3 · `mech-typing` 0.75 · `ui-tap` press · `whoosh-short` 2.6

## 2. Statement + proof card + chips
```js
CM.speak(tl, line, times);
CM.pop(tl, card, 1.8, { from: 0.85, ease: "expo.out", dur: 0.45 });
CM.pop(tl, chip1, 2.4); CM.pop(tl, chip2, 3.1);
```
Card: `<div class="cm-card"><div class="lbl">Savings</div><div class="amt">$1,000</div></div>`;
chips: `<div class="cm-chip" style="color:#1F9D4C;font-weight:700">+$80</div>` overlapping the card's corner.
SFX: `enter` card · `pop` / `bubble-pop` chips · `swoosh-fast` exit

## 3. Number grows (count + bars)
Build bars in script first, then: `CM.count(tl, amt, t0, 10000, 46610, { dur: 2.2, ease: "power2.in", fmt })`,
bars `fromTo scaleY 0.04→1` staggered across the same window, final colour flip to green at the end.
SFX: `glass-swell` landing at the end of the count, `ping` on the final number.

## 4. Chat / message beat
```html
<div id="m-in" class="cm-bubble-in">Hey, you coming?</div>
<div id="m-out" class="cm-bubble-out">But I need a ride</div>
```
```js
CM.pop(tl, $("#m-in"), 0.2, { from: 0.7 });   // message-ping
CM.pop(tl, $("#m-out"), 1.1, { from: 0.7 });  // message-ping (lower volume) or pop
```
Bubbles enter from their side: add `x: ±40` to the from-state by wrapping in your own fromTo if wanted.

## 5. Notification stack on a phone
`.cm-phone > .cm-screen` (a screenshot or a built UI inside), then notification cards
(`.cm-card` 600 px wide, avatar + two lines) dropping in: `fromTo y -60→0, opacity 0→1, expo.out 0.45`,
each 0.35 s apart; the phone itself arrives with `CM.lens` or a tilted `fromTo rotationX 18→0`.
SFX: `notification` per card (rotate with `message-ping`).

## 6. Problem → solution (VSL)
Two layers: blush ground (problem) and a `sky` gradient div above it at opacity 0. The problem UI
(red calendar, red number with `.cm-glow`) shows first; on "we fix that": `CM.flood(tl, skyLayer, t)`,
swap the UI's red parts to blue (fromTo `color`/`backgroundColor`), pop in the filled state.
SFX: `error` (soft) on the problem, `swish` on the flood, `enter`/`pop` on the new items.

## 7. Inline UI in the sentence
```html
<div class="cm-line" style="display:flex;align-items:center;justify-content:center;gap:24px;font-size:64px">
  <span id="i-a">Your</span><div id="i-card" class="cm-card" style="padding:18px 26px">…</div><span id="i-b">is limited by one number</span>
</div>
```
`CM.speak` the spans, `CM.pop` the card on its word, then `CM.camera` push into the card for the next beat.

## 8. Logo / wordmark end card (contrast beat)
Dark ground (`#0E0E10` div), wordmark `CM.lens` at 0.08, sub line `CM.blurIn` at 0.45; hold ≥ 2 s
(scene `min` ≥ 2.6). Real logo files only (`<img src="assets/logo.svg">`), never redrawn.
SFX: `magic-whoosh` (peak on the reveal), optionally `impact-bass-1` at low volume.

## 9. Slot roll (dates, options, prices)
```html
<div style="height:120px;overflow:hidden"><div id="r-stack"><div>13</div><div>14</div><div>15</div><div>16</div></div></div>
```
`CM.roll(tl, $("#r-stack"), t, { step: 0.12 })`. SFX: `key-press` every step (rotate volume), `pop` on the last.

## 10. Barcode glitch cut
At a beat change: `CM.barcode(tl, outgoingWrapper, t)` then the next scene starts with a hard entry.
SFX: `glitch-1` at volume 0.25, or `granular-transition`.
