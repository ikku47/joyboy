"""joyboy scaffold: make the missing piece. When the catalog has nothing that fits a beat, build it for this video (and promote it into the toolkit if it will be reused).

    python scaffold.py scene NAME      local_NAME.py with a working new scene:   film.extend("local_NAME.py"); film.NAME(...)
    python scaffold.py theme NAME      local_theme_NAME.py: a new theme with its own background painter:  Film(theme="NAME")
    python scaffold.py fx NAME         local_fx_NAME.py: a whole-film picture effect:  Film(fx=local_fx_NAME.fx)
    python scaffold.py asset NAME      how to make a character / sheet / model and keep it (prints the Blender and assets commands)

Files are written in the current folder (the project folder). A scene made this way is recorded in script.md like any other. Promote it into kinds.py
(and describe it in SKILL.md) only when a second video needs it; until then it lives with the project that made it.
"""
import os, sys
SCENE = '''"""Local scene: {name}. {{what it shows}}. Made for this video; promote it into the toolkit if another video needs it."""
import numpy as np, cv2
import joyboy as jb
from joyboy import eo, eio, clamp, spring

def install(Film):
    def {name}(self, text="...", dur=3.0, **k):
        """One line, in plain words, saying what this scene shows (the catalog lists it)."""
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U                    # frame size and the scale factor (1.0 at 1080 wide)
            img = self.bg(None, u, n, f)                          # the theme's background; after this self.ink is the readable text colour
            o = self._io(u, n, 5, 6)                              # fades in over 5 frames, out over 6
            # draw with cv2 / numpy on img (float32 BGR, 0..255), using u (frames into the scene) for every animation:
            self.block(img, self.wrap(text, 110, True), H * 0.5, 110, True, eio(u / 8) * o, scale=1 + 0.2 * (1 - eo(u / 8, 4)))
            return img
        return self._add(draw, dur, kind="{name}", meta={{}}, **k)   # meta feeds sound cues; sfx=[(seconds, "pop")] adds sounds
    Film.register_scene("{name}", {name})
'''
THEME = '''"""Local theme: {name}. A background nobody else has."""
import numpy as np, cv2
import joyboy as jb
import themes

def paint(c, f, fps, U, pal):
    """c: the base colour (BGR); return a full-frame float32 BGR image. f is the frame number: animate with it."""
    W, H = jb.W, jb.H; t = f / fps
    img = np.broadcast_to(np.float32(c), (H, W, 3)).copy()
    img += 18 * np.sin(jb.xx / (90 * U) + t)[..., None] * np.sin(jb.yy / (140 * U) - t)[..., None]
    return img

themes.register("{name}", ["#101820", "#ffcc00", "#ff5a36", "#19f0ff"], paint, look="clean", bloom=0.2, desc="local theme {name}")
# then: Film("{name}-video", theme="{name}")
'''
FX = '''"""Local effect: {name}. Applied to every finished frame of the film."""
import numpy as np, cv2

def fx(img, f, U, fps):
    """img: float32 BGR 0..255, the finished frame. Return the same shape."""
    out = img.copy(); sh = int(3 * U) + 1
    out[..., 0] = np.roll(img[..., 0], sh, 1); out[..., 2] = np.roll(img[..., 2], -sh, 1)    # a plain colour split: replace with your own
    return out
# then: import local_fx_{name}; Film("{name}-video", fx=local_fx_{name}.fx)
'''
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("scene", "theme", "fx", "asset"): print(__doc__); sys.exit(1)
    kind, name = a[0], "".join(c if c.isalnum() else "_" for c in a[1].lower())
    if kind == "asset":
        print("Make it once, keep it, rebuild it:\n  python lib/blender_asset.py mascot NAME --color '#hex' --anim idle|walk|hop     (toy character: model, sheet, sprites)\n  python lib/blender_asset.py sheet|turntable|sprites MODEL NAME                      (any .glb .fbx .obj .stl .blend)\n  python lib/assets.py add NAME --kind K --tool T --file F --cmd '<exact command>' --tag t   (anything made another way)\nthen: film.asset(\"NAME\"), film.sprite(\"NAME-sprites\")"); sys.exit(0)
    fn, body = {"scene": ("local_%s.py" % name, SCENE), "theme": ("local_theme_%s.py" % name, THEME), "fx": ("local_fx_%s.py" % name, FX)}[kind]
    if os.path.exists(fn): sys.exit("%s already exists" % fn)
    open(fn, "w").write(body.format(name=name)); print("wrote", fn)
    print({"scene": "use: film.extend(\"%s\"); film.%s(...)" % (fn, name), "theme": "use: import local_theme_%s  then  Film(..., theme=\"%s\")" % (name, name), "fx": "use: import local_fx_%s  then  Film(..., fx=local_fx_%s.fx)" % (name, name)}[kind])
