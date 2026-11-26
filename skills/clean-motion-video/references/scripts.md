# Writing the script

Measured from the reference videos that had voiceover: 124–173 words per minute (median ~150),
the first word inside 0.2 s, no pause longer than 0.35 s, one thought per sentence. Every spoken
phrase also appears on screen at the same moment, word by word.

## Formulas

**Explainer (concept)**: 12–25 s
1. Hook: a question or a surprising claim the viewer feels. *"What if your money grew while you slept?"*
2. Name it: *"That's compound interest."* + the one-line definition.
3. Proof: one concrete number or example, shown as UI (card, chart, counter).
4. The takeaway, reframed: *"The secret isn't how much. It's how early."*
5. End card: 2–4 words (no VO), held ≥ 2 s.

**Product ad / launch**: 12–20 s
1. Pain or desire as a question: *"Need a ride?"*, *"Sending money should be simple…"*
2. *"Introducing / Welcome to <Brand>."* + logo build.
3. 2–3 feature beats, each = one verb the UI performs on screen (choose → set → track).
4. Tagline + logo/wordmark sting.

**VSL / sales hook**: 8–15 s
1. The number that hurts: *"Your revenue is limited by one number."* (problem colour: red/blush)
2. Show the empty state (calendar with no calls, red).
3. *"We're gonna fix that."* → colour flood to blue, the filled state.
4. CTA line.

**Q&A rhythm** (works for anything short): question → answer, repeated:
*"Need a ride? Take a Bolt. Enjoy the trip? Pay as you go."*

**Manifesto / documentary** (B&W `mono` theme, heavier type): short punchy fragments, each
fragment its own beat: *"People don't buy from strangers. They buy from faces they recognize."*

## Line rules
- 4–14 words per beat line. Split anything longer into two beats.
- Put the accent word late in the line, where the voice lands on it; that is the `<b>` word.
- Numbers: write them as spoken in `vo` ("forty six thousand") and as digits on screen ("$46,610").
- No "In this video…", no greetings, no "Let's dive in".
- End lines short: the end card holds 2+ s without voice.

## Plan entries
```json
{"id": "hook", "vo": "What if your money grew while you slept?", "min": 3.0, "lead": 0.15}
```
`lead` = seconds before the voice starts in that scene (default 0.15). `pad` = seconds kept after
the voice ends (default 0.25). `min` = minimum scene length (use it for scenes whose animation
needs more time than the line, and for the end card). Scene ids are short, lowercase, unique.

In a **one-take** film (user recording, Gemini, or Kokoro `"take": "full"`) the voice is one
continuous clip: scene lengths come from where each scene's words fall in the take, so `lead`
(plan-level, default 0.15) and the last scene's `pad`/`min` are the only timing knobs; `min` on a
middle scene cannot stretch the voice.

## A script the user wrote
Keep it word for word. Split it into beats (sentence ends; long sentences at a comma or "and/but";
join fragments under ~1.5 s), give each beat an id and a visual, and write each beat's exact words
as its `vo`. Speaking style comes from the voice choice and `voice_style` (Gemini), not from
rewording. If the script is long, the film is long: that's fine; vary the patterns across beats so
it doesn't repeat every 3 scenes.

## Spoken call to action (when you write the script)
One short line, earned by value just delivered, in the narrator's voice, never at the very start:
- Long-form, ~30-40% in, right after a strong point: "If this is hitting home, subscribe and turn on
  notifications, because next week we're talking about <next topic>." Then straight back to content.
- Long-form ending: "Subscribe so you don't miss the next one," before or after the comment question.
- Shorts, last 2 s: "Follow for part two." / "Follow if you want the full breakdown."
Pair every spoken CTA with `cmv.py cta` at the same moment so the screen shows the tap.
