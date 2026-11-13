"""joyboy model3d: real 3D model files (GLB) as scenes, drawn with 67.js (github.com/codepawl/67.js).

    m = film.model("assets/product.glb", light="studio")       # load once
    m.shot("turntable", dur=4, text="Meet the new one")          # each shot is one scene, like world shots
    m.shot("push", dur=3, tr="cut")
    m.still("hero", "work/hero.png")                             # one frame, to check framing before rendering

Use it when the user supplies a 3D model: a product, an object, a vehicle, a building, an animated character.
It does not make models. For people talking in a place use film.world(); for simple glass or metal shapes use GSS.

Cameras: turntable (spins round the model), orbit (a slow arc), push, pull, hero (three-quarter view with a slight drift),
low, top. Lights: studio, soft, sun, dramatic. If the file has animation clips, the chosen clip plays (clip=0, speed=1.0, loop=True).
67.js only draws when asked and poses animation at an exact time, so capture is frame-exact with no special clock."""
import os, sys, json, hashlib, subprocess
HOME = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); KIT = os.path.join(HOME, "web"); PKG = os.path.join(KIT, "node_modules", "67js")
CAMS = ("turntable", "orbit", "push", "pull", "hero", "low", "top")
LIGHTS = {"studio": dict(lightDirection=[-0.6, 0.8, 0.5], keyIntensity=1.0, fillIntensity=0.5, ambientIntensity=0.5),
          "soft": dict(lightDirection=[-0.3, 0.9, 0.4], keyIntensity=0.6, fillIntensity=0.7, ambientIntensity=0.8),
          "sun": dict(lightDirection=[-0.7, 0.55, 0.3], keyIntensity=1.5, fillIntensity=0.25, ambientIntensity=0.4, keyColor=[1.0, 0.93, 0.82]),
          "dramatic": dict(lightDirection=[-0.9, 0.35, -0.2], keyIntensity=1.7, fillIntensity=0.08, ambientIntensity=0.15)}
PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;width:100vw;height:100vh;overflow:hidden;background:%s}canvas{display:block;width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas><script type="module">
import { Renderer67 } from "file://%s/build/67.module.js";
import { parseGltf } from "file://%s/build/gltf.js";
const spec = %s, canvas = document.getElementById("c"); canvas.width = innerWidth; canvas.height = innerHeight;
try {
  const data = await new Promise((ok, no) => { const x = new XMLHttpRequest(); x.open("GET", spec.glb); x.responseType = "arraybuffer"; x.onload = () => ok(x.response); x.onerror = () => no(new Error("could not read " + spec.glb)); x.send(); });
  const asset = await parseGltf(data), parts = asset.parts, clip = asset.animations[spec.clip], lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  const pose = t => { if (clip) { const d = clip.duration || 1, tt = t * spec.speed; return asset.applyAnimation(spec.loop ? tt %% d : Math.min(tt, d), spec.clip); } return null; };
  pose(0);
  for (const p of parts) { const m = p.matrix, q = p.geometry.positions, step = Math.max(3, Math.floor(q.length / 3 / 4000) * 3);      // bounds from a sample of the vertices
    for (let i = 0; i + 2 < q.length; i += step) { const x = q[i], y = q[i + 1], z = q[i + 2], v = [m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]];
      for (let k = 0; k < 3; k++) { if (v[k] < lo[k]) lo[k] = v[k]; if (v[k] > hi[k]) hi[k] = v[k]; } } }
  const c = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2], r = Math.max(1e-4, Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2);
  const renderer = new Renderer67(canvas, parts, { ground: spec.floor, samples: 4, memoryBudgetMiB: 512, environment: spec.environment });
  const fovY = spec.fov * Math.PI / 180, fovX = 2 * Math.atan(Math.tan(fovY / 2) * canvas.width / canvas.height), D = r / Math.sin(Math.min(fovY, fovX) / 2) * 1.12;
  const rad = d => d * Math.PI / 180, ease = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); }, dur = spec.dur;
  const cams = { turntable: u => [rad(spec.start + 360 * spec.turns * u), rad(12), 1], orbit: u => [rad(spec.start - 35 + 70 * ease(u)), rad(10), 1], push: u => [rad(spec.start + 25), rad(9), 1.55 - 0.6 * ease(u)],
    pull: u => [rad(spec.start + 25), rad(9), 0.95 + 0.6 * ease(u)], hero: u => [rad(spec.start + 30 + 6 * Math.sin(u * Math.PI)), rad(8), 0.98], low: u => [rad(spec.start + 20 + 10 * u), rad(2), 1.05], top: u => [rad(spec.start + 40 * u), rad(58), 1.15] };
  const seek = t => { const ch = pose(t); if (ch) renderer.updateParts(ch); const [az, el, k] = (cams[spec.cam] || cams.turntable)(Math.min(1, Math.max(0, t / dur))), d = D * k * spec.zoom;
    renderer.render({ eye: [c[0] + Math.sin(az) * Math.cos(el) * d, c[1] + Math.sin(el) * d, c[2] + Math.cos(az) * Math.cos(el) * d], target: c, fov: spec.fov }); };
  seek(0); window.model = { clips: asset.animations.map(a => a.name + " " + (a.duration || 0).toFixed(2) + "s"), warnings: asset.warnings || [], parts: parts.length, radius: r };
  window.joyboy = { seek };
} catch (e) { console.error("model3d: " + e.message + " " + (e.stack || "")); }
</script></body></html>"""

class Model:
    def __init__(self, film, glb, clip=0, speed=1.0, loop=True, floor=True, light="studio", bg="#0b0b10", fov=35):
        """glb = path to a .glb file (a single-file model; a .gltf with separate files must be packed into a .glb first).
        clip = which animation clip to play (if the file has any)."""
        if not os.path.exists(os.path.join(PKG, "build", "67.module.js")):
            sys.exit("joyboy: 67.js is not installed in the workspace. Run setup.sh, or: cd ~/joyboy/web && bun add 67js@npm:@codepawlhq/67js@0.19.0  (npm install works too)")
        if not os.path.isfile(glb): sys.exit(f"joyboy: 3D model not found: {glb}")
        if light not in LIGHTS: sys.exit(f"joyboy: light must be one of {', '.join(LIGHTS)}")
        self.film, self.glb = film, os.path.abspath(glb); self.base = dict(glb="file://" + self.glb, clip=clip, speed=speed, loop=loop, floor=bool(floor), environment=LIGHTS[light], fov=fov, mtime=os.path.getmtime(glb)); self.bg = bg
    def page(self, cam, dur, turns=0.5, start=0.0, zoom=1.0):
        """Write the page for one shot and return its path (cached by content in work/model3d/)."""
        name = cam if cam in CAMS else sys.exit(f"joyboy: camera must be one of {', '.join(CAMS)}")
        spec = dict(self.base, cam=name, dur=float(dur), turns=turns, start=start, zoom=zoom); src = PAGE % (self.bg, PKG, PKG, json.dumps(spec))
        d = os.path.join(self.film.work, "model3d"); os.makedirs(d, exist_ok=True); p = os.path.join(d, hashlib.md5(src.encode()).hexdigest()[:12] + ".html")
        if not os.path.exists(p): open(p, "w").write(src)
        return p
    def shot(self, cam="turntable", dur=4.0, text=None, turns=0.5, start=0.0, zoom=1.0, **k):
        """One camera shot of the model = one scene. Takes tr, voice, pace, note, sfx like any scene; text is the caption.
        turns = how many times a turntable goes round; start = starting angle in degrees; zoom < 1 moves closer."""
        n = max(self.film.beat * 2, round(dur * self.film.fps / self.film.beat) * self.film.beat)
        self.film.web(self.page(cam, n / self.film.fps + 0.5, turns, start, zoom), dur=dur, text=text, **k); self.film.scenes[-1]["kind"] = "model"
        self.film.scenes[-1]["call"] = ("model:" + cam, (os.path.basename(self.glb),) + ((text,) if text else ()), {}); return self
    def still(self, cam, out, at=1.0, size=None, **kw):
        """Render one frame of a shot to a PNG, to check framing and lighting in a few seconds."""
        w, h = size or (self.film.W, self.film.H); os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        subprocess.run(["node", os.path.join(KIT, "world_still.mjs"), os.path.abspath(self.page(cam, 4.0, **kw)), os.path.abspath(out), str(w), str(h), str(at)], check=True, cwd=KIT); return out
