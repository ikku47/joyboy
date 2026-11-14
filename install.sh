#!/bin/bash
# joyboy installer: copies the skill into the skills folder of each AI coding tool it finds.
#   curl -fsSL https://raw.githubusercontent.com/ikku47/joyboy/main/install.sh | bash
#   bash install.sh [--claude] [--codex] [--agents] [--dir <folder>] [--all] [--no-companions]
# With no flags it installs for every tool found on this machine (Claude Code if none is found).
# It also installs the companion skills in this pack (the /ig-* Instagram skills) and, when the Agent Reach command is
# installed, links its skill (`agent-reach skill link`) so research and reading links work. --no-companions skips both.
# An existing skill is moved aside to <name>.backup-<time>, never deleted.
set -e
REPO="https://github.com/ikku47/joyboy"
TARGETS=(); COMPANIONS=1
while [ $# -gt 0 ]; do
  case "$1" in
    --claude) TARGETS+=("$HOME/.claude/skills") ;;
    --codex)  TARGETS+=("$HOME/.codex/skills") ;;
    --agents) TARGETS+=("$HOME/.agents/skills") ;;
    --all)    TARGETS+=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills") ;;
    --dir)    shift; TARGETS+=("$1") ;;
    --no-companions) COMPANIONS=0 ;;
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
  if command -v git >/dev/null; then
    # fetch only the skill folder, not the example videos; fall back to a plain clone on older git
    (git clone --depth 1 --filter=blob:none --sparse --quiet "$REPO" "$TMP/joyboy" 2>/dev/null && git -C "$TMP/joyboy" sparse-checkout set skills >/dev/null 2>&1) || { rm -rf "$TMP/joyboy"; git clone --depth 1 --quiet "$REPO" "$TMP/joyboy"; }
  else curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP" && mv "$TMP"/joyboy-* "$TMP/joyboy"; fi
  SRC="$TMP/joyboy/skills/joyboy"
fi
[ -f "$SRC/SKILL.md" ] || { echo "could not find the skill files"; exit 1; }

for T in "${TARGETS[@]}"; do
  mkdir -p "$T"
  if [ -e "$T/joyboy" ]; then mv "$T/joyboy" "$T/joyboy.backup-$(date +%Y%m%d-%H%M%S)"; echo "kept your previous copy as a backup in $T"; fi
  cp -R "$SRC" "$T/joyboy"; chmod +x "$T/joyboy/scripts/setup.sh"
  echo "installed: $T/joyboy"
  if [ "$COMPANIONS" = "1" ]; then
    for C in "$(dirname "$SRC")"/*/; do
      N="$(basename "$C")"; [ "$N" = "joyboy" ] && continue; [ -f "$C/SKILL.md" ] || continue
      if [ -e "$T/$N" ]; then mv "$T/$N" "$T/$N.backup-$(date +%Y%m%d-%H%M%S)"; fi
      cp -R "$C" "$T/$N"; INSTALLED="$INSTALLED $N"
    done
    [ -n "$INSTALLED" ] && echo "installed companions in $T:$INSTALLED"
    INSTALLED=""
    # Agent Reach (reads YouTube, Instagram, X, Reddit and the web; read-only). Its skill is linked, not copied, so it updates with the tool.
    if command -v agent-reach >/dev/null 2>&1; then
      agent-reach skill link "$T" >/dev/null 2>&1 && echo "linked Agent Reach skill in $T" || echo "note: Agent Reach is installed but its skill could not be linked into $T (try: agent-reach skill link $T)"
    else
      REACH_MISSING=1
    fi
  fi
done
[ -n "$TMP" ] && rm -rf "$TMP"
[ "${REACH_MISSING:-0}" = "1" ] && echo "note: Agent Reach is not installed, so the research skills fall back to the web tools of your agent. Install Agent Reach (its own installer; it only reads, and you log in yourself), then run:  agent-reach skill link <skills folder>"
echo
echo "Done. Start a new session in your tool and ask for a video, for example:"
echo "  make a 20 second teaser for my coffee shop"
echo "The first video sets up a workspace in ~/joyboy and installs what it needs once."
