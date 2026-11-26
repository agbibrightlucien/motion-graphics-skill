# cm-kit.js API

Loaded globally by the template (`window.CM`). Every helper adds tweens to the scene timeline `tl`
at absolute scene-local time `t` and **returns the time its motion ends**, so beats chain:
`let t = CM.speak(tl, line, times); t = CM.pop(tl, card, t + 0.1);`

| Helper | What it does | Key options |
|---|---|---|
| `CM.speak(tl, el, times, o)` | Words of `el` blur in at the given spoken times (`timing.json` words[].t) | `mode:"ink"` (visible grey at frame 0, words turn colour as spoken), `blur`, `scale`, `early` (default 0.05 s) |
| `CM.blurWords(tl, el, t, o)` | Words blur in on a fixed stagger (no voice) | `stagger` 0.08, `dur` 0.18, `blur` 10 |
| `CM.greyToInk(tl, el, t, o)` | Words change colour grey → ink, no motion | `stagger`, `from`, `to` |
| `CM.type(tl, el, text, t, o)` | Typewriter into `el` with caret | `cps` 20, `caret` |
| `CM.blurIn / blurOut(tl, el, t, o)` | Whole element focus-in / defocus-out | `dur`, `blur`, `scale`, `y` |
| `CM.pop(tl, el, t, o)` | Scale-in with overshoot (chips, icons, cards) | `from` 0.6, `ease`, `dur` |
| `CM.roll(tl, stack, t, o)` | Slot-machine roll through the children of `stack` (a column inside an `overflow:hidden` window one item tall) | `step` 0.12 |
| `CM.count(tl, el, t, from, to, o)` | Number counts in `el` | `dur`, `ease`, `fmt(n)` |
| `CM.assemble / scatter(tl, el, t, o)` | Words fly in from / out to a seeded scatter | `seed`, `spread`, `dur` |
| `CM.morph(tl, el, t, o)` | clip-path morph from a pill to the full box | `from:[top,right,bottom,left]` px insets, `fromRadius`, `toRadius`, `fade:false` to stay visible at start |
| `CM.tap(tl, cursor, target, root, t, o)` | Cursor glides to `target`, presses; returns the **press time** (put `ui-tap` there) | `from:{x,y}`, `travel`, `dx/dy`, `leave` |
| `CM.camera(tl, stage, t, o)` | Push/pan a wrapper (`.cm-stage`) | `scale`, `x`, `y`, `dur`, `fromScale` |
| `CM.whip(tl, outEl, inEl, t, o)` | Fast horizontal exit/entry with blur | `dir` left/right, `dist`, `dur` |
| `CM.barcode(tl, el, t, o)` | Vertical streak glitch for ~5 frames | `amount` 60, `dur` 0.16 |
| `CM.iris(tl, el, t, o)` | Circle reveal of `el` | `x`, `y` (CSS %), `dur` |
| `CM.lens(tl, el, t, o)` | Defocused zoom-in reveal | `dur` |
| `CM.flood(tl, bg, t, toBackground?)` | Fade in a full-bleed colour/gradient layer | `dur` |
| `CM.rng(seed)` | Seeded random generator (use instead of Math.random) | — |
| `CM.pos(el, root)` | Element box relative to root, transform-free | — |

## CSS parts (cm-kit.css)
Themes via `data-theme` on the root (set by `cmv.py new --theme`): `light`, `cream`, `blush`,
`sky`, `periwinkle`, `dark`, `mono`. Variables: `--bg --ink --muted --accent --accent-2 --card
--shadow --radius --font --font-mono --font-serif --font-condensed`.

Classes: `.cm-ground` (full-bleed background), `.cm-stage` (centred camera wrapper), `.cm-line`
(text line; `b` accent, `em` quiet, `.cm-glow` red glow), `.cm-mono`, `.cm-serif`, `.cm-heavy`,
`.cm-script`, `.cm-card`, `.cm-pill`, `.cm-glass`, `.cm-search`, `.cm-btn`, `.cm-chip`,
`.cm-bubble-in`, `.cm-bubble-out`, `.cm-avatar`, `.cm-icon`, `.cm-cursor` (use
`<img class="cm-cursor" src="assets/cursor.svg">`), `.cm-phone > .cm-screen`, `.cm-grain`,
`.cm-vignette`.

## Gotchas
- Query elements through the scene root: `const root = document.querySelector('[data-composition-id="<id>"]')`.
- Elements built by script (e.g. chart bars) must be created **before** any tween.
- A second tween on the same element and property needs `immediateRender: false` (the helpers'
  exit tweens already set it).
- `CM.speak` splits the element's words once; don't call two word helpers on the same element.
