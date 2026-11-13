"""Write <workspace>/SYSTEM.md: a short checklist of what this machine has for making videos.
Run by setup.sh on every start. Anything under '## Notes' in the existing file is kept."""
import os, sys, glob, shutil, subprocess, datetime, importlib

ws = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")))
path = os.path.join(ws, "SYSTEM.md")
box = lambda ok: "[x]" if ok else "[ ]"

def ver(mod, attr="__version__"):
    try: return str(getattr(importlib.import_module(mod), attr, "installed"))
    except Exception: return None
def cmd(*a):
    try: return subprocess.run(a, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception: return ""

ff = shutil.which("ffmpeg"); ffv = cmd("ffmpeg", "-version").split("\n")[0].replace("ffmpeg version ", "").split(" ")[0] if ff else None
pk = [("opencv", ver("cv2")), ("numpy", ver("numpy")), ("pillow", ver("PIL")), ("scipy", ver("scipy"))]
try:
    from importlib.metadata import version; piper = version("piper-tts")
except Exception: piper = None
voices = sorted(os.path.basename(v)[:-5] for v in glob.glob(os.path.join(ws, "voices", "*.onnx")))
eleven = bool(os.environ.get("ELEVENLABS_API_KEY")); say = bool(shutil.which("say"))
try: supertonic = version("supertonic")
except Exception: supertonic = None
st_model = os.path.isdir(os.path.join(ws, "voices", "supertonic", "onnx"))
voice = "ElevenLabs" if eleven else "Piper" if piper and voices else "system voice (say)" if say else "none"
node = cmd("node", "--version") or None
bun = cmd("bun", "--version") or (cmd(os.path.expanduser("~/.bun/bin/bun"), "--version") if os.path.exists(os.path.expanduser("~/.bun/bin/bun")) else "") or None
npm_ = cmd("npm", "--version") or None
try: gsap = __import__("json").load(open(os.path.join(ws, "web", "node_modules", "gsap", "package.json")))["version"]
except Exception: gsap = None
chrome = next((n for n, p in (("Google Chrome", "/Applications/Google Chrome.app"), ("Chromium", "/Applications/Chromium.app"), ("Brave", "/Applications/Brave Browser.app"), ("Edge", "/Applications/Microsoft Edge.app"),
                               ("google-chrome", "/usr/bin/google-chrome"), ("chromium", "/usr/bin/chromium")) if os.path.exists(p)), None)
def npmver(pkg):
    try: return __import__("json").load(open(os.path.join(ws, "web", "node_modules", pkg, "package.json")))["version"]
    except Exception: return None
ricons, lucide, gss = npmver("react-icons"), npmver("lucide-static"), npmver("gss-lang"); nicons = len(glob.glob(os.path.join(ws, "icons", "*.png")))
nmaps = len(glob.glob(os.path.join(ws, "maps", "*.json")))
fonts = [n for n, p in (("Avenir Next", "/System/Library/Fonts/Avenir Next.ttc"), ("Helvetica", "/System/Library/Fonts/Helvetica.ttc"), ("Menlo (mono)", "/System/Library/Fonts/Menlo.ttc"),
                        ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")) if os.path.exists(p)]
own = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ws, "fonts", "*")))
lib = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ws, "lib", "*.py")))
projects = []
for d in sorted(glob.glob(os.path.join(ws, "projects", "*"))):
    if os.path.isdir(d):
        outs = sorted(os.path.basename(f) for f in glob.glob(os.path.join(d, "out", "*.mp4")))
        projects.append(f"- `{os.path.basename(d)}`" + (": " + ", ".join(outs) if outs else " (no finished video yet)") + ("" if os.path.exists(os.path.join(d, "script.md")) else "  - no script.md yet"))
notes = "- (add anything installed by hand, account details that are safe to note, or preferences)\n"
if os.path.exists(path):
    old = open(path).read()
    if "## Notes" in old: notes = old.split("## Notes", 1)[1].lstrip("\n") or notes

L = [f"# joyboy system checklist", "",
     f"Updated {datetime.datetime.now():%Y-%m-%d %H:%M} by `setup.sh`. Read this first; it says what is ready so nothing is installed twice.", "",
     "## Ready to use", "",
     f"- {box(True)} Workspace: `{ws}`",
     f"- {box(True)} Python {sys.version.split()[0]}: `{sys.executable}`",
     f"- {box(ff)} ffmpeg" + (f" {ffv}" if ff else " - MISSING (ask the user before installing)")]
