# Real images in motion-graphics videos

Built UI (cards, receipts, charts, chat bubbles) is the default and tells most stories best. Bring in
**real images only when they make the video more true or more relatable** and built graphics can't:

| Use real images | Don't |
|---|---|
| History: the actual people, places, events, documents, maps, artworks | Generic "person looking at phone" stock |
| A real place or landmark the script names | Abstract ideas (debt, discipline): build UI instead |
| A real object or invention whose look matters | Anything you can draw cleanly as UI |
| Archive evidence that proves the point (a newspaper, a ration card) | Decoration with no job in the beat |

Rule of thumb: if the narrator names something real and specific (a person, year, place, artefact),
show the real thing. If the line is about a feeling or a concept, build it.

## Getting them (free, licensed, credited)
```bash
python -I SKILL/scripts/fetch_images.py projects/<slug> "Great Depression breadline" --n 4 --tag breadline
python -I SKILL/scripts/fetch_images.py projects/<slug> "Colosseum Rome" --source openverse --tag colosseum
```
- Sources: **Wikimedia Commons** first (archive photos, paintings, maps; most history is public domain),
  then **Openverse** (Flickr, museums, NASA, rawpixel public-domain sets).
- Licences kept: public domain, CC0, CC BY. Never NonCommercial, NoDerivatives, ShareAlike, "fair use",
  news/agency photos, film stills, or anything from a random web page.
- Files: `assets/images/<tag>-N.jpg`; `assets/images/images.json` (title, author, licence, source);
  `assets/images/CREDITS.md`: paste its lines into the video description (required for CC BY).
- **Look at `_sheet-<tag>.jpg` before using anything**: search results can be wrong (a 1939 car came
  back for "1930s" once). Use the built-in browser to verify a fact or find a better search term
  (e.g. the exact name of an event or archive collection); download only through the script.
- Search concretely: people + place + year + object ("Rosa Parks bus 1955", "Berlin Wall 1989 crowd").
- Never invent a real person's face with AI or redraw a real logo; never present a reconstruction as a photo.

## Using them in a scene (keep the clean style)
- **Framed print:** the photo sits in a white card (radius 18–24, 10–14 px white border, soft shadow),
  tilted −3…3°, with a small caption chip ("New York, 1932"), like an exhibit, not a full-bleed slide.
- **Motion:** arrive with `CM.lens` or a 0.5 s rise; then a slow push 1.0 → 1.08 over the beat **that ends**
  (no endless drift); exit with the beat.
- **Combine with UI:** a photo + a data card ("25% unemployed") or a map + pins beats a lone photo.
- **Paper look for history:** `--theme paper`, serif titles, grain; photos in sepia frames.
- Grading, grain, blur or vignettes on photos go through `HF media-treatment` (`/media-use`), never CSS filters.
- Credit: add `assets/images/CREDITS.md` to the publish pack's YouTube description.
