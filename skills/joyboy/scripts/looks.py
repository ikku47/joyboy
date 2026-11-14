"""joyboy looks: screen-space print, sensor and film looks that turn any finished frame into another medium.

    Film("x", fx="riso")                                   a name, with its default settings
    Film("x", fx=("riso", {"inks": ("#ff48b0", "#0078bf")}))   a name with settings

Print:    riso (two spot inks overprinted, halftone, misregistration), halftone (four-plate dots), dither (two inks, ordered dither),
          engrave (hatching by tone), bands (flat stepped colour, silkscreen), duotone (two-colour gradient map)
Sensors:  thermal (heat palette, sensor noise), xray (dual-energy colours), ascii (a grid of glyphs)
Film:     film (silent-film flicker, weave, scratches, silver tone), cel (flat two-step shading with ink outlines), tiltshift (miniature blur band)

Each look is a function (img, f, U, fps, **settings) on a float32 BGR frame, 0..255. They depend only on the frame number f, so any frame renders alone.
Dots, hatching and grain are fixed to the screen (the paper), not to the picture, like a print that is made again for every frame.
"""
import numpy as np, cv2

_cache = {}
def _hex(c):
    if isinstance(c, str): c = c.lstrip("#"); return np.float32([int(c[4:6], 16), int(c[2:4], 16), int(c[0:2], 16)])
    return np.float32(c)

def _grid(H, W, angle, period):
    k = (H, W, round(angle, 2), round(period, 2))
    if k not in _cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); a = np.deg2rad(angle); u = (xx * np.cos(a) + yy * np.sin(a)) / period; v = (-xx * np.sin(a) + yy * np.cos(a)) / period; _cache[k] = (u, v)
    return _cache[k]

def _noise(H, W, seed, scale=1.0):
    k = ("n", H, W, seed, scale)
    if k not in _cache:
        r = np.random.default_rng(seed); n = r.standard_normal((max(2, int(H / scale)), max(2, int(W / scale)))).astype(np.float32); _cache[k] = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR) if scale > 1 else n
    return _cache[k]

def _lum(img): return (img @ np.float32((0.114, 0.587, 0.299))) / 255.0

def _dots(d, angle, period, H, W, soft=1.0):
    """Halftone coverage 0..1 for a density field d (0..1): round dots on a screen rotated by `angle`, dot size grows with density."""
    u, v = _grid(H, W, angle, period); cell = (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)) * 0.25 + 0.5          # 1 at the dot centre, 0 between dots
    return np.clip((d - (1 - cell)) * (period * 0.9 * soft) + 0.5, 0, 1) * (d > 0.02)

def _shift(plate, dx, dy):
    if dx == 0 and dy == 0: return plate
    return cv2.warpAffine(plate, np.float32([[1, 0, dx], [0, 1, dy]]), (plate.shape[1], plate.shape[0]), borderMode=cv2.BORDER_REPLICATE)

def _paper(H, W, color, grain=6.0):
    base = np.broadcast_to(_hex(color), (H, W, 3)).astype(np.float32).copy(); return base + (_noise(H, W, 5, 2.0) * grain + _noise(H, W, 6, 1.0) * grain * 0.5)[..., None]

# ---------------------------------------------------------------------------------------------------- print
def riso(img, f, U, fps, inks=("#ff48b0", "#0078bf"), paper="#f1ead8", period=7.0, mis=3.0, grain=0.12):
    """Two translucent spot inks on warm paper. Shadows go to the second ink, warm and red areas to the first; overlaps print darker."""
    H, W = img.shape[:2]; L = _lum(img); red = np.clip((img[..., 2] - (img[..., 0] + img[..., 1]) / 2) / 255.0 * 2.2, 0, 1); p = period * U
    d2 = np.clip((1 - L) * 1.25 - 0.08, 0, 1); d1 = np.clip(red * 1.2 + (1 - L) * 0.35 * (1 - red), 0, 1)
    n = _noise(H, W, 9, 1.0) * grain; c1 = _dots(np.clip(d1 + n, 0, 1), 15, p, H, W); c2 = _dots(np.clip(d2 + n, 0, 1), 75, p, H, W)
    c1 = _shift(c1, mis * U, -mis * 0.5 * U); c2 = _shift(c2, -mis * 0.5 * U, mis * U); out = _paper(H, W, paper)
    for cov, ink in ((c1, _hex(inks[0])), (c2, _hex(inks[1]))): out = out * (1 - cov[..., None] * (1 - ink / 255.0))
    return out

