# Footage mode: edit the user's own talking-head clips

Use this mode when the user gives **raw video of themselves** (a phone clip, several takes, a folder of clips)
and wants it edited into a short. The look is the **"split + face"** style, studied from 30 videos of a
popular talking-head creator (fast "split + face" tech explainers). Copy the editing
patterns, **not** that creator's colours or topics: palette and imagery come from the user's own subject.

## The style in numbers
- **Two layouts, switching every ~3 s** (median shot 2.8 s; 20–25 cuts in a 55 s video):
  - **split** (~60% of screen time): plain palette ground. The panel is kicker (y≈292) + headline (y≈340) + cards
    (y≈560–930) + caption word (y≈928) + a small sub-label (y≈1056). The **face window** is a rounded
    rect from x 247 to 833, y 1262 to the bottom. The person is cut out, so their **head pops ~90 px above
    the window's top edge**.
  - **face** (~40%): full-frame footage. The framing changes on every cut (zoom 1.0 / 1.12 / 1.22,
    centred on the face), so a jump cut reads as a punch-in.
- **When to use which:** split for facts, names, places, numbers, lists and steps; face for opinions,
  reactions, jokes, "trust me", the hook's punch and the CTA. Never three face beats in a row.
- **Zero dead air**: the edit leaves no pause over ~0.25 s; switching layout hides the jump cuts.
- **Captions**: one word at a time (plan `"captions": {"words": 1}`; 2–3 if preferred), white on a
  faint dark box, between the panel and the face window, **on split beats only**. Full-face beats stay
  clean by default (`"captions": {"face": true}` turns them back on).
- **Flashes**: a light leak tinted to the palette, about 2 per video, on topic changes (set `"flash": true`
  on the beat that starts the new topic).
- **Sound**: the voice leads. A low music bed (≈0.08–0.12) and only a few soft SFX (whoosh on a flash,
  a tick per checklist row, a pop on a stat). **Keep SFX volumes ≤ 0.25**: this creator's mixes are
  nearly SFX-free, and loud SFX fight the speaker's own voice.
- **Script shape** of the user's talk (don't rewrite their words; pick the beats): a hook claim in the first
  second → one line of context → 3–5 concrete beats → a face-beat reaction between them → CTA on face.

## Style A and its layouts (the default; B and fused are retired)

