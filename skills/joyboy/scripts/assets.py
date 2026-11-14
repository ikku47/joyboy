"""joyboy assets: a library of things made once and reused, each with the recipe that rebuilds it.

Character sheets, sprite sheets, 3D models, turntables, textures, logos, voices, music: anything made with Blender, a local
image model, Codex or by hand goes here with how it was made, so it can be found, reused in any video and rebuilt later.

    python assets.py add NAME --kind character-sheet --tool blender --file sheet.png --script job.py \\
           --cmd '{blender} -b --factory-startup -P {asset}/recipe/job.py -- mascot --out {asset}' --tag mascot
    python assets.py list [--kind K]        what exists, with a check mark when its files are still on disk
    python assets.py show NAME              the manifest
    python assets.py path NAME [--role R]   the main file (or the file with that role), for use in a script
    python assets.py rebuild NAME           run the saved recipe again (old files are kept in _prev/)
    python assets.py use NAME PROJECT       note that a video used it
    python assets.py index                  rewrite assets/INDEX.md (the checklist)

In a film script:  film.image(film.asset("joybot-sheet"))  or  film.sprite("joybot-sprites", ...)

Layout:  <workspace>/assets/<kind>/<name>/  asset.json, the files, recipe/ (the script that made it), _prev/ (older versions).
Command placeholders: {blender} {python} {ffmpeg} {asset} (the asset folder) {skill} (the lib folder). Nothing is ever deleted.
"""
import os, sys, json, glob, time, shutil, argparse, subprocess, datetime

WS = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy"))
ROOT = os.path.join(WS, "assets")
KINDS = ("character", "character-sheet", "sprite-sheet", "model3d", "turntable", "texture", "logo", "image", "voice", "music", "video", "other")

def _dir(kind, name): return os.path.join(ROOT, kind, name)
def _slug(n): return "".join(c if c.isalnum() or c in "-_" else "-" for c in n.strip()).strip("-").lower()

def find(name):
    """The manifest dict of an asset (with its folder in ['dir']), or None."""
    n = _slug(name)
    for f in glob.glob(os.path.join(ROOT, "*", n, "asset.json")):
        m = json.load(open(f)); m["dir"] = os.path.dirname(f); return m
    return None

def path(name, role="main"):
    """Absolute path of an asset's main file (or the file with `role`: preview, source, data, frames ...). Raises if it is missing."""
    m = find(name)
    if not m: raise FileNotFoundError("no asset named %r; see `python assets.py list`" % name)
    for fl in m["files"]:
        if fl.get("role") == role: return os.path.join(m["dir"], fl["path"])
    raise FileNotFoundError("asset %r has no file with role %r (it has: %s)" % (name, role, ", ".join(sorted({f.get('role', '') for f in m['files']}))))

def data(name):
    """The asset's `data` dict (for a sprite sheet: cols, rows, frames, fps, cell size; for a model: height, animations ...)."""
    m = find(name); return (m or {}).get("data", {})

def register(name, kind, files, tool="", script=None, command=None, params=None, tags=(), note="", info=None, tool_version=""):
    """Add or update an asset. files: paths, or (path, role) pairs (the first is the main file unless a role says otherwise).
    script: a file copied into recipe/ so the recipe survives changes to the skill. command: argv list or string with placeholders."""
    name = _slug(name)
    if kind not in KINDS: raise ValueError("kind must be one of: " + ", ".join(KINDS))
    d = _dir(kind, name); os.makedirs(os.path.join(d, "recipe"), exist_ok=True); old = find(name)
    if old and os.path.abspath(old["dir"]) != os.path.abspath(d): raise ValueError("asset %r already exists as kind %r" % (name, os.path.basename(os.path.dirname(old["dir"]))))
    fl = []
    for i, f in enumerate(files):
        src, role = (f if isinstance(f, (tuple, list)) else (f, "main" if i == 0 else "file"))
        src = os.path.abspath(src); dst = os.path.join(d, os.path.basename(src))
        if os.path.exists(dst) and os.path.abspath(dst) != src:               # keep the older version, never overwrite silently
            prev = os.path.join(d, "_prev", time.strftime("%Y%m%d-%H%M%S")); os.makedirs(prev, exist_ok=True); shutil.copy2(dst, prev)
        if os.path.abspath(dst) != src:
            if os.path.isdir(src): shutil.copytree(src, dst, dirs_exist_ok=True)
            else: shutil.copy2(src, dst)
        fl.append(dict(path=os.path.basename(src), role=role))
    rec = dict(script=None, command=command, params=params or {})
    if script:
        sd = os.path.join(d, "recipe", os.path.basename(script)); shutil.copy2(script, sd); rec["script"] = "recipe/" + os.path.basename(script)
    m = dict(name=name, kind=kind, tool=tool, tool_version=tool_version, created=(old or {}).get("created") or datetime.datetime.now().isoformat(timespec="seconds"),
             updated=datetime.datetime.now().isoformat(timespec="seconds"), files=fl, recipe=rec, tags=sorted(set(tags) | set((old or {}).get("tags", []))), note=note or (old or {}).get("note", ""),
             data=info or (old or {}).get("data", {}), used_in=(old or {}).get("used_in", []))
    json.dump(m, open(os.path.join(d, "asset.json"), "w"), indent=1); index(); return d

