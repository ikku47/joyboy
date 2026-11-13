"""joyboy sitekit: work with a real website in a video. The page is downloaded once (site_save.mjs) as a sharp image
of the whole page plus the position and words of every notable element, so shots can move to an element, light it,
lift it off the page, label it and click it.

    s = film.site("https://example.com")                 # downloads and caches the page (desktop; or device="mobile")
    s.show()                                             # print the elements: id, kind, words
    s.overview("work/site.jpg")                          # the page with every element numbered, to look at
    s.shot(dur=3, text="This is the home page")          # the top of the page
    s.shot(focus="Pricing", label="Three plans", voice="Pick the plan that fits.")     # move to an element and light it
    s.shot(focus=12, lift=True, click=True)              # by id; lift it off the page, click it
    s.shot(scroll=(0.2, 0.6), dur=4)                     # a plain scroll between two points of the page

Each shot is one scene and carries on from where the last one ended, so the camera travels over the page.
The page's own title, colours and fonts are in s.meta (use them so the video matches the site)."""
import os, sys, json, hashlib, subprocess
import numpy as np, cv2
import joyboy as jb
from joyboy import eo, eio, clamp, spring
HOME = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); KIT = os.path.join(HOME, "web")

def _rgb(css):
    """'rgb(1, 2, 3)' -> BGR float array."""
    import re
    v = [float(x) for x in re.findall(r"[\d.]+", css or "")[:3]]
    return np.float32(v[::-1]) if len(v) == 3 else np.float32((255, 255, 255))

