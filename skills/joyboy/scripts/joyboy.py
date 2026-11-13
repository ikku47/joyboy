"""joyboy: a small toolkit for code-rendered brand films (OpenCV + NumPy + Pillow + ffmpeg).

Call init(w, h, fps) once, write a frame(f) function that returns a uint8 BGR image,
then hand it to run(). Every helper works on float32 BGR images in 0..255 and reads the
stage size from this module, so the same film code renders portrait or landscape.
"""
import sys, os, re, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W = H = FPS = 0
xx = yy = VIG = None
WHITE = np.float32((250, 252, 250))

def init(w=1080, h=1920, fps=24):
    """Set the stage. Must run before any other helper (and again if the size changes)."""
    global W, H, FPS, xx, yy, VIG
    W, H, FPS = w, h, fps
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    VIG = (1 - 0.42 * np.clip(((xx - W / 2) / (W * 0.74)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2, 0, 1.3) ** 1.4)[..., None]
    tmask.cache_clear()

# ---------- easing ----------
def clamp(x): return float(min(max(x, 0), 1))
def eo(x, p=3): x = clamp(x); return 1 - (1 - x) ** p          # ease out: fast start, soft landing
def ei(x, p=3): x = clamp(x); return x ** p                     # ease in: slow start, accelerating
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)            # smoothstep
def spring(x, freq=2.2, damp=6.0): x = max(x, 0); return 1 - np.exp(-damp * x) * np.cos(2 * np.pi * freq * x)

