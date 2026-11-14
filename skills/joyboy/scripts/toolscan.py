"""joyboy toolscan: find every tool this machine offers for making video and assets, and write them down.

    python toolscan.py [workspace]        writes <workspace>/TOOLS.md (the checklist) and <workspace>/tools.json (the same, for scripts)
    python toolscan.py --find blender     prints the path of one tool, or nothing

What it looks at: command-line tools (on PATH and in the usual app folders: Blender.app, Codex, Godot, Unreal and so on),
installed apps, MCP servers configured for Claude Code and Codex, installed agent skills, local AI models (Hugging Face cache,
uv/pipx tools, Ollama, ComfyUI), which API keys are set (names only, never values) and the machine's hardware.
It only reads. It never installs, starts, signs in to or changes anything, and it never prints a secret.
Anything under '## Notes' in an existing TOOLS.md is kept.
"""
import os, sys, re, glob, json, shutil, subprocess, datetime, platform, plistlib

HOME = os.path.expanduser("~")
MAC = sys.platform == "darwin"
APPS = ["/Applications", os.path.join(HOME, "Applications")]

def run(cmd, timeout=8):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception: return ""

def app_path(name):
    for base in APPS:
        for n in ([name] if isinstance(name, str) else name):
            p = os.path.join(base, n + ".app")
            if os.path.exists(p): return p
    return None

def app_version(p):
    try:
        with open(os.path.join(p, "Contents", "Info.plist"), "rb") as f: d = plistlib.load(f)
        return str(d.get("CFBundleShortVersionString") or d.get("CFBundleVersion") or "")
    except Exception: return ""