L += [f"- {box(v)} {n}" + (f" {v}" if v else " - MISSING") for n, v in pk]
L += ["", "## Voice-over", "",
      f"**In use now: {voice}.** Order of choice: ElevenLabs, then Piper, then the system voice.", "",
      f"- {box(eleven)} ElevenLabs API key (`ELEVENLABS_API_KEY`)" + ("" if eleven else " - not set"),
      f"- {box(piper)} Piper TTS" + (f" {piper}" if piper else " - not installed"),
      f"- {box(voices)} Piper voices in `voices/`: " + (", ".join(voices) if voices else "none"),
      f"- {box(say)} System voice (`say`), last resort",
      f"- {box(supertonic)} Supertonic (emotional voices F1-F5, M1-M5; tags <laugh> <sigh> <breath>)" + (f" {supertonic}" + ("" if st_model else "; its model downloads on first use") if supertonic else " - not installed (once: `.venv/bin/python -m pip install supertonic`, only when a video needs emotional voices)"),
      "", "## Package installer", "",
      f"- {box(bun)} bun" + (f" {bun}: used for installs; packages already downloaded on this machine are reused from its cache" if bun else " - not installed. npm is used instead. Suggest bun to the user once (see SKILL.md): installs become several times faster and reuse packages already on the machine."),
      f"- {box(npm_)} npm" + (f" {npm_}" if npm_ else " - not installed") + " (fallback)",
      "", "## Web animation (GSAP)", "",
      f"- {box(node)} node" + (f" {node}" if node else " - not installed"),
      f"- {box(gsap)} GSAP with all plugins" + (f" {gsap}" if gsap else " - not installed") + " in `web/node_modules/gsap/dist`",
      f"- {box(chrome)} Browser for capture" + (f": {chrome}" if chrome else " - no Chrome-family browser found"),
      f"- {box(node and gsap and chrome)} `film.web()` scenes ready",
      "", "## Icons", "",
      f"- {box(ricons)} react-icons" + (f" {ricons}" if ricons else " - not installed") + " (about 30 icon sets; search with `node web/icon.mjs search <word>`)",
      f"- {box(lucide)} lucide-static" + (f" {lucide}" if lucide else " - not installed") + " (stroke icons for animated icons in web scenes)",
      f"- {box(True)} Rendered icons cached in `icons/`: {nicons}",
      "", "## People (DiceBear)", "",
      f"- {box(npmver('@dicebear/collection'))} DiceBear" + (f" {npmver('@dicebear/collection')}" if npmver('@dicebear/collection') else " - not installed (cd web && npm install @dicebear/core @dicebear/collection)") + "; illustrated characters for `film.person()` / `film.talk()`, list styles with `node web/avatar.mjs styles`",
      f"- {box(True)} Characters cached in `avatars/`: {len(glob.glob(os.path.join(ws, 'avatars', '*')))}",
      "", "## Worlds (three.js)", "",
      f"- {box(npmver('three'))} three.js" + (f" {npmver('three')}" if npmver('three') else " - not installed (cd web && npm install three)") + "; procedural low-poly worlds with people for `film.world()`, drawn by `web/world.js`",
      f"- {box(os.path.exists(os.path.join(ws, 'lib', 'ambience.py')))} Ambience sounds synthesized in code (`lib/ambience.py`): fire, wind, rain, thunder, waves, stream, crickets, traffic, passing cars",
      "", "## 3D models (67.js)", "",
      f"- {box(npmver('67js'))} 67.js" + (f" {npmver('67js')}" if npmver('67js') else " - not installed (run setup.sh)") + "; real GLB model files as scenes with `film.model(glb)`",
      "", "## 3D (GSS)", "",
      f"- {box(gss)} gss-lang" + (f" {gss}" if gss else " - not installed (cd web && npm install gss-lang)") + "; use with `film.web(page, clock=\"virtual\")`, template `web/gss_template.html`",
      "", "## Maps", "",
      f"- {box(True)} OpenStreetMap data via public Nominatim and Overpass (needs internet; cached in `maps/`, {nmaps} files cached)",
      "", "## Fonts", "",
      "- System: " + (", ".join(fonts) if fonts else "none found"),
      "- In `fonts/` (brand fonts saved for reuse): " + (", ".join(own) if own else "none yet"),
      "", "## Toolkit", "",
      "- `lib/`: " + (", ".join(lib) if lib else "empty"),
      "- Charts (bars, columns, line, donut, heatmap) are built in; no chart library is needed",
      "- Not installed (add only if a video needs it): extra Piper voices, extra fonts",
      "", "## Projects", ""] + (projects or ["- none yet"]) + ["", "## Notes", "", notes.rstrip("\n"), ""]
open(path, "w").write("\n".join(L))
print("checklist:", path)
