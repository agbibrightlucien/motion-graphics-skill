# Looks: matching the visuals to the content

The clean light look (the reference account's style) is the default, not the only option. Choose the
look from the **subject and the audience** before writing scenes, and say the choice in one line
("Look: paper, serif, slow camera, it's a history story"). A brand guide or an explicit request
always wins. Every look keeps the craft rules that make the style work: one idea per beat, words land
on the voice, things grow out of each other, a sound on every action, generous empty space.

Set the look with `CMV new ... --theme <name>` (or `data-theme` on `#root`). A theme sets
`--bg --ink --muted --accent --card --font --radius --shadow`, so the kit's parts (`.cm-card`,
`.cm-chip`, `.cm-line b`, ...) follow automatically. Override any token in a scene's `<style>` for a
one-off colour.

| Look (theme) | Best for | Palette & type | Motion energy | Transitions | Sound flavour |
|---|---|---|---|---|---|
| **Clean** (`light`, `cream`, `sky`, `blush`) | tech, apps, SaaS, finance explainers, product demos | near-white, one iOS-blue or brand accent; Inter | crisp, medium (0.2–0.5 s arrivals) | morph, blur swap, whip, barcode | UI taps, soft whooshes, pings |
| **Paper** (`paper` + `.cm-grain`) | art, history, books, stories, culture, quotes | warm parchment, ink black, terracotta accent; EB Garamond (italic for emphasis), Playfair for titles | slow and calm (0.5–0.9 s), gentle camera drift *with an end* | blur dissolve, iris, page-slide, ink wipe | paper rustle/swish, soft piano or none, low whoosh |
| **Midnight** (`midnight`) | AI, crypto, cybersecurity, futurism, gaming | deep navy, cyan + magenta glow accents; Outfit or JetBrains Mono | fast, punchy (0.15–0.3 s), glitch accents | barcode glitch, lens, whip, scale-through | glitches, risers, bass hits, digital blips |
| **Bold** (`bold`) | ads, sales, promos, youth brands, hype hooks | one loud solid colour (swap `--bg` to the brand colour), white type; Archivo Black / Montserrat 800, big words | snappy, overshoot pops, hard cuts on the beat | hard cut, colour flood, slam (scale 1.4 → 1) | impacts, pops, swooshes, music with a beat |
| **Sunset** (`sunset`) | lifestyle, beauty, travel, food, wellness, creators | peach → pink gradient, plum ink, rose accent; Poppins | smooth, soft overshoot, floaty arrivals (still no loops) | morph, blur swap, iris | sparkles, chimes, soft pops |
| **Forest** (`forest`) | luxury, real estate, sustainability, premium finance | deep green, cream type, gold accent; Playfair Display headlines, Inter body | slow, elegant, long holds | lens, blur dissolve, slow push | low whoosh, soft impact, warm pad |
| **Candy** (`candy`) | kids, education for young learners, fun facts, games | sunny yellow, navy ink, pink + blue accents, hard offset shadow; Nunito | bouncy (`back.out(2)`), wiggles allowed on arrival | pop, slide-in, iris | bubble pops, boings, cartoon whooshes |
| **Noir** (`noir`, `mono` for documentary) | true stories, drama, mystery, manifestos, serious topics | black, off-white type, one red accent; Playfair Display, condensed caps (`.cm-heavy`) for labels | slow builds, sudden hits | hard cut, flash to black, slow push-in | deep hits, drones, typewriter, heartbeat |
| **Dark** (`dark`) | contrast beats, logo stings, premium tech | near-black, white type | as clean | hard cut in, lens | magic whoosh, soft impact |

## Choosing
- **Topic decides first, platform second.** A finance explainer → clean; a story about a painter →
  paper; a crypto scam explainer → midnight; a gym promo → bold; a skincare ad → sunset.
- **Mixing:** one look per film, plus at most one contrast beat (a dark end card, a flood into the
  solution colour). Don't hop between three themes.
- **Brand colour:** if the user gives one, use the closest look and set `--accent` (or `--bg` for
  `bold`) to it. Keep text contrast ≥ 4.5:1: white type only on dark/saturated grounds.
- **Imagery:** paper/noir/forest can carry real photos or artworks (user-supplied or CC0 from
  `/media-use`) in thin-bordered frames with slow push-ins; clean/midnight prefer built UI; candy
  prefers simple flat shapes. Never invent a real person's face or a brand logo.
- **Fonts:** only the HyperFrames bundled families resolve by name (Inter, Montserrat, Outfit,
  Nunito, Oswald, League Gothic, Archivo Black, Space Mono, IBM Plex Mono, JetBrains Mono,
  EB Garamond, Playfair Display, Source Code Pro, Roboto, Open Sans, Lato, Poppins). Anything else
  needs a font file in `assets/fonts/` with `@font-face`.

## Motion per look (numbers)
| Look | Arrival | Exit | Word stagger | Camera |
|---|---|---|---|---|
| Clean | 0.2–0.5 s `expo.out` | 0.16 s blur | spoken times | push 1.0 → 1.4 on the subject |
| Paper / Forest | 0.5–0.9 s `power2.out` | 0.4 s dissolve | spoken times, blur 6 px | drift 1.0 → 1.06 over the beat, then stop |
| Midnight | 0.15–0.3 s `power4.out` | 0.12 s glitch/whip | spoken times, blur 14 px | snap zooms 1 → 1.25 in 0.2 s |
| Bold | 0.18 s `back.out(2)` | hard cut | words slam in (scale 1.5 → 1) | none or punch-ins on the beat |
| Sunset | 0.4 s `back.out(1.3)` | 0.25 s blur | spoken times | gentle push |
| Candy | 0.35 s `back.out(2.2)` + one wiggle (rotation ±6° → 0) | pop out (scale → 0) | spoken times | none |
| Noir | 0.6 s `power2.inOut` | cut to black | spoken times, slow ink | slow push 1.0 → 1.1 |

## Music by look (optional, CC0/CC BY or the user's own track)
Clean: none or light lo-fi. Paper: soft piano/acoustic. Midnight: dark synth pulse. Bold: upbeat
pop/trap with a clear beat (cut on the beat). Sunset: chill pop. Forest: warm ambient/strings.
Candy: ukulele/whistle. Noir: low drone, sparse piano. Keep music 18–24 dB under the voice
(`volume` 0.08–0.15) and duck it under speech.
