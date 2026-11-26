# SFX kit

72 sounds in `assets/sfx/`, grouped into role pools so long videos never lean on one file, levelled (peak −3 dBFS) and trimmed, indexed in
`assets/sfx/manifest.json`. All are free to use: CC0, the HyperFrames library (installed by `cmv.py setup`), or CC BY
(credited automatically in the project's `CREDITS.md` by `cmv.py assemble`; tell the user to
include those credits where they publish).

Cue them in `plan.json` with the **visual** time; `assemble` subtracts the peak so the hit lands
one frame after the picture. `volume` in a cue overrides the default.

## Action → sound (the reference's own palette, mapped to this kit)
| On screen | Sound(s) | Reference name |
|---|---|---|
| Small element slides / whips | `whoosh-short`, `swoosh-fast` (rotate) | Short Whoosh |
| Big card/scene moves, scale-through | `whoosh-low`, `whoosh-pass`, `swish` | SMOOTH Whoosh |
| Hero / logo reveal | `magic-whoosh` (+ `sparkle` sparingly) | Magic / Dreamy Whoosh |
| Morph or glitchy transition | `granular-transition`, `glitch-3` | Granular Transition |
| Barcode glitch cut | `glitch-1` (low volume) | Glitch |
| Build into the payoff | `glass-swell` (short), `rise-crash`/`riser` (long; place by peak) | Glass Riser |
| UI element lands / confirm | `enter` | Enter |
| Chip, word, icon pops | `pop`, `bubble-pop` (rotate) | ui-pop-sound |
| Cursor press | `ui-tap`, `click-soft` | — |
| Typing | `mech-typing` (start), `key-press` (single keys), `typing` (long burst) | — |
| Chat bubble / message | `message-ping` | Audio effects \| mensaje |
| Notification card | `notification` | Menu Notification |
| Stat / number lands | `ping` | Num |
| Success | `chime` | — |
| Payoff drop (once per film) | `bass-drop`, `impact-bass-1` | tiktok_drop |
| Problem / error beat | `error` | — |
| Snapshot / freeze frame | `shutter` | — |

## Density
A 15 s film typically has 12–25 cues. Over a voiceover keep SFX at their default volumes (they
sit under the voice); without voice you can raise them ~1.3×. Don't stack two whooshes within
0.25 s; let one sound per action speak.

## Variety: role groups and automatic rotation
Every sound has a `group` in `manifest.json` (error, whoosh, whoosh-big, appear, pop, click, key,
typing, notify, ping, success, impact, glitch, riser, reveal, shutter). When `assemble` places a cue
whose sound belongs to a group, it **rotates through the group's takes**: the first use plays the
named sound, later ones play other takes, and a take isn't repeated until up to 4 others have played.
Volumes are carried over relative to each take's level, so a cue's `volume` keeps meaning the same.
- Name a group directly with `"sound": "@error"` (or `@pop`, `@whoosh`, ...).
- Pin one exact file with `"exact": true` on the cue; turn rotation off for a project with
  `"sfx_vary": false` in `plan.json` (e.g. a deliberate repeated motif).
- Each chapter starts its rotation at a different take, so chapter joins don't repeat either.

| Group | Takes | Notes |
|---|---|---|
| error | 11 | bundled `error`, 5 synthesised tones (`error-synth-1..5`: two-tone down, double blip, falling glide, dissonant pair, low buzz), 5 CC0 buzzers/negatives |
| whoosh / whoosh-big | 7 / 3 | short whips vs. big scene moves |
| pop, click | 7 each | |
| key, notify | 6 each | |
| success, impact | 5 each | keep impacts rare (one big hit per minute at most) |
| ping, appear | 4 each | |

## Growing the kit
`python -I scripts/fetch_sfx_variants.py <staging> --groups error,pop --per 6` searches Openverse
(CC0 only, no credit needed), downloads short candidates and rejects ones that are too long, silent,
or contain speech. Pick the good ones by id and run
`python -I scripts/add_sfx_variants.py <staging> --pick error:<id>,<id> pop:<id>` to level them into
the kit as `<group>-vN.mp3` (peak −3 dBFS, trimmed, faded, peak time measured). Listen first:
`cmv.py sfxboard <outdir>` makes a board with every group's takes. Remove a bad take by deleting its
file and its manifest entry.

