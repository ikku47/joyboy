"""joyboy blender_asset: make characters, character sheets, sprite sheets, turntables and 3D models with Blender, and keep them.

    python blender_asset.py mascot NAME [--color "#f58a3a"] [--anim idle|walk|hop] [--frames 12] [--size 256]
        builds the toy mascot in Blender and registers three assets:  NAME (3D model: .glb + .blend),
        NAME-sheet (character sheet: front, three-quarter, side, back) and NAME-sprites (sprite sheet of the animation)
    python blender_asset.py sheet MODEL NAME [--views 4]          character sheet of any model (.glb .fbx .obj .stl .blend)
    python blender_asset.py turntable MODEL NAME [--frames 36]    a turn-around: sprite sheet + a short mp4
    python blender_asset.py sprites MODEL NAME [--anim ACTION] [--frames 12]    sprite sheet from a model's animation
    python blender_asset.py qa MODEL                              check a model: watertight, normals, scale, UVs, materials, size (exit 1 on FAIL)
    python blender_asset.py coverage MODEL NAME                   nine camera angles and lenses of a model on one sheet, plus the check

Every asset is registered in the asset library (assets.py) with the exact command that rebuilds it, so:
    python assets.py rebuild NAME-sheet
In a film script:  film.image(film.asset("NAME-sheet"))   film.sprite("NAME-sprites", fps=12)   film.model(film.asset("NAME"))

Needs Blender (found by toolscan.py: PATH, /Applications/Blender.app, Homebrew) and Pillow. Headless; nothing opens on screen.
Renders are one heavy job: run them one at a time.
"""
import os, sys, json, math, shutil, argparse, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import toolscan, assets
from PIL import Image, ImageDraw, ImageFont

WS = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy"))

def blender():
    p = toolscan.find("blender")
    if not p: sys.exit("joyboy: Blender was not found. Install it from blender.org (ask the user first), or set it up in /Applications, then run toolscan.py again.")
    return p

def run_blender(out, argv):
    job = os.path.join(HERE, "blender_job.py"); cmd = [blender(), "-b", "--factory-startup", "-P", job, "--"] + argv + ["--out", out]
    print("blender:", " ".join(os.path.basename(c) if c == job else c for c in cmd)); r = subprocess.run(cmd, capture_output=True, text=True)
    if "JOB DONE" not in r.stdout:
        sys.stderr.write((r.stdout[-1800:] + "\n" + r.stderr[-1800:]).strip() + "\n"); sys.exit("joyboy: the Blender job failed (output above)")
    return r

COVERAGE_NAMES = ["front", "three-quarter left", "three-quarter right", "side", "back", "top down", "low hero", "high wide", "close detail"]

def read_qa(d):
    p = os.path.join(d, "qa.json")
    return json.load(open(p)) if os.path.exists(p) else None

def print_qa(q, title="model check"):
    """Print the quality check as a table and return the number of FAILs."""
    fails = sum(1 for c in q["checks"] if c[1] == "FAIL"); warns = sum(1 for c in q["checks"] if c[1] == "WARN")
    print("%s: %d objects, %d faces (%d triangles), %.2f units" % (title, q["objects"], q["faces"], q["tris"], q["size"]))
    for n, lvl, d in q["checks"]: print("  %-4s  %-46s %s" % (lvl, n, "" if lvl == "PASS" else d))
    print("  => %s" % ("FAIL: fix the model before it is used in a video" if fails else ("PASS with %d warning(s)" % warns if warns else "PASS")))
    return fails

