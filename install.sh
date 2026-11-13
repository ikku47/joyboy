#!/bin/bash
# joyboy installer: copies the skill into the skills folder of each AI coding tool it finds.
#   curl -fsSL https://raw.githubusercontent.com/ikku47/joyboy/main/install.sh | bash
#   bash install.sh [--claude] [--codex] [--agents] [--dir <folder>] [--all]
# With no flags it installs for every tool found on this machine (Claude Code if none is found).
# An existing joyboy skill is moved aside to joyboy.backup-<time>, never deleted.
set -e
REPO="https://github.com/ikku47/joyboy"
TARGETS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --claude) TARGETS+=("$HOME/.claude/skills") ;;
    --codex)  TARGETS+=("$HOME/.codex/skills") ;;
    --agents) TARGETS+=("$HOME/.agents/skills") ;;
    --all)    TARGETS+=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills") ;;
    --dir)    shift; TARGETS+=("$1") ;;
    -h|--help) sed -n '2,6p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
  shift
done
if [ ${#TARGETS[@]} -eq 0 ]; then
  [ -d "$HOME/.claude" ] && TARGETS+=("$HOME/.claude/skills")
  [ -d "$HOME/.codex" ]  && TARGETS+=("$HOME/.codex/skills")
  [ -d "$HOME/.agents" ] && TARGETS+=("$HOME/.agents/skills")
  [ ${#TARGETS[@]} -eq 0 ] && TARGETS+=("$HOME/.claude/skills")
fi

# Use the copy next to this script when run from a clone; otherwise download the repository.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$HERE" ] && [ -f "$HERE/skills/joyboy/SKILL.md" ]; then
  SRC="$HERE/skills/joyboy"; TMP=""
else
  TMP="$(mktemp -d)"
  echo "downloading joyboy..."
  if command -v git >/dev/null; then git clone --depth 1 --quiet "$REPO" "$TMP/joyboy"
  else curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP" && mv "$TMP"/joyboy-* "$TMP/joyboy"; fi
  SRC="$TMP/joyboy/skills/joyboy"
fi
[ -f "$SRC/SKILL.md" ] || { echo "could not find the skill files"; exit 1; }

for T in "${TARGETS[@]}"; do
  mkdir -p "$T"
  if [ -e "$T/joyboy" ]; then mv "$T/joyboy" "$T/joyboy.backup-$(date +%Y%m%d-%H%M%S)"; echo "kept your previous copy as a backup in $T"; fi
  cp -R "$SRC" "$T/joyboy"; chmod +x "$T/joyboy/scripts/setup.sh"
  echo "installed: $T/joyboy"
done
[ -n "$TMP" ] && rm -rf "$TMP"
echo
echo "Done. Start a new session in your tool and ask for a video, for example:"
echo "  make a 20 second teaser for my coffee shop"
echo "The first video sets up a workspace in ~/joyboy and installs what it needs once."
