# @i.editverse: Style Analysis (40 videos)

Source: the 20 oldest (Dec 2025 – Apr 2026) and the 20 newest (Jun – Nov 2026) of the account's 57 videos.
Method: every video was downloaded, then measured. That covered cuts, brightness and colour, loudness, onsets, a transcript, and a frame every 0.5 s. Every frame sheet was then reviewed by eye.
Raw data: `samples/<oldest|newest>/<date>_<id>/analysis/` and `samples/_summary.json`.

---

## 1. The one-paragraph summary

These are **short (median 11.6 s) UI and product motion-design showcases**. They are minimal, Apple-like, and nearly always on a light background. They show **one idea per beat, centred on a large empty canvas**. Text appears word by word, with the newest word blurring into focus. UI elements (search bars, pills, cards, chat bubbles, buttons) **morph** into one another instead of cutting. A fake cursor taps things, and the camera pushes into whatever is being typed. There are very few hard cuts (median shot length about 3.8 s): continuous motion does the work. The **sound design is the star**. Every visible action gets a sound: whoosh on moves, "Enter"/pop on appears, typing ticks, risers into reveals. That is why the two videos that **show the SFX timeline** are the account's biggest hits by far (987k and 892k views versus a median of about 5k).

---

## 2. How the account evolved

| Era | Dates | Format | Look |
|---|---|---|---|
| **A. CapCut mockup** | Dec 2025 – Jan 2026 | 720×1280 vertical. A 16:9 render floats in a rounded card at the top, with the CapCut logo above it, the **"EV" logo** in the middle and the **live CapCut timeline** below. | White and light-grey canvases, brand-recreation UI (Netflix, Spotify, Uber, Bolt, PayPal, Apple Music, Pinterest, Discord). |
| **B. Documentary / B&W** | Jan – Feb 2026 (2 videos) | Full vertical. | Greyscale, heavy vignette, grain, AI-generated sculptural masks and silhouettes, condensed bold sans plus a script accent, red keyword. |
| **C. Clean full-frame UI** | Apr 2026 | 16:9 or 1:1, no mockup. | Pure white or grey, big UI close-ups, camera push-ins, motion-blur whips, vertical "barcode" streak transitions. |
| **D. Editorial + sound-design reveal** | Jun – Nov 2026 | Mixed: 16:9 inside a black vertical frame with a **caption on top** ("Just Sfx", "Best frame wins✨") and the **SFX timeline below**; 2×2 grids comparing four works; side-by-side "Left or right?" | Warmer: cream (#F3F1EA-ish), pastel pink, sky-blue gradients, typewriter mono, editorial serif, product photography, 3D phone mockups, Memoji sign-off. |

The newest 20 have a median of **2.8× more views** than the oldest 20, almost entirely because of the "show the sound design" format.

---

## 3. Visual language (what to copy)

**Canvas and colour**
- Default background: off-white `#F2F2F2` to `#F5F5F7`, or warm cream `#F3F1EA`. Measured brightness is 175–250 of 255 in 31 of 40 videos.
- Accents are rare and taken from the brand: Netflix red, Spotify green, iOS blue `#0A84FF`, PayPal blue.
- Mood shifts use soft **full-frame gradients**: pink to white for a "problem", blue to white for a "solution", periwinkle `#6B9BE0` for social apps.
- Dark scenes (near-black `#111`) appear only as a **contrast beat** (a logo sting, "Use AI", a voice orb).
- Saturation is very low (median 0.05). Colour arrives in one element at a time.

**Typography**
- A clean geometric or grotesk sans (SF Pro / Inter style), medium weight, set **small** relative to the frame. That leaves lots of negative space.
- Secondary voices: a **typewriter mono** for "quick question" and script beats, an **editorial serif** for premium brands, and a **condensed heavy sans** for the B&W documentary style.
- Emphasis: the last word is set in grey or the brand colour ("city *together*"), or one word in red with a soft red glow ("Est. Delivery Time: *I don't know*").

**Signature text moves**
1. **Word-by-word blur-in.** Each new word arrives blurred and slightly scaled, sharpens in about 6–8 frames, and pushes the line along.
2. **Typewriter with a caret.** Used inside search bars and inputs, often with the camera pushing in so the field fills the frame.
3. **Scatter and reassemble.** Words fly apart into a loose cloud, then snap back into a new sentence.
4. **Inline UI in a sentence.** "Your [Total Revenue $5,386 card] is limited by one number". The card sits where a word would.
5. **Slot or roll.** Dates and numbers roll through like a picker (13, 14, 15…).

**Signature UI moves**
- **Morph chain**: dot → pill → search bar → card → app screen. Each element grows out of the previous one, Dynamic-Island style, with no cut.
- **Fake cursor or hand tap**: the cursor glides in, presses (the element scales to 0.95), and the element reacts.
- **Fan or orbit**: posters fan out from a centre card, and avatars orbit a logo.
- **Logo build**: the icon draws or pops, then the wordmark slides out beside it.
- **3D phone mockups** tilt in on a gradient, with notification cards dropping onto the screen.

**Transitions** (ranked by how often they appear)
1. Morph or scale-through (most common)
2. Blur dissolve or focus pull
3. Fast whip pan with directional motion blur
4. "Barcode" glitch: vertical streak smear for 2–4 frames
5. Iris or lens reveal: white vignette opening onto the next scene
6. Hard cut only on a beat or a change of mood

**Pacing**
- Median length 11.6 s (range 3.9–44.6 s). Median shot length about 3.8 s, but motion never stops. Something eases in or out every 0.3–0.6 s.
- Eases look like strong ease-out / expo-out for arrivals, with a small overshoot on pops. Holds are short (0.3–0.8 s) on finished states.
- There's no long intro. Something is moving in the first 0.2 s.

---

## 4. Sound design (the key ingredient)

**SFX palette.** These names are visible on the creator's own timelines:
`Short Whoosh`, `SMOOTH Whoosh`, `Dreamy Whoosh`, `Magic Whoosh`, `Glass Riser`, `Granular Combo`, `Granular Transition`, `Enter` (UI pop/confirm), `ui-pop-sound`, `Num` (number/tick), `Audio effects | mensaje` (message ding), `Menu Notification`, `Glitch`, `tiktok_drop` (impact), `2 Short Whoosh`.

**Rules seen across the videos**
- **One sound per visible action**: a move gets a whoosh, an appear gets a pop or "Enter", typing gets ticks, a reveal gets a riser into a hit, a notification gets a ding.
- Sounds are **stacked tight**. A typical 11 s video has 15–25 SFX clips across 3–4 layers.
- **Music is optional and often absent.** The "SFX only + Voiceover only = Full mix" video says it outright: music isn't needed if the SFX are strong. When music is used, it's a trending rap or hip-hop track, or a minimal corporate bed, at low level.
- Loudness: median −20 LUFS, which is quiet for TikTok. We should master to about −14 LUFS.

---

## 5. Voiceover

Present in 9 of 40 videos. Many other "transcripts" were actually song lyrics.

| Video | Words per min | Style |
|---|---|---|
| Revolut explainer | 142 | Problem → "Welcome to Revolut" → steps |
| Bolt | 124 | Q&A rhythm: "Need a ride? Take a Bolt." |
| PayPal | 164 | Question → "Introducing PayPal" → stats |
| System 1/2 brain | 173 | Educational definition |
| ElevenLabs | 145 | "Introducing X, a way for developers to…" + user line |
| VSL (sales video) | 168 | Hook stat → "We're gonna fix that" |
| Chess VSL | 215 | Founder talking-head, fast |
| Startups (B&W) | 128 | Slow, punchy, manifesto |

- The voice starts **within 0.2 s**, with no pauses over 0.35 s, so it's continuous and tight.
- Script shape: **hook question or pain point → "Introducing / Welcome to [Brand]" → 2–3 feature beats → tagline**.
- Every spoken phrase appears **on screen at the same moment**, one word at a time.
- Voice timbre can't be confirmed from data alone. It reads as a calm, clear, modern American narrator. Closest Kokoro voices: `am_michael` / `am_adam` (male), `af_heart` / `af_nova` (female).

---

## 6. What performs

| Rank | Video | Views | Why |
|---|---|---|---|
| 1 | "Great motion design isn't just what you see… it's what you hear" (cream editorial + SFX timeline) | **987k** | Teaches a secret (sound), satisfying, rewatchable |
| 2 | "SFX breakdown" (AI search UI + timeline) | **892k** | Same format |
| 3 | "Sfx breakdown" (search, collage) | 102k | Same format |
| 4 | Brain System 1/2 (CapCut mockup + VO) | 81k | Clear educational hook |
| 5 | Bolt (CapCut mockup + VO) | 27.5k | Brand recreation + Q&A script |

Brand UI recreations without sound or VO sit at 1–6k views. **The breakdown format and an educational hook win.**

---

## 7. Per-video notes

| # | Date | Len | Format | What it does |
|---|---|---|---|---|
| O1 | 2025-12-06 | 9.6s | CapCut mockup, VO | Brain splits peach/red, serif labels "System One / Two" bullet in with hand-drawn arrows |
| O2 | 2025-12-08 | 14.2s | CapCut, VO | Bolt: "Need a ride?" (warped type) → phone UI scroll → driver progress bar → map → green circle wipe |
| O3 | 2025-12-09 | 7.9s | CapCut | Spotify: radar rings + orbiting avatars → search bar types → genre cards → logo on black |
| O4 | 2025-12-11 | 10.2s | CapCut | Netflix: "Need a movie fix?" → logo N-glitch → search typing → poster fan → "A Netflix Original Series" |
| O5 | 2025-12-12 | 20.0s | CapCut | Uber: iMessage chat → cursor taps "Go Uber" → logo → "Where to?" → ride options → "Ride requested" |
| O6 | 2025-12-14 | 9.9s | CapCut | Apple Music: dot bounces → "Millions of songs. No ads." → Dynamic-Island player morphs → volume pill |
| O7 | 2025-12-17 | 19.2s | CapCut | Apple widgets: calendar date roll → clock pill "Meeting" → weather card → camera bump on red/blue shapes |
| O8 | 2025-12-23 | 7.1s | CapCut | Pinterest: app-store pill → board cards stack → blue "Get" button |
| O9 | 2026-01-05 | 12.0s | CapCut, VO | PayPal: blue gradient text → payment cards → logo → +430M globe with avatars → countries → "Flexible" |
| O10 | 2026-01-07 | 3.9s | CapCut | Flighty: icon flips to flight card → "Tracking Alert Analytics" |
| O11 | 2026-01-08 | 24.9s | B&W doc, VO | Motivation-text wall + silhouette, statue, red bold keywords, hands, "GIFT" |
| O12 | 2026-01-18 | 11.2s | CapCut | Discord: calendar → join-voice pill → call UI → dock icons → photo widget |
| O13 | 2026-01-31 | 19.2s | 2×2 grid | "2k followers" montage of four earlier videos at once |
| O14 | 2026-02-28 | 14.9s | B&W doc, VO | "People don't buy from strangers": shattering masks, condensed type + script, chess king, eyeball |
| O15 | 2026-04-02 | 21.4s | 16:9 full, VO | Revolut: "Sending money = simple" → receipt → red "I don't know" glow → logo → recipients → $66.09 → success |
| O16 | 2026-04-04 | 11.6s | 16:9 | ClickUp: logo → "+ New" → menu (barcode glitch) → forms → "Click Up" huge type on black |
| O17 | 2026-04-08 | 10.4s | 16:9 | Apple ID sign-in: dot ring loader → camera push into typed email → account card → wordmark |
| O18 | 2026-04-11 | 11.3s | 16:9 | Shazam: store card → "Listening for music" → result card → emoji reactions |
| O19 | 2026-04-13 | 21.4s | 2×2 grid | "Which edit goes hardest?" with four April edits |
| O20 | 2026-04-15 | 22.3s | 1:1 | Google Drive: logo → "+ New" tap → menu → typed folder name → drop zone → "Uploading two items" |
| N1 | 2026-06-24 | 21.5s | 16:9 cream | Audo Copenhagen: typewriter "Quick question." → scattered words → photo strip → "Beyond [photo] Decor" |
| N2 | 2026-06-26 | 21.5s | "Just Sfx" + timeline | Same piece with the SFX timeline shown: **987k views** |
| N3 | 2026-06-30 | 14.0s | 1:1 | Selar store ad: comment card "where do you get everything for your edits?" → product grid → profile |
| N4 | 2026-07-04 | 11.4s | 1:1 | AI search: browser bar → pastel gradient → word scatter → "how to find this [Figma] files?" icon roll → "Use AI" |
| N5 | 2026-07-10 | 8.1s | 16:9 pink | VSL: "Your [revenue card] is limited by one number" → red calendar → blue calendar fix |
| N6 | 2026-07-13 | 11.3s | 1:1 + timeline | N4 with SFX timeline: **892k views** |
| N7 | 2026-07-18 | 16.1s | 2×2 grid | "Best frame wins✨" with four recent works |
| N8 | 2026-07-25 | 12.7s | 16:9, VO | ElevenLabs: bars → logo → typed text → chat input → toggle → dark voice orb with live caption |
| N9 | 2026-08-02 | 11.7s | 16:9, VO | Desktop: sky → meadow wallpaper → dock → Slack message → notes app → "fn and start speaking" |
| N10 | 2026-08-15 | 23.4s | 2×2 grid | SaaS explainer frames (Velbaz): cyan ribbon, typed taglines, dashboards |
| N11 | 2026-08-28 | 11.4s | 16:9 | Pinterest: search typing → collage → "do something with your mind" kinetic type with red highlight |
| N12 | 2026-08-30 | 8.1s | 16:9, VO | VSL pink → blue (same as N5 with VO) |
| N13 | 2026-08-31 | 37.4s | 16:9 + toggle | ElevenLabs piece played 3×: SFX / Voiceover / SFX+VO |
| N14 | 2026-09-14 | 14.7s | 2×2 grid | Chess VSL frames: talking head + green subtitle boxes + red/green keywords |
| N15 | 2026-09-16 | 5.8s | + timeline | Pinterest search with SFX timeline: 102k |
| N16 | 2026-10-11 | 44.6s | Talking-head VSL | Founder on camera, cutaways to UI cards, green chat-box captions, timeline overlay |
| N17 | 2026-10-20 | 8.5s | 2×2 grid | Italian real estate: Italian verbs rolling, house photos, URL typing |
| N18 | 2026-10-26 | 11.5s | 1:1 periwinkle | Social map app: blur-in "may i ask where you are?" → glass pill → chat bubble tap → lens reveal map → 3D phone → Memoji |
| N19 | 2026-11-04 | 11.2s | Side by side | "Left or right?" comparing N4 and N18 |
| N20 | 2026-11-10 | 11.3s | 1:1 + timeline | N18 with SFX timeline |

---

## 8. Recipe for our videos (input to the skill)

1. **Default canvas** 1080×1920 (TikTok/Reels) or 1920×1080, at 30 fps. Off-white or cream background, a single accent colour.
2. **Beats every 1.5–3 s**, one idea per beat, centred, with plenty of negative space.
3. **Text** goes in word by word with a blur-in, and the key word gets the accent colour or grey.
4. **Element continuity**: each beat's object morphs out of the last one's.
5. **Cursor taps** and **typed inputs** with a camera push-in for any UI moment.
6. **Transitions**: morph, blur, whip, barcode glitch or iris. Hard cuts only on mood changes.
7. **SFX on every action** (whoosh, pop, tick, riser, hit, ding). Music optional and low. Master at −14 LUFS.
8. **Voiceover** (when used): 140–170 wpm, no dead air, script = hook → introduce → 2–3 benefits → tagline. Captions mirror the VO word for word.
9. **End** on a logo or wordmark sting, or a Memoji/avatar sign-off.
10. **Optional bonus format**: a "sound design breakdown" version (caption on top, render in the middle, SFX timeline at the bottom), which is the account's most viral format.
