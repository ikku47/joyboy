"""joyboy imagegen: still images from a signed-in Codex CLI or a local model, written the way a consistent set of pictures needs.

    python imagegen.py check                               is the Codex CLI installed and signed in? (read-only)
    python imagegen.py prompt STYLE "subject" [--aspect 9:16]   print the full prompt for a style (no generation)
    python imagegen.py make STYLE "subject" --out DIR --name NAME [--aspect 9:16] [--ref IMG ...] --yes     generate one image

Sending a prompt to Codex sends it, and any reference picture, to an outside service. So `make` does nothing without --yes, and the workflow says to ask the user first;
a local model (mflux, listed in TOOLS.md) needs no permission and can use the same `prompt` text.

The prompt is built the way a set of images stays consistent:
  1. the aspect ratio first, then the subject, then ONE shared style suffix (from the style's family), then hard constraints repeated every time (no text, no logos, no people unless asked);
  2. references first: make the character sheet and the hero prop once, then make every other picture as an edit of them (--ref), never from scratch;
  3. the same words for the same thing in every prompt; change one thing per picture;
  4. the result is checked: size, aspect ratio, and that it is not a copy of the reference. A wrong aspect is kept with a suffix and reported.
Register what you make in the asset library with the exact prompt and references (assets.py add ... --note), so it can be remade.
"""
import os, sys, re, glob, time, shutil, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
CODEX = shutil.which("codex") or "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
FAMILY = {
    "print": "a printed illustration: flat ink colours, visible halftone dots or hatching, paper grain, slight misregistration of the colour plates",
    "hand": "a hand-made drawing on paper or board: visible strokes, grain from the tool, imperfect lines, nothing digital-clean",
    "screen": "seen through an instrument: a screen or sensor image with its own palette, scan lines or noise, interface detail drawn flat",
    "technical": "a technical drawing: precise line work on a plain ground, labels as short marks, orderly and flat, no shading tricks",
    "film": "a film still: one clear light source, a limited colour grade, grain, a calm composition with the subject large in frame",
    "layout": "a designed layout: clean shapes, one accent colour, generous space, soft studio light",
}
CONSTRAINTS = "No text, no letters, no numbers, no logos, no watermarks, no brand marks, no real people or faces unless the subject says so."

def prompt_for(style, subject, aspect="9:16"):
    import styles
    s = styles.get(style); return "%s image. %s. Style: %s; %s. %s" % (aspect, subject.rstrip("."), s["desc"], FAMILY.get(s["family"], ""), CONSTRAINTS)

def check():
    if not os.path.exists(CODEX): print("Codex CLI not found (see TOOLS.md)"); return 4
    r = subprocess.run([CODEX, "login", "status"], capture_output=True, text=True, timeout=30); msg = (r.stdout + r.stderr).strip().split("\n")[0]
    print("codex:", CODEX); print("status:", msg or "unknown"); return 0 if r.returncode == 0 and "not" not in msg.lower() else 4

def make(style, subject, out, name, aspect, refs, retries=1, timeout=480):
    from PIL import Image
    prompt = prompt_for(style, subject, aspect); home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex")); gdir = os.path.join(home, "generated_images"); os.makedirs(out, exist_ok=True)
    before = set(glob.glob(os.path.join(gdir, "**", "*.*"), recursive=True))
    cmd = [CODEX, "exec", "--skip-git-repo-check", "-s", "read-only"] + sum((["-i", os.path.abspath(r)] for r in refs), []) + ["-"]
    instruction = "Use the image generation tool exactly once to make the image described below, then stop. Do nothing else.\n\n" + prompt
    for attempt in range(retries + 1):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True); p.stdin.write(instruction); p.stdin.close(); t0 = time.time(); new = []
        while time.time() - t0 < timeout:
            new = [f for f in glob.glob(os.path.join(gdir, "**", "*.*"), recursive=True) if f not in before and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
            if new or p.poll() is not None: break
            time.sleep(2)
        if p.poll() is None: p.terminate()
        if new: break
    if not new: sys.exit("joyboy: no image was produced (is Codex signed in with image generation? try `imagegen.py check`)")
    src = max(new, key=os.path.getmtime); im = Image.open(src); w, h = im.size; dst = os.path.join(out, "%s_%s.png" % (name, time.strftime("%Y%m%d-%H%M%S"))); im.convert("RGB").save(dst)
    aw, ah = (int(x) for x in aspect.split(":")); bad = abs(w / h - aw / ah) / (aw / ah) > 0.05
    if bad: os.rename(dst, dst.replace(".png", "_wrongaspect.png")); dst = dst.replace(".png", "_wrongaspect.png")
    if os.path.getsize(dst) < 8000: sys.exit("joyboy: the image is too small to be real; nothing kept")
    for r in refs:
        if os.path.getsize(r) == os.path.getsize(dst): sys.exit("joyboy: the result looks like a copy of a reference; nothing kept")
    print(dst, "%dx%d" % (w, h), "(wrong aspect: kept with a suffix)" if bad else ""); return dst

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True); sub.add_parser("check")
    p1 = sub.add_parser("prompt"); p1.add_argument("style"); p1.add_argument("subject"); p1.add_argument("--aspect", default="9:16")
    p2 = sub.add_parser("make"); p2.add_argument("style"); p2.add_argument("subject"); p2.add_argument("--out", required=True); p2.add_argument("--name", required=True); p2.add_argument("--aspect", default="9:16"); p2.add_argument("--ref", action="append", default=[]); p2.add_argument("--yes", action="store_true")
    x = ap.parse_args()
    if x.cmd == "check": sys.exit(check())
    if x.cmd == "prompt": print(prompt_for(x.style, x.subject, x.aspect))
    else:
        if not x.yes: sys.exit("joyboy: this sends the prompt (and any reference pictures) to an outside service. Ask the user, then run again with --yes.")
        make(x.style, x.subject, x.out, x.name, x.aspect, x.ref)