def font(size):
    for p in ("/System/Library/Fonts/Avenir Next.ttc", "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def charsheet(views, out_png, out_jpg, labels, bg="#f6f6f3"):
    ims = [Image.open(v).convert("RGBA") for v in views]; w, h = ims[0].size; pad = int(w * 0.08); lab = int(h * 0.16)
    sheet = Image.new("RGBA", (len(ims) * w + (len(ims) + 1) * pad, h + lab + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(sheet); f = font(max(14, int(h * 0.06)))
    for i, (im, lb) in enumerate(zip(ims, labels)):
        x = pad + i * (w + pad); sheet.alpha_composite(im, (x, pad)); tw = d.textlength(lb, font=f); d.text((x + (w - tw) / 2, pad + h + lab * 0.25), lb.upper(), font=f, fill=(40, 40, 50, 255))
    sheet.save(out_png); flat = Image.new("RGB", sheet.size, bg); flat.paste(sheet, mask=sheet.split()[3]); flat.save(out_jpg, quality=92)
    return sheet.size

def spritesheet(frames, out_png, cols=None):
    ims = [Image.open(f).convert("RGBA") for f in frames]; w, h = ims[0].size; n = len(ims); cols = cols or min(n, 6); rows = math.ceil(n / cols)
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    for i, im in enumerate(ims): sheet.alpha_composite(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out_png); return dict(cols=cols, rows=rows, frames=n, cell_w=w, cell_h=h)

def preview_mp4(frames_dir, out_mp4, fps=24, bg="#f6f6f3"):
    ff = shutil.which("ffmpeg")
    if not ff: return False
    r = subprocess.run([ff, "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "frame_%03d.png"), "-f", "lavfi", "-i", "color=c=%s:s=512x512" % bg.replace("#", "0x"),
                        "-filter_complex", "[1:v][0:v]scale2ref=w=iw:h=ih[b][f];[b][f]overlay=shortest=1,format=yuv420p", "-c:v", "libx264", "-crf", "20", out_mp4], capture_output=True)
    return r.returncode == 0 and os.path.exists(out_mp4)

def cmd_for(argv): return ["{python}", "{skill}/blender_asset.py"] + argv

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mascot"); m.add_argument("name"); m.add_argument("--color", default="#f58a3a"); m.add_argument("--anim", default="idle", choices=("idle", "walk", "hop")); m.add_argument("--frames", type=int, default=12); m.add_argument("--size", type=int, default=256); m.add_argument("--tag", action="append", default=[])
    qp = sub.add_parser("qa", help="check a model for problems (open edges, flipped normals, scale, UVs, materials, size)"); qp.add_argument("model")
    cp = sub.add_parser("coverage", help="render nine different camera angles of a model and check it"); cp.add_argument("model"); cp.add_argument("name"); cp.add_argument("--size", type=int, default=384); cp.add_argument("--tag", action="append", default=[])
    for c in ("sheet", "turntable", "sprites"):
        s = sub.add_parser(c); s.add_argument("model"); s.add_argument("name"); s.add_argument("--views", type=int, default=4); s.add_argument("--frames", type=int, default=36 if c == "turntable" else 12); s.add_argument("--size", type=int, default=512 if c == "sheet" else 256); s.add_argument("--anim", default=""); s.add_argument("--tag", action="append", default=[])
    x = ap.parse_args(); name = assets._slug(getattr(x, "name", "model")); tmp = tempfile.mkdtemp(prefix="jb-blender-"); labels = ["Front", "Three-quarter", "Side", "Back", "Left", "Rear-quarter"]; ver = ""
    try: ver = subprocess.run([blender(), "--version"], capture_output=True, text=True, timeout=20).stdout.split("\n")[0].replace("Blender ", "")
    except Exception: pass
    job = os.path.join(HERE, "blender_job.py")
    if x.cmd == "qa":
        model = os.path.abspath(x.model); run_blender(tmp, ["qa", "--model", model]); q = read_qa(tmp); fails = print_qa(q, os.path.basename(model)); shutil.rmtree(tmp, ignore_errors=True); sys.exit(1 if fails else 0)
    if x.cmd == "coverage":
        model = os.path.abspath(x.model)
        if not os.path.exists(model): sys.exit("joyboy: model file not found: " + model)
        run_blender(tmp, ["coverage", "--model", model, "--size", str(x.size)]); q = read_qa(tmp); fails = print_qa(q, name + " model check"); views = sorted(os.path.join(tmp, "views", f) for f in os.listdir(os.path.join(tmp, "views")))
        png, jpg = os.path.join(tmp, name + "-coverage.png"), os.path.join(tmp, name + "-coverage.jpg"); ims = [Image.open(v).convert("RGBA") for v in views]; w, h = ims[0].size; cols = 3; rows = math.ceil(len(ims) / cols); pad = int(w * 0.05); lab = int(h * 0.12)
        sheet = Image.new("RGBA", (cols * w + (cols + 1) * pad, rows * (h + lab) + (rows + 1) * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(sheet); f = font(max(14, int(h * 0.05)))
        for i, (im, lb) in enumerate(zip(ims, COVERAGE_NAMES)):
            xx, yy = pad + (i % cols) * (w + pad), pad + (i // cols) * (h + lab + pad); sheet.alpha_composite(im, (xx, yy)); d.text((xx + w / 2 - d.textlength(lb.upper(), font=f) / 2, yy + h + lab * 0.2), lb.upper(), font=f, fill=(40, 40, 50, 255))
        sheet.save(png); flat = Image.new("RGB", sheet.size, "#f6f6f3"); flat.paste(sheet, mask=sheet.split()[3]); flat.save(jpg, quality=92)
        assets.register(name + "-coverage", "character-sheet", [(png, "main"), (jpg, "preview")], "blender", job, cmd_for(["coverage", model, x.name, "--size", str(x.size)]), dict(model=model), ["blender", "coverage"] + x.tag, "nine camera angles and lenses for review and shot planning", dict(views=len(views), qa=dict(faces=q["faces"], tris=q["tris"], checks={c[0]: c[1] for c in q["checks"]})), ver)
        print("registered: %s-coverage (look at it: pick the angles the film will use)" % name); shutil.rmtree(tmp, ignore_errors=True); sys.exit(1 if fails else 0)
    if x.cmd == "mascot":
        run_blender(tmp, ["mascot", "--name", name, "--color", x.color, "--anim", x.anim, "--frames", str(x.frames), "--size", str(x.size), "--render", "sheet"])
        run_blender(tmp + "/s", ["mascot", "--name", name, "--color", x.color, "--anim", x.anim, "--frames", str(x.frames), "--size", str(x.size), "--render", "sprites"])
        q = read_qa(tmp)
        if q and print_qa(q, name + " model check"): sys.exit("joyboy: the mascot failed its model check; nothing was registered")
        views = sorted(os.path.join(tmp, "views", f) for f in os.listdir(os.path.join(tmp, "views"))); fr = sorted(os.path.join(tmp + "/s", "frames", f) for f in os.listdir(os.path.join(tmp + "/s", "frames")))
        sheet_png, sheet_jpg, sp_png = os.path.join(tmp, name + "-sheet.png"), os.path.join(tmp, name + "-sheet.jpg"), os.path.join(tmp, name + "-sprites.png")
        charsheet(views, sheet_png, sheet_jpg, labels[:len(views)]); info = spritesheet(fr, sp_png); info["fps"] = 12; info["animation"] = x.anim
        base = ["mascot", x.name, "--color", x.color, "--anim", x.anim, "--frames", str(x.frames), "--size", str(x.size)]
        tags = ["mascot", "character", "blender"] + x.tag
        assets.register(name, "model3d", [(os.path.join(tmp, name + ".glb"), "main"), (os.path.join(tmp, name + ".blend"), "source")], "blender", job, cmd_for(base), dict(color=x.color, anim=x.anim), tags, "toy mascot, rounded cube with eyes and legs", dict(animation=x.anim, frames=x.frames, qa=dict(faces=q["faces"], tris=q["tris"], checks={c[0]: c[1] for c in q["checks"]}) if q else {}), ver)
        assets.register(name + "-sheet", "character-sheet", [(sheet_png, "main"), (sheet_jpg, "preview")], "blender", job, cmd_for(base), dict(color=x.color), tags, "front, three-quarter, side and back", dict(views=len(views)), ver)
        assets.register(name + "-sprites", "sprite-sheet", [(sp_png, "main")], "blender", job, cmd_for(base), dict(color=x.color, anim=x.anim), tags, "transparent sprite sheet, " + x.anim, info, ver)
        print("registered: %s, %s-sheet, %s-sprites  (see %s)" % (name, name, name, os.path.join(assets.ROOT, "INDEX.md")))
    else:
        model = os.path.abspath(x.model)
        if not os.path.exists(model): sys.exit("joyboy: model file not found: " + model)
        base = [x.cmd, model, x.name]
        if x.cmd == "sheet":
            run_blender(tmp, ["render", "--model", model, "--render", "sheet", "--views", str(x.views), "--size", str(x.size)]); views = sorted(os.path.join(tmp, "views", f) for f in os.listdir(os.path.join(tmp, "views")))
            png, jpg = os.path.join(tmp, name + "-sheet.png"), os.path.join(tmp, name + "-sheet.jpg"); charsheet(views, png, jpg, labels[:len(views)])
            assets.register(name, "character-sheet", [(png, "main"), (jpg, "preview")], "blender", job, cmd_for(base + ["--views", str(x.views), "--size", str(x.size)]), dict(model=model), ["blender"] + x.tag, "character sheet of " + os.path.basename(model), dict(views=len(views)), ver)
        else:
            mode = "turntable" if x.cmd == "turntable" else "sprites"
            args = ["render", "--model", model, "--render", mode, "--frames", str(x.frames), "--size", str(x.size)] + (["--anim", x.anim] if x.anim else [])
            run_blender(tmp, args); fr = sorted(os.path.join(tmp, "frames", f) for f in os.listdir(os.path.join(tmp, "frames"))); png = os.path.join(tmp, name + ".png"); info = spritesheet(fr, png, 6 if mode == "turntable" else None); info["fps"] = 24 if mode == "turntable" else 12
            files = [(png, "main")]
            if mode == "turntable" and preview_mp4(os.path.join(tmp, "frames"), os.path.join(tmp, name + ".mp4")): files.append((os.path.join(tmp, name + ".mp4"), "video"))
            assets.register(name, "turntable" if mode == "turntable" else "sprite-sheet", files, "blender", job, cmd_for(base + ["--frames", str(x.frames), "--size", str(x.size)] + (["--anim", x.anim] if x.anim else [])), dict(model=model, anim=x.anim), ["blender"] + x.tag, "%s of %s" % (mode, os.path.basename(model)), info, ver)
        print("registered:", name)
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__": main()
