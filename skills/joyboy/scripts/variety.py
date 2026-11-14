"""joyboy variety: keep every video different from the ones before it.

Each finished render records a fingerprint (theme, genre, grade, fx, look, mood, tempo, palette, the order of scene types, the opening and closing scene,
the hook words) in <workspace>/history.json. Before a render, and when planning, compare the plan with what was made lately:

    python variety.py                 the last videos and what they used
    python variety.py --suggest       what has NOT been used lately: themes, genres, grades, scene types
    python variety.py check FILE.json a fingerprint (or the one printed by a render) against history

Film.render() runs the check by itself and prints `variety:` lines. The rules (each a warning, not a block; override when the brand demands it):
  - the same theme as one of the last 3 videos, the same genre as one of the last 2
  - the same opening scene type as the last 3, or scene-type overlap above 60% with any of the last 5
  - a colour palette that is nearly the same as one of the last 3
A series for one brand may keep its palette and logo; it should still change at least two of theme, genre and the main scene type each time.
"""
import os, sys, json, datetime
import numpy as np

WS = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); PATH = os.path.join(WS, "history.json")

def load():
    try: return json.load(open(PATH))
    except Exception: return []

def fingerprint(film):
    kinds = [sc["kind"] for sc in film.scenes]; pal = ["#%02x%02x%02x" % tuple(int(c) for c in np.float32(p)[::-1]) for p in film.pal[:4]]
    first = next((sc.get("call", (sc["kind"],))[1] for sc in film.scenes[:1] if len(sc.get("call", ())) > 1), ())
    hook = " ".join(str(x) for x in first if isinstance(x, str))[:80] if first else ""
    return dict(name=film.name, date=datetime.datetime.now().isoformat(timespec="minutes"), theme=(film.theme or {}).get("name"), genre=film.genre or "classic" if film.mood != "none" else None,
                grade=film.grade if isinstance(film.grade, (str, type(None))) else "custom", fx=film.fx if isinstance(film.fx, (str, type(None))) else "custom", look=film.look_name, mood=film.mood,
                bpm=round(film.fps * 60 / film.beat), palette=pal, kinds=kinds, opening=kinds[0] if kinds else None, closing=kinds[-1] if kinds else None, size="%dx%d" % (film.W, film.H), seconds=round(film.total / film.fps, 1), hook=hook)

def _lab(h): import cv2; return cv2.cvtColor(np.uint8([[[int(h[5:7], 16), int(h[3:5], 16), int(h[1:3], 16)]]]), cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)

def check(fp, hist=None):
    """Warnings (a list of strings) comparing a fingerprint with the recent history."""
    h = [x for x in (hist if hist is not None else load()) if x.get("name") != fp["name"]]; w = []
    if not h: return w
    if fp["theme"] and fp["theme"] in [x.get("theme") for x in h[-3:]]: w.append("theme '%s' was used in one of the last 3 videos" % fp["theme"])
    if fp["genre"] and fp["genre"] in [x.get("genre") for x in h[-2:]]: w.append("music genre '%s' was used in one of the last 2 videos" % fp["genre"])
    first = [sc for sc in fp["kinds"][:2] if sc not in ("intro", "title")][:1]          # the opener itself is always an intro; compare what comes right after it
    prev = [[k for k in x.get("kinds", [])[:2] if k not in ("intro", "title")][:1] for x in h[-3:]]
    if first and len(h) >= 3 and all(p_ == first for p_ in prev): w.append("the first real scene type '%s' opened the last 3 videos" % first[0])
    ks = set(fp["kinds"]) - {"intro", "outro", "end", "title"}
    for x in h[-5:]:
        o = set(x.get("kinds", [])) - {"intro", "outro", "end", "title"}
        if ks and o and len(ks & o) / len(ks | o) > 0.6: w.append("scene types overlap %d%% with '%s'" % (100 * len(ks & o) / len(ks | o), x["name"])); break
    for x in h[-3:]:
        try:
            d = np.mean([np.linalg.norm(_lab(a) - _lab(b)) for a, b in zip(fp["palette"][:3], x["palette"][:3])])
            if d < 14: w.append("palette is nearly the same as '%s'" % x["name"]); break
        except Exception: pass
    return w

def record(fp):
    h = [x for x in load() if x.get("name") != fp["name"]]; h.append(fp); os.makedirs(WS, exist_ok=True); json.dump(h[-60:], open(PATH, "w"), indent=1)

def suggest(n=8):
    import themes, genres, kinds
    h = load()[-n:]; used = lambda k: {x.get(k) for x in h}; out = {}
    out["themes not used lately"] = [t for t in themes.THEMES if t not in used("theme")]
    out["genres not used lately"] = [g for g in genres.GENRES if g not in used("genre")]
    out["grades not used lately"] = [g for g in kinds.GRADES if g not in used("grade")]
    seen = {k for x in h for k in x.get("kinds", [])}; out["scene types not used lately"] = [k for k in kinds.NAMES if k not in seen]
    return out

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); a = sys.argv[1:]
    if a[:1] == ["--suggest"]:
        for k, v in suggest().items(): print("%-30s %s" % (k, ", ".join(v) or "(all used)"))
    elif a[:1] == ["check"]:
        fp = json.load(open(a[1])); w = check(fp); print("\n".join("variety: " + x for x in w) or "variety: ok, different from the recent videos")
    else:
        for x in load()[-10:]: print("%-28s %-9s %-10s grade %-11s fx %-6s %3d bpm  %s" % (x["name"], x.get("theme") or "-", x.get("genre") or "-", x.get("grade") or "-", x.get("fx") or "-", x.get("bpm", 0), " ".join(dict.fromkeys(x.get("kinds", [])))[:60]))
        if not load(): print("no videos recorded yet")
