# Third-party notices

## Sound effects (`skills/clean-motion-video/assets/sfx/`)
- **CC0 1.0** (public domain dedication): most files, from Freesound via Openverse. No attribution
  required; sources are listed in `assets/sfx/CREDITS.md` and in `manifest.json` (`credit`).
- **CC BY 4.0**: `whoosh-pass.mp3`, `swish.mp3`, `magic-whoosh.mp3`, `granular-transition.mp3`,
  `bubble-pop.mp3`. Attribution is required wherever a video using them is published; the skill's
  `assemble` step writes the exact lines to each project's `CREDITS.md`.
- **Synthesised** (`error-synth-1..5.mp3`): generated from sine-wave maths for this kit; CC0.
- **Not included**: 15 sounds from the HyperFrames sound library (Pixabay Content License: free to use
  in videos, but the raw files may not be redistributed on their own). `cmv.py setup` copies them from
  the user's own HyperFrames `media-use` skill. Their names are listed in `manifest.json` with
  `"license": "library"`.

## Voices (`extras/voice-audition/`)
Generated locally with **Kokoro-82M** (Apache License 2.0, https://huggingface.co/hexgrad/Kokoro-82M)
through the HyperFrames CLI. The model itself is downloaded on first use, not included here.

## Software used at runtime (not included)
- **HyperFrames** by HeyGen (https://github.com/heygen-com/hyperframes): rendering, TTS and
  transcription CLI, installed from npm on demand.
- **GSAP** (https://gsap.com), loaded from a CDN by the video templates.
- **NVIDIA Parakeet** (transcription model, CC BY 4.0), downloaded by HyperFrames on first use.
- **ffmpeg** (https://ffmpeg.org), installed by the user.
- **Openverse** and **Wikimedia Commons** APIs: searched for CC0 / public-domain / CC BY images and
  sounds; each downloaded item keeps its own licence and credit.

## Images
`docs/images/` shows frames from videos made with this skill (original graphics, no third-party images).
