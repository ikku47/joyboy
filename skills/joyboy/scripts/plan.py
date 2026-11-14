"""joyboy plan: the gate between a request and a script. The script is written LAST.

    python plan.py new NAME [--reference VIDEO]   makes projects/NAME/ with plan.md (and scans the reference if one is given)
    python plan.py check [plan.md]                 which sections are still unfilled (exit 1 if anything blocks writing the script)
    python plan.py status [plan.md]                the same, one line per section

plan.md has the sections below. Fill them in order. Every `TODO` must be replaced by real content before the script (section 7) is written, and film.py is
only started after that. A render prints the plan's status, so a script written before the plan was complete is visible.
"""
import os, sys, re, shutil, subprocess, datetime
WS = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy"))
HERE = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
    ("1", "Brief", True, "What it is for, where it runs, what we have (logo, photos, reference), the words, the language, how long, the sound, what to avoid. From the user, one question at a time."),
    ("2", "Research", True, "What is working now for this idea. Formulas (hook shapes, structures, lengths), the evidence (accounts, links, numbers like likes against followers), what to copy (formula only) and what to avoid. Source: ig-viral (+ Agent Reach, or the browser), or the public web."),
    ("3", "Reference analysis", None, "ONLY if the user gave a reference video or picture. Output of refscan.py plus your own description of each shot (what is drawn, the words, type, motion, sound). What must match exactly and what may differ."),
    ("4", "Toolkit match", True, "One row per beat of the planned video: what the beat needs -> what exists (scene, theme, genre, asset, tool) found with `catalog.py find`, or MAKE. No row may say 'close enough'. For a 3D film add the camera plan: each shot and its angle (at least 4 different: establishing, a low or high one, a close one, a moving one)."),
    ("5", "What to make", True, "Every beat marked MAKE: what it is, how it will be built (a new scene with scaffold.py, a Blender asset, a theme, an effect), and how it will be checked. Write 'nothing, everything exists' only if section 4 has no MAKE rows. Every 3D model: the QA result (blender_asset.py qa: PASS) and the coverage sheet you looked at (blender_asset.py coverage)."),
    ("6", "Variety", True, "Output of `variety.py --suggest` and the check against recent videos; which of theme, genre, grade, scene mix, hook formula, layout and colour differ from the last videos and why."),
    ("7", "Script", True, "WRITTEN LAST, from sections 1-6. First the treatment (references/directing.md): three candidate structures and the one chosen, logline and arc, benchmark (learn / do not take), a shot list with a reason for each shot, a cue map, a sound-design table (ambience, foley material, music state per section), the one native move, and the two planned silences. Then the words, the order, the timing and the scene list with its options (use ig-reel for hooks and the beat sheet, ig-human on the text). Render three style frames first to prove the look."),
    ("8", "Fidelity checklist", None, "ONLY with a reference: the measurable targets (length, cut times, tempo, colours) and the result of `refscan.py check` (aim for 85 or more), plus what you checked by eye."),
    ("9", "Delivery", True, "Final files, the caption (ig-caption, then ig-human), what could not be verified, one next step."),
]

TEMPLATE = """# {name}: plan

Made {date}. Fill the sections in order. Replace every TODO. The script (section 7) is written last.

""" + "\n".join("## %s. %s\n\n%s\n\nTODO\n" % (n, t, "*" + d + "*" + ("" if req else "")) for n, t, req, d in SECTIONS)

def parse(path):
    txt = open(path).read(); out = {}
    for m in re.finditer(r"^## (\d)\. (.+?)\n(.*?)(?=^## \d\. |\Z)", txt, re.S | re.M):
        body = re.sub(r"^\*.*?\*\s*$", "", m.group(3), flags=re.S | re.M).strip(); out[m.group(1)] = body
    return out, txt

def status(path="plan.md"):
    if not os.path.exists(path): return dict(problems=["no plan.md"], sections={}, ok=False)
    s, txt = parse(path); ref = os.path.isdir("reference") or "REFERENCE: yes" in txt; rows = {}; problems = []
    for n, title, req, _ in SECTIONS:
        body = s.get(n, ""); done = bool(body) and "TODO" not in body and len(body) > 25
        needed = req or (req is None and ref)
        if n in ("3", "8") and not ref and "TODO" in body: done = True      # not applicable without a reference
        rows[n] = dict(title=title, done=done, needed=bool(needed) or done)
    first = [n for n in "123456" if rows[n]["needed"] and not rows[n]["done"]]
    if first: problems.append("sections not done before the script: " + ", ".join("%s %s" % (n, rows[n]["title"]) for n in first))
    if rows["7"]["done"] and first: problems.append("the script (7) was written before the plan was complete")
    if ref and rows["8"]["needed"] and not rows["8"]["done"] and rows["7"]["done"]: problems.append("a reference was given: section 8 (fidelity) is not filled")
    return dict(problems=problems, sections=rows, ok=not problems)

def new(name, reference=None):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"); d = os.path.join(WS, "projects", slug); os.makedirs(os.path.join(d, "assets"), exist_ok=True); os.makedirs(os.path.join(d, "out"), exist_ok=True)
    p = os.path.join(d, "plan.md")
    if not os.path.exists(p): open(p, "w").write(TEMPLATE.format(name=name, date=datetime.date.today().isoformat()))
    if reference:
        r = subprocess.run([sys.executable, os.path.join(HERE, "refscan.py"), "scan", reference, "--out", os.path.join(d, "reference", "ref")], capture_output=True, text=True); print(r.stdout.strip() or r.stderr.strip())
        txt = open(p).read(); open(p, "w").write(txt.replace("# %s: plan\n" % name, "# %s: plan\n\nREFERENCE: yes (%s), scanned into reference/ref/\n" % (name, os.path.basename(reference)), 1))
    return d

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["new"]:
        ref = a[a.index("--reference") + 1] if "--reference" in a else None; name = a[1]; d = new(name, ref); print("project:", d); print("plan:   ", os.path.join(d, "plan.md"))
        print("NEXT: 1 brief (ask the user), 2 research (ig-viral, Agent Reach), 3 reference (look at reference/ref/contact.jpg), 4 toolkit match (catalog.py find), 5 make what is missing, 6 variety, THEN 7 the script.")
    else:
        path = a[1] if len(a) > 1 else "plan.md"; st = status(path)
        if a[:1] == ["status"] or True:
            for n, r in st["sections"].items(): print("[%s] %s. %s%s" % ("x" if r["done"] else (" " if r["needed"] else "-"), n, r["title"], "" if r["needed"] else " (not needed)"))
        print("OK: the plan is complete" if st["ok"] else "BLOCKED: " + "; ".join(st["problems"])); sys.exit(0 if st["ok"] else 1)