def all_assets():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "*", "*", "asset.json"))):
        m = json.load(open(f)); m["dir"] = os.path.dirname(f); out.append(m)
    return out

def ok(m): return all(os.path.exists(os.path.join(m["dir"], f["path"])) for f in m["files"])

def index():
    """Rewrite assets/INDEX.md: a checklist with how to use and rebuild each asset."""
    os.makedirs(ROOT, exist_ok=True); L = ["# joyboy asset library", "", f"Updated {datetime.datetime.now():%Y-%m-%d %H:%M}. [x] = files present. Use in a script with `film.asset(\"name\")`; rebuild with `python lib/assets.py rebuild NAME`.", ""]
    ms = all_assets()
    for k in KINDS:
        sel = [m for m in ms if m["kind"] == k]
        if not sel: continue
        L += [f"## {k}", ""]
        for m in sel:
            main = next((f["path"] for f in m["files"] if f.get("role") == "main"), m["files"][0]["path"] if m["files"] else "")
            L.append(f"- [{'x' if ok(m) else ' '}] `{m['name']}` ({m['tool'] or 'by hand'}) `assets/{k}/{m['name']}/{main}`" + (f" - {m['note']}" if m["note"] else "") + (f" [{', '.join(m['tags'])}]" if m["tags"] else "")
                     + ("; rebuildable" if m["recipe"].get("command") else "; no recipe saved") + (f"; used in {', '.join(m['used_in'])}" if m["used_in"] else ""))
        L.append("")
    if not ms: L += ["- nothing yet. Make a character, sprite sheet or 3D model with `blender_asset.py` and it is registered here.", ""]
    open(os.path.join(ROOT, "INDEX.md"), "w").write("\n".join(L)); return os.path.join(ROOT, "INDEX.md")

def _fill(arg, m):
    import toolscan
    rep = {"{asset}": m["dir"], "{python}": sys.executable, "{skill}": os.path.dirname(os.path.abspath(__file__)), "{blender}": toolscan.find("blender") or "blender", "{ffmpeg}": shutil.which("ffmpeg") or "ffmpeg"}
    for a, b in rep.items(): arg = arg.replace(a, b)
    return arg

def rebuild(name):
    """Run an asset's saved recipe again in its folder. Existing files are copied to _prev/ first. Returns the exit code."""
    m = find(name)
    if not m: raise FileNotFoundError(name)
    cmd = m["recipe"].get("command")
    if not cmd: raise RuntimeError("asset %r has no saved recipe command" % name)
    prev = os.path.join(m["dir"], "_prev", time.strftime("%Y%m%d-%H%M%S")); os.makedirs(prev, exist_ok=True)
    for f in m["files"]:
        p = os.path.join(m["dir"], f["path"])
        if os.path.isfile(p): shutil.copy2(p, prev)
    argv = [_fill(a, m) for a in cmd] if isinstance(cmd, list) else [_fill(a, m) for a in __import__("shlex").split(cmd)]
    print("rebuild:", " ".join(argv)); r = subprocess.run(argv, cwd=m["dir"]).returncode
    if r == 0 and not ok(m): print("warning: some files are still missing after the rebuild")
    index(); return r

def use(name, project):
    m = find(name)
    if not m: raise FileNotFoundError(name)
    if project not in m["used_in"]: m["used_in"].append(project)
    d = m.pop("dir"); json.dump(m, open(os.path.join(d, "asset.json"), "w"), indent=1); index()

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("name"); a.add_argument("--kind", required=True, choices=KINDS); a.add_argument("--tool", default=""); a.add_argument("--file", action="append", required=True, help="path, or path:role")
    a.add_argument("--script"); a.add_argument("--cmd"); a.add_argument("--param", action="append", default=[]); a.add_argument("--tag", action="append", default=[]); a.add_argument("--note", default="")
    l = sub.add_parser("list"); l.add_argument("--kind")
    for c in ("show", "rebuild"): sub.add_parser(c).add_argument("name")
    p = sub.add_parser("path"); p.add_argument("name"); p.add_argument("--role", default="main")
    u = sub.add_parser("use"); u.add_argument("name"); u.add_argument("project"); sub.add_parser("index")
    x = ap.parse_args()
    if x.cmd == "add":
        files = [tuple(f.rsplit(":", 1)) if ":" in f and not os.path.exists(f) else f for f in x.file]
        print(register(x.name, x.kind, files, x.tool, x.script, x.cmd and __import__("shlex").split(x.cmd), dict(p.split("=", 1) for p in x.param), x.tag, x.note))
    elif x.cmd == "list":
        for m in all_assets():
            if not x.kind or m["kind"] == x.kind: print("[%s] %-28s %-16s %-8s %s" % ("x" if ok(m) else " ", m["name"], m["kind"], m["tool"] or "-", "rebuildable" if m["recipe"].get("command") else ""))
    elif x.cmd == "show":
        m = find(x.name); print(json.dumps(m, indent=1) if m else "not found")
    elif x.cmd == "path": print(path(x.name, x.role))
    elif x.cmd == "rebuild": sys.exit(rebuild(x.name))
    elif x.cmd == "use": use(x.name, x.project)
    else: print(index())