def halftone(img, f, U, fps, paper="#f3ecda", period=9.0, plates=None):
    """Four-plate dots (cyan, magenta, yellow, black) on cream paper: the Ben-Day / newspaper look."""
    H, W = img.shape[:2]; x = np.clip(img / 255.0, 0, 1); b, g, r = x[..., 0], x[..., 1], x[..., 2]; k = 1 - np.maximum(np.maximum(r, g), b); den = np.maximum(1 - k, 1e-3)
    cy, cm, cyel = (1 - r - k) / den, (1 - g - k) / den, (1 - b - k) / den; p = period * U; out = _paper(H, W, paper)
    inks = plates or ((200, 150, 0), (140, 20, 220), (20, 215, 245), (22, 20, 20))
    for d, ang, ink in ((cy, 15, inks[0]), (cm, 75, inks[1]), (cyel, 0, inks[2]), (k, 45, inks[3])):
        cov = _dots(np.clip(d, 0, 1), ang, p, H, W); out = out * (1 - cov[..., None] * (1 - np.float32(ink) / 255.0 * 0.92))
    return out

_BAYER = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
                   [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25], [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]], np.float32) / 64.0
def dither(img, f, U, fps, ink="#0d0d12", paper="#ece7d6", cell=2.0, gamma=1.0, contrast=1.15):
    """Exactly two inks. Every grey becomes a fixed pattern of dots (ordered dither); the pattern belongs to the screen, so it does not crawl."""
    H, W = img.shape[:2]; c = max(1, int(round(cell * U))); L = np.clip((_lum(img) - 0.5) * contrast + 0.5, 0, 1) ** gamma
    k = ("bayer", H, W, c)
    if k not in _cache:
        yy, xx = np.mgrid[0:H, 0:W]; _cache[k] = _BAYER[(yy // c) % 8, (xx // c) % 8]
    on = L > _cache[k]; return np.where(on[..., None], _hex(paper), _hex(ink)).astype(np.float32)

def engrave(img, f, U, fps, ink="#1c1510", paper="#f1e8d2", spacing=6.0, outline=True):
    """Hatching by tone: darker areas get more crossing line families, lines swell where it is darkest. Paper and lines are fixed to the screen."""
    H, W = img.shape[:2]; L = np.clip(_lum(cv2.GaussianBlur(img, (0, 0), 1.2 * U + 0.3)), 0, 1); s = spacing * U; out = _paper(H, W, paper, 4.0); cov = np.zeros((H, W), np.float32)
    for ang, thr in ((45, 0.78), (-45, 0.52), (0, 0.30), (90, 0.16)):
        u, _ = _grid(H, W, ang, s); w = np.clip((thr - L) / max(thr, 0.01), 0, 1) * 0.62; line = np.abs(((u % 1.0) + 1) % 1.0 - 0.5) < (w * 0.5); cov = np.maximum(cov, line.astype(np.float32))
    cov = cv2.GaussianBlur(cov, (0, 0), 0.6)
    if outline:
        e = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY), (0, 0), 1.2), 60, 140).astype(np.float32) / 255.0; cov = np.maximum(cov, cv2.GaussianBlur(e, (0, 0), 0.7) * 0.9)
    return out * (1 - cov[..., None] * (1 - _hex(ink) / 255.0))

