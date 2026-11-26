#!/usr/bin/env bash
# Install the clean-motion-video skill into one or more AI coding agents (macOS / Linux / Git Bash).
#   bash install/install.sh --agent claude,codex,antigravity --scope global
#   bash install/install.sh --agent all --scope project --project ~/videos
#   options: --skip-hyperframes  --yes
set -euo pipefail

AGENTS="claude"; SCOPE="global"; PROJECT="$(pwd)"; SKIP_HF=0; YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --agent) AGENTS="$2"; shift 2 ;;
    --scope) SCOPE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --skip-hyperframes) SKIP_HF=1; shift ;;
    --yes|-y) YES=1; shift ;;
    -h|--help) sed -n 2,6p "$0"; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
done

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/skills/clean-motion-video"
[ -f "$SRC/SKILL.md" ] || { echo "can't find skills/clean-motion-video/SKILL.md"; exit 1; }

global_dir() { case "$1" in
  claude) echo "$HOME/.claude/skills" ;; codex) echo "$HOME/.agents/skills" ;;
  antigravity) echo "$HOME/.gemini/config/skills" ;; gemini) echo "$HOME/.gemini/skills" ;;
  cursor) echo "$HOME/.cursor/skills" ;; copilot) echo "$HOME/.copilot/skills" ;;
  opencode) echo "$HOME/.config/opencode/skills" ;; windsurf) echo "$HOME/.codeium/windsurf/skills" ;;
  *) echo "" ;; esac; }
project_dir() { case "$1" in
  claude) echo ".claude/skills" ;; windsurf) echo ".windsurf/skills" ;;
  codex|antigravity|gemini|cursor|copilot|opencode) echo ".agents/skills" ;; *) echo "" ;; esac; }
cli_name() { case "$1" in
  claude) echo claude-code ;; gemini) echo gemini-cli ;; copilot) echo github-copilot ;; *) echo "$1" ;; esac; }

[ "$AGENTS" = "all" ] && AGENTS="claude,codex,antigravity,gemini,cursor,copilot,opencode,windsurf"
IFS=',' read -r -a LIST <<< "$AGENTS"

TARGETS=()
for a in "${LIST[@]}"; do
  a="$(echo "$a" | tr '[:upper:]' '[:lower:]' | xargs)"
  if [ "$SCOPE" = "global" ]; then base="$(global_dir "$a")"; else rel="$(project_dir "$a")"; base="${rel:+$PROJECT/$rel}"; fi
  [ -n "$base" ] || { echo "unknown agent '$a'"; continue; }
  case " ${TARGETS[*]-} " in *" $base "*) ;; *) TARGETS+=("$base") ;; esac
done

for base in "${TARGETS[@]}"; do
  dst="$base/clean-motion-video"
  mkdir -p "$base"
  if [ -e "$dst" ]; then bak="$dst.bak-$(date +%Y%m%d-%H%M%S)"; mv "$dst" "$bak"; echo "  previous version moved to $bak"; fi
  cp -R "$SRC" "$dst"
  echo "installed -> $dst"
done

if [ "$SKIP_HF" -eq 0 ]; then
  ans="y"; [ "$YES" -eq 1 ] || { read -r -p "Install the HyperFrames skills too (recommended)? [Y/n] " ans || true; }
  if [[ ! "$ans" =~ ^[nN] ]]; then
    flags=(--yes skills add heygen-com/hyperframes)
    [ "$SCOPE" = "global" ] && flags+=(-g)
    for a in "${LIST[@]}"; do flags+=(-a "$(cli_name "$(echo "$a" | xargs)")"); done
    [ "$YES" -eq 1 ] && flags+=(-y)
    echo "npx ${flags[*]}"
    ( [ "$SCOPE" = "project" ] && cd "$PROJECT"; npx "${flags[@]}" ) || echo "warning: HyperFrames skills install failed (the skill still works through npx)"
  fi
fi

PY="$(command -v python3 || command -v python || true)"
if [ -n "$PY" ] && [ "${#TARGETS[@]}" -gt 0 ]; then
  "$PY" -I -u "${TARGETS[0]}/clean-motion-video/scripts/cmv.py" setup
else
  echo "warning: Python not found: install Python 3.9+, then run: python3 -I -u <skill>/scripts/cmv.py setup"
fi
echo
echo "Done. Start a new agent session and ask for a video (or call the skill: /clean-motion-video, \$clean-motion-video)."
