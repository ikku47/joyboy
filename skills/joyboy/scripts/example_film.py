"""joyboy API demo: shows how the picture toolkit, the audio toolkit and the renderer plug together.

This is NOT a template for a concept. The shots, words and order here are arbitrary; they only
exercise the helpers (crt, cam, tmask/put, trace, impact, dmask, put_letters, post, Score, run).
Design every real film from the user's request, then borrow the wiring from this file.

Self-contained: it paints its own placeholder artwork and mark, so it runs anywhere.

    python example_film.py sheet sheet.jpg 10 40 60 80 110 150 170 186 200 230    # preview frames
    python example_film.py                                                        # full render + audio
    LAND=1 python example_film.py                                                 # 16:9
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")), "lib"))   # workspace toolkit
import joyboy as jb
from joyboy import eo, ei, eio, clamp
from score import Score

LAND = bool(os.environ.get("LAND"))
jb.init(*((1920, 1080) if LAND else (1080, 1920)), 24)
W, H = jb.W, jb.H
F = 240
OUT = os.path.abspath("example-16x9.mp4" if LAND else "example.mp4")
FONT = "/System/Library/Fonts/Avenir Next.ttc"          # swap for the brand typeface (variable woff2 works too)
PAL = [(50, 168, 90), (245, 163, 78), (13, 138, 255), (45, 43, 239), (214, 99, 126)]   # BGR accents

# --- placeholder art: replace with jb.art("painting.webp") -------------------------------
def painting(top, mid, ground, seed):
    h, w = (941, 1672) if LAND else (1672, 941); y = np.linspace(0, 1, h)[:, None, None]
    sky = np.float32(top) * (1 - y) + np.float32(mid) * y; im = np.broadcast_to(sky, (h, w, 3)).copy()
    r = np.random.default_rng(seed); x = np.arange(w)
    for i in range(4):
        base = h * (0.68 + 0.07 * i); ridge = base + 30 * np.sin(x / (90 + 40 * i) + r.uniform(0, 6)) + 18 * np.sin(x / 37 + i)
        m = (np.arange(h)[:, None] > ridge[None, :])[..., None]; im = np.where(m, np.float32(ground) * (0.55 + 0.15 * i), im)
    return np.clip(im, 0, 255).astype(np.uint8)
SCENES = [painting((150, 90, 20), (235, 190, 120), (60, 150, 70), 1), painting((120, 30, 60), (150, 140, 255), (120, 60, 150), 2)]

# --- placeholder mark: replace with jb.mark_from_image(jb.art("logo-on-art.png")) or a rendered logo mask ---
_m = np.zeros((400, 400), np.uint8); cv2.ellipse(_m, (170, 200), (150, 180), 0, -90, 90, 255, -1); cv2.rectangle(_m, (60, 20), (170, 380), 255, -1)
cv2.fillPoly(_m, [np.array([[130, 110], [190, 110], [230, 200], [130, 330]])], 0)
MARK = jb.mark_contours(_m)
MX, MY, MH = W // 2, int(H * 0.40), int(min(W, H) * 0.32)
CS = jb.letters("COMING SOON", 64, FONT, None, 24, MY + MH * 0.5 + 110)
CRT_LINES = [("somewhere, 2026.", 8, 1.6), ("> begin", 36, 1.6)]

def frame(f):
    if f < 72:                                           # 1. the machine wakes, blooms to white
        img = jb.crt(f, CRT_LINES, flash_at=48)
    elif f < 136:                                        # 2. a painted world, one word slammed in on the beat
        u = f - 72; z = 1.3 + 0.5 * (1 - eo(u / 11, 4)) - 0.1 * u / 64
        img = jb.cam(SCENES[0], z, 0.5, 0.72, f, par=-10 + 20 * u / 64)
        jb.petals(img, f, [(250, 250, 250), PAL[1]], 0.6)
        sc = 1 + 0.5 * (1 - eo(u / 9, 4)) + 0.03 * u / 64
        jb.put(img, *jb.tmask("BUILD", 300, FONT, None, 6, W * 0.8, 8), H * 0.33, clamp(u / 3) * (1 - eio((u - 58) / 6)), scale=sc, shadow=0.3)
        img = img + 255 * (1 - eo(u / 14, 2)) + 0
    elif f < 184:                                        # 3. black: a line of light draws the mark
        u = f - 136; img = jb.trace(MARK, eio((u - 3) / 42), u, MH, MX, MY, PAL)
    else:                                                # 4. the hit: mark fills, world returns, COMING SOON
        u = f - 184; z = 1 + 0.22 * (1 - eo(u / 14, 4)) + 0.04 * u / 56
        img = jb.shake(jb.cam(SCENES[1], 1.1 * z, 0.5, 0.56, f), u)
        jb.petals(img, f, [(250, 250, 250), PAL[4]], 0.7, 1.4)
        img = jb.impact(img, u, MX, MY, PAL)
        dm = jb.dmask(MARK, MH * z, MX, MY); a = dm[..., None]
        img = img * (1 - 0.2 * cv2.GaussianBlur(dm, (0, 0), 20)[..., None]); img = img * (1 - a) + jb.WHITE * a
        img = img + cv2.GaussianBlur(dm, (0, 0), 36)[..., None] * 255 * (0.06 + 0.6 * np.exp(-u / 10)) + 255 * np.exp(-u / 4.5)
        jb.put_letters(img, CS, u - 8, 2)
    img = jb.post(img, f)
    if f > F - 14: img = img * (1 - eio((f - (F - 14)) / 12))
    return np.clip(img, 0, 255).astype(np.uint8)

def score(path):
    s = Score(F, 24)
    s.hum(0, 70); s.add(s.dry, s.taiko(0.6, 50), 0, g=0.5)
    for txt, t0, sp in CRT_LINES:
        for i, c in enumerate(txt):
            if c != " ": s.add(s.wet, s.click(), s.t(t0 + i * sp), g=0.15)
    s.add(s.wet, s.riser(s.t(22)), s.t(50), g=0.28)
    s.add(s.dry, s.taiko(), s.t(72), g=0.95); s.add(s.wet, s.strings((43, 55, 58, 62), s.t(64) + 0.4, 0.2, 0.5, 2400), s.t(72), g=0.1)
    s.add(s.wet, s.riser(s.t(40)), s.t(96), g=0.4); s.roll(100, 135); s.add(s.dry, s.taiko(1.0, 48), s.t(136), g=0.9)
    for i in range(3): s.add(s.dry, s.taiko(0.5, 44), s.t(136 + i * 16), g=0.55)
    s.add(s.wet, s.reverse_crash(1.8), s.t(184) - 1.8, g=0.2)
    s.add(s.dry, s.boom(), s.t(184)); s.add(s.wet, s.crash(4, 1.0), s.t(184), g=0.25); s.add(s.wet, s.braam(26, 3), s.t(184), g=0.2)
    s.add(s.wet, s.strings((38, 50, 57, 62, 66), 3.2, 0.08, 1.8, 2400), s.t(184), g=0.14); s.add(s.wet, s.choir((62, 69, 74), 3.2), s.t(184), g=0.04)
    for fr, m in ((202, 78), (214, 81), (226, 86)): s.add(s.wet, s.piano(m, 3), s.t(fr), g=0.15)
    s.write(path, sections=[(0, 72), (72, 136), (136, 184), (184, 240)], fade_out=1.0)

if __name__ == "__main__":
    wav = os.path.splitext(OUT)[0] + ".wav"
    if len(sys.argv) == 1: score(wav)
    jb.run(frame, F, OUT, audio=wav)
    if len(sys.argv) == 1 and os.path.exists(wav): os.remove(wav)
