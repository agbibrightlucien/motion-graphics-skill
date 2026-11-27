# Publish pack (every finished video)

A video isn't delivered until it ships with everything needed to post it. Every video project ends with
two delivery folders (working files stay where they are):

```
projects/<slug>/
  YouTube/   <Title>.mp4 (the mastered upload), thumbnail-v1.png, thumbnail-v2.png, YOUTUBE.md, CREDITS.md
  TikTok/    Part 1 - <title>.mp4, Part 1 - caption.txt, ... , TIKTOK.md
```
`CMV thumb` writes thumbnails into `YouTube/`, `CMV tiktok` writes the parts into `TikTok/`, and
`CMV package <dir> --title "<Title>"` copies the mastered video into `YouTube/` under its title, merges
all sound/image credits into `YouTube/CREDITS.md`, and writes `YOUTUBE.md` / `TIKTOK.md` skeletons
(with chapter timestamps) if you haven't written them yet. Write the final copy into those files.
Tell the user the two folder paths when you deliver. Shorts: `YouTube/` holds the short + its
YouTube Shorts copy, `TikTok/` the same file + caption.

## Long-form (YouTube)
1. **`YouTube/YOUTUBE.md`**
   - 3 title options (≤ 60 chars, curiosity + clear payoff; the first is your pick). No clickbait the video
     doesn't pay off.
   - Description: 1–2 line hook restating the promise, chapters (`cmv.py chapterlist <dir>` gives the
     timestamps; write short chapter names), the subscribe link
     `https://www.youtube.com/@<handle>?sub_confirmation=1`, image/SFX credits (CREDITS.md files), 3 hashtags.
   - Tags: **comma-separated** (that's what YouTube Studio expects), 15–25 tags, ≤ 500 characters, mixing
     the exact topic, broader topic, and channel name.
   - Pinned comment: a question that invites replies (often the video's closing question).
2. **Thumbnails** (`cmv.py thumb`, saved in `YouTube/`): make 2 options, 1280×720.
   - 2–4 huge words (the emotional core, not the full title), one accent word; optional kicker chip.
   - One strong visual from the video (`--frame <seconds>` of a fully built, readable moment) and at
     most one sticker (a number, a stamp: `--sticker "$4.12" --sticker-label "Available balance"`).
   - Readable at phone size: test by looking at the PNG small. Don't repeat the title word for word.
   - Accent red for problem/warning topics, blue for neutral/explainer, green for wins.
3. **TikTok parts** (no new render; `cmv.py tiktok`): see below.

## TikTok parts from a long video
Cut the finished film into **parts** that each work alone; post them in order as "Part 1, Part 2, …".
```bash
CMV tiktok projects/<slug> --parts "s1..s19|s20..s62|s63..s103" --titles "Hook title|Part 2 title|Part 3 title" \
  --captions "Caption 1 #tags|Caption 2 #tags|Caption 3 #tags"
```
- **Default output = ready to post** (the user picks these up and posts them as they are):
  `TikTok/Part N - <title>.mp4`, 1080×1920 with "PART N" + title above, logo + handle +
  "Full video on YouTube" below, the film in the middle band, plus `Part N - caption.txt` (caption + the
  first-comment line). Plain landscape cuts stay in `publish/tiktok-cuts/` (working files). No motion-graphics re-render; ffmpeg only.
- Before delivering, grab one frame from every part and check each title is right, then send the whole
  `TikTok/` folder (not just a sample).
- **Choosing the parts (deliberately):**
  - **Part 1 = the hook**: from 0:00 to the first natural cliffhanger (the end of the intro, "let's talk
    about it"), 45–90 s. It decides whether anyone watches Part 2.
  - **Every part starts on a line that makes sense cold** (a section start: "First, …", "Here's the
    uncomfortable part…") and **ends on a resolved point or a cliffhanger**, never mid-thought. Cut only
    at scene boundaries (`s12..s30` uses the film's own scene times).
  - 1–3 minutes each (TikTok rewards completion; shorter parts finish more often). Merge short sections,
    split long ones at a strong line.
  - Keep story order so the numbering matches the narration ("Second, …" is in Part 2's range).
  - The last part carries the call to action / comment question.
- **`TikTok/TIKTOK.md`**: for each part, the time range, a caption (hook line + "Part N"), 3–5 hashtags
  (#<channel> + topic tags), and the on-screen title used. Note any part that leans on an earlier one.

## Shorts (vertical videos)
`YOUTUBE.md`/`TIKTOK.md` with one title, a caption with 3–5 hashtags and the comment question; one
thumbnail/cover frame (`cmv.py thumb` or the film's frame 0).
