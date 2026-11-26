---
name: clean-motion-video
description: Make motion-graphics videos with voiceover, by default in a clean, minimal, Apple-like "UI motion design" style (word-by-word blur-in text, morphing pills and cards, cursor taps, typed search bars, whips and glitch cuts, a sound effect on every action), with alternative looks for art, stories, tech, ads, kids and luxury content. Rendered with HyperFrames and free tools; the voice can be local Kokoro, Google Gemini TTS, or the user's own recording (cleaned, paced and synced). Use this whenever the user asks for a video, reel, TikTok, short, explainer, ad, promo, product demo, app/UI animation, VSL, story video, "motion graphics", "make a video about X", gives a script or a voiceover file to turn into a video, wants to audition or change voices, or wants a concept explained with animation and voiceover, even if they don't name the style. Also use it for the "sound design breakdown" format (SFX timeline under the video).
---

# Clean Motion Video

Motion-graphics videos (8 s shorts to 10+ min explainers) in the style studied from @i.editverse (40 videos;
full analysis in `references/source-analysis.md`): one idea per beat, centred on a big quiet
canvas; words blur into focus as they are spoken; UI elements grow out of each other instead of
cutting; a cursor taps, a field types, the camera pushes in; every visible action has a sound.

It is built on [HyperFrames](https://hyperframes.heygen.com) (HTML rendered to video). If the
HyperFrames skills are installed (`npx skills add heygen-com/hyperframes`), read the `hyperframes`
skill first for its render contract; either way, the rules that matter are: `fromTo` only, no timers or
unseeded randomness, `class="clip"` on timed elements, one paused timeline per scene registered on
`window.__timelines`. Everything here runs with free tools on the user's machine: no sign-ins, no paid APIs.

**Paths.** `SKILL` = the folder this file is in. `CMV` = `python -I -u SKILL/scripts/cmv.py`
(`python3` on macOS/Linux; `-u` streams output live). `HF` = `CMV hf`: it runs the HyperFrames CLI
through an installed HyperFrames skill if there is one, else `npx hyperframes@<pinned version>`. Never
call `npx hyperframes` directly. Projects go in the user's working folder under `projects/<slug>/`
unless they say otherwise.

**First use on a machine:** run `CMV setup --test` once. It checks Python, Node.js 22+, ffmpeg and
HyperFrames, and installs the HyperFrames library sounds into the kit. Kokoro (voice) and Parakeet
(word timing) models download automatically the first time they're used (a few hundred MB).

## Running commands: let the user watch
Long commands (voice, render, chapters) take minutes. Run them in the background if your agent can,
and let their output stream: never pipe them through `tail`/`head`/`grep` (that hides everything until
the end), keep `-u` on Python, and don't pass `--quiet` to `HF render`. Read the output only when you
need a line from it. Render one thing at a time: renders are memory-hungry.

## The workflow

### 1. Pin down the brief (briefly)
From the request, decide: topic, purpose (explainer / ad / product demo / VSL / social hook),
format (default **vertical 1080×1920** for TikTok/Reels/Shorts; landscape 1920×1080 for
YouTube/web; square for feeds), length (default 12–20 s; a supplied script or recording sets
its own length), voiceover source (below), brand colour if any, and the **look**. Ask only what
you truly cannot infer; otherwise state your choices in one line and go.

**Look.** Read `references/looks.md` and pick the look from the subject: the clean light style is
the default for tech/finance/apps, but a story about art gets `paper`, an AI/crypto piece
`midnight`, a promo `bold`, a beauty ad `sunset`, a kids' explainer `candy`, a true story `noir`,
and so on. One look per film plus at most one contrast beat. The craft rules below apply to all.

### 2. Script: write it, or take the user's
Three ways in, and each ends in the same thing, a list of beats (one scene = one spoken line =
one idea on screen, about 2–5 s):
- **You write it** from a topic. Read `references/scripts.md`. Shape: **hook (question or pain) →
  name it / "Introducing X" → 2–3 proof or feature beats → tagline/logo**. 140–170 words per
  minute, no filler, the voice starts within 0.2 s.
- **The user gives a script** (a story, an explainer, an ad). Keep their words **verbatim**; your
  job is to split it into beats and design what each beat shows. Split at sentence ends; break
  sentences longer than ~5 s at a comma or "and/but"; join fragments shorter than ~1.5 s. Fix only
  obvious typos, and ask before cutting or rewording anything. A long script (> 60 s) is fine: plan
  more beats, reuse patterns, and show the beat list first.
- **The user gives a recording** (their own voiceover). Its words are the script. Run
  `CMV voice <dir> --file <audio>` with no scenes in `plan.json`: it auto-splits the take into beats
  by sentence and writes them to `plan.json`; then rename the scene ids and adjust if needed.
Show the user the beat list (line + what's on screen) before building if the video is longer than
~20 s or the brief was vague; for a short clear brief, build straight away.

### 3. Scaffold and voice
```bash
CMV new projects/<slug> --format vertical --theme <look> --title "<Title>"
# write projects/<slug>/plan.json (scenes with "vo", "min", optional "lead"/"pad"; sfx later)
CMV voice projects/<slug>        # makes/imports the voice + word timings -> timing.json
```
Pick the voice source (set in `plan.json`):

| Source | plan.json | Notes |
|---|---|---|
| **Kokoro (local, free)** | `"voice": "af_heart", "speed": 1.1` | Default. Per-scene clips (cached per line); `"take": "full"` speaks the whole script in one take for more natural flow. |
| **User's recording** | `"voice_file": "path/to/vo.mp3"` or `--file` | One take: kept as `assets/voice/original.*`, then cleaned and cut into scenes. |
| **Google Gemini TTS** | `"engine": "gemini", "voice": "Kore", "voice_style": "Say this like an upbeat creator"` | Needs `GEMINI_API_KEY` in the environment (free key from Google AI Studio; the user sets it, never paste or store it in files). One take. Model via `"gemini_model"` (default `gemini-2.5-flash-preview-tts`). Sends the script text to Google. |

**Recommended Kokoro voices** (the most lively in a 28-voice audition): female `af_heart`
(default), male `am_adam` or `am_liam`, all at speed 1.1. Avoid `am_michael` (sounds flat). Pick
female or male to suit the content and say which in your one-line brief; if the user has a saved
preference, use it. To help them choose, make an
audition board: `CMV voices <outdir>` (all 28 English Kokoro voices) or
`CMV voices <outdir> --engine gemini` (30 Gemini voices), each saying the same ~10 s line, with an
`index.html` player.

**Voice polish (`voice_fx`, on by default).** Every take goes through presence EQ + compression +
loudness (`energize`). One-take sources also get long pauses shortened (`tighten`: pauses over
0.38 s cut to 0.28 s) and, when the read is slower than ~148 wpm, sped up toward 160 wpm without
changing pitch (`"tempo": "auto"`, max 1.2×). Override: `"voice_fx": {"tempo": 1.0}` to keep the
original pace, `"pitch": 0.5` (semitones) to brighten a heavy voice, `{"energize": false}` for a
voice that is already produced. Per-scene Kokoro clips get `energize` only (their own pauses stay).
A dull, flat or "down" voice ruins an otherwise good video: if the user says the voice sounds low,
first try a brighter voice and speed 1.1–1.15, then `pitch` 0.3–0.8.

`voice` prints every word with its scene-local time. **Check the printout against the script**:
the transcriber sometimes drops or merges a word (e.g. "grew" vanished once). When a word is
missing, estimate its time between its neighbours when you sync text to it. With one-take sources
the scene cuts come from matching each scene's `vo` to the transcript; if a cut lands on the wrong
word, adjust that scene's `vo` text and re-run. A scene without `vo` in a one-take film can only
come after the voice ends (e.g. the logo card).

### 4. Build one scene file per beat
Each scene is `compositions/<id>.html`. Start from `references/scene-patterns.md` (copy-ready
patterns) and the worked example in `examples/compound-interest/`. The template already loads
`assets/cm-kit.js` (motion helpers, API in `references/cm-kit.md`) and `assets/cm-kit.css`
(themes + UI parts). In each scene:
- a `.cm-ground` background (or a full-bleed colour/gradient div), then the beat's elements;
- `CM.speak(tl, el, [word times])` so on-screen words land on the spoken words (times from
  `timing.json`, scene-local); `mode: "ink"` for the hook line so frame 0 already shows it;
- one or two UI moves per beat (pop, morph, type, tap, count, camera) that **show** the line;
- an exit at the end of the scene (blurOut / whip / scale-through) so beats flow, except into a
  hard-cut contrast beat (e.g. a dark logo end card).

Style rules that make it look like the reference, not like a template (details in
`references/style-guide.md`; for non-default looks, the palette/type/motion numbers in
`references/looks.md` replace the clean-look values, the rest still applies):
- A quiet canvas in the chosen look, ONE accent colour, lots of empty space.
- Text small-to-medium and centred; one accent word (`<b>`), quiet last word (`<em>`).
- Things **grow out of** the previous thing (dot → pill → search bar → card). Avoid hard cuts
  except for mood changes; never crossfade two full scenes.
- Arrivals: `expo.out`/`power3.out`, 0.2–0.5 s; exits 40–50% shorter. Landed text holds still.
- Something moves every 0.3–0.6 s, but no floating/breathing/pulsing loops.
- Vary entrances across beats (blur words, pop, morph, type, assemble, lens).

**Platform safe area (vertical 1080×1920)**: keep text inside x 120–888, y 288–1248, and
below y 840 inside x 120–780 (TikTok, Reels and Shorts buttons cover the rest). Decorative
elements may go outside. Centre each beat's group of elements around **y ≈ 800**, not near the
top: in the first test, content placed at y 380–1100 left the lower half dead and the frame looked
top-heavy. Landscape/square: keep text inside the central 80%, group centred.

### 5. Sound design (this is what makes the style work)
Read `references/sfx-kit.md`. Add cues to `plan.json` `"sfx"` as
`{"scene": "<id>", "t": <scene-local visual time>, "sound": "<kit name>", "volume"?: n}`.
`assemble` places each file so its peak lands one frame after the picture, copies it into the
project and writes `CREDITS.md` for CC BY sounds.
- One sound per visible action: move/whip → whoosh, appear → `enter`/`pop`, typing →
  `mech-typing`/`key-press`, cursor press → `ui-tap`, message/notification → `message-ping`,
  number lands → `ping`, reveal → `magic-whoosh` or a riser, colour flood → `swish`.
- Variety is automatic: every kit sound belongs to a role group (11 failure takes, 7 whooshes,
  7 pops, 7 clicks, ...) and `assemble` rotates through the group, so the same file isn't heard
  again until others have played. Cue a role with `"sound": "@error"` or name a take; `"exact": true`
  pins one. One failure sound repeated 33 times across a 10-minute film felt cheap to viewers: never
  switch rotation off without a reason. One big impact/riser per film at most.
- Music is optional (the reference often has none). If the user wants it: their own file, or a
  CC0/CC BY track they choose; set `"music": {"file": "assets/music/x.mp3", "volume": 0.12}`.
  Local MusicGen exists but its weights are **non-commercial**: never use it for ads/clients.

### 6. Assemble, check, look
```bash
CMV assemble projects/<slug>     # writes scene hosts + voice + sfx into index.html, sets duration
cd projects/<slug> && HF check --no-cache
HF snapshot --at <a few key seconds>   # then READ the contact sheet
```
Fix every error. Weigh warnings: `outside_safe_zone` → move text; `first_frame_empty` → show
the hook at 0 s; `line_unread` on the end card → hold it ≥ 2 s (raise the scene's `min`);
contrast warnings on not-yet-spoken grey words in `mode: "ink"` are expected. Look at the
snapshots like a viewer: is each beat's idea readable at a glance? Anything clipped, overlapping,
or jammed against an edge? Is a frame dead/empty in the middle of the film?

### 7. Render, master, deliver
```bash
HF render -o renders/<slug>.mp4 --workers 2 --skill=clean-motion-video
CMV master projects/<slug> renders/<slug>.mp4      # -> renders/<slug>_master.mp4 at -14 LUFS
HF audio renders/<slug>_master.mp4 --json           # confirm voice + hits present, loudness ok
```
The machine has little free RAM: keep `--workers 2`, run renders in the background, one at a time,
and never run TTS/transcription/another render alongside one (a render died at "Starting browsers" once).
Deliver the `_master.mp4`, say what was measured (not heard), and list `CREDITS.md` if present.
Offer the HyperFrames desktop app / Studio preview (`HF preview --background`) for hands-on edits.

### Long videos (over ~90 s: explainers, stories, 5–15 min voiceovers)
Same craft, different logistics. Rendering runs about 12× slower than real time on this machine
(18 s took ~3.7 min with `--workers 2`), so 10 minutes is roughly 2 hours of rendering, and one
giant project is fragile (one crash loses everything; memory is tight). Work in chapters:
```bash
CMV new projects/<slug> --format landscape --theme <look> --title "<Title>"
CMV voice projects/<slug> --file <long_voiceover.mp3>   # cleans, paces, auto-splits beats
CMV chapters projects/<slug> --at s20,s40,...           # cut at section starts (or --size 75)
# per chapter: write compositions/*.html + sfx in its plan.json, assemble, check, snapshot, render
#   (render each to chapters/chNN/renders/chNN.mp4, in the background, one at a time)
CMV concat projects/<slug>                               # -> renders/<slug>.mp4
CMV master projects/<slug> renders/<slug>.mp4
```
- **Approve the direction on chapter 1 first.** Build and render ch01, deliver it, get a yes on
  the look and pacing, then do the rest. Don't spend hours building chapters the user may redirect.
- **Plan the whole film before building.** Read the full transcript, write a one-line outline per
  chapter, and give the film a visual system: a recurring layout for "section titles", a recurring
  layout for "key facts", one for lists, one for quotes/stats, so 150+ beats feel like one film,
  not 150 one-offs. Vary within the system; repeat a pattern at most every ~4 beats.
- **Same quality bar as a short, on every beat.** Viewers judge a long film against the
  best short: every beat gets the full craft (words on the voice, grow-out UI, one sound per
  action, a real exit), every chapter gets its own check + snapshot review before rendering. Never
  fall back to text-only slides or reuse one scene with new words to save time; if time is short,
  say so and do fewer chapters well rather than all of them thinly.
- **Pacing for long form:** keep the short-form density (something moves every 0.3–0.6 s). A beat
  may run 4–8 s only when motion fills it (a list building up, a diagram drawing step by step, a
  camera push across a layout). Add a section-title card between chapters. Sound stays one cue per visible action, but
  softer (volumes ~30% lower) so 10 minutes isn't tiring; music, if any, very low and ducked.
- **Calm word entrances.** `chapters` sets `data-word-style="soft"` on each chapter's root, so
  `CM.speak`/`CM.blurWords` fade + lightly unblur words with no size change (0.28 s). The short-form
  scale-snap (1.08 → 1 in 0.18 s) on every word of a fast narration (~190 wpm) reads as the text
  vibrating (flagged on the first long film made with this skill). Use soft for any narration over ~170 wpm too.
- **Format:** long explainers are usually landscape 1920×1080 (YouTube); ask if unclear.
- **Build chapters with the scene builder** in `scripts/longform/` (copy `mk.py` + `qc.py` into the
  project's `shared/` folder; `chapter_example.py`, `parts_example.py` and `example_theme.css` are a
  real 10-minute episode's files, renamed). `mk.Chapter("ch02")` writes a scene from css/html/js where
  `{{T:spoken phrase}}` becomes that phrase's word times and `{{t:word}}` / `{{t:word#2}}` one word's
  time, straight from `timing.json` (a phrase that isn't in the transcript stops the build and prints
  the real words, which catches misreads like "callestyle"); `$ID` is the scene id; `c.sfx(...)`
  collects cues. `python -I qc.py chNN "t1,t2,..."` assembles, checks (full log in `chNN/qc.log`),
  prints only errors + notable warnings, and snapshots. Shared look in one CSS file copied into every
  chapter's `assets/` and linked from its `index.html`.
- **Layout rules learned the hard way (landscape):** a two-line `ep-mid` headline at top ≈120 ends
  near y 330, so content under it starts at y ≥ 380; a card's text never below 28 px (also after a
  scale-down); white initials need dark avatar colours; things that move by design (stacking cards,
  stamps) get `data-layout-allow-overlap`; blur a headline out before a camera push crops it.
- A chapter's voice and timing are locked (`voice_locked`), so don't re-run `voice` inside one; to
  change the cut, re-run `chapters` on the parent (it keeps each chapter's compositions and sfx).
- Tell the user the honest time budget up front (authoring all chapters plus ~12× real time of
  rendering) and keep them posted chapter by chapter.

### Real images (only when they make it truer)
History, real places, real people, real events: read `references/real-images.md`. The narrator names
something real and specific → show the real thing (public-domain archive photo, painting, map), fetched
with `scripts/fetch_images.py` (Wikimedia Commons + Openverse, licences checked, credits written). A
feeling or a concept → keep building UI. Always look at the contact sheet before using an image, frame
photos as exhibits inside the clean style, and put the credits in the YouTube description.

### Deliver with a publish pack (every video)
Read `references/publish-pack.md`. A long video ships with `publish/YOUTUBE.md` (3 titles,
description with chapters + subscribe link + credits, comma-separated tags, pinned comment), two
thumbnails (`CMV thumb`), and TikTok parts cut from the finished film (`CMV tiktok --parts ... --titles ... --captions ...`:
framed 9:16 "Part N" videos + caption files in `publish/tiktok-ready/`, ready to post, no re-render): Part 1 is the hook up to the first cliffhanger, every part starts on a line that makes sense
cold and ends on a resolved point, 1–3 min each, story order, plus `publish/TIKTOK.md` with captions and
hashtags. Shorts ship with a caption, hashtags and a cover.

### Growing the channel: subscribe / follow call to action (every video)
Every finished video asks viewers to subscribe/follow, organically: a short overlay that rides on
top of the film at a calm moment, never a hard stop. Channel details live in `plan.json`
`"channel": {"name", "tagline", "color", "avatar"}` (avatar = the user's logo file; never draw a
platform logo). Ask for them once; keep them in `plan.json` (and your agent's memory if it has one).
```bash
CMV cta projects/<slug>                       # auto kind + placement (see below)
CMV cta projects/<slug> --at 312 --line "Want part 2? Subscribe and turn on notifications"
CMV assemble projects/<slug>                  # or the chapter it reports, then render
```
- **Long-form (landscape): subscribe + bell.** A lower-third card slides up, a cursor taps
  Subscribe (turns to "Subscribed ✓"), then taps the bell (it rings, "All notifications on"), 5.2 s.
  `--at auto` puts it over the first section title card at or after ~30% of the film (after viewers
  have had real value, while the frame is calm); on a chaptered film it routes itself into the right
  chapter. Once mid-film, plus optionally once in the last 20 s if the ending isn't already a
  comment prompt. Never over a reveal, a number landing, or dense text.
- **Shorts (vertical): follow.** One compact card (avatar, @handle, "Follow for more like this",
  Follow → Following), 3.8 s, inside the safe area (y 1100–1232, x 120–780). `--at auto` = the last
  seconds. On a dark end card it sits under the tagline; check the snapshot for collisions.
- **Words make it organic.** Tie the line to the payoff, not a generic plea: "Getting value from this?
  Subscribe and turn on notifications", "Want the money plan next week? Subscribe", "Follow for part 2".
  When you write the script, also put a spoken CTA in the voiceover (see `references/scripts.md`);
  with the user's own recording, the overlay alone carries it unless they record a line.
- Its sounds come from the kit groups (appear, tap, success, bell ping, whoosh out) at soft levels.

### Optional: the "sound design breakdown" version
The reference account's most viral format (≈ 900k views vs ≈ 5k median): the finished video on
top, a caption ("Just Sfx"), and the SFX timeline scrolling under a playhead.
```bash
CMV breakdown projects/<slug> renders/<slug>_master.mp4 --caption "Just Sfx"
cd projects/<slug>-breakdown && HF check && HF render -o renders/breakdown.mp4 --workers 2
```
Offer it once after delivering a video; don't make it unasked.

## When something goes wrong
- `npm error notarget No matching version found for hyperframes@X` → npm's "latest" points at a
  release that isn't downloadable yet; set `HYPERFRAMES_STANDALONE_CLI_VERSION` to the last version
  that worked (e.g. 0.9.97) for every `HF` call of that project (keeps long films on one version too).
- Gemini returns 400/404 → the TTS model name changed; set `"gemini_model"` to the current
  `*-tts` model listed in Google AI Studio. 429 → free-tier rate limit; wait a minute.
- `tts` says Python is required → `cmv.py` sets `HYPERFRAMES_PYTHON` itself; if you call `HF tts`
  directly, set `HYPERFRAMES_PYTHON` to `python -c "import sys;print(sys.executable)"`.
- A scene renders blank → its root `data-composition-id`, host id and `window.__timelines` key must
  all equal the scene id; the timeline must be registered after all tweens.
- Text jumps on seek → you used `from()` or set a start state in CSS; use `fromTo`.
- An element should be hidden before it enters → its first tween is a `fromTo` (immediateRender
  hides it at 0); later tweens on the same element need `immediateRender: false`.
- Morph pill invisible at start → the `from` inset is larger than half the element's width.