class Site:
    def __init__(self, film, url, device="desktop"):
        self.film, self.url, self.device = film, url, device
        self.dir = os.path.join(HOME, "captures", "sites", hashlib.md5(f"{url}|{device}".encode()).hexdigest()[:12])
        if not os.path.exists(os.path.join(self.dir, "elements.json")):
            if not os.path.exists(os.path.join(KIT, "site_save.mjs")): sys.exit("joyboy: the web kit is not set up; run setup.sh (needs node and a Chrome-family browser)")
            r = subprocess.run(["node", os.path.join(KIT, "site_save.mjs"), url, self.dir, device], cwd=KIT, capture_output=True, text=True)
            if not os.path.exists(os.path.join(self.dir, "elements.json")): sys.exit("joyboy: could not download " + url + " " + (r.stderr or r.stdout).strip()[:300])
            print((r.stdout.strip().splitlines() or ["saved"])[-1])
        self.meta = json.load(open(os.path.join(self.dir, "elements.json"))); self.els = self.meta["elements"]; self.sc = float(self.meta["scale"])
        self.bg = _rgb(self.meta["colors"]["background"]); self._pyr = None; self.state = None
    # ----- looking at the page -----
    def _levels(self):
        """The page image at full, half and quarter size, so zoomed-out views stay clean."""
        if self._pyr is None:
            P = cv2.imread(os.path.join(self.dir, "page.png")); self._pyr = [(P, 1.0)]
            for _ in range(2): P = cv2.resize(P, (P.shape[1] // 2, P.shape[0] // 2), interpolation=cv2.INTER_AREA); self._pyr.append((P, self._pyr[-1][1] / 2))
        return self._pyr
    def elements(self, kind=None, contains=None):
        """Elements, optionally of one kind (heading, text, button, link, image, card, section, input, nav, footer, block) or containing words."""
        return [e for e in self.els if (not kind or e["kind"] == kind) and (not contains or contains.lower() in e["text"].lower())]
    def show(self, kind=None, limit=120):
        """Print the page's elements: id, kind, position and words. Read this before choosing what to focus on."""
        m = self.meta; print(f'{m["title"]}  ({m["width"]}x{m["height"]}, {len(self.els)} elements)  colours {m["colors"]}  fonts {m["fonts"]}')
        for e in self.elements(kind)[:limit]: r = e["rect"]; print(f'  {e["id"]:3d}  {e["kind"]:8s} y={r["y"]:5d} {r["w"]:4d}x{r["h"]:<4d} {e["text"][:70]}')
    def find(self, what):
        """An element by id (a number), or the first whose words contain the text; headings and buttons win over longer text."""
        if isinstance(what, dict): return what
        if isinstance(what, int): return self.els[what]
        hits = self.elements(contains=str(what))
        if not hits: sys.exit(f'joyboy: nothing on {self.url} contains "{what}". Run s.show() to see what is there.')
        rank = {"heading": 0, "button": 1, "card": 2, "link": 3, "image": 4, "input": 5, "text": 6, "block": 7, "section": 8, "nav": 9, "footer": 9}
        return sorted(hits, key=lambda e: (rank.get(e["kind"], 9), len(e["text"])))[0]
    def overview(self, out="work/site.jpg", width=1400):
        """Save the whole page with every element outlined and numbered, so you can see which id is which."""
        P = self._levels()[0][0]; k = width / P.shape[1]; im = cv2.resize(P, (width, int(P.shape[0] * k)), interpolation=cv2.INTER_AREA)
        col = {"heading": (60, 60, 230), "button": (40, 170, 60), "image": (220, 140, 30), "card": (200, 60, 200)}
        for e in self.els:
            r = e["rect"]; x, y, w, h = [int(v * self.sc * k) for v in (r["x"], r["y"], r["w"], r["h"])]; c = col.get(e["kind"], (150, 150, 150))
            cv2.rectangle(im, (x, y), (x + w, y + h), c, 1); cv2.rectangle(im, (x, y), (x + 9 * len(str(e["id"])) + 6, y + 15), c, -1); cv2.putText(im, str(e["id"]), (x + 3, y + 12), 0, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True); cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 85]); return out
    # ----- camera -----
    def _fit(self, cx, cy, k):
        """Keep the view inside the page."""
        P = self._levels()[0][0]; W, H = self.film.W, self.film.H; hw, hh = W / 2 / k, H / 2 / k
        cx = P.shape[1] / 2 if 2 * hw >= P.shape[1] else min(max(cx, hw), P.shape[1] - hw); cy = P.shape[0] / 2 if 2 * hh >= P.shape[0] else min(max(cy, hh), P.shape[0] - hh)
        return cx, cy, k
    def _view(self, cx, cy, k):
        """One frame of the page seen with centre (cx, cy) in page pixels and k frame pixels per page pixel."""
        W, H = self.film.W, self.film.H; im, ls = next(((im, ls) for im, ls in reversed(self._levels()) if k / ls <= 1.0), self._levels()[0]); kk = k / ls
        M = np.float32([[kk, 0, W / 2 - cx * ls * kk], [0, kk, H / 2 - cy * ls * kk]])
        return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=tuple(float(v) for v in self.bg)).astype(np.float32)
    def _target(self, e, zoom):
        P = self._levels()[0][0]; W, H = self.film.W, self.film.H; k0 = W / P.shape[1]; r = e["rect"]; ew, eh = max(r["w"] * self.sc, 1), max(r["h"] * self.sc, 1)
        k = min(max(min(W * 0.80 / ew, H * 0.52 / eh), k0), k0 * 2.6) * zoom
        return self._fit((r["x"] + r["w"] / 2) * self.sc, (r["y"] + r["h"] / 2) * self.sc, k)
    def _mask(self, x0, y0, x1, y1, radius=18):
        """A soft-cornered box as a 0..1 mask the size of the frame."""
        W, H = self.film.W, self.film.H; x0, y0, x1, y1 = int(max(x0, -50)), int(max(y0, -50)), int(min(x1, W + 50)), int(min(y1, H + 50)); m = np.zeros((H, W), np.float32)
        if x1 <= x0 or y1 <= y0: return m
        r_ = int(min(radius * self.film.U, (x1 - x0) / 2, (y1 - y0) / 2)); cv2.rectangle(m, (x0 + r_, y0), (x1 - r_, y1), 1, -1); cv2.rectangle(m, (x0, y0 + r_), (x1, y1 - r_), 1, -1)
        for px, py in ((x0 + r_, y0 + r_), (x1 - r_, y0 + r_), (x0 + r_, y1 - r_), (x1 - r_, y1 - r_)): cv2.circle(m, (px, py), r_, 1, -1, cv2.LINE_AA)
        return m
    # ----- shots -----
    def shot(self, focus=None, label=None, lift=False, click=False, zoom=1.0, scroll=None, dur=3.5, text=None, dim=0.55, **k):
        """One shot of the page = one scene; takes voice, pace, tr, note and sfx like any scene.
        focus    an element (id, or words it contains): the camera travels to it and lights it while the rest dims.
        label    a short tag shown beside the element.      lift   the element rises off the page with a shadow.
        click    a cursor arrives and clicks it.             zoom   more than 1 goes closer.      dim   how dark the rest goes (0 = no spotlight).
        scroll   (from, to) as fractions of the page, for a plain scroll with no focus.   text   a caption at the bottom."""
        film = self.film; W, H, U = film.W, film.H, film.U; P = self._levels()[0][0]; k0 = W / P.shape[1]; top = self._fit(P.shape[1] / 2, 0, k0)
        A = self.state or top; e = self.find(focus) if focus is not None else None
        if e is not None: B = self._target(e, zoom)
        elif scroll: span = max(P.shape[0] - H / k0, 0); A = self._fit(P.shape[1] / 2, H / 2 / k0 + span * scroll[0], k0); B = self._fit(P.shape[1] / 2, H / 2 / k0 + span * scroll[1], k0)
        else: B = top
        self.state = B; fps = film.fps; move = 0 if (scroll or A == B) else int(min(1.2, dur * 0.4) * fps); acc = film._c(0)
        cues = ([(0.0, "whoosh", 0.5)] if move else []) + ([((move + 6) / fps, "pop")] if label else []) + ([((move + 20) / fps, "click")] if click else [])
        def draw(u, n, f):
            t = eio(u / max(n - 1, 1)) if scroll else (eio(u / move) if move else 1.0); cx, cy, kk = (A[i] + (B[i] - A[i]) * t for i in range(3)); img = self._view(cx, cy, kk)
            if e is not None:
                r = e["rect"]; x0 = W / 2 + (r["x"] * self.sc - cx) * kk; y0 = H / 2 + (r["y"] * self.sc - cy) * kk; w_, h_ = r["w"] * self.sc * kk, r["h"] * self.sc * kk; pad = 14 * U
                v = eio((u - move * 0.6) / 12) * (1 - eio((u - (n - 8)) / 8)); m = self._mask(x0 - pad, y0 - pad, x0 + w_ + pad, y0 + h_ + pad)
                if lift and v > 0:
                    xa, ya, xb, yb = [int(q) for q in (max(x0 - pad, 0), max(y0 - pad, 0), min(x0 + w_ + pad, W), min(y0 + h_ + pad, H))]
                    if xb > xa and yb > ya:
                        s_ = 1 + 0.06 * v; crop = img[ya:yb, xa:xb].copy(); big = cv2.resize(crop, (int((xb - xa) * s_), int((yb - ya) * s_)), interpolation=cv2.INTER_LINEAR)
                        sh = cv2.GaussianBlur(np.roll(m, int(16 * U * v), 0), (0, 0), 22 * U + 1)[..., None]; img = img * (1 - 0.5 * v * sh)
                        bx, by = int((xa + xb) / 2 - big.shape[1] / 2), int((ya + yb) / 2 - big.shape[0] / 2 - 6 * U * v); x1, y1 = max(bx, 0), max(by, 0); x2, y2 = min(bx + big.shape[1], W), min(by + big.shape[0], H)
                        if x2 > x1 and y2 > y1: img[y1:y2, x1:x2] = big[y1 - by:y2 - by, x1 - bx:x2 - bx]; m = self._mask(x1, y1, x2, y2)
                if dim: soft = cv2.GaussianBlur(m, (0, 0), 6 * U + 1)[..., None]; img = img * (1 - dim * v * (1 - soft))
                if label:
                    lv = u - move - 6
                    if lv > 0:
                        g = float(spring(lv / fps * 1.8, 1.8, 5.5)) * (1 - eio((u - (n - 8)) / 8)); lw = film._len(label, 40, True) + 56 * U; lh = 70 * U
                        ly = y0 - pad - lh - 14 * U if y0 - pad - lh - 14 * U > 20 * U else min(y0 + h_ + pad + 14 * U, H - lh - 20 * U); lx = min(max(x0 + w_ / 2 - lw / 2, 20 * U), W - lw - 20 * U); ly += (1 - min(g, 1)) * 14 * U
                        film.card(img, lx, ly, lx + lw, ly + lh, acc, radius=35, op=clamp(g)); film.ltext(img, label, lx + lw / 2, ly + lh / 2, 40, True, clamp(g), align="center", maxw=lw - 30 * U)
                if click:
                    tx, ty = x0 + w_ * 0.5, y0 + h_ * 0.55; c0 = (W * 0.86, H * 0.92); p = eo((u - move * 0.4) / max(move * 0.6 + 16, 1), 3); px, py = c0[0] + (tx - c0[0]) * p, c0[1] + (ty - c0[1]) * p; cv_ = u - move - 20
                    if 0 <= cv_ < 16: cv2.circle(img, (int(tx), int(ty)), int((10 + 46 * cv_ / 16) * U), tuple(float(q) for q in acc), max(2, int(5 * U * (1 - cv_ / 16))), cv2.LINE_AA)
                    s_ = 34 * U * (0.88 if 0 <= cv_ < 5 else 1.0); arrow = np.float32([[0, 0], [0, 1], [0.27, 0.76], [0.45, 1.16], [0.6, 1.09], [0.42, 0.7], [0.74, 0.7]]) * s_ + (px, py)
                    cv2.fillPoly(img, [np.int32(arrow * 8)], (252, 252, 252), cv2.LINE_AA, 3); cv2.polylines(img, [np.int32(arrow * 8)], True, (30, 28, 28), max(2, int(2.5 * U)), cv2.LINE_AA, 3)
            if text:
                band = np.clip((jb.yy / H - 0.62) / 0.3, 0, 1)[..., None]; img = img * (1 - 0.7 * band); film.block(img, film.wrap(text, 54, True), H * 0.86, 54, True, film._io(u, n, 8), maxh=H * 0.2)
            return img
        film.custom(draw, dur, sfx=cues + list(k.pop("sfx", [])), **k); sc = film.scenes[-1]; sc["kind"] = "site"
        sc["call"] = ("site " + ("focus" if e is not None else "scroll" if scroll else "top"), tuple(x for x in ((e["text"][:60] if e is not None else self.url), label, text) if x), {}); return self