## Full list
\* `library` = HyperFrames sound library (Pixabay licence): not shipped in this repository; `cmv.py setup`
installs them from your HyperFrames `media-use` skill. Without them, rotation simply uses the other takes.

| Sound | Use for | Length | Peak at | Default vol | Licence |
|---|---|---|---|---|---|
| `whoosh-short` | move: small card/text slide, whip (take A) | 0.50 s | 0.16 s | 0.55 | library* |
| `swoosh-fast` | move: fast whip / swipe (take B) | 0.33 s | 0.05 s | 0.45 | cc0 |
| `whoosh-low` | move: soft low whoosh under a big scale/morph (take C) | 1.60 s | 0.21 s | 0.9 | cc0 |
| `whoosh-pass` | move: big pass-by / scene transition | 3.62 s | 2.87 s | 0.35 | by |
| `swish` | move: airy swish, soft scene change | 2.70 s | 0.72 s | 0.8 | by |
| `magic-whoosh` | reveal: shimmering whoosh into a hero/logo | 1.85 s | 0.80 s | 0.45 | by |
| `whoosh-cinematic` | transition: long swell that peaks on a cut | 4.72 s | 2.54 s | 0.35 | library* |
| `granular-transition` | transition: granular/electric texture on a morph or glitch | 4.06 s | 1.79 s | 0.35 | by |
| `glass-swell` | riser: short glassy inhale into a reveal | 1.31 s | 0.79 s | 0.4 | cc0 |
| `rise-crash` | riser: build into the payoff (peak ~4 s in) | 7.75 s | 3.99 s | 0.4 | cc0 |
| `riser` | riser: long cinematic build (peak ~3.5 s) | 4.87 s | 4.05 s | 0.3 | library* |
| `enter` | appear: UI element lands / confirm (the 'Enter' sound) | 0.73 s | 0.17 s | 0.4 | cc0 |
| `pop` | appear: chip, badge, word or icon pops in | 0.42 s | 0.11 s | 0.5 | library* |
| `bubble-pop` | appear: tiny bubble pop (rotate with pop) | 0.20 s | 0.09 s | 0.45 | by |
| `ui-tap` | click: cursor tap on a button | 0.12 s | 0.00 s | 0.6 | cc0 |
| `click-soft` | click: quiet selection / toggle | 0.31 s | 0.05 s | 0.6 | library* |
| `key-press` | typing: single keystroke | 0.28 s | 0.07 s | 0.6 | library* |
| `mech-typing` | typing: short mechanical burst | 0.31 s | 0.02 s | 0.4 | cc0 |
| `typing` | typing: 1.5 s burst of keys | 1.50 s | 0.45 s | 0.6 | library* |
| `message-ping` | notify: message / chat bubble arrives | 1.91 s | 0.00 s | 0.6 | cc0 |
| `notification` | notify: toast / notification card | 1.57 s | 0.22 s | 0.45 | library* |
| `ping` | accent: data point / stat lands | 1.08 s | 0.32 s | 0.5 | library* |
| `chime` | accent: success / done | 2.50 s | 0.41 s | 0.5 | library* |
| `sparkle` | accent: shine on a hero element | 1.80 s | 0.02 s | 0.35 | library* |
| `shutter` | accent: snapshot / frame freeze | 0.29 s | 0.10 s | 0.5 | cc0 |
| `impact-bass-1` | impact: logo/headline slam | 2.12 s | 0.07 s | 0.4 | library* |
| `bass-drop` | impact: drop on the payoff (use once) | 4.47 s | 0.00 s | 0.3 | cc0 |
| `glitch-1` | glitch: barcode/streak transition | 2.64 s | 0.94 s | 0.3 | library* |
| `glitch-3` | glitch: subtle digital shift | 2.20 s | 1.82 s | 0.45 | library* |
| `error` | problem beat: 'wrong' / failure | 1.05 s | 0.73 s | 0.5 | library* |

## Adding sounds
Find CC0/CC BY sounds with `HF media-use resolve --type sfx --intent "<concrete name>" --project <tmp>`
(Openverse; licence is in `.media/manifest.jsonl`), copy into `assets/sfx/`, add an entry to
`SOUNDS` in `scripts/build_sfx_kit.py`, and re-run it. A one-off sound can also live in a project's
own `assets/sfx/` and be cued by file name with `"peak"` and `"volume"` set in the cue.