# id, label, category, binary names on PATH, extra places (files or .app names), version arguments, what joyboy uses it for
TOOLS = [
    ("claude", "Claude Code", "Agents", ["claude"], [os.path.join(HOME, ".local/bin/claude")], ["--version"], "the agent running joyboy; sub-agents for parallel pieces"),
    ("codex", "Codex CLI", "Agents", ["codex"], [os.path.join(HOME, ".codex/bin/codex"), os.path.join(HOME, ".local/bin/codex"), "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex", "glob:/Applications/*.app/Contents/Resources/codex-cli/bin/codex", "app:Codex"], ["--version"], "a second agent: parallel scene pages, code review, image generation where it supports it (its outputs land in ~/.codex/generated_images)"),
    ("gemini", "Gemini CLI", "Agents", ["gemini"], [], ["--version"], "a second opinion or long-context reading"),
    ("blender", "Blender", "3D and art", ["blender"], ["app:Blender", "/opt/homebrew/bin/blender", "/usr/bin/blender", "/snap/bin/blender"], ["--version"], "3D characters and props, turntables, character sheets, sprite sheets, GLB models, renders with transparent background (see blender_asset.py)"),
    ("godot", "Godot", "3D and art", ["godot"], ["app:Godot", "app:Godot_mono"], ["--version"], "2D/3D scenes and game footage; sprite and tile work"),
    ("unreal", "Unreal Engine", "3D and art", [], ["glob:/Users/Shared/Epic Games/UE_*", "app:UnrealEditor"], [], "cinematics and virtual production shots"),
    ("unity", "Unity", "3D and art", ["unity"], ["app:Unity Hub", "glob:/Applications/Unity/Hub/Editor/*"], [], "real-time scenes and game footage"),
    ("krita", "Krita", "3D and art", ["krita"], ["app:krita", "app:Krita"], ["--version"], "painting and texture work"),
    ("gimp", "GIMP", "3D and art", ["gimp"], ["app:GIMP"], ["--version"], "image editing"),
    ("inkscape", "Inkscape", "3D and art", ["inkscape"], ["app:Inkscape"], ["--version"], "SVG logos and vector art"),
    ("aseprite", "Aseprite", "3D and art", ["aseprite"], ["app:Aseprite"], ["--version"], "pixel art and sprite animation"),
    ("figma", "Figma", "3D and art", [], ["app:Figma"], [], "design files (read through its MCP when connected)"),
    ("ffmpeg", "ffmpeg", "Media", ["ffmpeg"], [], ["-version"], "the encoder every video goes through"),
    ("ffprobe", "ffprobe", "Media", ["ffprobe"], [], ["-version"], "checking a finished video"),
    ("magick", "ImageMagick", "Media", ["magick", "convert"], [], ["--version"], "batch image conversion, sprite sheet assembly"),
    ("gifski", "gifski", "Media", ["gifski"], [], ["--version"], "small sharp GIF previews"),
    ("yt-dlp", "yt-dlp", "Media", ["yt-dlp"], [], ["--version"], "saving a reference video the user is allowed to use (ask first; never for re-posting other people's work)"),
    ("sox", "SoX", "Media", ["sox"], [], ["--version"], "audio conversion and editing"),
    ("exiftool", "ExifTool", "Media", ["exiftool"], [], ["-ver"], "reading media metadata"),
    ("handbrake", "HandBrake", "Media", ["HandBrakeCLI"], ["app:HandBrake"], ["--version"], "re-encoding for size limits"),
    ("davinci", "DaVinci Resolve", "Media", [], ["app:DaVinci Resolve"], [], "colour and finishing when a project needs a person's edit"),
    ("whisper", "Whisper (speech to text)", "Speech", ["whisper", "whisper-cli", "whisper-cpp", "mlx_whisper"], [], ["--help"], "transcripts, lyrics timing, captions from a voice or song"),
    ("piper", "Piper TTS", "Speech", ["piper"], [os.path.join(HOME, "joyboy/.venv/bin/piper")], ["--help"], "local narration"),
    ("say", "System voice (say)", "Speech", ["say"], [], [], "last-resort narration on macOS"),
    ("node", "Node.js", "Dev", ["node"], [], ["--version"], "web, icon, character and 3D scenes"),
    ("bun", "bun", "Dev", ["bun"], [os.path.join(HOME, ".bun/bin/bun")], ["--version"], "fast installs that reuse the shared package cache"),
    ("deno", "Deno", "Dev", ["deno"], [], ["--version"], "alternative script runtime"),
    ("python3", "Python 3", "Dev", ["python3"], [], ["--version"], "the renderer and every script"),
    ("uv", "uv", "Dev", ["uv"], [], ["--version"], "Python tools and environments"),
    ("pipx", "pipx", "Dev", ["pipx"], [], ["--version"], "Python command-line tools"),
    ("cargo", "Rust (cargo)", "Dev", ["cargo"], [os.path.join(HOME, ".cargo/bin/cargo")], ["--version"], "building native tools"),
    ("swift", "Swift", "Dev", ["swift"], [], ["--version"], "native Mac tools"),
    ("xcode", "Xcode", "Dev", ["xcodebuild"], ["app:Xcode"], ["-version"], "iOS simulator footage for app demos"),
    ("git", "git", "Dev", ["git"], [], ["--version"], "keeping every video's script and versions"),
    ("gh", "GitHub CLI", "Dev", ["gh"], [], ["--version"], "reading repos, pull requests"),
    ("docker", "Docker", "Dev", ["docker"], ["app:Docker"], ["--version"], "running services that have no Mac build"),
    ("chrome", "Chrome-family browser", "Dev", ["google-chrome", "chromium"], ["app:Google Chrome", "app:Chromium", "app:Brave Browser", "app:Microsoft Edge"], [], "capturing web pages and GSAP scenes headless; the built-in browser pane for research"),
    ("agent-reach", "Agent Reach", "Research", ["agent-reach"], [os.path.join(HOME, ".local/bin/agent-reach")], ["--help"], "reading YouTube, Instagram, X, Reddit, Bilibili and the web; search and subtitles (read-only; the user logs in)"),
    ("ollama", "Ollama", "Local AI", ["ollama"], ["app:Ollama"], ["--version"], "local language models for drafting and summarising"),
    ("mflux", "mflux (FLUX on Apple silicon)", "Local AI", ["mflux-generate"], [os.path.join(HOME, ".local/bin/mflux-generate")], ["--help"], "local image generation: stills, character frames, backgrounds, stop-motion frames"),
    ("comfyui", "ComfyUI", "Local AI", [], ["app:ComfyUI", "dir:" + os.path.join(HOME, "ComfyUI"), "dir:" + os.path.join(HOME, "Documents/ComfyUI")], [], "node-based image and video generation"),
    ("lmstudio", "LM Studio", "Local AI", ["lms"], ["app:LM Studio"], [], "local language models"),
]

