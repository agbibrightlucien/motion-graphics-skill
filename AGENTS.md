# For AI coding agents working in this repository

This repository **is** an Agent Skill: `skills/clean-motion-video/SKILL.md`. It makes motion-graphics
videos with voiceover (rendered with HyperFrames).

- **If the user asks you to install it:** follow `README.md` → Install. The skill folder to install is
  `skills/clean-motion-video/` (the folder containing `SKILL.md`). Prefer
  `npx skills add <this repo> -g -a <agent>`; otherwise run `install/install.ps1` (Windows) or
  `install/install.sh` (macOS/Linux), then `python -I -u skills/clean-motion-video/scripts/cmv.py setup --test`.
- **If the user asks you to make a video from inside this repository** (without installing): read
  `skills/clean-motion-video/SKILL.md` and follow it, with `SKILL` = `skills/clean-motion-video`. Put
  video projects in `projects/<slug>/` (ignored by git).
- **If you change the skill:** keep `SKILL.md` agent-neutral (no agent-specific tool names or paths),
  keep scripts runnable on Windows, macOS and Linux, and never commit Pixabay library sounds,
  rendered videos, voice recordings or API keys.