A user chose style A (graphics + the face) as the house style and retired B and fused (their code still works
with `--style B|fused`, but don't offer them). To keep videos from looking like one template, style A has **five
layouts** and a **per-video look**. `beats --style A` picks both and writes them to the plan:

| Layout | What it is | Head pop-out | Captions |
|---|---|---|---|
| **A1 classic** | panel on top, face window below | yes | y 928 |
| **A2 flip** | face window at the top (flush to the frame), graphics below | no (whole head inside, extra headroom) | y 1508 |
| **A4 big stage** | graphics fill the screen, a wide face card at the bottom-left | yes | y 838 |
| **A5 floating card** | full-frame face, the graphics on a glass card above the head (never over it); no sub label | no | none |
| **A6 half and half** | graphics edge to edge on top, the face edge to edge below | no | y 666 |

- A video uses **3 layouts** (4 when it has 10+ split beats), rotated over its split beats, never the same one twice in
  a row, and always at least one pop-out layout (A1/A4). Plan `"variants": ["A6","A4","A1","A5"]`; a beat's
  `"variant"` overrides. Face beats (full-frame punch-ins) stay as they were.
- **Look** (plan `"look"`, one per video): `window` round | arch | soft (the face window's corners), `ground` glow |
  grid | dots (the background), `enter` cut | slide | wipe (how each split beat's graphics come in), `caption` pop |
  box | line (the one-word caption style).
- A3 (side by side) was tried and dropped: a 400-500 px column can't keep the whole head in view while the speaker moves.
- A project's build script fills a layout exactly like a classic split beat: call
  `F.split_html(bid, st, du, vo, g, has_cut, words, cut_src, s.get("variant"), face, plan.get("look"))` and replace
  KICKER, the headline, `<!-- cards go here -->` and SUB LABEL. The stage moves with a static transform on
  `#<beat>-stage`; animate inside it, never the stage itself.
- `cutout` only cuts the beats whose layout pops the head (A1, A4).

**The head is measured over the whole edit, not one frame.** `ingest` (or `FOOT face <dir>` on an existing project)
samples ~14 frames, removes the background and takes the highest the head ever gets and its full left-right range;
plan `"face"` is that envelope, so every window and card is sized for the speaker's movement. (A user saw their
face cut off and black patches when they leaned or sat up while the window was sized from a single frame.)
**Check frames across each beat** (snapshot every ~1.5 s), not one frame per beat: a lean shows up mid-beat.

## The panel: show exactly what is being said
The panel is what makes this style feel interactive. For every split beat, ask: **what does this line name?**
1. **A real thing** (a place, school, hall, food, market, brand, app, person, event): show the real thing.
   Fetch it with `scripts/fetch_images.py` (Wikimedia Commons, Openverse: PD, CC0 or CC BY only) or
   use the user's own photos or the brand's official logo. Put it in `fk-photo` or in a `fk-tile`. Look at the
   contact sheet before using it, and add the credit lines to the description. **Do this at almost every
   beat**: it is what makes the video feel like the speaker's life and not a template.
   **The speaker's own places first** (their school, hall, hostel, area): use photos of those exact places, not generic
   stock. These are rarely on Commons, so **search Google Images in the built-in browser** (google.com → Images;
   Tools → Usage rights → Creative Commons helps). Open the best result's source page (the place's official
   website is best) and take the full-size image from that page. Download it into a fresh, empty folder,
   re-encode it into `assets/images/` with ffmpeg (`-frames:v 1 -update 1`), look at it, and credit the source page
   in `CREDITS.md`. Tell the user when an image has no stated licence. Landscape photos too small for full screen
   go on a big `fk-photo` card over `fk-ground`. Show the pictures only: no school, hall or hostel names on screen
   unless the user asks for them.
2. **A number** (price, fare, rent, followers, cedis, hours, days): a `fk-stat` card (tile + number +
   label + pill + mini bars). The number starts blurred and sharpens on the word (`CM.sharpen`).
3. **A list or steps**: a `fk-check` card, one row ticking in per spoken item (`CM.ticks` with the
   items' spoken times).
4. **A comparison or flow** ("normally… but now…"): `fk-node` tiles with connector paths drawn
   (`CM.draw`), the old route crossed out (`fk-x`).
5. **A feeling or opinion**: make it a face beat instead, maybe with one `fk-quote` word ("WAHALA").

Headline: a two-tier `fk-kicker` (small caps) + `fk-head` (heavy caps, ONE `<b>` accent word, about 2–4
words). It changes with `CM.decode` (letter scramble), never a slide. Keep the headline about the beat,
not a transcript.

## Palettes (on the root, plan `"palette"`)
`ghana` (warm black, kente gold + terracotta: lifestyle, student life, food), `kente` (deep green, gold,
red: culture, events), `legon` (navy + gold: campus issues, school news), `coral` (warm black + coral: AI tools, creator talk), `campus` (black + pink: app promos), `light`
(daytime, clean), `ocean` (cool blue: money, tech, study tips), `mono` (black and white + red: serious
stories). A brand gets its own block in `footage-kit.css` (copy one and change the variables).

## Commands
```bash
CMV new projects/<slug> --format vertical --theme dark --title "<Title>"
FOOT ingest projects/<slug> "<clip1.mp4>" ["<clip2.mp4>" ...]    # cut + clean + transcribe (natural pace; --speed only if asked, max 1.2)
FOOT beats projects/<slug>                       # style A: beats + layouts (A1/A2/A4/A5/A6) + a look -> plan.json, timing.json
FOOT cutout projects/<slug>                      # pop-out cutouts, A1/A4 beats only (~1 frame/s: background task; after layouts are final)
FOOT scaffold projects/<slug>                    # starter beat files + overlay (captions, flashes)
#   ... design each split beat's panel; set "flash"/"layout"/"zoom" in plan.json; re-run scaffold for the overlay
CMV assemble projects/<slug>                     # voice, SFX, music, overlay
CMV hf check / snapshot ...                      # from inside the project
CMV hf render -o renders/<slug>.mp4 --workers 2
CMV master projects/<slug> renders/<slug>.mp4 && CMV package projects/<slug>
```
`FOOT` = `python -I -u SKILL/scripts/footage.py`.

**Read the cut before building.** `ingest` prints the kept transcript, the dropped fillers and every dropped
retake (`assets/footage/cuts.json`). Check that no real line was lost. If one was, re-run with
`--keep-retakes`, or raise `--max-gap`. Retakes are found when a phrase is restarted within the next three
phrases (the last take wins). Parakeet's punctuation decides beat boundaries; merge or split beats by
editing `plan.json`/`timing.json` before scaffolding if a beat is under 1.2 s or over 4.5 s.

**Every cut must sound clean: check the whole edit before delivering** (a user heard half-removed words and
"or… or… or" repeats in a delivered edit). Parakeet's word times run ~0.1–0.3 s late and it skips stutters, so:
- `ingest` moves every cut to the nearest real silence (audio envelope), strips short leftover bursts
  (≤ 0.2 s) before removed words, then re-transcribes the edit and removes any word or phrase said twice in a row.
- Then run `python -I SKILL/scripts/review_joins.py projects/<slug>`. It lists every cut: the words on each side,
  what was removed, and the sound at each edge. Look at each one. A short burst kept right before a cut is
  a leftover (an "or", a half word). If a join is unclear, transcribe just the audio before and after the cut on
  their own (`hyperframes transcribe snippet.wav`) and read them.
- A stutter inside one transcribed word ("a… a lot"): find it in the loudness envelope and remove it with
  `--cut-raw START-END` (raw seconds). A trailing "or like" after the last sentence: trim the end.
- Captions come from the edit's transcript, which can miss or mishear a word that is in the audio. Fix the
  caption text (the project's build script), not the cut.

**Voice.** Phone takes often sound flat and boxy. `ingest` cleans the voice with the "punch" chain (light denoise,
less 220/420 Hz boxiness, +4.5 dB presence, air, de-ess, firm compression, a little excitement). Set
`"voice_fx": {"punch": false}` in plan.json for the gentler chain. When a user says their voice sounds dull, A/B a
16 s sample (same loudness) before re-rendering. Processing can't fix a flat delivery: suggest standing, smiling,
the phone a hand's width from the mouth, and a quiet soft room.

**Speed: never by default.** Keep the speaker's natural pace (`--speed 1.0`, the default). Only speed up when the speaker
asks, and then by ×1.1–1.2 at most; above that the voice sounds unnatural.
than ~140 wpm; the reference creator sits around 200+ wpm after cuts, and ~130–145 wpm is a comfortable floor.

**Face window.** `ingest` measures the head from one frame (plan `"face": {cx, top, head_w}` in source
px), and scaffold places the footage so the head is centred and pops above the window. If the crop is off
(a wide shot, the person off-centre), adjust `"face"` and re-scaffold the split beats (`--force` rewrites
ALL beat files: copy designed panels out first, or fix the two video `style`s by hand).

**The full head always shows.** Never crop the top of the speaker's head (hair, cap) in the face window or in a
punch-in. With a cutout, the head pops above the window; a split beat without a cutout places the whole head inside
the window with a margin (`window_geometry(face, pop=False)`); face-beat zooms are capped by `face_zoom()`. If
`plan.json "face"` is wrong (the head gets cut anyway), fix `top`/`cx` there and rebuild.

**Pop-out.** Two `<video>` elements per split beat, same placement: `edit.mp4` (media-start = beat start)
clipped by the window, and the beat's `cut_<beat>.webm` (media-start 0) clipped to the area above the window (`clip-path: inset(0 0
658px 0)` on its untimed wrapper). Without a cutout the beat simply has no pop-out. Changing a beat's layout to split later means running `cutout` again (it only does missing beats). Keep the sub-label above y≈1100 (a cap or tall hair pops higher): the head pops up to y≈1172.

## Building a split beat (example)
```html
<div id="b3-kick" class="fk-kicker">Night market</div>
<h1 id="b3-head" class="fk-head">Osu <b>food run</b></h1>
<div id="b3-panel" class="fk-panel">
  <div id="b3-photo" class="fk-photo" style="width:420px;height:420px"><img src="assets/images/osu-1.jpg" alt=""><div class="fk-cap2">Oxford Street</div></div>
  <div id="b3-stat" class="fk-card fk-stat" style="flex-direction:column;align-items:flex-start;padding:30px">
    <div id="b3-num" class="fk-num">GH₵ 45</div><div class="fk-label">kelewele + drink</div><div class="fk-pill">Friday night</div>
  </div>
</div>
<div id="b3-sub" class="fk-sub">every week without fail</div>
```
```js
CM.decode(tl, $("#b3-head"), 0.0);
CM.blurIn(tl, $("#b3-kick"), 0.0, { dur: 0.25 });
tl.fromTo($("#b3-photo"), { scale: 0.85, opacity: 0, rotation: -4 }, { scale: 1, opacity: 1, rotation: 0, duration: 0.45, ease: "expo.out" }, 0.25);
CM.pop(tl, $("#b3-stat"), 0.7, { from: 0.85, ease: "expo.out", dur: 0.45 });
CM.sharpen(tl, $("#b3-num"), 1.4);          // on the spoken number
CM.blurIn(tl, $("#b3-sub"), 0.9, { dur: 0.25 });
```
Panel motion stays inside the panel area: nothing slides over the face window or the caption line, and an
outgoing card is fully gone before the next one lands in its spot (overlaps read as mistakes).

## Checklist before rendering
- Every split beat shows something specific to its words (real image, number, list or diagram); no
  placeholder `KICKER`/`WORD`/`SUB LABEL` text is left.
- Real images were looked at; credits are in `assets/images/CREDITS.md` and in the description.
- Layouts alternate; the hook beat (b1) is split with a strong headline; the CTA beat is a face beat.
- `CMV hf check` passes; snapshots at every layout switch show no element covering text or the face.
- SFX ≤ 0.25 volume, music ≤ 0.12; master to −14 LUFS.