# what a video usually needs, and the tools to prefer for it, best first (the first one found is the pick)
NEEDS = [
    ("3D character, prop or model made once and reused", ["blender"], "blender_asset.py: `mascot`, `model`, `sheet`, `turntable`, `sprites`; the recipe is saved so it can be rebuilt"),
    ("Character sheet or sprite sheet", ["blender", "mflux", "aseprite", "magick"], "Blender renders exact views and frames; mflux for painted looks; magick or Pillow to assemble"),
    ("Still images, backgrounds, concept art", ["mflux", "comfyui", "codex"], "local models first; never cloud services unless the user asks"),
    ("Video clips generated by a model", ["comfyui"], "only when the user asks; code-rendered scenes are the default"),
    ("Research: trends, a profile, reading a link", ["agent-reach"], "also the ig-viral skill; read-only; the user logs in to any site themselves"),
    ("Transcribe a voice, a song or footage", ["whisper"], "captions and lyric timing; without it, the user supplies the words"),
    ("Narration", ["piper", "say"], "joyboy picks ElevenLabs, Supertonic, Piper or the system voice by itself"),
    ("Music", ["ffmpeg"], "generated by joyboy's own genres; a local music model if the user has one (see Local AI models below)"),
    ("A second agent working in parallel", ["codex", "gemini", "claude"], "hand it one self-contained piece with the exact file and the result you need"),
    ("GIF preview or share clip", ["gifski", "ffmpeg"], "ffmpeg is always enough"),
    ("Pixel art and sprite animation", ["aseprite", "blender", "magick"], "Blender can render a pixelated look; film(fx='pixel') covers the whole film"),
    ("Game footage or real-time 3D", ["godot", "unreal", "unity"], "capture a short run and use it as `clip` footage"),
    ("Phone app footage", ["xcode"], "the iOS simulator tools: screen recordings for `phone` scenes"),
]

