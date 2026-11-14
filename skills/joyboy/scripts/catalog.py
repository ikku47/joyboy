"""joyboy catalog: everything the toolkit can do, in one searchable list, so a video is built from what exists (or from something new, on purpose).

    python catalog.py build [workspace]        writes <workspace>/CATALOG.md and catalog.json (setup.sh runs this)
    python catalog.py find "word per beat hook typography" [--n 8]      the best matches across scenes, themes, genres, looks, grades, fx, sounds, assets
    python catalog.py show kinetic             the full entry for one item (signature and docstring)

The catalog is read from the code itself (scene methods, themes, genres, grades ...), so it can never go out of date. `find` is the
"toolkit match" step of the workflow: for each beat of the planned video, search for it. A strong match: use it. A weak or no match:
that beat is a GAP, and the workflow says to make the missing piece (see references/workflow.md, "Make what is missing").
"""
import os, sys, re, json, inspect, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WS = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy"))

# plain-word tags that help search find things by what they are for (the docstrings give the rest)
SUITS = {
    "scene:intro": "opening hook name logo start", "scene:outro": "closing call to action end contact", "scene:title": "headline hook chapter",
    "scene:image": "photo picture still camera move caption slideshow", "scene:clip": "footage video cut highlight", "scene:web": "gsap animation svg typography 3d web page",
    "scene:words": "kinetic type words fast colour fields", "scene:bullets": "list steps features agenda explainer", "scene:stat": "number counter percent offer result",
    "scene:bars": "chart data compare", "scene:columns": "chart data", "scene:line": "chart trend growth data", "scene:donut": "chart share data", "scene:heatmap": "chart table activity",
    "scene:icons": "features services benefits grid", "scene:map": "location address directions find us", "scene:quote": "testimonial quote lyrics poem", "scene:phone": "app demo screenshot website mobile",
    "scene:browser": "website tour desktop page scroll", "scene:crt": "retro terminal typing hacker boot", "scene:logo": "logo reveal sting mark", "scene:end": "closing card",
    "scene:window": "logo reel images", "scene:slices": "reel strips", "scene:carousel": "cards reel apps", "scene:grid": "logo wall reel", "scene:tunnel": "logo reel hype", "scene:loader": "loading glitch reel",
    "scene:lockcut": "fast cut logo locked reel", "scene:talk": "character talking presenter dialogue", "scene:custom": "anything else one-off custom shot",
    "scene:kinetic": "hook manifesto typography one word per beat motion blur viral reel text", "scene:highlight": "caption sentence marker box key word emphasis talking point",
    "scene:stages": "stages of relatable skit emotion steps escalation creator", "scene:timeline": "timestamps day in the life appointment schedule history", "scene:countdown": "top 5 ranking list listicle numbers",
    "scene:versus": "comparison us vs them before after split screen", "scene:product": "product hero ad studio shot callouts cutout ecommerce", "scene:chat": "text message imessage story skit conversation dm",
    "scene:satisfying": "loop asmr hypnotic calming wordless background pendulum", "scene:stick": "stickman stick figure faceless story explainer", "scene:anatomy": "structure breakdown sections how a video is built",
    "scene:before_after": "transformation slider wipe compare photos", "scene:wire": "wireframe 3d technical drawing blueprint built from prompt ai dev", "scene:cta": "comment keyword lead magnet send link call to action dm",
    "scene:skit": "comedy two characters dialogue mascot client ai joke bokeh speaker caption", "scene:laptop": "pov laptop screen reflection work sample portfolio client paid",
    "scene:notes": "apple notes ad checklist typing plain note", "scene:review": "social proof testimonials stars rating reviews live badge", "scene:wrapped": "year in review recap stats story cards spotify",
    "scene:lyrics": "lyric video karaoke song words", "scene:changelog": "release notes version update what's new software", "scene:sprite": "sprite sheet character turntable blender asset animation walk",
    "theme:flat": "kinetic type hooks listicles creator reels bright colour fields", "theme:studio": "products apps ads saas premium clean white", "theme:blueprint": "dev tools how it works architecture specs tech grid",
    "theme:brutal": "startups creators offers loud shout", "theme:aurora": "ai wellness finance premium launch glow", "theme:paper": "stories quotes books editorial memories serif calm", "theme:neon": "music gaming nightlife synthwave hype night",
    "theme:retro": "food fun community nostalgia pop halftone",
    "look:cinematic": "trailers drama launches", "look:soft": "stories calm brands explainers", "look:clean": "apps products data screenshots ui", "look:punchy": "reels offers sport energetic", "look:warm": "food home festivals nostalgia",
    "look:cool": "tech night rain winter", "look:vintage": "memories retro", "look:none": "exact colours brand",
    "grade:teal_orange": "cinema action trailer", "grade:noir": "black and white drama", "grade:bleach": "gritty war documentary", "grade:sunset": "warm romance travel", "grade:mint": "fresh clean health", "grade:cross": "fashion edgy",
    "grade:pastel": "soft cute kids", "grade:night": "dark moody night",
    "fx:vhs": "retro glitch tape nostalgia", "fx:pixel": "game pixel retro 8-bit", "fx:riso": "risograph print two inks dots", "fx:halftone": "newspaper pop art dots print", "fx:dither": "one-bit photocopy dither", "fx:engrave": "engraving woodcut hatching", "fx:bands": "silkscreen poster flat bands", "fx:duotone": "two colour gig poster", "fx:thermal": "heat camera sensor", "fx:xray": "scanner x-ray", "fx:ascii": "terminal glyphs text art", "fx:film": "silent film newsreel flicker scratches", "fx:cel": "anime cartoon cel outlines", "fx:tiltshift": "miniature model blur",
    "scene:write": "handwriting chalk marker pencil writes itself chalkboard whiteboard", "scene:sketch": "draw on lines then colour sketch pen illustration", "scene:stamp": "rubber stamp approved slam verdict",
}

