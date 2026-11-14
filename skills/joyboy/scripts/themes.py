"""joyboy themes: eight complete visual systems, so videos stop looking alike.

    Film("promo", theme="flat")        # bright colour fields, huge heavy type: the kinetic-type reel look
    Film("promo", theme="studio")      # white seamless studio: products, apps, clean ads
    Film("promo", theme="blueprint")   # engineering grid, mono type: tech, how-it-works, dev tools
    Film("promo", theme="brutal")      # neo-brutalist: hard black frame, loud colours: startups, creators
    Film("promo", theme="aurora")      # slow glowing colour clouds: AI, wellness, premium
    Film("promo", theme="paper")       # cream paper, serif type: editorial, stories, quotes, books
    Film("promo", theme="neon")        # night grid and neon: music, gaming, nightlife, synthwave
    Film("promo", theme="retro")       # halftone dots, pop colours, slab serif: food, fun, nostalgia
    Film("promo", theme=None)          # the original dark cinematic look (default when no theme is given)

A theme sets the background, the colour palette, the typeface, the ink (text) colour and the finish. The ink flips to
black or white by itself to stay readable on whatever colour a scene sits on. Any theme setting can still be overridden
by `palette=`, `font=`, `look=` and `bloom=` on the Film.
"""
import os
import numpy as np, cv2
import joyboy as jb

_SF = "/System/Library/Fonts/"; _SUP = "/System/Library/Fonts/Supplemental/"
def _font(*cands):
    for p, ix in cands:
        if os.path.exists(p): return (p, None, ix)
    return None

