# Style guide (numbers, not adjectives)

Distilled from 40 reference videos. These are the numbers for the default clean look; other looks
(paper, midnight, bold, sunset, forest, candy, noir) change palette, type and motion per `looks.md`.
A brand guide or an explicit request wins.

## Canvas
- Backgrounds: `light` #F4F4F6 (default), `cream` #F3F1EA (premium/editorial), `blush` white→#FBE3E5
  (problem beats), `sky` white→#DCEBFF (solution beats), `periwinkle` #6B9BE0 (social/consumer apps),
  `dark` #0E0E10 (contrast beat: logo sting, "Use AI", voice orb), `mono` grey radial + vignette
  (documentary/manifesto).
- Saturation stays low. Colour arrives one element at a time; ONE accent per film (brand colour, or
  iOS blue #0A84FF). Green #1F9D4C only for money-up/success, red #FF3B30/#E5484D only for problems.
- Optional texture: `.cm-grain` (6% noise) on cream/mono; `.cm-vignette` on mono.

## Type
- Inter 500 for lines, 700 for hero numbers/headlines; letter-spacing −0.025em (−0.045em at 100 px+).
- Sizes (1080-wide canvas): hero 100–136 px, line 64–96 px, sub 44–56 px, UI labels 30–40 px.
  Keep it smaller than you think: empty space is the style.
- Secondary voices: `.cm-mono` (typewriter beats, "Quick question."), `.cm-serif` (premium/editorial
  brands), `.cm-heavy` condensed caps + `.cm-script` accents (documentary only).
- Emphasis: one `<b>` accent word per line; `<em>` for a quieter last word; `.cm-glow` for one red
  problem phrase ("Est. delivery: I don't know").

## Motion
- Word entrance: blur 10 px → 0, scale 1.08 → 1, 0.18 s, `power3.out`, words 60–120 ms apart or on
  their spoken times. No translate on words.
- UI arrival: pop (scale 0.6 → 1, `back.out(1.6)`, 0.35 s) for chips/icons; card arrival scale
  0.85 → 1, `expo.out`, 0.45–0.5 s.
- Morph: clip-path from a pill to the full box, `expo.out`, 0.45–0.6 s.
- Typing: 18–24 characters per second with a caret; push the camera in (scale 1.4–1.8) when the
  field is the subject.
- Cursor: glides 0.5–0.6 s `power3.inOut`, presses (cursor 0.82, target 0.95, 80 ms each way).
- Exits: blur-out 0.16 s, or scale-through (scale 1.6 + blur 14 px, 0.3 s `power3.in`), or whip.
- Holds: a line holds ~0.5 s + 0.3 s/word after its last word; the end card ≥ 2 s.
- Never: floating/breathing loops, bounce on big UI, every element sliding up, slow creeping zooms.

## Transitions (use 3–5 kinds per film)
| Kind | When | Helper |
|---|---|---|
| Morph / grow-out | default between related beats | `CM.morph`, `CM.pop` |
| Blur swap | same stage, new text | `CM.blurOut` → `CM.speak` |
| Scale-through | zoom into the thing that becomes the next beat | fromTo scale 1→1.6 + blur |
| Whip | change of topic, fast energy | `CM.whip` |
| Barcode glitch | punchy cut accent, 4–5 frames | `CM.barcode` |
| Iris / lens | reveal a new world (map, app, logo) | `CM.iris`, `CM.lens` |
| Colour flood | problem → solution, mood change | `CM.flood` |
| Hard cut | only into a contrast beat (dark end card) | — |

## Composition
- One idea per beat, centred in the safe area (vertical: x 120–888, y 288–1248; below y 840
  keep within x 120–780). Centre the beat's group around y ≈ 800 (not 960, which pushes text
  into the narrow band; not 500, which leaves the lower half dead).
- Text above, UI below (or UI inline in the sentence: "Your [revenue card] is limited by one number").
- Cards: white, radius 28, soft shadow (`.cm-card`). Pills: black or glass. Avatars round.
- Prefer real UI-looking elements (search bars, chat bubbles, notification cards, calendars,
  balance cards, buttons) over abstract shapes or icons-as-decoration. No emoji as icons.
- Brand logos: use the real file (SVG/PNG from the brand or the user), never redraw.

## Pacing
- Median reference length 11.6 s; ours 12–20 s with voice. Beats 2–5 s.
- Shot changes are rare (median shot 3.8 s); motion inside the shot never stops for > 0.6 s.
- Frame 0 must already show something meaningful (it is the thumbnail).