def build():
    import quick, kinds, themes, genres
    from quick import Film, LOOKS, MOVES, TRANSITIONS, SCENE_NAMES
    items = []
    def add(kind, name, line, extra=""):
        key = f"{kind}:{name}"; items.append(dict(kind=kind, name=name, line=line, tags=SUITS.get(key, ""), extra=extra))
    for n in SCENE_NAMES:
        fn = getattr(Film, n); doc = " ".join((fn.__doc__ or "").split()); first = re.split(r"(?<=[.!?])\s", doc, maxsplit=1)[0] if doc else ""
        try: sig = str(inspect.signature(fn)).replace("(self, ", "(").replace("(self)", "()")
        except Exception: sig = "(...)"
        add("scene", n, first or n, sig + " | " + doc)
    for n, t in themes.THEMES.items(): add("theme", n, t["desc"], "palette " + " ".join(t["pal"]))
    for n, g in genres.GENRES.items(): add("genre", n, g["desc"], "bpm %s; layers %s" % (g["bpm"], ", ".join(g["layers"])))
    for n in LOOKS: add("look", n, "picture finish: " + n)
    for n in kinds.GRADES: add("grade", n, "colour grade: " + n.replace("_", " "))
    for n in kinds.FX: add("fx", n, "whole-film treatment: " + n)
    for n in MOVES: add("move", n, "camera move on a still: " + n)
    for n in TRANSITIONS: add("transition", n, "transition into a scene: " + n)
    import score
    for n in ("thud", "pop", "tick", "ding", "blip", "rise", "scribble", "sweep", "shimmer", "whoosh", "click"): add("sound", n, "sound effect matched to on-screen action: " + n)
    import styles
    for n, s in styles.STYLES.items(): add("style", n, s["desc"], " ".join((s["family"], s["scenes"], s["moves"])))
    for n in ("idle", "walk", "hop"): add("mascot", n, "Blender mascot animation: " + n)
    try:
        import assets
        for m in assets.all_assets(): add("asset", m["name"], "%s made with %s %s" % (m["kind"], m["tool"] or "hand", m["note"]), " ".join(m["tags"]))
    except Exception: pass
    return items

def write(ws=None):
    ws = os.path.abspath(ws or WS); items = build(); os.makedirs(ws, exist_ok=True); L = ["# joyboy catalog", "", f"Built {datetime.datetime.now():%Y-%m-%d %H:%M} from the code itself. Search it: `python lib/catalog.py find \"<what the beat needs>\"`. If nothing fits a beat, that is a gap: make the missing piece (references/workflow.md).", ""]
    for k, title in (("scene", "Scenes (film.<name>)"), ("theme", "Themes (Film(theme=...))"), ("genre", "Music genres (Film(genre=...))"), ("style", "Styles (Film(style=...))"), ("look", "Looks (Film(look=...))"), ("grade", "Grades (Film(grade=...))"), ("fx", "Treatments (Film(fx=...))"),
                     ("move", "Camera moves (image(move=...))"), ("transition", "Transitions (tr=...)"), ("sound", "Sound effects (sfx=[...])"), ("mascot", "Blender mascot animations"), ("asset", "Saved assets (film.asset(name))")):
        sel = [i for i in items if i["kind"] == k]
        if not sel: continue
        L += [f"## {title}", ""] + [f"- `{i['name']}`: {i['line']}" + (f" [{i['tags']}]" if i["tags"] and k in ("theme", "grade", "fx", "look") else "") for i in sel] + [""]
    open(os.path.join(ws, "CATALOG.md"), "w").write("\n".join(L)); json.dump(items, open(os.path.join(ws, "catalog.json"), "w"), indent=1); return len(items)

def find(query, n=8):
    items = build(); toks = [t for t in re.findall(r"[a-z0-9']+", query.lower()) if len(t) > 2]; out = []
    for i in items:
        hay = (i["name"] + " " + i["line"] + " " + i["tags"] + " " + i["extra"]).lower(); name = i["name"].lower().replace("_", " ")
        sc = sum((3 if t in name else 0) + (2 if t in i["tags"].lower() else 0) + (1 if t in hay else 0) for t in toks)
        if sc: out.append((sc, i))
    out.sort(key=lambda x: -x[0]); return out[:n], toks

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "build": n = write(a[1] if len(a) > 1 else None); print("catalog:", os.path.join(WS if len(a) < 2 else a[1], "CATALOG.md"), "(%d entries)" % n)
    elif a[0] == "find":
        nn = 8
        if "--n" in a: k = a.index("--n"); nn = int(a[k + 1]); a = a[:k] + a[k + 2:]
        res, toks = find(" ".join(a[1:]), nn)
        if not res: print("NO MATCH for: %s\n-> this is a GAP: make it (references/workflow.md, 'Make what is missing')" % " ".join(a[1:]))
        for sc, i in res: print("%3d  %-10s %-16s %s" % (sc, i["kind"], i["name"], i["line"][:100]))
        if res and res[0][0] < 4: print("\nweak match (best score %d): check it really fits; if it does not, this beat is a GAP." % res[0][0])
    elif a[0] == "show":
        for i in build():
            if i["name"] == a[1]: print(f"{i['kind']}: {i['name']}\n{i['line']}\n\n{i['extra']}")
    else: print(__doc__)