KEYS = ["ELEVENLABS_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "REPLICATE_API_TOKEN", "FAL_KEY", "STABILITY_API_KEY", "GROQ_API_KEY", "SCENARIO_API_KEY", "HF_TOKEN"]

def locate(spec):
    """(path, version) for one tool spec, or (None, "")."""
    _id, label, cat, bins, extra, vargs, use = spec
    path = None
    for b in bins:
        p = shutil.which(b)
        if p: path = p; break
    app = None
    for e in extra:
        if path: break
        if e.startswith("app:"):
            a = app_path(e[4:])
            if a: app = a; break
        elif e.startswith("glob:"):
            g = sorted(glob.glob(e[5:]))
            if g: path = g[-1]
        elif e.startswith("dir:"):
            if os.path.isdir(e[4:]): path = e[4:]
        elif os.path.exists(e): path = e
    if not path and app:
        inner = {"Blender": "Contents/MacOS/Blender", "Godot": "Contents/MacOS/Godot", "Xcode": None}.get(os.path.basename(app)[:-4], None)
        path = os.path.join(app, inner) if inner and os.path.exists(os.path.join(app, inner)) else app
    if not path: return None, ""
    ver = ""
    if vargs and os.path.isfile(path) and os.access(path, os.X_OK):
        out = run([path] + vargs)
        m = re.search(r"(\d+\.\d+(?:\.\d+)?(?:[-+.\w]*)?)", out.split("\n")[0] if out else "")
        ver = m.group(1) if m else ""
    if not ver and app: ver = app_version(app)
    if not ver and path.endswith(".app"): ver = app_version(path)
    return path, ver

def mcp_servers():
    out = []
    try:
        d = json.load(open(os.path.join(HOME, ".claude.json")))
        for n, v in (d.get("mcpServers") or {}).items(): out.append(("Claude Code", n, str(v.get("command") or v.get("url") or v.get("type") or "")))
        for proj, pv in (d.get("projects") or {}).items():
            for n, v in (pv.get("mcpServers") or {}).items(): out.append(("Claude Code (project %s)" % os.path.basename(proj), n, str(v.get("command") or v.get("url") or "")))
    except Exception: pass
    try:
        import tomllib
        d = tomllib.load(open(os.path.join(HOME, ".codex/config.toml"), "rb"))
        for n, v in (d.get("mcp_servers") or {}).items(): out.append(("Codex", n, str(v.get("command") or v.get("url") or "")))
    except Exception: pass
    return out

def skills():
    seen, out = set(), []
    for label, base in (("Claude Code", os.path.join(HOME, ".claude/skills")), ("Codex", os.path.join(HOME, ".codex/skills")), ("Agents", os.path.join(HOME, ".agents/skills"))):
        for d in sorted(glob.glob(os.path.join(base, "*"))):
            f = os.path.join(d, "SKILL.md")
            if not os.path.isfile(f): continue
            name = os.path.basename(d)
            try:
                t = open(f, errors="ignore").read(2500); m = re.search(r"^description:\s*(.*?)(?:\n[a-z-]+:|\n---)", t, re.S | re.M)
                desc = " ".join((m.group(1) if m else "").replace(">-", "").replace(">", "").split())[:130]
            except Exception: desc = ""
            key = os.path.realpath(d)
            if key in seen: continue
            seen.add(key); out.append((label, name, desc, os.path.islink(d)))
    return out

def local_models():
    out = []
    hf = os.environ.get("HF_HOME") or os.path.join(HOME, ".cache/huggingface")
    for d in sorted(glob.glob(os.path.join(hf, "hub", "models--*"))):
        n = os.path.basename(d)[8:].replace("--", "/"); sz = 0
        for r, _, fs in os.walk(os.path.join(d, "blobs")):
            for f in fs:
                try: sz += os.path.getsize(os.path.join(r, f))
                except OSError: pass
        out.append(("Hugging Face cache", n, sz))
    if shutil.which("ollama"):
        for ln in run(["ollama", "list"]).split("\n")[1:]:
            if ln.strip(): out.append(("Ollama", ln.split()[0], 0))
    for lab, base in (("LM Studio", os.path.join(HOME, ".lmstudio/models")), ("ComfyUI", os.path.join(HOME, "ComfyUI/models/checkpoints"))):
        for d in sorted(glob.glob(os.path.join(base, "*"))): out.append((lab, os.path.basename(d), 0))
    for t in (run(["uv", "tool", "list"]).split("\n") if shutil.which("uv") else []):
        m = re.match(r"^([A-Za-z0-9_.-]+) v?([\d.]+)", t)
        if m: out.append(("uv tool", m.group(1) + " " + m.group(2), 0))
    ai_local = os.path.join(HOME, "ai-local")
    if os.path.isdir(ai_local):
        for d in sorted(os.listdir(ai_local)):
            if not d.startswith("."): out.append(("~/ai-local", d, 0))
    return out

def hardware(ws):
    chip = run(["sysctl", "-n", "machdep.cpu.brand_string"]) if MAC else platform.processor()
    mem = run(["sysctl", "-n", "hw.memsize"]) if MAC else ""
    gb = round(int(mem) / 2 ** 30) if mem.isdigit() else None
    try: free = round(shutil.disk_usage(ws if os.path.isdir(ws) else HOME).free / 2 ** 30)
    except Exception: free = None
    return dict(os=platform.platform(terse=True), chip=chip or platform.machine(), ram_gb=gb, cores=os.cpu_count(), disk_free_gb=free)

def scan(ws):
    tools = {}
    for spec in TOOLS:
        p, v = locate(spec); tools[spec[0]] = dict(label=spec[1], category=spec[2], present=bool(p), path=p, version=v, use=spec[6])
    # Python-package tools that live in the workspace environment
    py = os.path.join(ws, ".venv/bin/python")
    for pid, label, mod, use in (("supertonic", "Supertonic voices", "supertonic", "emotional narration (F1-F5, M1-M5)"), ("piper-tts", "Piper (python)", "piper", "local narration")):
        ok = os.path.exists(py) and subprocess.run([py, "-c", "from importlib.metadata import version; version('%s')" % pid], capture_output=True).returncode == 0
        tools[pid] = dict(label=label, category="Speech", present=ok, path=py if ok else None, version="", use=use)
    needs = []
    for need, cands, how in NEEDS:
        pick = next((c for c in cands if tools.get(c, {}).get("present")), None); needs.append(dict(need=need, pick=pick, candidates=cands, how=how))
    return dict(updated=datetime.datetime.now().isoformat(timespec="minutes"), hardware=hardware(ws), tools=tools, mcp=[dict(host=h, name=n, command=c) for h, n, c in mcp_servers()],
                skills=[dict(host=h, name=n, description=d, linked=l) for h, n, d, l in skills()], models=[dict(source=s, name=n, bytes=b) for s, n, b in local_models()],
                keys={k: bool(os.environ.get(k)) for k in KEYS}, needs=needs)

def write(ws):
    ws = os.path.abspath(ws); os.makedirs(ws, exist_ok=True); path = os.path.join(ws, "TOOLS.md"); data = scan(ws); box = lambda ok: "[x]" if ok else "[ ]"
    notes = "- (anything the scan cannot see: tools on another machine, accounts, preferences)\n"
    if os.path.exists(path):
        old = open(path).read()
        if "## Notes" in old: notes = old.split("## Notes", 1)[1].lstrip("\n") or notes
    hw = data["hardware"]; L = ["# joyboy tools checklist", "",
         f"Updated {datetime.datetime.now():%Y-%m-%d %H:%M} by `toolscan.py`. Read this with SYSTEM.md before any video: it says which tools, apps, MCP servers, skills and local models exist on this machine, so use them for what they are good at and install nothing twice. Read-only scan; nothing was installed or started.", "",
         f"**Machine:** {hw['os']}, {hw['chip']}" + (f", {hw['ram_gb']} GB memory" if hw["ram_gb"] else "") + f", {hw['cores']} cores" + (f", {hw['disk_free_gb']} GB free disk" if hw["disk_free_gb"] is not None else ""), ""]
    L += ["## Pick a tool for the need", "", "| Need | Use | How |", "|---|---|---|"]
    for n in data["needs"]:
        L.append(f"| {n['need']} | " + (f"**{data['tools'][n['pick']]['label']}**" if n["pick"] else "joyboy's own scenes (no extra tool found: " + ", ".join(n["candidates"]) + ")") + f" | {n['how']} |")
    cats = []
    for t in data["tools"].values():
        if t["category"] not in cats: cats.append(t["category"])
    for c in cats:
        L += ["", f"## {c}", ""]
        for tid, t in data["tools"].items():
            if t["category"] != c: continue
            L.append(f"- {box(t['present'])} {t['label']}" + (f" {t['version']}" if t["version"] else "") + (f": `{t['path']}`" if t["present"] and t["path"] else " - not found") + f"; {t['use']}")
    L += ["", "## MCP servers (live tools the agent can call)", ""] + ([f"- {box(True)} `{m['name']}` for {m['host']}" + (f" ({m['command']})" if m["command"] else "") for m in data["mcp"]] or ["- none configured"])
    if any(m["name"].lower().startswith("blender") for m in data["mcp"]): L.append("- Blender MCP is configured: with Blender open and its add-on connected, scenes can be built and inspected live; use `blender_asset.py` for repeatable headless jobs.")
    L += ["", "## Agent skills installed", ""]
    for s in data["skills"]: L.append(f"- {box(True)} `{s['name']}` ({s['host']}{', linked' if s['linked'] else ''})" + (f": {s['description']}" if s["description"] else ""))
    if not data["skills"]: L.append("- none found")
    L += ["", "## Local AI models and tools", ""]
    gb = lambda b: f" ({b / 2 ** 30:.1f} GB)" if b > 2 ** 27 else ""
    L += [f"- {box(True)} {m['source']}: `{m['name']}`{gb(m['bytes'])}" for m in data["models"]] or ["- none found"]
    L += ["", "## API keys set (names only)", ""] + [f"- {box(v)} `{k}`" for k, v in data["keys"].items()]
    L += ["", "## Rules for using these", "",
          "- Prefer what is already here. Ask before installing, downloading a model, signing in or spending money.",
          "- Local first: do not send the user's files or brand material to a cloud service unless they ask.",
          "- Large models (above) can freeze a laptop when run in parallel: one heavy job at a time.",
          "- Anything made with an outside tool (Blender, mflux, a model) goes in the asset library with its recipe: `python lib/assets.py add ...` (see SKILL.md, \"Asset library\").",
          "", "## Notes", "", notes.rstrip("\n"), ""]
    open(path, "w").write("\n".join(L)); json.dump(data, open(os.path.join(ws, "tools.json"), "w"), indent=1)
    return path, data

def find(tool_id, ws=None):
    """Path of one tool from the last scan (or a live probe), else None."""
    ws = ws or os.environ.get("JOYBOY_HOME", os.path.join(HOME, "joyboy"))
    try:
        t = json.load(open(os.path.join(ws, "tools.json")))["tools"].get(tool_id)
        if t and t["present"] and t["path"] and os.path.exists(t["path"]): return t["path"]
    except Exception: pass
    for spec in TOOLS:
        if spec[0] == tool_id: return locate(spec)[0]
    return None

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--find"]:
        p = find(a[1]); print(p or "", end="\n" if p else ""); sys.exit(0 if p else 1)
    ws = a[0] if a else os.environ.get("JOYBOY_HOME", os.path.join(HOME, "joyboy")); p, d = write(ws)
    print("tools:", p, "(%d of %d tools present, %d MCP servers, %d skills, %d local models)" % (sum(t["present"] for t in d["tools"].values()), len(d["tools"]), len(d["mcp"]), len(d["skills"]), len(d["models"])))