THEMES = {
    "flat": dict(pal=["#ffe14d", "#ffffff", "#bff3d0", "#ff6b4a", "#2340ff", "#f4c6ff", "#0d0d0f"], bg="field", look="clean", bloom=0.08, desc="bright colour fields, huge heavy type, motion blur",
                 font=[(_SUP + "Arial Black.ttf", 0), (_SF + "Avenir Next Condensed.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
    "studio": dict(pal=["#f2f2f0", "#111111", "#2f6bff", "#ff5a36", "#14b886"], bg="studio", look="clean", bloom=0.1, desc="white seamless studio, soft shadows, clean type",
                   font=[(_SF + "Avenir Next.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
    "blueprint": dict(pal=["#0b2a6f", "#ffffff", "#8fd3ff", "#ffd166", "#ff7a59"], bg="blueprint", look="clean", bloom=0.25, desc="engineering grid, registration marks, mono type",
                      font=[(_SF + "Menlo.ttc", 1)], font_reg=[(_SF + "Menlo.ttc", 0)]),
    "brutal": dict(pal=["#ffde59", "#ff90e8", "#7ae582", "#5ec8ff", "#ffffff", "#ff6b4a"], bg="brutal", look="clean", bloom=0.05, desc="thick black frame, loud colours, hard shadows",
                   font=[(_SUP + "Arial Black.ttf", 0), (_SUP + "Impact.ttf", 0)], font_reg=[(_SF + "Avenir Next.ttc", 8)]),
    "aurora": dict(pal=["#090a1c", "#6a5cff", "#ff5ca8", "#2ee6c5", "#ffb347"], bg="aurora", look="soft", bloom=0.15, desc="slow glowing colour clouds on dark",
                   font=[(_SF + "Avenir Next.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
    "paper": dict(pal=["#f3ead8", "#1b1b1b", "#c8442b", "#2d5f4a", "#e9b44c"], bg="paper", look="soft", bloom=0.08, desc="cream paper, ink-black serif type",
                  font=[(_SUP + "Georgia Bold.ttf", 0), (_SF + "Avenir Next.ttc", 8)], font_reg=[(_SUP + "Georgia.ttf", 0), (_SF + "Avenir Next.ttc", 5)]),
    "neon": dict(pal=["#07040f", "#ff2bd6", "#19f0ff", "#ffd400", "#8a5cff"], bg="neon", look=dict(base="punchy", vignette=0.7, grain=0.01), bloom=1.0, desc="night grid, sun and neon glow",
                 font=[(_SF + "Avenir Next Condensed.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
    "retro": dict(pal=["#f7e7c6", "#e8432a", "#1d3a8a", "#f2a900", "#14110f"], bg="halftone", look=dict(base="warm", vignette=0.2, grain=0.02, contrast=0.4), bloom=0.1, desc="halftone dots, pop colours, slab serif",
                  font=[(_SUP + "Rockwell.ttc", 2)], font_reg=[(_SUP + "Rockwell.ttc", 0)]),
    "chalkboard": dict(pal=["#1d2a26", "#f4f1e8", "#ffd966", "#ff8f8f", "#8fd3ff"], bg="chalk", look="soft", bloom=0.05, desc="a slate blackboard with chalk dust and wiped ghosts",
                       font=[(_SUP + "ChalkboardSE.ttc", 1), (_SF + "Avenir Next.ttc", 8)], font_reg=[(_SUP + "ChalkboardSE.ttc", 0), (_SF + "Avenir Next.ttc", 5)]),
    "whiteboard": dict(pal=["#f4f6f7", "#1f2933", "#e63946", "#2a6fdb", "#2a9d5c"], bg="whiteboard", look="clean", bloom=0.05, desc="a glossy dry-erase board with faint wiped ghosts and a sheen",
                       font=[(_SF + "MarkerFelt.ttc", 1), (_SF + "Avenir Next.ttc", 8)], font_reg=[(_SF + "MarkerFelt.ttc", 0), (_SF + "Avenir Next.ttc", 5)]),
    "dotgrid": dict(pal=["#f6f3ea", "#14161a", "#ffd23f", "#2b6cb0", "#c0392b"], bg="dotgrid", look="clean", bloom=0.05, desc="dot-grid notebook paper for sketchnotes and hand-made explainers",
                    font=[(_SUP + "Bradley Hand Bold.ttf", 0), (_SF + "Avenir Next.ttc", 8)], font_reg=[(_SUP + "Bradley Hand Bold.ttf", 0), (_SF + "Avenir Next.ttc", 5)]),
    "circuit": dict(pal=["#0f4a2a", "#f3f0e0", "#e0b24a", "#7fe3a0", "#ff6b4a"], bg="circuit", look="soft", bloom=0.35, desc="a printed circuit board: green solder mask, copper traces, white silkscreen",
                    font=[(_SF + "Menlo.ttc", 1)], font_reg=[(_SF + "Menlo.ttc", 0)]),
    "scope": dict(pal=["#050806", "#7dff9a", "#e8fff0", "#ffd166", "#ff6b6b"], bg="scope", look=dict(base="clean", glow=0.4), bloom=0.9, ink="#7dff9a", desc="phosphor green on near-black with a dotted graticule, like an oscilloscope",
                  font=[(_SF + "Menlo.ttc", 1)], font_reg=[(_SF + "Menlo.ttc", 0)]),
    "keynote": dict(pal=["#07080c", "#f5f5f7", "#3b82f6", "#a78bfa", "#34d399"], bg="keynote", look="clean", bloom=0.35, desc="a dark tech-launch stage: near-black, a hairline grid and one soft glow",
                    font=[(_SF + "Avenir Next.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
    "swiss": dict(pal=["#f1efe9", "#111111", "#e4002b", "#1d3557", "#f4a300"], bg="swiss", look="clean", bloom=0.05, desc="a modular grid on off-white with one signal colour and heavy sans type",
                  font=[(_SF + "HelveticaNeue.ttc", 1), (_SF + "Helvetica.ttc", 1)], font_reg=[(_SF + "HelveticaNeue.ttc", 0), (_SF + "Helvetica.ttc", 0)]),
    "kraft": dict(pal=["#c8a77a", "#2b1d12", "#f6efe0", "#b23a2a", "#2f5d50"], bg="kraft", look="soft", bloom=0.05, desc="brown kraft paper with fibre: hand-made, packaging, craft",
                  font=[(_SUP + "AmericanTypewriter.ttc", 2), (_SF + "Avenir Next.ttc", 8)], font_reg=[(_SUP + "AmericanTypewriter.ttc", 0), (_SF + "Avenir Next.ttc", 5)]),
    "lighttable": dict(pal=["#e6f0f4", "#16212b", "#d14d3a", "#2f7fb8", "#caa24a"], bg="lighttable", look="clean", bloom=0.2, desc="a cool backlit light table with a soft falloff: archives, negatives, a loupe",
                       font=[(_SF + "Avenir Next.ttc", 8)], font_reg=[(_SF + "Avenir Next.ttc", 5)]),
}

CUSTOM = {}
def register(name, pal, painter, look="clean", bloom=0.1, desc="custom theme", fonts=None, fonts_reg=None):
    """Add a theme made for one video (see scaffold.py theme): painter(c, f, fps, U, pal) -> a full-frame float32 BGR background; c is the base colour.
    Use it with Film(theme=name). It is kept only for this run, so call it near the top of the film script."""
    CUSTOM[name] = painter; THEMES[name] = dict(pal=pal, bg="custom:" + name, look=look, bloom=bloom, desc=desc, font=fonts or [], font_reg=fonts_reg or [])

def resolve(name):
    """Theme dict with fonts resolved to existing files (or None to keep the default), or None for no theme."""
    if not name: return None
    if name not in THEMES: raise SystemExit("joyboy: unknown theme %r; choose from %s" % (name, ", ".join(THEMES)))
    t = dict(THEMES[name]); t["name"] = name; t["font"] = _font(*t["font"]); t["font_reg"] = _font(*t["font_reg"]); return t

def lum(c): c = np.asarray(c, np.float32); return float(c @ np.float32((0.114, 0.587, 0.299)))

# ----------------------------------------------------------------------------------------- backgrounds
_cache = {}
def _static(key, fn):
    k = (key, jb.W, jb.H)
    if k not in _cache: _cache[k] = fn()
    return _cache[k]

def paint(kind, c, f, fps, U, pal):
    """One background frame for theme `kind`, base colour `c` (BGR), at frame f."""
    W, H = jb.W, jb.H; xx, yy = jb.xx, jb.yy; t = f / fps
    if kind.startswith("custom:"): return np.asarray(CUSTOM[kind[7:]](c, f, fps, U, pal), np.float32)
    if kind == "field":                                    # flat colour: the whole point
        return np.broadcast_to(c, (H, W, 3)).astype(np.float32).copy()
    if kind == "studio":
        r2 = ((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H * 0.42) / (H * 0.75)) ** 2; k = np.clip(1.0 - 0.10 * r2, 0.86, 1.0)[..., None]
        fl = np.clip((yy / H - 0.70) / 0.3, 0, 1)[..., None]; img = c * k * (1 - 0.06 * fl); return img.astype(np.float32)
    if kind == "blueprint":
        def grid():
            minor, major = 54 * U, 270 * U; g = np.zeros((H, W), np.float32)
            g += 0.10 * (((xx % minor) < max(1.5 * U, 1)) | ((yy % minor) < max(1.5 * U, 1))); g += 0.22 * (((xx % major) < max(2.5 * U, 1.5)) | ((yy % major) < max(2.5 * U, 1.5)))
            m = 60 * U; L = 26 * U; w = max(3 * U, 2)                   # registration marks in the corners
            for cx, cy in ((m, m), (W - m, m), (m, H - m), (W - m, H - m)):
                g += 0.55 * ((np.abs(xx - cx) < w / 2) & (np.abs(yy - cy) < L)) + 0.55 * ((np.abs(yy - cy) < w / 2) & (np.abs(xx - cx) < L))
            return np.clip(g, 0, 1)[..., None]
        g = _static("bp", grid); sh = (0.5 + 0.5 * np.sin(t * 0.7)) * 0.05
        return (c * (1 - g) + np.float32((255, 235, 200)) * g * 0.9 + c * sh).astype(np.float32)
    if kind == "brutal":
        def dots():
            s = 46 * U; m = ((((xx % s) - s / 2) ** 2 + ((yy % s) - s / 2) ** 2) < (3.2 * U) ** 2).astype(np.float32)
            b = 16 * U; fr = ((xx < b) | (xx > W - b) | (yy < b) | (yy > H - b)).astype(np.float32); return m[..., None], fr[..., None]
        m, fr = _static("br", dots); img = c * (1 - 0.10 * m); return (img * (1 - fr)).astype(np.float32)
    if kind == "aurora":
        sw, sh = max(W // 5, 64), max(H // 5, 64); gx, gy = np.meshgrid(np.linspace(0, W, sw), np.linspace(0, H, sh)); img = np.broadcast_to(c, (sh, sw, 3)).astype(np.float32).copy()
        cols = [col_ for col_ in pal[1:5]] if len(pal) > 1 else [c]
        for i, cc in enumerate(cols):
            cx = W * (0.5 + 0.38 * np.sin(t * 0.33 + i * 1.9)); cy = H * (0.5 + 0.34 * np.cos(t * 0.27 + i * 2.3)); s2 = (min(W, H) * (0.55 + 0.12 * np.sin(t * 0.5 + i))) ** 2
            img += np.float32(cc)[None, None, :] * (0.34 * np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * s2)))[..., None]
        return cv2.resize(np.clip(img, 0, 255), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    if kind == "paper":
        def fibre():
            r = np.random.default_rng(4); n = r.standard_normal((H // 3 + 1, W // 3 + 1)).astype(np.float32); n = cv2.resize(cv2.GaussianBlur(n, (0, 0), 1.2), (W, H)); return n[..., None]
        n = _static("pp", fibre); v = np.clip(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.8)) ** 2, 0, 1)[..., None]
        return (c * (1 - 0.10 * v) + n * 6).astype(np.float32)
    if kind == "neon":
        hz = H * 0.80; img = np.broadcast_to(c, (H, W, 3)).astype(np.float32).copy(); a, b = np.float32(pal[1]), np.float32(pal[2])
        sky = np.clip(1 - np.abs(yy - hz) / (H * 0.30), 0, 1)[..., None] ** 2; img += a * 0.55 * sky * (yy[..., None] < hz) + b * 0.30 * sky * (yy[..., None] >= hz)
        sx, sy, sr = W / 2, hz - H * 0.04, min(W, H) * 0.17; d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2); stripe = ((yy - sy) % (22 * U) > (6 * U + 12 * U * np.clip((yy - sy) / sr, 0, 1))) | (yy < sy)
        sun = (d < sr) & (yy < hz) & stripe; g = np.clip((yy - (sy - sr)) / (2 * sr), 0, 1)[..., None]; img = np.where(sun[..., None], np.float32(pal[3]) * (1 - g) + a * g, img)
        fl = yy > hz; z = np.where(fl, (H * 0.30) / np.maximum(yy - hz, 1), 0); ph = (z + t * 0.9) % 1.0
        hline = fl & (ph < 0.045 * np.clip(z, 0.3, 3)); vx = (xx - W / 2) * z / (W * 0.16); vline = fl & (np.abs(vx - np.round(vx)) < 0.028 * np.clip(z, 0.5, 3) * 1.2)
        gl = (hline | vline).astype(np.float32)[..., None] * np.clip(1 - z / 12, 0, 1)[..., None]; return np.clip(img + b * 1.1 * gl + np.float32((255, 255, 255)) * gl * 0.15, 0, 255).astype(np.float32)
    if kind == "halftone":
        def ht():
            s = 34 * U; cx, cy = W * 0.92, H * 0.08; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / np.sqrt(W ** 2 + H ** 2); rad = (1 - np.clip(d * 1.5, 0, 1)) * s * 0.52
            m = ((((xx % s) - s / 2) ** 2 + ((yy % s) - s / 2) ** 2) < rad ** 2).astype(np.float32); return cv2.GaussianBlur(m, (0, 0), 0.8)[..., None]
        m = _static("ht", ht); acc = np.float32(pal[1]); return (c * (1 - m) + acc * m).astype(np.float32)
    if kind == "chalk":
        n = _static("ch1", lambda: cv2.resize(np.random.default_rng(21).standard_normal((H // 40 + 2, W // 40 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC))[..., None]; fine = _static("ch2", lambda: np.random.default_rng(22).standard_normal((H, W)).astype(np.float32)[..., None])
        return (c + np.clip(n * 0.5 + 0.3, 0, 1) ** 2 * 14 + fine * 2.5).astype(np.float32)
    if kind == "whiteboard":
        n = _static("wb", lambda: cv2.resize(np.random.default_rng(23).standard_normal((H // 60 + 2, W // 60 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC))[..., None]; sheen = np.exp(-(((xx - (0.2 + 0.6 * ((t * 0.04) % 1.0)) * W - yy * 0.4) / (W * 0.18)) ** 2))[..., None] * 9
        return (c - np.clip(n, 0, 3) * 2.2 + sheen).astype(np.float32)
    if kind == "dotgrid":
        def dg():
            s = 44 * U; m = ((((xx % s) - s / 2) ** 2 + ((yy % s) - s / 2) ** 2) < (2.6 * U) ** 2).astype(np.float32); return m[..., None]
        return (c * (1 - 0.28 * _static("dg", dg)) + _static("dgn", lambda: np.random.default_rng(24).standard_normal((H, W)).astype(np.float32)[..., None]) * 1.5).astype(np.float32)
    if kind == "circuit":
        def pcb():
            r = np.random.default_rng(25); m = np.zeros((H, W), np.float32); s = max(8, int(60 * U))
            for _ in range(int(H * W / (s * s) * 0.9)):
                x, y = int(r.integers(0, W // s)) * s, int(r.integers(0, H // s)) * s; L = int(r.integers(1, 5)) * s; d = r.integers(0, 2)
                x2, y2 = (min(x + L, W), y) if d == 0 else (x, min(y + L, H)); cv2.line(m, (x, y), (x2, y2), 1.0, max(2, int(5 * U)), cv2.LINE_AA); cv2.circle(m, (x2, y2), max(3, int(8 * U)), 1.0, -1, cv2.LINE_AA)
            return cv2.GaussianBlur(m, (0, 0), 0.8)[..., None]
        m = _static("pcb", pcb); pulse = (0.85 + 0.15 * np.sin(t * 1.6))
        return (c * (1 - m * 0.55) + np.float32((90, 180, 210)) * m * 0.30 * pulse + _static("pcbn", lambda: np.random.default_rng(26).standard_normal((H, W)).astype(np.float32)[..., None]) * 2.0).astype(np.float32)
    if kind == "scope":
        def grat():
            s = 90 * U; m = ((((xx % s) - s / 2) ** 2 + ((yy % s) - s / 2) ** 2) < (2.4 * U) ** 2).astype(np.float32) * 0.6; m += (((xx % (s * 5)) < 1.5) | ((yy % (s * 5)) < 1.5)).astype(np.float32) * 0.25; return m[..., None]
        v = np.clip(1 - 0.7 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0.2, 1)[..., None]
        return (c * v + np.float32((90, 255, 125)) * _static("grat", grat) * 0.20 * v).astype(np.float32)
    if kind == "keynote":
        r2 = ((xx - W * 0.5) / (W * 0.8)) ** 2 + ((yy - H * 0.30) / (H * 0.7)) ** 2; glow = np.exp(-(((xx - W * (0.62 + 0.04 * np.sin(t * 0.3))) / (W * 0.5)) ** 2 + ((yy - H * 0.35) / (H * 0.4)) ** 2))[..., None]
        def hl():
            s = 48 * U; m = (((xx % s) < 1.2) | ((yy % s) < 1.2)).astype(np.float32) * 0.035 + (((xx % (s * 4)) < 1.2) | ((yy % (s * 4)) < 1.2)).astype(np.float32) * 0.035; return m[..., None]
        return (c * np.clip(1.15 - 0.55 * r2, 0.35, 1.2)[..., None] + np.float32((255, 150, 80)) * glow * 0.12 + 255 * _static("hl", hl)).astype(np.float32)
    if kind == "swiss":
        def gr():
            m = np.zeros((H, W), np.float32); cols, rows = 6, 10
            for i in range(cols + 1): x0 = min(int(W * 0.06 + (W * 0.88) * i / cols), W - 2); m[:, x0:x0 + 2] = 1
            for j in range(rows + 1): y0 = min(int(H * 0.05 + (H * 0.9) * j / rows), H - 2); m[y0:y0 + 2, :] = 1
            return m[..., None]
        return (c * (1 - 0.07 * _static("sw", gr)) + _static("swn", lambda: np.random.default_rng(27).standard_normal((H, W)).astype(np.float32)[..., None]) * 1.0).astype(np.float32)
    if kind == "kraft":
        n = _static("kr1", lambda: cv2.resize(np.random.default_rng(28).standard_normal((H // 3 + 1, W // 3 + 1)).astype(np.float32), (W, H))); fib = _static("kr2", lambda: cv2.GaussianBlur(np.random.default_rng(29).standard_normal((H, W)).astype(np.float32), (0, 0), 1.2) * 14)
        v = np.clip(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.8)) ** 2, 0, 1)[..., None]; return (c * (1 - 0.14 * v) + (n * 5 + fib)[..., None]).astype(np.float32)
    if kind == "lighttable":
        v = np.clip(1 - 0.55 * (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.35, 1)[..., None]; flick = 1 + 0.012 * np.sin(t * 100.0)
        return (c * v * flick + np.float32((255, 245, 235)) * np.exp(-(((xx - W / 2) / (W * 0.45)) ** 2 + ((yy - H * 0.45) / (H * 0.4)) ** 2))[..., None] * 0.03).astype(np.float32)
    return np.broadcast_to(c, (H, W, 3)).astype(np.float32).copy()
