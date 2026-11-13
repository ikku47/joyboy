#!/bin/bash
# joyboy workspace setup. Safe to run every time: it only does work that has not been done yet.
#   setup.sh [workspace]        default workspace: ~/joyboy  (or $JOYBOY_HOME)
# Creates:  <workspace>/.venv      Python environment, packages installed once
#           <workspace>/lib        the toolkit (joyboy.py, score.py, quick.py), refreshed when the skill changes
#           <workspace>/voices     Piper voice models, downloaded once
#           <workspace>/SYSTEM.md  checklist of what this machine has, rewritten on every run
#           <workspace>/projects   one folder per video
set -e
WS="${1:-${JOYBOY_HOME:-$HOME/joyboy}}"
SKILL="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WS/lib" "$WS/projects"

command -v ffmpeg >/dev/null || { echo "MISSING: ffmpeg is not installed (macOS: brew install ffmpeg). Ask the user before installing."; exit 1; }

if [ ! -x "$WS/.venv/bin/python" ]; then
  echo "creating environment (one time)..."
  python3 -m venv --system-site-packages "$WS/.venv"     # reuse packages the system already has
fi
PY="$WS/.venv/bin/python"
MISSING=""
for pair in cv2:opencv-python numpy:numpy PIL:pillow scipy:scipy; do
  "$PY" -c "import ${pair%%:*}" 2>/dev/null || MISSING="$MISSING ${pair##*:}"
done
if [ -n "$MISSING" ]; then
  echo "installing (one time):$MISSING"
  "$PY" -m pip install --quiet $MISSING
fi

# voice-over: Piper TTS (local, free) plus one default voice, installed once
"$PY" -c "import piper" 2>/dev/null || { echo "installing Piper TTS (one time)..."; "$PY" -m pip install --quiet piper-tts || echo "WARNING: Piper could not be installed; narration will use the system voice"; }
mkdir -p "$WS/voices" "$WS/fonts" "$WS/maps" "$WS/icons" "$WS/captures" "$WS/brand"
if ! ls "$WS/voices"/*.onnx >/dev/null 2>&1 && "$PY" -c "import piper" 2>/dev/null; then
  echo "downloading default Piper voice (one time)..."
  "$PY" -m piper.download_voices --download-dir "$WS/voices" en_US-lessac-medium || echo "WARNING: voice download failed"
fi

for f in joyboy.py score.py quick.py maps.py ambience.py world.py model3d.py sitekit.py; do
  if [ ! -f "$WS/lib/$f" ] || [ "$SKILL/$f" -nt "$WS/lib/$f" ]; then cp "$SKILL/$f" "$WS/lib/$f"; fi
done

# web kit (optional): GSAP + headless capture, for film.web() scenes. Installed once when node is available.
# Package installer: bun when it is there (several times faster, and it keeps one shared cache on this machine, so a package
# already downloaded for any other project is linked in instead of downloaded again); npm otherwise, reusing its own cache.
PKGS="gsap puppeteer-core react-icons react react-dom lucide-static gss-lang @dicebear/core @dicebear/collection three 67js@npm:@codepawlhq/67js@0.19.0"
if command -v bun >/dev/null; then INSTALLER="bun"; elif [ -x "$HOME/.bun/bin/bun" ]; then INSTALLER="$HOME/.bun/bin/bun"; elif command -v npm >/dev/null; then INSTALLER="npm"; else INSTALLER=""; fi
if [ -n "$INSTALLER" ]; then
  mkdir -p "$WS/web"
  NEED=""
  for d in gsap puppeteer-core react-icons lucide-static gss-lang @dicebear/collection three 67js; do [ -d "$WS/web/node_modules/$d" ] || NEED="yes"; done
  if [ -n "$NEED" ]; then
    echo "installing web kit with ${INSTALLER##*/} (one time): gsap, capture, icons, gss-lang, DiceBear, three.js, 67.js..."
    if [ "${INSTALLER##*/}" = "bun" ]; then
      (cd "$WS/web" && { [ -f package.json ] || echo '{"name":"joyboy-web","private":true}' > package.json; } && "$INSTALLER" add $PKGS >/dev/null 2>&1) || echo "WARNING: web kit install failed; web, icon, character and 3D scenes will be unavailable"
    else
      (cd "$WS/web" && { [ -f package.json ] || npm init -y >/dev/null; } && npm install --silent --prefer-offline --no-audit --no-fund $PKGS >/dev/null) || echo "WARNING: web kit install failed; web, icon, character and 3D scenes will be unavailable"
      echo "TIP: bun is not installed. With bun this step is several times faster and reuses packages already downloaded for other projects. See SYSTEM.md."
    fi
  fi
  for f in web_capture.mjs web_template.html icon.mjs avatar.mjs world.js world_still.mjs icon_anim_template.html gss_template.html page_capture.mjs site_save.mjs; do
    if [ ! -f "$WS/web/$f" ] || [ "$SKILL/$f" -nt "$WS/web/$f" ]; then cp "$SKILL/$f" "$WS/web/$f"; fi
  done
fi

"$PY" "$SKILL/inventory.py" "$WS" >/dev/null || true

echo "READY"
echo "workspace: $WS"
echo "python:    $PY"
echo "lib:       $WS/lib"
echo "projects:  $WS/projects"
echo "checklist: $WS/SYSTEM.md   (read this first)"