# ---------- art ----------
@functools.lru_cache(None)
def art(path):
    """Load an image as BGR uint8 (alpha is flattened onto white). Cached."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None: raise FileNotFoundError(path)
    if im.ndim == 2: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[..., 3:].astype(np.float32) / 255; im = (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    return im

def cam(im, z, nx, ny, f=0, par=0.0, horizon=0.66, wob=2.2, wob_from=0.74):
    """2.5D camera over a painting. z=1 fits the image width to the frame; (nx, ny) is the
    view centre in 0..1 image coordinates (clamped so the frame never leaves the picture).
    par shifts the ground (below `horizon`) sideways in source pixels for parallax; wob sways
    the bottom strip (below `wob_from`) like grass in wind. Animate z/nx/ny/par over time."""
    ih, iw = im.shape[:2]; k = (W / iw) * z; hw, hh = W / 2 / k, H / 2 / k
    cx = min(max(nx * iw, hw + abs(par) + 3), iw - hw - abs(par) - 3) if 2 * hw + 2 * abs(par) + 6 < iw else iw / 2
    cy = min(max(ny * ih, hh + 1), ih - hh - 1) if 2 * hh + 2 < ih else ih / 2
    sx = cx + (xx - W / 2) / k; sy = cy + (yy - H / 2) / k
    if par:
        g = np.clip((sy / ih - horizon) / (1 - horizon), 0, 1); sx = sx - par * g ** 1.5
    if wob:
        a = wob * np.clip((sy / ih - wob_from) / (1 - wob_from), 0, 1)
        sx = sx + a * np.sin(2 * np.pi * 0.55 * f / FPS + sx / 38 + sy / 55)
    return cv2.remap(im, sx, sy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)

def whip(a, b, p):
    """Whip-pan from frame a to frame b; p runs 0..1 over ~4 frames."""
    off = int(eio(p) * W); img = np.empty_like(a); img[:, :W - off] = a[:, off:]; img[:, W - off:] = b[:, :off]
    return cv2.blur(img, (int(np.sin(np.pi * clamp(p)) * W * 0.5) | 1, 1))

# ---------- type ----------
def font(path, size, weight=None, index=0):
    f = ImageFont.truetype(path, size, index=index)
    if weight is not None:
        try: f.set_variation_by_axes([weight])     # variable fonts (e.g. Outfit, DM Sans woff2)
        except Exception: pass
    return f

@functools.lru_cache(None)
def tmask(txt, size, path, weight=None, track=0, maxw=0, index=0):
    """Centred single-line text as (mask, soft shadow), both full frame width. maxw shrinks to fit."""
    if maxw:
        while size > 8 and sum(font(path, size, weight, index).getlength(c) for c in txt) + track * (len(txt) - 1) > maxw: size -= 4
    ft = font(path, size, weight, index); ws = [ft.getlength(c) for c in txt]; tot = sum(ws) + track * (len(txt) - 1)
    im = Image.new("L", (W, int(size * 1.5)), 0); d = ImageDraw.Draw(im); x = (W - tot) / 2
    for c, cw in zip(txt, ws): d.text((x, size * 0.12), c, font=ft, fill=255); x += cw + track
    m = np.asarray(im, np.float32) / 255
    return m, cv2.GaussianBlur(m, (0, 0), max(size / 9, 4))

def put(img, m, sh, cy, op=1.0, col=WHITE, shadow=0.45, scale=1.0):
    """Composite a tmask() result onto img (in place), vertically centred on cy."""
    if op <= 0.003: return
    if scale != 1.0:
        pad = int(m.shape[0] * (scale - 1) / 2) + 2 if scale > 1 else 0
        if pad: m = cv2.copyMakeBorder(m, pad, pad, 0, 0, cv2.BORDER_CONSTANT); sh = cv2.copyMakeBorder(sh, pad, pad, 0, 0, cv2.BORDER_CONSTANT)
        M = np.float32([[scale, 0, W / 2 * (1 - scale)], [0, scale, m.shape[0] / 2 * (1 - scale)]])
        m = cv2.warpAffine(m, M, (W, m.shape[0])); sh = cv2.warpAffine(sh, M, (W, m.shape[0]))
    y0 = int(cy - m.shape[0] / 2); a0, a1 = max(y0, 0), min(y0 + m.shape[0], H)
    if a1 <= a0: return
    m = m[a0 - y0:a1 - y0]; sh = sh[a0 - y0:a1 - y0]; reg = img[a0:a1]
    if shadow: reg *= (1 - shadow * op * sh[..., None])
    a = (m * op)[..., None]; reg[:] = reg * (1 - a) + np.float32(col) * a

def caption(img, lines, f, f0, f1, y, size, path, weight=None, gap=1.28):
    """Quiet subtitle-style lines that drift up as they fade in at f0 and fade out at f1."""
    op = eio((f - f0) / 12) * (1 - eio((f - f1) / 12))
    if op <= 0: return
    dy = 14 * (1 - eo((f - f0) / 20))
    for i, l in enumerate(lines): put(img, *tmask(l, size, path, weight, 1), y + i * size * gap + dy, op)

def letters(txt, size, path, weight, track, cy):
    """Per-letter masks for a staggered reveal: [(x0, y0, mask, shadow)]. Draw with put_letters()."""
    ft = font(path, size, weight); ws = [ft.getlength(c) for c in txt]; tot = sum(ws) + track * (len(txt) - 1); x = (W - tot) / 2; out = []
    for c, cw in zip(txt, ws):
        if c != " ":
            im = Image.new("L", (int(cw) + 16, int(size * 1.5)), 0); ImageDraw.Draw(im).text((8, size * 0.12), c, font=ft, fill=255)
            m = np.asarray(im, np.float32) / 255; out.append((int(x) - 8, int(cy - size * 0.75), m, cv2.GaussianBlur(m, (0, 0), 6)))
        x += cw + track
    return out

def put_letters(img, ls, u, stagger=4, col=WHITE):
    """u = frames since the reveal started; each letter rises and fades in `stagger` frames after the last."""
    for j, (x0, y0, m, s_) in enumerate(ls):
        w_ = u - j * stagger; op = eo(w_ / 18)
        if op <= 0: continue
        dy = int(round(16 * (1 - eo(w_ / 22)))); reg = img[y0 + dy:y0 + dy + m.shape[0], x0:x0 + m.shape[1]]
        if reg.shape[:2] != m.shape: continue
        reg *= (1 - 0.4 * op * s_[..., None]); a = (m * op)[..., None]; reg[:] = reg * (1 - a) + np.float32(col) * a

# ---------- the mark (logo) ----------
def detect_mark(img, lo=238, aspect=(0.6, 1.4), fill=(0.3, 0.9)):
    """Find a flat white mark painted into an image. Returns its bbox (x, y, w, h) or None."""
    m = (img.min(axis=2) > lo).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(m, 8); best = None
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if h < img.shape[0] * 0.05 or not aspect[0] <= w / h <= aspect[1] or not fill[0] <= a / (w * h) <= fill[1]: continue
        if best is None or a > best[4]: best = (x, y, w, h, a)
    return best[:4] if best else None

def lock(img, box, mark_h, cx, cy):
    """Scale and place an image so its mark (bbox `box`) is exactly mark_h tall and centred on
    (cx, cy). Locking every scene this way lets cuts fly past while the mark never moves.
    Gaps above/below are filled with the edge colour and feathered (reflection would mirror the mark)."""
    x, y, w, h = box; s = mark_h / h; ty = cy - s * (y + h / 2)
    M = np.float32([[s, 0, cx - s * (x + w / 2)], [0, s, ty]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    for top, edge in ((True, int(np.ceil(ty))), (False, int(ty + s * img.shape[0]))):
        if (top and edge > 0) or (not top and edge < H):
            row = min(max(edge + (6 if top else -6), 0), H - 1)
            col = np.median(out[row, W // 2 - 200:W // 2 + 200].reshape(-1, 3), axis=0)
            m = np.clip((edge + 110 - yy) / 120, 0, 1) if top else np.clip((yy - edge + 110) / 120, 0, 1)
            m = (m * m * (3 - 2 * m))[..., None]; out = (out * (1 - m) + col[None, None, :] * m).astype(np.uint8)
    return out

def mark_contours(mask):
    """Vector outline of a mark from a float/uint8 mask (white = mark): a list of point arrays,
    centred on the mark and normalised so its height is 1. Feed to dmask() and trace()."""
    m = mask.astype(np.float32); m = m / m.max()
    ys, xs = np.where(m > 0.5); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); h = y1 - y0 + 1
    k = max(1, int(np.ceil(1200 / h)))
    big = cv2.GaussianBlur(cv2.resize(m, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC), (0, 0), max(k * 0.8, 1))
    cs, _ = cv2.findContours((big > 0.5).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    c0 = np.float32([(x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2])
    return [(c.reshape(-1, 2).astype(np.float32) / k - c0) / h for c in cs if cv2.contourArea(c) > (k * h) ** 2 * 0.002]

def mark_from_image(img, box=None):
    """Contours of a white mark painted in an image (auto-detected unless box is given)."""
    box = box or detect_mark(img)
    if box is None: raise ValueError("no white mark found; pass box=(x, y, w, h)")
    x, y, w, h = box; p = 8; reg = img[max(y - p, 0):y + h + p, max(x - p, 0):x + w + p].astype(np.float32).min(axis=2)
    bg = cv2.GaussianBlur(cv2.erode(reg, np.ones((31, 31), np.uint8)), (0, 0), 20)
    return mark_contours(np.clip((reg - bg - 30) / np.maximum(240 - bg - 30, 1), 0, 1))

def dmask(contours, height, cx, cy, stroke=0, rot=0.0):
    """Antialiased mask of the mark, `height` px tall, centred on (cx, cy). stroke > 0 draws an outline."""
    m = np.zeros((H * 2, W * 2), np.uint8); c, s = np.cos(rot), np.sin(rot); R = np.float32([[c, -s], [s, c]])
    pts = [np.round(((p @ R.T) * height + np.float32([cx, cy])) * 16).astype(np.int32) for p in contours]
    if stroke: cv2.polylines(m, pts, True, 255, int(stroke * 2), cv2.LINE_AA, 3)
    else: cv2.fillPoly(m, pts, 255, cv2.LINE_AA, 3)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

def _arcs(contours):
    out = []
    for c in contours:
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.r_[c, c[:1]], axis=0), axis=1))]; out.append(d / d[-1])
    return out

def trace(contours, p, u, height, cx, cy, colors, sparks=140, seed=9):
    """A line of light draws the mark on black. p = 0..1 progress, u = frame within the shot.
    Returns an additive float layer (use it as the frame, then post()). `colors` is a list of
    BGR colours the glow travels through as p goes 0..1."""
    arcs = _arcs(contours); cen = np.float32([cx, cy]); core = np.zeros((H // 2, W // 2), np.uint8); heads = []
    for c, a in zip(contours, arcs):
        n = min(int(np.searchsorted(a, p)), len(c))
        if n > 1: cv2.polylines(core, [np.round((c[:n] * height + cen) / 2 * 8).astype(np.int32)], p >= 1, 255, 3, cv2.LINE_AA, 3)
        heads.append(c[min(n, len(c) - 1)] * height + cen)
    core = core.astype(np.float32) / 255; hot = np.zeros_like(core); spk = np.zeros_like(core)
    cols = np.float32(colors); q = p * (len(cols) - 1)
    col = sum(cols[j] * max(0, 1 - abs(q - j)) for j in range(len(cols)))
    if 0 < p < 1:
        for h in heads: cv2.circle(hot, (int(h[0] / 2 * 8), int(h[1] / 2 * 8)), 40, 1.0, -1, cv2.LINE_AA, 3)
    r = np.random.default_rng(seed)
    su, ang, v, life, ci = np.sort(r.uniform(0, 1, sparks)), r.uniform(0, 6.28, sparks), r.uniform(1.5, 7, sparks), r.integers(8, 20, sparks), r.integers(0, len(contours), sparks)
    for i in range(sparks):
        age = (p - su[i]) * 56
        if 0 <= age < life[i] and p < 1:
            c = contours[ci[i]]; o = c[min(int(np.searchsorted(arcs[ci[i]], su[i])), len(c) - 1)] * height + cen
            x = o[0] + np.cos(ang[i]) * v[i] * age; y = o[1] + np.sin(ang[i]) * v[i] * age + 0.35 * age * age
            cv2.circle(spk, (int(x / 2 * 8), int(y / 2 * 8)), 12, float(1 - age / life[i]), -1, cv2.LINE_AA, 3)
    glow = cv2.GaussianBlur(core, (0, 0), 5) * 1.3 + cv2.GaussianBlur(core, (0, 0), 22) * 1.6 + cv2.GaussianBlur(hot, (0, 0), 9) * 5 + cv2.GaussianBlur(hot, (0, 0), 40) * 9
    white = cv2.GaussianBlur(core, (0, 0), 1.0) * 1.2 + cv2.GaussianBlur(hot, (0, 0), 3) * 2 + cv2.GaussianBlur(spk, (0, 0), 1.2)
    fill = cv2.resize(dmask(contours, height, cx, cy), (W // 2, H // 2)) * (0.05 * p + 0.5 * ei((p - 0.82) / 0.18, 3))
    lay = glow[..., None] * col * (0.8 + 0.2 * np.sin(u * 1.3)) + (white + fill)[..., None] * 255
    return cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)

def impact(img, u, cx, cy, colors, n=90, seed=12):
    """The hit after a reveal: shockwave ring + burst of petals from (cx, cy). u = frames since the hit.
    Returns the new image. Add your own white flash: img += 255 * np.exp(-u / 4.5)."""
    if u >= 60: return img
    r = np.random.default_rng(seed); a, v, s, ph, ci = r.uniform(0, 6.28, n), r.uniform(9, 46, n), r.uniform(5, 15, n), r.uniform(0, 6, n), r.integers(0, len(colors), n)
    lay = np.zeros((H, W, 3), np.float32); cols = np.float32(colors)
    for i in range(n):
        d = v[i] * (1 - np.exp(-u / 9)) * 10; x = cx + np.cos(a[i]) * d; y = cy + np.sin(a[i]) * d + 0.05 * u * u
        c = tuple(float(q) for q in (cols[ci[i]] * 0.5 + 127) * (1 - u / 60))
        cv2.ellipse(lay, (int(x * 8), int(y * 8)), (int(s[i] * 8), int(s[i] * 3.5)), np.degrees(ph[i] + u * 0.2), 0, 360, c, -1, cv2.LINE_AA, 3)
    img = np.maximum(img, cv2.GaussianBlur(lay, (0, 0), 2))
    ring = np.zeros((H // 2, W // 2), np.float32); cv2.circle(ring, (int(cx / 2), int(cy / 2)), int(60 + u * 36), float(np.exp(-u / 9)), 10, cv2.LINE_AA)
    return img + cv2.resize(cv2.GaussianBlur(ring, (0, 0), 6), (W, H))[..., None] * 380

def shake(img, u, amp=26, decay=6):
    """Decaying camera shake; u = frames since the hit."""
    sh = amp * np.exp(-u / decay)
    if sh < 0.4: return img
    r = np.random.default_rng(u)
    return cv2.warpAffine(img, np.float32([[1, 0, r.normal(0, sh)], [0, 1, r.normal(0, sh)]]), (W, H), borderMode=cv2.BORDER_REFLECT_101)

# ---------- air: petals, birds ----------
def petals(img, f, cols, op=0.85, speed=1.0, n=42, seed=4):
    """Drifting petals/leaves/dust, closed-form in f (so frames can render in any order). In place."""
    r = np.random.default_rng(seed); px, py, pz, ph, sw, ci = r.uniform(0, W + 300, n), r.uniform(0, H + 300, n), r.uniform(0.2, 1, n), r.uniform(0, 6.28, n), r.uniform(0.3, 0.7, n), r.integers(0, 3, n)
    t = f / FPS * speed; lay = np.zeros((H, W, 3), np.uint8); al = np.zeros((H, W), np.uint8)
    for i in range(n):
        z = pz[i]
        x = (px[i] + (60 + 120 * z) * t + 40 * np.sin(t * sw[i] * 2 + ph[i])) % (W + 300) - 150
        y = (py[i] + (30 + 70 * z) * t + 20 * np.sin(t * sw[i] * 3 + ph[i] * 2)) % (H + 300) - 150
        fl = abs(np.cos(t * 4 * sw[i] + ph[i])); s = 4 + 13 * z
        ax = (int(s * 8), int(s * (0.2 + 0.4 * fl) * 8)); ang = np.degrees(ph[i] + t * 1.5); c = tuple(int(q) for q in cols[ci[i] % len(cols)])
        cv2.ellipse(lay, (int(x * 8), int(y * 8)), ax, ang, 0, 360, c, -1, cv2.LINE_AA, 3)
        cv2.ellipse(al, (int(x * 8), int(y * 8)), ax, ang, 0, 360, 255, -1, cv2.LINE_AA, 3)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.6); a = cv2.GaussianBlur(al, (0, 0), 1.6).astype(np.float32)[..., None] / 255 * op
    img[:] = img * (1 - a) + lay.astype(np.float32) * op

def birds(img, f, n=5, x0=-80, y0=620, vx=5.2, vy=-1.1, col=(245, 245, 245), seed=1):
    """A small flock of flapping 'v' birds crossing the sky. In place."""
    r = np.random.default_rng(seed); lay = np.zeros((H, W), np.uint8)
    for i in range(n):
        ox, oy, ph, s = r.uniform(-150, 0), r.uniform(-90, 90), r.uniform(0, 6), r.uniform(11, 19)
        x = x0 + ox + vx * f + i * 44; y = y0 + oy + vy * f + 9 * np.sin(f * 0.11 + ph); fl = np.sin(f * 0.62 + ph) * 0.75
        pts = np.array([[x - s, y - s * fl], [x - s * 0.4, y - s * fl * 0.25 - 2], [x, y], [x + s * 0.4, y - s * fl * 0.25 - 2], [x + s, y - s * fl]])
        cv2.polylines(lay, [np.round(pts * 8).astype(np.int32)], False, 255, 3, cv2.LINE_AA, 3)
    a = cv2.GaussianBlur(lay, (0, 0), 0.8).astype(np.float32)[..., None] / 255 * 0.9
    img[:] = img * (1 - a) + np.float32(col) * a

# ---------- digital effects and wipes ----------
def chroma(img, px=6):
    """Colour-split: red and blue channels pulled apart sideways by px pixels."""
    b, g, r = cv2.split(img); return cv2.merge([np.roll(b, -int(px), 1), g, np.roll(r, int(px), 1)])
def scanlines(img, strength=0.25):
    """Dark horizontal lines every other row, like an old screen."""
    return img * (1 - strength * (0.5 + 0.5 * np.sin(yy * np.pi))[..., None])
def glitch(img, f, amount=0.5, seed=0):
    """Random horizontal bands knocked sideways plus a colour split. Call for 2-4 frames on a beat."""
    r = np.random.default_rng(seed + f); out = img.copy()
    for _ in range(int(2 + 6 * amount)):
        y = int(r.integers(0, H - 10)); h = int(r.integers(6, int(H * 0.06) + 7)); out[y:y + h] = np.roll(out[y:y + h], int(r.normal(0, W * 0.06 * amount)), 1)
    return chroma(out, amount * 10)
def wipe(a, b, p, kind="iris"):
    """Shape wipe from frame a to frame b, p = 0..1. kind: iris, bars, doors, pie, diagonal."""
    p = clamp(p)
    if kind == "iris": v = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
    elif kind == "bars": band = np.floor(yy / (H / 8)); v = np.where(band % 2 == 0, xx / W, 1 - xx / W)
    elif kind == "doors": v = 1 - np.abs(xx - W / 2) / (W / 2)
    elif kind == "pie": v = (np.arctan2(xx - W / 2, -(yy - H / 2)) + np.pi) / (2 * np.pi)
    else: v = xx / W * 0.6 + yy / H * 0.4
    m = np.clip((p * 1.04 - v) * 60, 0, 1)[..., None]; return a * (1 - m) + b * m
def fireflies(img, f, n=26, color=(120, 240, 255), seed=7):
    """Slow glowing dots that drift and pulse (night scenes). In place."""
    r = np.random.default_rng(seed); x0, y0, ph, sp = r.uniform(60, W - 60, n), r.uniform(H * 0.5, H * 0.96, n), r.uniform(0, 6.28, n), r.uniform(0.3, 0.9, n)
    t = f / FPS; q = np.zeros((H // 4, W // 4), np.float32)
    for i in range(n):
        x = x0[i] + 50 * np.sin(t * sp[i] + ph[i]); y = y0[i] + 36 * np.cos(t * sp[i] * 0.8 + ph[i] * 1.3) - 6 * t
        cv2.circle(q, (int(x / 4 * 8), int(y / 4 * 8)), 22, float((0.35 + 0.65 * max(0, np.sin(t * 2.2 * sp[i] + ph[i] * 3))) ** 2), -1, cv2.LINE_AA, 3)
    q = cv2.GaussianBlur(q, (0, 0), 1.6) + 0.6 * cv2.GaussianBlur(q, (0, 0), 6); img += cv2.resize(q, (W, H))[..., None] * np.float32(color)
def stars(img, f, n=40, top=0.35, seed=8):
    """Twinkling stars in the upper part of the frame. In place."""
    r = np.random.default_rng(seed); x0, y0, ph, sp = r.uniform(20, W - 20, n), r.uniform(20, H * top, n), r.uniform(0, 6.28, n), r.uniform(0.5, 1.6, n)
    t = f / FPS; q = np.zeros((H // 4, W // 4), np.float32)
    for i in range(n): cv2.circle(q, (int(x0[i] / 4 * 8), int(y0[i] / 4 * 8)), 9, float((0.25 + 0.75 * max(0, np.sin(t * sp[i] * 2 + ph[i]))) ** 2 * 0.9), -1, cv2.LINE_AA, 3)
    img += cv2.resize(cv2.GaussianBlur(q, (0, 0), 1.4), (W, H))[..., None] * 255

# ---------- CRT terminal opening ----------
def crt(f, lines, mono="/System/Library/Fonts/Menlo.ttc", flash_at=102, phosphor=(205, 255, 150)):
    """An old CRT switches on, types `lines` = [(text, start_frame, frames_per_char)], then blooms to
    white from flash_at over ~24 frames. Rendered at half resolution and scaled up."""
    w, h = W // 2, H // 2
    cy_, cx_ = np.mgrid[0:h, 0:w].astype(np.float32); nx, ny = (cx_ - w / 2) / (w / 2), (cy_ - h / 2) / (h / 2)
    r2 = nx * nx + ny * ny if h >= w else (nx * 0.9) ** 2 + ny ** 2
    sw_ = min(w * 0.78, h * 0.76 * 1.36); sh_ = sw_ / 1.36 if w >= h else min(h * 0.52, sw_ * 1.2)
    scr = np.zeros((h, w), np.float32); cv2.rectangle(scr, (int(w / 2 - sw_ / 2 + 36), int(h / 2 - sh_ / 2 + 36)), (int(w / 2 + sw_ / 2 - 36), int(h / 2 + sh_ / 2 - 36)), 1, -1)
    scr = cv2.GaussianBlur(cv2.dilate(scr, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71))), (0, 0), 5)
    fs = int(max(12, min(31, (sw_ - 150) / ((max(len(t_) for t_, _, _ in lines) + 2) * 0.602))))   # type sized so the longest line fits the screen
    ft = ImageFont.truetype(mono, fs)
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im); x0 = int(w / 2 - sw_ / 2 + 60); y = int(h / 2 - sh_ / 2 + 110); last = (x0, y)
    for txt, t0, sp in lines:
        if f >= t0: s = txt[:int(max(0, (f - t0) / sp))]; d.text((x0, y), s, font=ft, fill=255); last = (x0 + ft.getlength(s), y)
        y += int(fs * 1.87)
    if (f // 7) % 2 == 0 or f > flash_at - 2: d.rectangle((last[0] + 3, last[1] + 3, last[0] + int(fs * 0.65), last[1] + int(fs * 1.1)), fill=255)
    T = np.asarray(im, np.float32) / 255
    lum = T + 0.8 * cv2.GaussianBlur(T, (0, 0), 2.5) + 0.55 * cv2.GaussianBlur(T, (0, 0), 14)
    scan = 0.62 + 0.38 * np.sin(cy_ * np.pi * 0.5) ** 2; roll = 1 + 0.25 * np.exp(-(((cy_ - (f * 8) % (h + 300) + 140) / 55) ** 2))
    on = clamp(f / 10); gate = np.clip((6 + h * 0.55 * eo(on, 3) - np.abs(cy_ - h / 2)) / 6, 0, 1)
    fl = 0.93 + 0.07 * np.sin(f * 2.1) + (0.5 * np.exp(-f / 3) if f < 12 else 0)
    v = ((lum * 1.15 + 0.085 + 0.04 * np.random.default_rng(f).random((h, w)).astype(np.float32)) * scan * roll * fl * gate) * scr * (1 - 0.35 * r2)
    bx, by = w / 2 + nx * (1 + 0.09 * r2) * (w / 2) * 0.95, h / 2 + ny * (1 + 0.09 * r2) * (h / 2) * 0.95
    v = cv2.remap(v, bx, by, cv2.INTER_LINEAR); rim = np.clip(cv2.remap(scr, bx, by, cv2.INTER_LINEAR), 0, 1)
    rim = np.clip(cv2.GaussianBlur(rim, (0, 0), 22) - rim, 0, 1) * 0.22 * on
    col = v[..., None] * np.float32(phosphor) + rim[..., None] * np.float32((150, 200, 215))
    z = 1.0 + 0.16 * (f / (flash_at + 26)) ** 1.6 + 0.9 * ei((f - flash_at - 2) / 24, 3)
    M = np.float32([[2 * z, 0, W / 2 * (1 - z)], [0, 2 * z, H / 2 * (1 - z)]])
    return cv2.warpAffine(col, M, (W, H), flags=cv2.INTER_CUBIC) + 255 * ei((f - flash_at) / 24, 2.5)

# ---------- finishing ----------
def post(img, f, bloom=1.0, grain=0.016, vignette=1.0, tint=1.0, fringe=1.0, contrast=1.0, streak=1.0, warmth=0.0, sat=1.0):
    """Film finish, applied once per frame, last, then fades. Every part has its own strength (0 = off, 1 = the classic look):
    bloom (glow on highlights) and streak (wide lens streak), fringe (colour fringing toward the edges), contrast (soft
    shoulder and S-curve), tint (cool shadows, warm highlights), warmth (-1 cool ... +1 warm overall), sat (colour amount),
    vignette (darker corners), grain. With everything at 0 the picture passes through untouched."""
    if bloom > 0:
        sm = cv2.resize(img, (W // 6, H // 6), interpolation=cv2.INTER_AREA) / 255
        hi = np.clip(sm.min(axis=2) * 0.5 + sm.max(axis=2) * 0.5 - 0.80, 0, 1)[..., None] * sm * 3.0
        bl = cv2.GaussianBlur(hi, (0, 0), 7) + 0.6 * cv2.GaussianBlur(hi, (0, 0), 22) * np.float32((0.75, 0.85, 1.25))
        add = bl * 0.32
        if streak > 0: add = add + cv2.blur(cv2.blur(hi, (151, 1)), (101, 3)) * np.float32((1.3, 1.0, 0.75)) * 1.5 * 0.16 * streak
        img = img + cv2.resize(add, (W, H), interpolation=cv2.INTER_LINEAR) * 255 * bloom
    if fringe > 0:
        b, g, r = cv2.split(img); k = 0.003 * fringe
        r = cv2.warpAffine(r, np.float32([[1 + k, 0, -W / 2 * k], [0, 1 + k, -H / 2 * k]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
        b = cv2.warpAffine(b, np.float32([[1 - k, 0, W / 2 * k], [0, 1 - k, H / 2 * k]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
        img = cv2.merge([b, g, r])
    x = np.clip(img / 255, 0, 1.6)
    if contrast > 0:
        y = x / (1 + 0.18 * x) * 1.18; y = y * y * (3 - 2 * np.clip(y, 0, 1)) * 0.35 + y * 0.65; x = x + (y - x) * contrast
    if tint or warmth or sat != 1.0:
        l = x.mean(axis=2, keepdims=True)
        if sat != 1.0: x = l + (x - l) * sat
        if tint: x = x + ((1 - l) * np.float32((0.022, 0.008, -0.012)) + l * np.float32((-0.012, 0.004, 0.02))) * tint
        if warmth: x = x * (1 + np.float32((-0.07, 0.0, 0.06)) * warmth)
    if vignette > 0: x = x * (1 - vignette * (1 - VIG))
    if grain > 0: x = x + np.random.default_rng(1000 + f).normal(0, grain, (H, W, 1)).astype(np.float32) * (1.15 - 0.6 * x.mean(axis=2, keepdims=True))
    return x * 255

# ---------- render driver ----------
# ---------- going easy on the machine ----------
def gentle_workers():
    """How many render processes to run at once: the fast cores minus one (so the machine stays usable and cool),
    never more than 8. JOYBOY_JOBS=<n> overrides it."""
    if os.environ.get("JOYBOY_JOBS"): return max(1, int(os.environ["JOYBOY_JOBS"]))
    perf = None
    if sys.platform == "darwin":
        try: perf = int(subprocess.run(["sysctl", "-n", "hw.perflevel0.physicalcpu"], capture_output=True, text=True).stdout.strip())
        except Exception: perf = None
    return max(2, min(8, (perf or max(2, (os.cpu_count() or 4) // 2)) - 1))
def heat():
    """How hot the machine is: 'ok', or 'hot' when the system is slowing the processor down to cool off
    (macOS: pmset reports a CPU speed limit under 100 or a thermal warning; Linux: a sensor above 88 C)."""
    try:
        if sys.platform == "darwin":
            o = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True, timeout=5).stdout
            lim = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", o); warn = re.search(r"Thermal Warning Level\s*=\s*(\d+)", o)   # absent ("no ... has been recorded") = fine
            return "hot" if (lim and int(lim.group(1)) < 100) or (warn and int(warn.group(1)) > 0) else "ok"
        import glob
        t = [int(open(f).read()) / 1000 for f in glob.glob("/sys/class/thermal/thermal_zone*/temp")]
        return "hot" if t and max(t) > 88 else "ok"
    except Exception: return "ok"
_cool = {"t": 0.0, "paused": 0.0}
def cool_down(every=4.0, max_wait=90.0):
    """Call often from a long job. Every few seconds it checks the heat; while the machine is hot it waits (up to
    max_wait) so the fans can catch up, then carries on. Picture and sound are not changed, only the pace.
    JOYBOY_COOL=0 turns it off. Returns the seconds waited."""
    import time
    if os.environ.get("JOYBOY_COOL") == "0" or time.time() - _cool["t"] < every: return 0.0
    _cool["t"] = time.time(); t0 = time.time()
    while heat() == "hot" and time.time() - t0 < max_wait: time.sleep(3)
    w = time.time() - t0; _cool["paused"] += w if w > 1 else 0; _cool["t"] = time.time(); return w

def run(frame, total, out, audio=None, crf=20, workers=None):
    """CLI for a film script. `frame(f)` returns uint8 BGR (H, W, 3).
      python film.py sheet out.jpg 0 40 80 ...   contact sheet of chosen frames (do this first, and look at it)
      python film.py                              render everything in parallel chunks, then mux with `audio`
      python film.py chunk i n                    (internal) render chunk i of n
    Frames must depend only on f, never on previous frames, because chunks render out of order."""
    a = sys.argv[1:]; tmp = os.path.splitext(out)[0]
    if a and a[0] == "sheet":
        fs = [int(v) for v in a[2:]]; tw = 324 if H > W else 640; th = int(tw * H / W); cols = 8 if H > W else 4
        ims = [cv2.copyMakeBorder(cv2.resize(frame(f), (tw - 8, th - 8)), 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(40, 40, 40)) for f in fs]   # gutter between cells
        for im, f in zip(ims, fs): cv2.putText(im, str(f), (8, 24), 0, 0.7, (0, 255, 255), 2)
        while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(a[1], np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 86]); return
    if a and a[0] == "chunk":
        i, n = int(a[1]), int(a[2]); f0, f1 = total * i // n, total * (i + 1) // n
        try: os.nice(8)                                   # render below everything else, so the machine stays responsive
        except Exception: pass
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-threads", "2", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                               "-c:v", "libx264", "-crf", str(crf), "-maxrate", "14M", "-bufsize", "28M", "-preset", "medium", "-pix_fmt", "yuv420p", "-bsf:v", "h264_mp4toannexb", "-f", "mpegts", f"{tmp}.{i:02d}.ts"], stdin=subprocess.PIPE)
        for f in range(f0, f1): ff.stdin.write(np.ascontiguousarray(frame(f)).tobytes()); cool_down()
        ff.stdin.close(); ff.wait()
        if _cool["paused"] > 1: print(f"chunk {i}: paused {_cool['paused']:.0f}s to let the machine cool")
        return
    n = workers or gentle_workers()
    ps = [subprocess.Popen([sys.executable, sys.argv[0], "chunk", str(i), str(n)]) for i in range(n)]
    if any(p.wait() for p in ps): sys.exit("a chunk failed; run `chunk i n` directly to see the error")
    parts = [f"{tmp}.{i:02d}.ts" for i in range(n)]; cmd = ["ffmpeg", "-v", "error", "-y", "-i", "concat:" + "|".join(parts)]
    cmd += (["-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k"] if audio else ["-c:v", "copy"]) + ["-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    for p in parts: os.remove(p)
    print(out, total, "frames", f"{total / FPS:.1f}s")