def bands(img, f, U, fps, palette=("#14213d", "#2b4c7e", "#e07a5f", "#f2cc8f", "#f4f1de"), edge=True):
    """Flat stepped colour, no gradients: the picture is cut into as many bands as there are colours (silkscreen, poster)."""
    L = np.clip(_lum(cv2.GaussianBlur(img, (0, 0), 1.0)), 0, 0.999); n = len(palette); idx = (L * n).astype(int); pal = np.stack([_hex(c) for c in palette]); out = pal[idx]
    if edge: out = out * (1 - 0.55 * (np.abs(cv2.Laplacian(idx.astype(np.float32), cv2.CV_32F)) > 0.5)[..., None] * 0.0)
    return out.astype(np.float32)

def duotone(img, f, U, fps, dark="#101a3a", light="#ffd9a0", grain=0.03):
    """Brightness mapped onto a gradient between two colours (shadow ink to light ink)."""
    L = np.clip(_lum(img) + _noise(*img.shape[:2], 3, 1.0) * grain, 0, 1)[..., None]; return _hex(dark) * (1 - L) + _hex(light) * L

# ---------------------------------------------------------------------------------------------------- sensors
def thermal(img, f, U, fps, sensor=3.0, noise=0.025, palette="inferno"):
    """A heat-camera picture: brightness read as temperature, a low sensor grid, a little sensor noise and fixed-pattern columns."""
    H, W = img.shape[:2]; L = np.clip(_lum(cv2.GaussianBlur(img, (0, 0), 1.5 * U)), 0, 1); s = max(1, int(sensor * U)); small = cv2.resize(L, (max(W // s, 8), max(H // s, 8)), interpolation=cv2.INTER_AREA)
    r = np.random.default_rng(f); small = small + r.standard_normal(small.shape).astype(np.float32) * noise + (_noise(small.shape[0], small.shape[1], 7, 1.0)[:1] * 0.012)
    g = np.clip(small * 255, 0, 255).astype(np.uint8); cm = {"inferno": cv2.COLORMAP_INFERNO, "magma": cv2.COLORMAP_MAGMA, "turbo": cv2.COLORMAP_TURBO, "hot": cv2.COLORMAP_HOT}.get(palette, cv2.COLORMAP_INFERNO)
    return cv2.resize(cv2.applyColorMap(g, cm), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)

def xray(img, f, U, fps, bg="#0b1530"):
    """A baggage-scanner picture: thin things orange, middling green, thick blue, very thick black, on a navy belt; edges enhanced."""
    H, W = img.shape[:2]; t = np.clip(1 - _lum(cv2.GaussianBlur(img, (0, 0), 1.0 * U)), 0, 1)                    # thickness
    hue = np.clip(t * 2.0, 0, 2); orange, green, blue = np.float32((20, 140, 255)), np.float32((90, 220, 90)), np.float32((230, 120, 40))
    col = np.where((hue < 1)[..., None], orange * (1 - hue)[..., None] + green * hue[..., None], green * (2 - hue)[..., None] + blue * (hue - 1)[..., None]); lit = np.clip(np.clip(np.sin(np.pi * np.clip(t * 1.05, 0, 1)), 0, 1) ** 0.7 * 1.25, 0, 1)[..., None]
    edge = np.clip(np.abs(cv2.Laplacian(t, cv2.CV_32F, ksize=3)) * 8, 0, 1)[..., None] * 90; out = _hex(bg) * (1 - lit) + col * lit + edge
    return out + _noise(H, W, 8, 1.0)[..., None] * 3.0

_ASCII = {}
def ascii_art(img, f, U, fps, ink="#7dff9a", paper="#050a06", cell=9.0, ramp=" .:-=+*#%@"):
    """The picture is rebuilt from characters on a monospace grid: density of glyph follows brightness."""
    H, W = img.shape[:2]; cw = max(4, int(cell * U)); ch = cw * 2; k = (cw, ch, ramp)
    if k not in _ASCII:
        atlas = np.zeros((len(ramp), ch, cw), np.uint8)
        for i, c in enumerate(ramp): cv2.putText(atlas[i], c, (0, int(ch * 0.82)), cv2.FONT_HERSHEY_SIMPLEX, cw / 20.0, 255, max(1, cw // 8), cv2.LINE_AA)
        _ASCII[k] = atlas.astype(np.float32) / 255.0
    atlas = _ASCII[k]; gh, gw = H // ch, W // cw; small = cv2.resize(_lum(img), (gw, gh), interpolation=cv2.INTER_AREA); idx = np.clip((np.clip(small * 1.5, 0, 1) ** 0.55 * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)
    mask = atlas[idx].transpose(0, 2, 1, 3).reshape(gh * ch, gw * cw); out = np.broadcast_to(_hex(paper), (H, W, 3)).astype(np.float32).copy(); m = np.zeros((H, W), np.float32); m[:gh * ch, :gw * cw] = mask
    glow = cv2.GaussianBlur(m, (0, 0), 2.0 * U + 0.5); return out + (m * 1.1 + glow * 0.55)[..., None] * _hex(ink)

# ---------------------------------------------------------------------------------------------------- film
def film(img, f, U, fps, tone="#d8c9a8", flicker=0.07, scratches=6, dust=40):
    """A silent-film print: silver tone, brightness flicker, gate weave, vertical scratches and dust that change every other frame."""
    H, W = img.shape[:2]; r = np.random.default_rng(f // 2); g = np.clip(_lum(img) * (1 + flicker * (r.random() - 0.5) * 2), 0, 1)[..., None]
    out = np.float32((15, 14, 12)) * (1 - g) + _hex(tone) * g; out = cv2.warpAffine(out, np.float32([[1, 0, r.normal(0, 1.2) * U], [0, 1, r.normal(0, 1.5) * U]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    for _ in range(int(r.integers(0, scratches))): x = int(r.integers(0, W)); out[:, max(x - 1, 0):x + 1] = out[:, max(x - 1, 0):x + 1] * 0.35 + 255 * 0.55
    for _ in range(int(r.integers(0, dust))): cv2.circle(out, (int(r.integers(0, W)), int(r.integers(0, H))), int(r.integers(1, 3)), (30, 30, 30) if r.random() < 0.6 else (230, 230, 225), -1)
    vig = 1 - 0.55 * np.clip(((np.arange(W) - W / 2) / (W * 0.7)) ** 2 + (((np.arange(H) - H / 2) / (H * 0.7)) ** 2)[:, None], 0, 1.2)[..., None]; return out * vig

def cel(img, f, U, fps, steps=3, outline=2.0, sat=1.25):
    """Flat cel shading: the brightness is cut into a few hard steps, colours are boosted, and a dark ink outline is drawn at the edges."""
    u8 = np.clip(img, 0, 255).astype(np.uint8); hsv = cv2.cvtColor(u8, cv2.COLOR_BGR2HSV).astype(np.float32); v = hsv[..., 2] / 255.0; q = (np.floor(v * steps + 0.35) / steps).clip(0.12, 1.0)
    hsv[..., 2] = q * 255; hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255); out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    e = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(u8, cv2.COLOR_BGR2GRAY), (0, 0), 1.4), 50, 120); e = cv2.dilate(e, np.ones((max(1, int(outline * U)),) * 2, np.uint8)); return np.where(e[..., None] > 0, np.float32((18, 16, 20)), out)

def tiltshift(img, f, U, fps, centre=0.55, band=0.18, blur=9.0, sat=1.35):
    """The miniature look: a sharp band across the picture and a strong blur above and below it, with boosted colour."""
    H, W = img.shape[:2]; yy = (np.arange(H, dtype=np.float32) / H)[:, None]; m = np.clip((np.abs(yy - centre) - band) / 0.30, 0, 1) ** 1.2
    bl = cv2.GaussianBlur(img, (0, 0), blur * U); out = img * (1 - m[..., None]) + bl * m[..., None]; hsv = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255); return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

LOOKS = dict(riso=riso, halftone=halftone, dither=dither, engrave=engrave, bands=bands, duotone=duotone, thermal=thermal, xray=xray, ascii=ascii_art, film=film, cel=cel, tiltshift=tiltshift)
