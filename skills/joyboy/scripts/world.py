"""joyboy world: story scenes in a procedural low-poly 3D world (three.js, drawn by web/world.js).

    w = film.world(place="forest", time="night", weather="snow", seed=11, props=["campfire", "tent"],
                   people=[(asha, "sit", {"scarf": "#e3b23c"}), (ravi, "sit")])        # people come from film.person()
    w.shot("crane", dur=4)                               # one camera shot = one scene
    w.shot("close:ravi", say=(ravi, "I remember your ringtone."), tr="cut")
    w.still("two", "work/two.png")                       # one frame, to check a shot before rendering

Places: forest, street, village (a Kerala village road), meadow, beach, snowfield. Times: day, dusk, dawn, night. Weather: clear, snow, rain, storm, fog.
Props: campfire, lamp, tent, bench, logs. Cameras: wide, full, two, close:<name>, over:<name>, fallen:<name>, orbit, crane, low, top, prop.
Movement: w.shot(..., walk=True) and w.shot(..., fall=(person, seconds)).
The same seed always builds the same world, so every shot matches. Ambience (ambience.py) is added by itself."""
import os, sys, json, base64, hashlib, subprocess, math
import numpy as np
HOME = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); KIT = os.path.join(HOME, "web")
HAIR = {"bun": "bun", "shortCurly": "curly", "curly": "curly", "fro": "curly", "froBand": "curly", "dreads": "curly", "bob": "long", "longButNotTooLong": "long", "straight01": "long", "straight02": "long", "straightAndStrand": "long", "curvy": "long", "miaWallace": "long", "bigHair": "long", "hat": "beanie", "winterHat1": "beanie", "winterHat02": "beanie", "winterHat03": "beanie", "winterHat04": "beanie"}
PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;width:100vw;height:100vh;overflow:hidden;background:#000}canvas{display:block;width:100vw;height:100vh}
.t{position:fixed;left:6vw;right:6vw;text-align:center;color:#fff;opacity:0;font-family:"Malayalam Sangam MN","Noto Sans Malayalam","Kohinoor Devanagari","Noto Sans Devanagari","Tamil Sangam MN","Noto Sans","Nirmala UI",sans-serif;text-shadow:0 .35vmin 1.4vmin rgba(0,0,0,.9),0 0 .5vmin rgba(0,0,0,.95)}
#shade{position:fixed;left:0;right:0;bottom:0;height:46vh;background:linear-gradient(transparent,rgba(0,0,0,.6));opacity:0}
#cap{font-weight:700;font-size:5.4vmin;line-height:1.4} #ttl b{display:block;font-weight:800;font-size:15vmin;line-height:1.2} #ttl span{display:block;font-weight:500;font-size:5vmin;line-height:1.5;margin-top:2.5vmin}
@media (orientation:portrait){#cap{bottom:22vh} #ttl{top:20vh}} @media (orientation:landscape){#cap{bottom:9vh} #ttl{top:16vh}}</style></head>
<body><canvas id="c"></canvas><div id="shade"></div><div id="ttl" class="t"><b></b><span></span></div><div id="cap" class="t"></div><script type="module">
import { build } from "file://%s/world.js";
const spec = %s, ov = spec.overlay || {};
const c = document.getElementById("c"); c.width = innerWidth; c.height = innerHeight;
const cap = document.getElementById("cap"), ttl = document.getElementById("ttl"), shade = document.getElementById("shade"), cl = v => Math.min(1, Math.max(0, v)), dur = spec.shot.dur;
cap.textContent = ov.caption || ""; ttl.querySelector("b").textContent = ov.title || ""; ttl.querySelector("span").textContent = ov.sub || "";
const over = t => { const a = ov.caption ? cl((t - (ov.at || 0)) / 0.3) * cl((dur - t) / 0.3) : 0, b = ov.title ? cl((t - 0.5) / 0.7) * cl((dur - 0.25 - t) / 0.5) : 0; cap.style.opacity = a; shade.style.opacity = Math.max(a, b * 0.6); ttl.style.opacity = b; ttl.style.transform = "translateY(" + (1 - b) * 2 + "vmin)"; };
try { const w = await build(spec, c); document.fonts.ready.then(() => { over(0); window.joyboy = { seek: t => { w.seek(t); over(t); } }; }); } catch (e) { console.error("world: " + e.message + " " + e.stack); }
</script></body></html>"""

class World:
    def __init__(self, film, place="forest", time="day", weather="clear", seed=1, props=(), people=(), extras=None):
        """people = [(person from film.person(), "sit" | "stand", {extra: scarf, hat, pants, umbrella ...}), ...]"""
        self.film, self.t0 = film, 0.0; self.shots = []; self.events = []; self.dist = 0.0; self.down = set(); self.level = 1.6; self.music = 0.45;   # ambience loudness, and how much of the music stays under the world's shots
        film.sound_layer(self._ambience); self.base = dict(place=place, time=time, weather=weather, seed=seed, props=list(props), fps=film.fps, people=[])
        if extras is not None: self.base["extras"] = extras
        for it in people:
            p, pose, extra = it[0], it[1] if len(it) > 1 else "stand", (it[2] if len(it) > 2 else {}); o = p.get("options") or {}
            d = os.path.join(HOME, "avatars", "face3d-" + hashlib.md5((p["name"] + p["dir"]).encode()).hexdigest()[:10])
            if not all(os.path.exists(os.path.join(d, f"{p['name']}__{m}__{e}.png")) for m in p["mouths"] for e in p["eyes"]):
                opts = {k: v for k, v in o.items() if k in ("eyebrows",)}; opts["backgroundColor"] = ["transparent"]
                r = subprocess.run(["node", os.path.join(KIT, "avatar.mjs"), "render", d, p["name"], p["style"] + "Neutral", p.get("seed") or p["name"], json.dumps(opts), ",".join(p["mouths"]), ",".join(p["eyes"]), "384"], cwd=KIT, capture_output=True, text=True)
                if r.returncode: sys.exit("world: " + r.stderr.strip())
            faces = {f"{m}|{e}": "data:image/png;base64," + base64.b64encode(open(os.path.join(d, f"{p['name']}__{m}__{e}.png"), "rb").read()).decode() for m in p["mouths"] for e in p["eyes"]}
            first = lambda k, dflt: "#" + o[k][0] if o.get(k) else dflt
            self.base["people"].append({**dict(id=p["name"], pose=pose, skin=first("skinColor", "#d08b5b"), hair=first("hairColor", "#2c1b18"), shirt=first("clothesColor", "#c2410c"),
                                               hairStyle=HAIR.get((o.get("top") or ["short"])[0], "short"), mouths=list(p["mouths"]), eyes=list(p["eyes"]), faces=faces), **extra})
    def page(self, cam, dur, speak=None, extra=None):
        spec = dict(self.base, shot=dict(cam=cam, dur=dur), t0=round(self.t0, 3), dist0=round(self.dist, 3))
        spec["people"] = [dict(p, state="down") if p["id"] in self.down else p for p in self.base["people"]]
        if speak: spec["speak"] = speak
        spec.update(extra or {})
        src = PAGE % (KIT, json.dumps(spec, ensure_ascii=False)); d = os.path.join(self.film.work, "world"); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, hashlib.md5(src.encode()).hexdigest()[:12] + ".html")
        if not os.path.exists(p): open(p, "w", encoding="utf-8").write(src)
        return p
    def still(self, cam, out, t=1.0, size=None, **extra):
        """One frame of a shot, to check it before rendering. Extra spec values can be passed (walk=1.1, fall={"id": ..., "at": 1.0})."""
        w, h = size or (self.film.W, self.film.H); subprocess.run(["node", os.path.join(KIT, "world_still.mjs"), os.path.abspath(self.page(cam, 4.0, extra=extra or None)), os.path.abspath(out), str(w), str(h), str(t)], cwd=KIT, check=True)
    def shot(self, cam="wide", dur=3.0, say=None, text=None, at=0.5, walk=None, fall=None, title=None, sub=None, role=None, **k):
        """One camera shot of the world as a scene.
        say=(person, "line")   that person speaks it (lip sync, caption).
        walk=True or a speed   everyone walks toward the camera (the place slides past); distance carries on from shot to shot.
        fall=(person, seconds or "end") that person slips and falls on their back at that moment of the shot, with a splash; they
                               stay on the ground in later shots (film them with cam="fallen:<name>"), and walking stops.
        title=, sub=           big words over the picture (an opening or closing shot); role="intro" or "outro" marks the
                               shot as the film's opening or closing card.
        Captions and titles are drawn by the browser, so every script (Malayalam, Hindi, Arabic ...) is shaped correctly."""
        film = self.film; speak = None; fps = film.fps; extra = {}
        if say:
            person, line = say; old = film.voice_name; film.voice_name = person["voice"] or old; pace = k.get("pace") or film.pace
            try: vf = film._say(line, float(pace)); env = film._envelope(vf[0]) if vf else np.zeros(1)
            finally: film.voice_name = old
            dur = max(dur, (vf[1] if vf else 0) + at + 0.5); speak = dict(id=person["name"], at=at, env=[round(float(v), 2) for v in env]); text = line if text is None else text
        if fall and fall[1] == "end": fall = (fall[0], round(at + (vf[1] if say and vf else 1.0) - 0.1, 2)); dur = max(dur, fall[1] + 2.2)     # fall as the line ends, then hold on the result
        n = max(film.beat * 2, round(dur * fps / film.beat) * film.beat); dur = n / fps
        v = 0.0 if (not walk or self.down) else (1.1 if walk is True else float(walk)); moved = dur
        if v: extra["walk"] = v
        if fall:
            who, fat = fall; ids = [p["id"] for p in self.base["people"]]; i = ids.index(who["name"]); npl = len(ids); x = (-0.72 + 1.44 * i / (npl - 1)) if npl > 1 else 0.0
            moved = min(dur, fat + 0.12); extra["fall"] = dict(id=who["name"], at=fat); self.base["puddle"] = [round(x, 2), round(self.dist + v * moved - 0.45, 2)]
            self.events += [(self.t0 + fat - 0.08, "slip", 0.16), (self.t0 + fat + 0.45, "splash", 0.55)]
        if v: self.events += [(self.t0 + tt, "step", 0.05) for tt in np.arange(0.15, moved, 0.714 / v / 2)]
        if text or title: extra["overlay"] = dict(caption=text or "", at=at, title=title or "", sub=sub or "")
        html = self.page(cam, dur, speak, extra); old = film.voice_name
        if say: film.voice_name = say[0]["voice"] or old
        try: film.web(html, dur=dur, voice=say[1] if say else None, voice_at=at, **k)
        finally: film.voice_name = old
        sc = film.scenes[-1]; sc["call"] = ("world shot " + cam, tuple(x for x in ((say[0]["name"] + ": " + say[1]) if say else text, title, sub) if x), {})
        if role in ("intro", "outro"): sc["kind"] = role; sc["meta"] = dict(letters=0, delay=0)
        self.shots.append((sc, cam.split(":")[0], self.t0)); self.t0 += dur; self.dist += v * moved
        if fall: self.down.add(fall[0]["name"])
        return film
    # ----- sound: the place's ambience under every shot, continuous across cuts -----
    NEAR = {"prop": 1.5, "close": 1.0, "over": 1.0, "two": 1.0, "full": 0.9, "fallen": 1.0, "low": 0.9, "wide": 0.65, "orbit": 0.7, "crane": 0.7, "top": 0.55}   # how close the camera is to the sound
    def _ambience(self, s, duck):
        """Called when the audio is mixed: fire, wind, rain, traffic ... chosen from the world, louder in close shots,
        thunder after each lightning flash and a whoosh as each car passes (same timing rules as world.js)."""
        if not self.shots: return
        from ambience import Ambience
        b, fps, sr = self.base, s.fps, s.sr; A = Ambience(sr, seed=int(b["seed"])); jh = lambda x, y: (lambda v: v - math.floor(v))(math.sin(x * 127.1 + y * 311.7) * 43758.5453)
        f0 = min(sc["start"] for sc, _, _ in self.shots); f1 = max(sc["start"] + sc["n"] for sc, _, _ in self.shots); i0 = int(f0 / fps * sr); n = min(int((f1 - f0) / fps * sr), s.N - i0)
        near = np.full(n, 0.7)
        for sc, cam, _ in self.shots: near[int((sc["start"] - f0) / fps * sr):int((sc["start"] + sc["n"] - f0) / fps * sr)] = self.NEAR.get(cam, 0.8)
        k = int(0.3 * sr); near = np.convolve(np.pad(near, k, mode="edge"), np.ones(k) / k, "same")[k:-k]                       # no jump in loudness on a cut
        edge = np.clip(np.arange(n) / (0.8 * sr), 0, 1) * np.clip((n - np.arange(n)) / (1.2 * sr), 0, 1); dk = 1 - (1 - duck[i0:i0 + n, 0]) * 0.45
        mg = 1 - (1 - self.music) * edge; s.wet[i0:i0 + n] *= mg[:, None]; s.dry[i0:i0 + n] *= mg[:, None]                    # music steps back while we are in the world
        mus = float(np.sqrt(((s.wet[i0:i0 + n] + s.dry[i0:i0 + n]) ** 2).mean())); amb0 = s.dry[i0:i0 + n].copy()
        for name, x, g in A.for_world(b["place"], b["time"], b["weather"], b["props"], n / sr + 0.2):
            cam_g = near if name == "fire" else 0.6 + 0.4 * near; s.dry[i0:i0 + n] += x[:n] * (cam_g * edge * dk * g * self.level)[:, None]
        print("ambience: music rms %.3f, ambience rms %.3f" % (mus, float(np.sqrt(((s.dry[i0:i0 + n] - amb0) ** 2).mean()))))
        def at(tw, sig, g):                                                                                                    # place an event given in world time
            for sc, cam, t0 in self.shots:
                if t0 <= tw < t0 + sc["n"] / fps:
                    i = int((sc["start"] / fps + tw - t0) * sr); L = min(len(sig), s.N - i)
                    if i >= 0 and L > 0: s.dry[i:i + L] += sig[:L] * g * self.level
        if b["weather"] == "storm":
            for kk in range(int(self.t0 / 2.6) + 1): at(kk * 2.6 + jh(kk, 9) * 1.6 + 0.45, A.thunder(near=0.4 + 0.5 * jh(kk, 3)), 0.5)
        for tw, name, g in self.events: at(tw, {"slip": A.slip, "splash": A.splash, "step": A.step}[name](), g)                   # walking, slipping, landing
        if b["place"] == "street":
            wet = b["weather"] in ("rain", "storm")
            for i in range(b.get("extras", 6)):
                d = 1 if i % 2 else -1; x0 = (jh(i * 3.1 + b["seed"], 17) - 0.5) * 110; v = 5 + jh(i * 5.3 + b["seed"], 29) * 4; per = 110 / v; tp = (-x0 / (d * v)) % per
                while tp < self.t0: at(tp - 1.3, A.car_pass(d, wet), 0.11); tp += per
