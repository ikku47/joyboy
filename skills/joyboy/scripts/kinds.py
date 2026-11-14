"""joyboy kinds: fourteen more scene types for the videos people actually watch.

Installed into Film by quick.py (`kinds.install(Film)`), so they are used like every other scene:

    film.kinetic("stop scrolling start building", per=0.4, style="blur")        huge words, one per beat, motion blur
    film.highlight("In 1999 everything changed", hl=["1999"])                    sentence that types, key words get a marker box
    film.stages("5 stages of shipping", ["excited", "confident", "stuck", "panic", "shipped"])
    film.timeline([("9:00", "walk in"), ("9:20", "consult"), ("10:05", "walk out")], title="my appointment")
    film.countdown(["Notes", "Maps", "Mail"], title="Top 3 apps")               big numerals, 3 2 1
    film.versus("Before", "After", ["slow", "manual"], ["fast", "automatic"])    split-screen comparison
    film.product("shoe.png", "AirFoam", "Light. Fast.", callouts=[("Mesh", (-0.4, -0.2))])   studio hero shot
    film.chat([("them", "you up?"), ("me", "always")], title="Alex")              text-message story
    film.satisfying("pendulum")                                                  hypnotic loop (rings, orbits, tiles, waves, pendulum, spiral)
    film.stick("walk", "Day one.")                                               stick figure acting (walk run wave point think celebrate type fall shrug idle)
    film.anatomy([("Intro", 5), ("Problem", 10), ("Use case", 15), ("CTA", 5)])  a timeline bar that shows how a video is built
    film.before_after("a.jpg", "b.jpg")                                          slider wipe
    film.wire("cylinder", "Built from one prompt")                               3D wireframe that draws itself (cube pyramid cylinder torus sphere)
    film.sprite("joybot-sprites", travel=True)                                   play a sprite sheet from the asset library (Blender characters)
    film.cta("KATANA", "and I'll send you the setup link")                       comment-keyword call to action

Every scene takes the usual options (dur, tr, voice, bg, note, sfx ...) and follows the film's theme, palette and ink.
"""
import re, os
import numpy as np, cv2
import joyboy as jb
from joyboy import eo, ei, eio, clamp, spring
import themes
SKIT_DIM = 1.0   # how dark skit rooms are (1.0 as drawn); a film script may set kinds.SKIT_DIM, or pass dim= to one skit

def _lum(c): return themes.lum(c)
_G = {}
def _grain(H, W, style):
    k = ('g', H, W, style)
    if k not in _G: r = np.random.default_rng(12); n = cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), 0.9); _G[k] = np.clip(n * 1.6 + 0.5, 0, 1)
    return _G[k]
def _blot(H, W):
    k = ('b', H, W)
    if k not in _G: r = np.random.default_rng(13); a = cv2.resize(r.random((max(H // 70, 3), max(W // 70, 3))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC); b = cv2.resize(r.random((max(H // 22, 3), max(W // 22, 3))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC); _G[k] = np.clip(a * 0.7 + b * 0.3, 0, 1)
    return _G[k]
def _hexc(c): return col(c) if isinstance(c, str) else np.float32(c)
def col(c):
    if isinstance(c, str): c = c.lstrip('#'); return np.float32([int(c[4:6], 16), int(c[2:4], 16), int(c[0:2], 16)])
    return np.float32(c)

def install(Film):
    # ------------------------------------------------------------------ helpers
    def _fc(self, i):                                                    # a field colour for step i
        th = self.theme
        pool = self.pal if (th and th["bg"] in ("field", "brutal")) else (self.pal[1:] or self.pal)
        return pool[(self.cur + i) % len(pool)]
    def _field(self, c):                                                 # a flat colour frame; ink follows its brightness
        self._ink = np.float32((20, 20, 24)) if _lum(c) > 140 else jb.WHITE
        return np.broadcast_to(np.float32(c), (self.H, self.W, 3)).astype(np.float32).copy()
    def _acc(self, k=0):                                                 # an accent colour that is visible on the current background
        bgc = self.pal[self.cur % len(self.pal)] if (self.theme and self.theme["bg"] in ("field", "brutal")) else self.pal[0]
        pool = [c for c in self.pal if np.abs(np.float32(c) - np.float32(bgc)).sum() > 120] or list(self.pal); pool.sort(key=lambda c: -(float(np.max(c)) - float(np.min(c)))); return pool[k % len(pool)]
    def _snap(self, per):                                                # a segment length close to `per` seconds that sits on the beat grid
        c = [max(3, int(self.beat * m)) for m in (0.25, 0.5, 1, 2, 4)]; return min(c, key=lambda x: abs(x - per * self.fps))
    def _mask_put(self, img, word, size, cy, op, color, dx=0.0, dy=0.0, blur=0, scale=1.0, rot=0.0, maxw=None):
        m, sh = self.T(word, size, True, 0, maxw or self.W * 0.9)
        if blur > 1: m = cv2.blur(m, (int(blur) | 1, 1))
        if dx or dy or scale != 1.0 or rot:
            h = m.shape[0]; M = cv2.getRotationMatrix2D((self.W / 2, h / 2), rot, scale); M[0, 2] += dx; M[1, 2] += 0
            m = cv2.warpAffine(m, M, (self.W, h)); sh = cv2.warpAffine(sh, M, (self.W, h))
        jb.put(img, m, sh, cy + dy, op, np.float32(color), 0.0 if _lum(color) < 120 else 0.3, 1.0)
    for fn in (_fc, _field, _acc, _snap, _mask_put): setattr(Film, fn.__name__, fn)

    # ------------------------------------------------------------------ kinetic
    def kinetic(self, words, per=0.4, style="blur", hl=(), fill=True, **k):
        """Huge words, one per beat, flying in with motion blur. style: blur, slide, drop, zoom, spin. hl: words (or indices) shown in the accent colour.
        On a colour-field theme every word gets a new colour field; fill=False keeps one background."""
        words = words.split() if isinstance(words, str) else list(words); seg = self._snap(per); hl = set(hl)
        def draw(u, n, f):
            i = min(max(u, 0) // seg, len(words) - 1); v = u - i * seg; w = words[i]
            c = self._fc(i) if fill and (self.theme is None or self.theme["bg"] in ("field", "brutal")) else None
            img = self._field(c) if c is not None else self.bg(None, u, n, f)
            if c is None and self.theme is None: self._ink = jb.WHITE
            size = 260 if len(w) <= 6 else 200 if len(w) <= 10 else 140; e = eo(v / max(seg * 0.55, 3), 3); ink = self._ink
            color = self._acc(1) if (i in hl or w.strip(".,!?").lower() in {str(x).lower() for x in hl}) else ink
            cy = self.H * 0.47; dx = dy = 0.0; blur = 0; sc = 1.0; rot = 0.0; d = 1 if i % 2 == 0 else -1
            if style == "blur": blur = 90 * self.U * (1 - e); sc = 1.0 + 0.30 * (1 - e)
            elif style == "slide": dx = d * self.W * 0.9 * (1 - e); blur = 120 * self.U * (1 - e)
            elif style == "drop": dy = -self.H * 0.5 * (1 - float(spring(v / (seg * 0.7), 1.2, 7))); blur = 0
            elif style == "zoom": sc = 1 + 2.2 * (1 - e) ** 2; blur = 40 * self.U * (1 - e)
            elif style == "spin": rot = d * 25 * (1 - e); sc = 1 + 0.4 * (1 - e); blur = 30 * self.U * (1 - e)
            lines = w.split("\n")
            for j, ln in enumerate(lines): self._mask_put(img, ln, size, cy + (j - (len(lines) - 1) / 2) * size * self.U * 1.05, clamp((v + 1) / 2) * (1 - eio((v - (seg - 2)) / 2) * (0.0)), color, dx, dy, blur, sc, rot)
            return img
        return self._add(draw, seg * len(words) / self.fps, tr=k.pop("tr", "cut"), kind="kinetic", meta=dict(seg=seg, count=len(words)), **k)

    # ------------------------------------------------------------------ highlight
    def highlight(self, text, hl=(), size=84, dur=None, **k):
        """A sentence that types in word by word; the words in `hl` get a marker box in the accent colour."""
        words = text.split(); hlset = {str(x).lower().strip(".,!?") for x in hl}
        def layout(sz):
            mw = self.W * 0.84; lines = [[]]; x = 0.0; sp = self._len(" ", sz, True)
            for w in words:
                wl = self._len(w, sz, True)
                if lines[-1] and x + wl > mw: lines.append([]); x = 0.0
                lines[-1].append((w, x, wl)); x += wl + sp
            return lines
        sz = size
        while True:
            L = layout(sz)
            if len(L) * sz * 1.4 * self.U <= self.H * 0.5 or sz < 30: break
            sz -= 4
        flat = [(w, x, wl, li) for li, ln in enumerate(L) for (w, x, wl) in ln]; step = max(3, int(self.beat * 0.5)); t_h = 8 + len(flat) * step + 6
        def draw(u, n, f):
            img = self.bg(None, u, n, f); o = 1 - eio((u - (n - 6)) / 6); lh = sz * 1.4 * self.U; y0 = self.H * 0.46 - (len(L) - 1) * lh / 2
            for i, (w, x, wl, li) in enumerate(flat):
                ln = L[li]; tw = ln[-1][1] + ln[-1][2]; xs = (self.W - tw) / 2 + x; cy = y0 + li * lh; is_h = w.lower().strip(".,!?") in hlset
                g = eio((u - 8 - i * step) / 6)
                if is_h:
                    a = self._acc(1); p = eo((u - t_h) / 9, 3) * o; pad = 14 * self.U
                    if p > 0: self.card(img, xs - pad, cy - lh * 0.46, xs - pad + (wl + 2 * pad) * p, cy + lh * 0.46, a, radius=16, op=1.0)
                    tc = np.float32((20, 20, 24)) if _lum(a) > 140 else jb.WHITE if p > 0.6 else self._ink
                else: tc = self._ink
                self.ltext(img, w, xs, cy + 12 * self.U * (1 - g), sz, True, g * o, tc)
            return img
        return self._add(draw, dur or (t_h / self.fps + 1.6), kind="highlight", meta=dict(count=len(flat), step=step), **k)

    # ------------------------------------------------------------------ stages
    def stages(self, title, items, dur=None, **k):
        """'5 stages of ...': one full-colour card per stage with its number and a progress track; the energy rises as the stages go on."""
        seg = max(self.beat * 2, self._snap(1.3)); N = len(items)
        def draw(u, n, f):
            i = min(max(u, 0) // seg, N - 1); v = u - i * seg; c = self._fc(i); img = self._field(c); ink = self._ink; o = self._io(u, n, 3, 5)
            sh = (i / max(N - 1, 1)) ** 1.6; amp = 9 * self.U * sh * (0.5 + 0.5 * np.sin(f * 1.9)); sc = 1 + 0.35 * (1 - eo(v / 6, 4))
            self.block(img, [f"{i + 1}/{N}"], self.H * 0.2, 120, True, clamp(v / 3) * o, color=ink, scale=1.0, shadow=0)
            self.block(img, self.wrap(items[i], 170, True, self.W * 0.8), self.H * 0.47 + amp, 170, True, clamp((v + 1) / 3) * o, color=ink, scale=sc, shadow=0, maxh=self.H * 0.4)
            self.block(img, self.wrap(title, 54, False, self.W * 0.8), self.H * 0.1, 54, False, 0.8 * o, color=ink, shadow=0, maxh=self.H * 0.1)
            x0, x1, y = self.W * 0.14, self.W * 0.86, self.H * 0.84; cv2.line(img, (int(x0), int(y)), (int(x1), int(y)), tuple(float(q) for q in ink * 0.35 + np.float32(c) * 0.65), max(2, int(6 * self.U)), cv2.LINE_AA)
            for j in range(N):
                px = x0 + (x1 - x0) * j / max(N - 1, 1); r = (22 if j == i else 12) * self.U * (1 + 0.25 * (1 - eo(v / 6)) * (j == i)); cv2.circle(img, (int(px), int(y)), int(r), tuple(float(q) for q in ink), -1 if j <= i else 3, cv2.LINE_AA)
            return img
        return self._add(draw, dur or seg * N / self.fps, kind="stages", meta=dict(seg=seg, count=N), **k)

    # ------------------------------------------------------------------ timeline
    def timeline(self, items, title=None, dur=None, **k):
        """Timestamps down a line: [(time, label), ...]. The line draws, each point lands, the latest one is the big one."""
        N = len(items); step = max(self.beat, self._snap(0.9))
        def draw(u, n, f):
            img = self.bg(None, u, n, f); ink = self._ink; o = self._io(u, n, 6, 6); a = self._acc(1)
            if title: self.block(img, self.wrap(title, 72, True), self.H * 0.13, 72, True, eio(u / 8) * o, maxh=self.H * 0.12)
            top, bot = self.H * 0.26, self.H * 0.9; rh = min(self.H * 0.13, (bot - top) / N); xl = self.W * 0.30; cur = min(max((u - 8) // step, -1), N - 1)
            yy_ = lambda j: top + rh * (j + 0.5)
            end = yy_(max(cur, 0)) if cur >= 0 else top; prog = eo((u - 8 - max(cur, 0) * step) / max(step * 0.6, 3)) if cur >= 0 else 0
            ye = (yy_(cur - 1) + (yy_(cur) - yy_(cur - 1)) * prog) if cur > 0 else (top if cur < 0 else yy_(0))
            cv2.line(img, (int(xl), int(top)), (int(xl), int(ye)), tuple(float(q) for q in ink * 0.55), max(3, int(6 * self.U)), cv2.LINE_AA)
            for j, (tm, lab) in enumerate(items):
                v = u - 8 - j * step
                if v < 0: continue
                g = eio(v / 7); big = (j == cur); y = yy_(j); r = (20 if big else 13) * self.U * (0.5 + 0.5 * eo(v / 8))
                cv2.circle(img, (int(xl), int(y)), int(r), tuple(float(q) for q in (a if big else ink)), -1, cv2.LINE_AA)
                self.ltext(img, str(tm), xl - 36 * self.U, y, 54 if big else 44, True, g * o, a if big else ink, align="right", maxw=self.W * 0.24)
                self.ltext(img, str(lab), xl + 48 * self.U + 18 * self.U * (1 - g), y, 58 if big else 46, big, g * o * (1.0 if big else 0.85), maxw=self.W * 0.56)
            return img
        return self._add(draw, dur or (14 + N * step) / self.fps + 1.2, kind="timeline", meta=dict(count=N, step=step), **k)

    # ------------------------------------------------------------------ countdown
    def countdown(self, items, title=None, per=1.5, **k):
        """A ranked list counted down from N to 1; each rank slams in as a giant numeral over a new colour."""
        N = len(items); seg = self._snap(per); seg = max(seg, self.beat * 2)
        def draw(u, n, f):
            i = min(max(u, 0) // seg, N - 1); v = u - i * seg; c = self._fc(i); img = self._field(c) if (self.theme is None or self.theme["bg"] in ("field", "brutal")) else self.bg(None, u, n, f)
            if self.theme is None: self._ink = np.float32((20, 20, 24)) if _lum(c) > 140 else jb.WHITE
            ink = self._ink; rank = N - i; o = self._io(u, n, 3, 5); it = items[i]; name, sub = (it if isinstance(it, (tuple, list)) else (it, None))
            s = float(spring(v / (seg * 0.6), 1.4, 6)); sz = 760 if rank < 10 else 560
            ghost = img.copy(); self.block(ghost, [str(rank)], self.H * 0.40, sz, True, 1.0, color=ink, shadow=0, scale=0.7 + 0.3 * s, maxw=self.W * 1.1, maxh=self.H * 0.8)
            img = img * (1 - 0.16 * clamp(v / 4)) + ghost * 0.16 * clamp(v / 4) if False else img * 0.84 + ghost * 0.16 if v > 0 else img
            self.block(img, self.wrap(str(name), 120, True, self.W * 0.8), self.H * 0.52, 120, True, clamp((v - 2) / 4) * o, color=ink, shadow=0, scale=1 + 0.25 * (1 - eo((v - 2) / 7, 4)), maxh=self.H * 0.3)
            if sub: self.block(img, self.wrap(str(sub), 50, False, self.W * 0.8), self.H * 0.52 + self.H * 0.17, 50, False, eio((v - 8) / 8) * o * 0.9, color=ink, shadow=0, maxh=self.H * 0.14)
            if title: self.block(img, self.wrap(title, 52, True, self.W * 0.8), self.H * 0.09, 52, True, o * 0.85, color=ink, shadow=0, maxh=self.H * 0.1)
            return img
        return self._add(draw, seg * N / self.fps, kind="countdown", meta=dict(seg=seg, count=N), **k)

    # ------------------------------------------------------------------ versus
    def versus(self, left, right, lpoints=(), rpoints=(), dur=None, **k):
        """Two sides head to head. Tall frames stack them, wide frames put them side by side; points arrive alternately."""
        np_ = max(len(lpoints), len(rpoints)); step = max(self.beat, self._snap(0.8))
        def draw(u, n, f):
            W, H = self.W, self.H; tall = H >= W; ca, cb = np.float32(self._fc(0)), np.float32(self._fc(1))
            if themes.lum(ca) > 140 and themes.lum(cb) > 140 and self.theme is None: pass
            img = np.zeros((H, W, 3), np.float32); o = self._io(u, n, 4, 5); e = eo(u / 9, 3)
            if tall:
                m = H / 2; img[: int(m)] = ca; img[int(m):] = cb; cx_, cy_ = W / 2, m
                ya = -H * 0.5 * (1 - e); yb = H * 0.5 * (1 - e); img = np.roll(img, 0, 0)
                boxes = [(0, H * 0.25 + ya, W, ca, left, lpoints), (0, H * 0.75 + yb, W, cb, right, rpoints)]
            else:
                m = W / 2; img[:, : int(m)] = ca; img[:, int(m):] = cb; cx_, cy_ = m, H / 2
                boxes = [(W * 0.25 - W * 0.5 * (1 - e), H * 0.5, W / 2, ca, left, lpoints), (W * 0.75 + W * 0.5 * (1 - e), H * 0.5, W / 2, cb, right, rpoints)]
            for bi, (bx, by, bw, bc, name, pts) in enumerate(boxes):
                ink = np.float32((20, 20, 24)) if _lum(bc) > 140 else jb.WHITE; cx = bx if not tall else W / 2; cy = by
                self.block(img, self.wrap(str(name), 110, True, bw * 0.82), cy - (H * 0.08 if tall else H * 0.20), 110, True, o, color=ink, shadow=0, maxw=bw * 0.86, maxh=H * 0.16, scale=1 + 0.2 * (1 - e))
                for j, p in enumerate(pts):
                    v = u - 14 - (j * 2 + bi) * step // 2
                    if v < 0: continue
                    g = eio(v / 7); yy_ = cy + (H * 0.02 if tall else H * 0.02) + j * (H * 0.065 if tall else H * 0.095) + 10 * self.U * (1 - g)
                    self.ltext(img, str(p), cx, yy_, 52, True, g * o, ink, align="center", maxw=bw * 0.8) if not tall else self.ltext(img, str(p), cx, yy_, 52, True, g * o, ink, align="center", maxw=bw * 0.8)
            s = float(spring((u - 6) / 14, 1.6, 6)); r = 92 * self.U * max(s, 0.01); cv2.circle(img, (int(cx_), int(cy_)), int(r + 10 * self.U), (20, 20, 24), -1, cv2.LINE_AA); cv2.circle(img, (int(cx_), int(cy_)), int(r), (255, 255, 255), -1, cv2.LINE_AA)
            if s > 0.3: self.ltext(img, "VS", cx_, cy_, 78 * min(s, 1), True, 1.0, np.float32((20, 20, 24)), align="center")
            return img
        return self._add(draw, dur or (20 + np_ * step) / self.fps + 1.4, kind="versus", meta=dict(count=np_ * 2), **k)

    # ------------------------------------------------------------------ product
    def product(self, image, name=None, tagline=None, callouts=(), dur=4.5, **k):
        """A studio hero shot. `image` is best as a cut-out PNG with transparency (it gets a soft floor shadow); a plain photo is shown as a rounded card.
        callouts: [(text, (dx, dy))] with dx, dy in -1..1 from the product centre; lines draw out to labels."""
        raw = cv2.imread(image, cv2.IMREAD_UNCHANGED)
        if raw is None: raise FileNotFoundError(image)
        if raw.ndim == 2: raw = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
        if raw.shape[2] == 3:
            h0, w0 = raw.shape[:2]; r_ = int(min(h0, w0) * 0.06); al = np.zeros((h0, w0), np.uint8); cv2.rectangle(al, (r_, 0), (w0 - r_, h0), 255, -1); cv2.rectangle(al, (0, r_), (w0, h0 - r_), 255, -1)
            for px, py in ((r_, r_), (w0 - r_, r_), (r_, h0 - r_), (w0 - r_, h0 - r_)): cv2.circle(al, (px, py), r_, 255, -1)
            raw = np.dstack([raw, al])
        ys, xs = np.where(raw[..., 3] > 10); raw = raw[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        def draw(u, n, f):
            W, H = self.W, self.H; tall = H >= W; img = self.bg(None, u, n, f); ink = self._ink; o = self._io(u, n, 6, 6); t = u / n
            box = min(W * 0.78, H * 0.46) if tall else min(W * 0.42, H * 0.7); ih, iw = raw.shape[:2]; k_ = box / max(ih, iw) * (0.9 + 0.1 * eo(u / 14) + 0.04 * t)
            cx, cy = (W / 2, H * 0.50) if tall else (W * 0.66, H * 0.5); cy += 14 * self.U * np.sin(f / self.fps * 1.6); ang = 3.0 * np.sin(f / self.fps * 0.9 + 0.6)
            M = cv2.getRotationMatrix2D((iw / 2, ih / 2), ang, k_); M[0, 2] += cx - iw / 2; M[1, 2] += cy - ih / 2
            pr = cv2.warpAffine(raw.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = (pr[..., 3:4] / 255.0) * clamp(u / 6) * o
            fy = cy + ih * k_ / 2 + 22 * self.U; sh = np.zeros((H, W), np.float32); cv2.ellipse(sh, (int(cx), int(fy)), (int(iw * k_ * 0.40), int(18 * self.U + 6)), 0, 0, 360, 1.0, -1); sh = cv2.GaussianBlur(sh, (0, 0), 16 * self.U + 2)[..., None] * 0.35 * clamp(u / 8) * o
            img = img * (1 - sh * (0.9 if _lum(ink) < 120 else 0.6)); img = img * (1 - a) + pr[..., :3] * a
            if name:
                if tall: self.block(img, self.wrap(name, 120, True), H * 0.17, 120, True, eio((u - 4) / 8) * o, maxh=H * 0.18)
                else: self.block(img, self.wrap(name, 110, True, W * 0.4), H * 0.40, 110, True, eio((u - 4) / 8) * o, maxw=W * 0.38, maxh=H * 0.3);
            if tagline:
                if tall: self.block(img, self.wrap(tagline, 52, False), H * 0.86, 52, False, eio((u - 10) / 8) * o, maxh=H * 0.1)
                else: self.block(img, self.wrap(tagline, 52, False, W * 0.38), H * 0.58, 52, False, eio((u - 10) / 8) * o, maxw=W * 0.36, maxh=H * 0.2)
            acc = np.float32(self._acc(1))
            for j, (txt, (dx, dy)) in enumerate(callouts):
                v = u - 18 - j * 8; g = eio(v / 10)
                if g <= 0: continue
                px, py = cx + dx * iw * k_ * 0.35, cy + dy * ih * k_ * 0.35; lx, ly = cx + dx * iw * k_ * 0.75 + (0.1 * W if dx >= 0 else -0.1 * W), cy + dy * ih * k_ * 0.75 - 0.04 * H
                tw = self._len(txt, 40, True) + 10 * self.U; lx = min(lx, W * 0.94 - tw) if dx >= 0 else max(lx, W * 0.06 + tw); ex, ey = px + (lx - px) * g, py + (ly - py) * g; cv2.line(img, (int(px), int(py)), (int(ex), int(ey)), tuple(float(q) for q in acc), max(2, int(4 * self.U)), cv2.LINE_AA); cv2.circle(img, (int(px), int(py)), int(8 * self.U), tuple(float(q) for q in acc), -1, cv2.LINE_AA)
                self.ltext(img, txt, lx, ly - 30 * self.U, 40, True, g * o, align="left" if dx >= 0 else "right", maxw=W * 0.3)
            return img
        return self._add(draw, dur, kind="product", meta=dict(count=len(callouts)), **k)

    # ------------------------------------------------------------------ chat
    def chat(self, messages, title="Alex", dur=None, **k):
        """A text-message story. messages: [("them", "text"), ("me", "text")] or plain strings that alternate. Incoming messages show typing dots first."""
        msgs = [(("them" if i % 2 == 0 else "me"), m) if isinstance(m, str) else (("me" if str(m[0]).lower() in ("me", "1", "right") else "them"), m[1]) for i, m in enumerate(messages)]
        step = max(self.beat, self._snap(1.0)); start = 10
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); light = _lum(img[H // 2, W // 2]) > 140; o = self._io(u, n, 5, 6)
            inc = np.float32((234, 233, 233)) if light else np.float32((52, 50, 48)); outc = np.float32(self._acc(1)) if _lum(self._acc(1)) < 200 else np.float32((255, 143, 47))
            hb = 160 * self.U; img[: int(hb)] = img[: int(hb)] * 0.5 + (np.float32((250, 250, 250)) if light else np.float32((22, 20, 20))) * 0.5
            cv2.circle(img, (int(W / 2), int(hb * 0.38)), int(34 * self.U), tuple(float(q) for q in outc), -1, cv2.LINE_AA); self.ltext(img, title[:1].upper(), W / 2, hb * 0.38, 40, True, 1.0, jb.WHITE, align="center")
            self.ltext(img, title, W / 2, hb * 0.78, 34, True, 1.0, np.float32((30, 30, 30)) if light else jb.WHITE, align="center")
            sz = 46; mw = W * 0.64; bh = []; rows = []
            for who, txt in msgs:
                ls = self.wrap(txt, sz, False, mw); w_ = max(self._len(l, sz, False) for l in ls) + 64 * self.U; h_ = len(ls) * sz * 1.3 * self.U + 44 * self.U; rows.append((ls, w_)); bh.append(h_)
            ys = []; y = hb + 40 * self.U
            for h_ in bh: ys.append(y); y += h_ + 22 * self.U
            shown = [i for i in range(len(msgs)) if u >= start + i * step - (0 if msgs[i][0] == "me" else 0)]
            last = shown[-1] if shown else 0; bottom = ys[last] + bh[last] + 30 * self.U if shown else 0; scroll = max(0.0, bottom - H * 0.9); sc = scroll * eio((u - (start + last * step)) / 8) if last else 0
            sc = scroll if last == 0 else (scroll - (ys[last] + bh[last] - ys[last - 1] - bh[last - 1] + 22 * self.U) * (1 - eio((u - (start + last * step)) / 8)) if scroll > 0 else 0.0); sc = max(sc, 0.0)
            for i in shown:
                who, txt = msgs[i]; ls, w_ = rows[i]; v = u - (start + i * step); y0 = ys[i] - sc; h_ = bh[i]
                if y0 + h_ < hb or y0 > H: continue
                typing = who == "them" and v < step * 0.55 and i > 0 or (who == "them" and v < step * 0.45 and i == 0)
                if who == "them" and typing:
                    self.card(img, W * 0.07, y0, W * 0.07 + 150 * self.U, y0 + 80 * self.U, inc, radius=40)
                    for d in range(3): cv2.circle(img, (int(W * 0.07 + (46 + 29 * d) * self.U), int(y0 + 40 * self.U - 6 * self.U * np.sin(f * 0.5 + d * 1.1))), int(9 * self.U), (150, 148, 146), -1, cv2.LINE_AA)
                    continue
                pop = float(spring(max(v - (step * 0.5 if who == "them" else 0), 0) / 10, 1.8, 7)); pw = w_ * min(pop, 1.0); x0 = W * 0.07 if who == "them" else W * 0.93 - pw
                self.card(img, x0, y0, x0 + pw, y0 + h_, inc if who == "them" else outc, radius=44, op=o)
                if pop > 0.8:
                    tc = np.float32((24, 24, 24)) if (who == "them" and light) else jb.WHITE
                    for j, l in enumerate(ls): self.ltext(img, l, x0 + 32 * self.U, y0 + 22 * self.U + (j + 0.5) * sz * 1.3 * self.U, sz, False, o, tc)
            return img
        return self._add(draw, dur or (start + len(msgs) * step) / self.fps + 1.6, kind="chat", meta=dict(count=len(msgs), step=step, start=start, who=[w for w, _ in msgs]), **k)

    # ------------------------------------------------------------------ satisfying
    def satisfying(self, style="pendulum", dur=6.0, **k):
        """A hypnotic loop that needs no words. style: pendulum, rings, orbits, tiles, waves, spiral."""
        assert style in ("pendulum", "rings", "orbits", "tiles", "waves", "spiral"), "style: pendulum, rings, orbits, tiles, waves, spiral"
        loop = max(self.beat * 8, int(dur * self.fps // 2) or 1)
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); U = self.U; t = (u % loop) / loop; o = self._io(u, n, 8, 8)
            cols = [np.float32(c) for c in (self.pal[1:] or self.pal)]; cxy = (W / 2, H / 2); S = min(W, H)
            def C(x): a = x * (len(cols)); i = int(a) % len(cols); b = a - int(a); return tuple(float(q) for q in cols[i] * (1 - b) + cols[(i + 1) % len(cols)] * b)
            lay = img.copy(); AA = cv2.LINE_AA
            if style == "pendulum":
                N = 16; x0, x1 = W * 0.1, W * 0.9; ytop = H * 0.28; Lh = H * 0.34
                for i in range(N):
                    ang = 0.62 * np.sin(2 * np.pi * (14 + i) * t); px = x0 + (x1 - x0) * i / (N - 1); bx, by = px + Lh * np.sin(ang) * 0.5, ytop + Lh * np.cos(ang)
                    cv2.line(lay, (int(px), int(ytop)), (int(bx), int(by)), tuple(float(q) for q in self._ink * 0.5), max(1, int(2 * U)), AA); cv2.circle(lay, (int(bx), int(by)), int(26 * U), C(i / N), -1, AA)
                cv2.line(lay, (int(x0 - 30 * U), int(ytop)), (int(x1 + 30 * U), int(ytop)), tuple(float(q) for q in self._ink), max(2, int(6 * U)), AA)
            elif style == "rings":
                N = 9
                for i in range(N):
                    r = S * (0.08 + 0.05 * i); d = 1 if i % 2 else -1; a0 = d * 360 * t * (1 + i % 3); th = max(3, int(S * 0.026))
                    cv2.ellipse(lay, (int(cxy[0]), int(cxy[1])), (int(r), int(r)), 0, a0, a0 + 250 - 12 * i, C(i / N), th, AA)
            elif style == "orbits":
                N = 28
                for i in range(N):
                    ph = i / N; r = S * (0.1 + 0.34 * ph)
                    for tr_ in range(6):
                        a = 2 * np.pi * (t * (1 + i % 3) * (1 if i % 2 else -1) + ph * 2) - tr_ * 0.07 * (1 if i % 2 else -1); x = cxy[0] + r * np.cos(a); y = cxy[1] + r * np.sin(a)
                        cv2.circle(lay, (int(x), int(y)), max(2, int((20 - tr_ * 2.5) * U)), tuple(float(q) * (1 - tr_ * 0.14) for q in C(ph)), -1, AA)
            elif style == "tiles":
                cols_n = 7; cs = W * 0.86 / cols_n; rows_n = int(H * 0.8 / cs); gx = (W - cols_n * cs) / 2 + cs / 2; gy = (H - rows_n * cs) / 2 + cs / 2
                for r_ in range(rows_n):
                    for c_ in range(cols_n):
                        d = (r_ + c_) * 0.09; ph = (t * 2 - d) % 1.0; ang = (np.pi / 2) * eio(ph * 1.6) ; s_ = cs * 0.38 * (1 - 0.35 * np.sin(np.pi * clamp(ph * 1.6)))
                        x, y = gx + c_ * cs, gy + r_ * cs; pts = np.array([[x + s_ * np.cos(ang + a), y + s_ * np.sin(ang + a)] for a in (np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4, 7 * np.pi / 4)], np.int32)
                        cv2.fillConvexPoly(lay, pts, C((r_ + c_) / (rows_n + cols_n)), AA)
            elif style == "waves":
                N = 14; xs = np.linspace(W * 0.06, W * 0.94, 90)
                for i in range(N):
                    y = H * (0.2 + 0.6 * i / (N - 1)); ys = y + H * 0.05 * np.sin(2 * np.pi * (t * 2 + xs / W * 1.5 + i * 0.07)) * (0.6 + 0.4 * np.sin(2 * np.pi * (t + i / N)))
                    pts = np.stack([xs, ys], 1).astype(np.int32).reshape(-1, 1, 2); cv2.polylines(lay, [pts], False, C(i / N), max(3, int(14 * U)), AA)
            else:
                N = 140
                for i in range(N):
                    a = i * 0.32 + 2 * np.pi * t; r = S * 0.012 * i ** 0.98 * (0.9 + 0.1 * np.sin(2 * np.pi * (t * 2 + i / N))); x, y = cxy[0] + r * np.cos(a), cxy[1] + r * np.sin(a)
                    cv2.circle(lay, (int(x), int(y)), max(2, int((6 + i * 0.12) * U)), C(i / N), -1, AA)
            return img * (1 - o) + lay * o if o < 1 else lay
        return self._add(draw, dur, kind="satisfying", meta=dict(style=style, count=int(dur * 1000 / (60000 / (60 * self.fps / self.beat)))), **k)

    # ------------------------------------------------------------------ stick
    def stick(self, action="idle", text=None, dur=3.0, x=0.5, travel=True, size=1.0, prop=None, **k):
        """A stick figure acting. action: idle, walk, run, wave, point, think, celebrate, type, fall, shrug. With travel=True walk/run cross the frame.
        text appears as a speech line; prop is a word shown on a sign (e.g. 'SALE')."""
        acts = ("idle", "walk", "run", "wave", "point", "think", "celebrate", "type", "fall", "shrug")
        assert action in acts, "action: " + ", ".join(acts)
        def pose(t, n_):                                                        # angles from straight-down, + = towards screen right; returns dict
            s, c = np.sin, np.cos; p = dict(tl=0.0, tr=0.0, kl=0.0, kr=0.0, al=0.15, ar=-0.15, el=0.1, er=0.1, lean=0.0, head=0.0, hop=0.0, off=0.0, rot=0.0, sit=0)
            w = 2 * np.pi * t * 1.5
            if action == "idle": p.update(al=0.12 + 0.03 * s(w * 0.5), ar=-0.12 - 0.03 * s(w * 0.5), hop=0.01 * s(w))
            elif action in ("walk", "run"):
                a = 0.5 if action == "walk" else 0.9; w *= 1.0 if action == "walk" else 1.7
                p.update(tl=a * s(w), tr=-a * s(w), kl=max(0, -s(w + 1)) * a * 1.3, kr=max(0, s(w + 1)) * a * 1.3, al=-a * 0.9 * s(w), ar=a * 0.9 * s(w), el=0.5 + 0.3 * (action == "run"), er=0.5 + 0.3 * (action == "run"), lean=0.0 if action == "walk" else 0.22, hop=abs(s(w)) * (0.03 if action == "walk" else 0.06))
            elif action == "wave": p.update(ar=np.pi - 0.5, er=0.5 * s(w * 2.2), al=0.1, el=0.1)
            elif action == "point": p.update(ar=np.pi / 2 + 0.05, er=0.0, al=0.1, lean=0.05)
            elif action == "think": p.update(ar=np.pi - 0.15, er=-2.1, al=0.1, head=0.18 * s(w * 0.4), hop=0.008 * s(w * 0.5))
            elif action == "celebrate": jmp = abs(s(w * 1.3)); p.update(al=np.pi - 0.4 + 0.3 * s(w * 2.6), ar=-np.pi + 0.4 - 0.3 * s(w * 2.6), tl=0.3 * jmp, tr=-0.3 * jmp, kl=0.4 * jmp, kr=0.4 * jmp, hop=0.16 * jmp)
            elif action == "type": p.update(sit=1, ar=1.0, al=0.9, er=0.6 + 0.4 * s(w * 4), el=0.6 - 0.4 * s(w * 4), tl=1.45, tr=1.45, kl=-1.45, kr=-1.45, lean=0.2)
            elif action == "fall": q = clamp(t / 0.8 / (n_ / 30)); p.update(rot=90 * eo(q, 3) * 0.95, al=0.5 + 2 * q, ar=-0.5 - 2 * q, tl=0.4 * q, tr=-0.4 * q, off=0.0, hop=-0.0)
            elif action == "shrug": p.update(al=0.9 + 0.1 * s(w), ar=-0.9 - 0.1 * s(w), el=-1.3, er=1.3, head=0.1 * s(w * 0.7))
            return p
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); ink = np.float32(self._ink); o = self._io(u, n, 5, 5); t = u / self.fps; U = self.U
            S = min(W, H) * 0.34 * size; thick = max(4, int(0.045 * S)); gy = H * 0.72; hx = W * x
            if travel and action in ("walk", "run"): hx = -0.15 * W + 1.3 * W * (u / n)
            p = pose(t, n); L_t, L_u, L_l = 0.34 * S, 0.30 * S, 0.30 * S; A_u, A_l = 0.22 * S, 0.22 * S
            hipy = gy - (L_u + L_l) * (0.98 if not p["sit"] else 0.55) - p["hop"] * S; hip = np.array([hx, hipy]); lean = p["lean"]
            if action == "fall": hip = np.array([hx, gy - 0.12 * S - (1 - eo(clamp(t / 0.8), 3)) * (L_u + L_l)])
            def jt(start, ang, ln): return start + ln * np.array([np.sin(ang), np.cos(ang)])
            pts = {}
            sh = hip + L_t * np.array([np.sin(lean), -np.cos(lean)]); neck = sh + 0.05 * S * np.array([np.sin(lean), -np.cos(lean)]); head_c = neck + 0.17 * S * np.array([np.sin(lean + p["head"]), -np.cos(lean + p["head"])])
            if p["sit"]:
                kl_ = hip + L_u * np.array([1.0, 0.0]); kr_ = kl_ + np.array([0, 0]); fl_ = kl_ + np.array([0, L_l * 0.9]); fr_ = fl_
                legs = [(hip, kl_), (kl_, fl_)]
            else:
                kl_ = jt(hip, p["tl"], L_u); fl_ = jt(kl_, p["tl"] - p["kl"], L_l); kr_ = jt(hip, p["tr"], L_u); fr_ = jt(kr_, p["tr"] - p["kr"], L_l); legs = [(hip, kl_), (kl_, fl_), (hip, kr_), (kr_, fr_)]
            el_ = jt(sh, p["al"] + lean, A_u); hl_ = jt(el_, p["al"] + p["el"] + lean, A_l); er_ = jt(sh, p["ar"] + lean, A_u); hr_ = jt(er_, p["ar"] + p["er"] + lean, A_l)
            segs = legs + [(hip, sh), (sh, el_), (el_, hl_), (sh, er_), (er_, hr_)]
            rot = p["rot"]; piv = np.array([hx, gy])
            if rot:
                R = cv2.getRotationMatrix2D((float(piv[0]), float(piv[1])), -rot, 1.0)[:, :2]; T_ = lambda q: R @ (q - piv) + piv; segs = [(T_(a), T_(b)) for a, b in segs]; head_c = T_(head_c)
            cv2.line(img, (int(W * 0.04), int(gy + thick)), (int(W * 0.96), int(gy + thick)), tuple(float(q) for q in ink * 0.5), max(3, int(5 * U)), cv2.LINE_AA)
            if action == "type": cv2.rectangle(img, (int(hx + 0.28 * S), int(gy - 0.5 * S)), (int(hx + 0.62 * S), int(gy - 0.2 * S)), tuple(float(q) for q in ink), -1, cv2.LINE_AA); cv2.line(img, (int(hx + 0.62 * S), int(gy - 0.2 * S)), (int(hx + 0.75 * S), int(gy - 0.12 * S)), tuple(float(q) for q in ink), thick, cv2.LINE_AA)
            for a, b in segs: cv2.line(img, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), tuple(float(q) * o + float(img[0, 0, i]) * (1 - o) for i, q in enumerate(ink)), thick, cv2.LINE_AA)
            cv2.circle(img, (int(head_c[0]), int(head_c[1])), int(0.17 * S), tuple(float(q) for q in ink), thick, cv2.LINE_AA)
            for sg in (-1, 1): cv2.circle(img, (int(head_c[0] + sg * 0.06 * S + 0.03 * S), int(head_c[1] - 0.02 * S)), max(2, int(0.018 * S)), tuple(float(q) for q in ink), -1, cv2.LINE_AA)
            if action == "think": self.ltext(img, "?", head_c[0] + 0.3 * S, head_c[1] - 0.3 * S, 90, True, o * (0.5 + 0.5 * np.sin(t * 5) ** 2), np.float32(self._acc(1)), align="center")
            if prop: self.card(img, W * 0.62, gy - 0.9 * S, W * 0.94, gy - 0.55 * S, np.float32(self._acc(1)), radius=20, op=o); self.ltext(img, prop, W * 0.78, gy - 0.725 * S, 56, True, o, np.float32((20, 20, 24)) if _lum(self._acc(1)) > 140 else jb.WHITE, align="center", maxw=W * 0.28)
            if text: self.block(img, self.wrap(text, 62, True), H * 0.16, 62, True, eio(u / 8) * o, maxh=H * 0.2)
            return img
        return self._add(draw, dur, kind="stick", meta=dict(action=action), **k)

    # ------------------------------------------------------------------ anatomy
    def anatomy(self, sections, title=None, dur=None, **k):
        """How a video is built, as a timeline bar: [(label, seconds), ...] or [(label, seconds, 'one line')]. A playhead sweeps it and the current part lights up."""
        secs = [(s_[0], float(s_[1]) if len(s_) > 1 else 5.0, s_[2] if len(s_) > 2 else None) if isinstance(s_, (tuple, list)) else (s_, 5.0, None) for s_ in sections]; tot = sum(s_[1] for s_ in secs); D = dur or min(max(tot * 0.4, 4.0), 12.0)
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); o = self._io(u, n, 6, 6); ink = self._ink; p = eio((u - 10) / max(n - 24, 1)); x0, x1 = W * 0.08, W * 0.92; yb = H * 0.58; bh = 64 * self.U
            if title: self.block(img, self.wrap(title, 64, True), H * 0.14, 64, True, eio(u / 8) * o, maxh=H * 0.12)
            acc = x0; cur_i = 0; ph = p * tot
            for i, (lab, d, ds) in enumerate(secs):
                w_ = (x1 - x0) * d / tot; c = np.float32(self._fc(i)); act = acc - x0 <= (x1 - x0) * ph / tot < acc - x0 + w_; done = acc - x0 + w_ <= (x1 - x0) * ph / tot
                if act: cur_i = i
                g = eo((u - 4 - i * 3) / 10)
                self.card(img, acc + 3 * self.U, yb - bh / 2, acc + w_ - 3 * self.U, yb + bh / 2, c * (1.0 if (act or done) else 0.45) + np.float32(img[0, 0]) * (0 if (act or done) else 0.55), radius=18, op=g * o)
                acc += w_
            px = x0 + (x1 - x0) * p; cv2.line(img, (int(px), int(yb - bh * 1.1)), (int(px), int(yb + bh * 1.1)), tuple(float(q) for q in ink), max(3, int(6 * self.U)), cv2.LINE_AA); cv2.circle(img, (int(px), int(yb - bh * 1.1)), int(12 * self.U), tuple(float(q) for q in ink), -1, cv2.LINE_AA)
            lab, d, ds = secs[cur_i]; self.block(img, [lab], H * 0.38, 150, True, o * clamp((u - 8) / 4), maxh=H * 0.2, scale=1 + 0.08 * (1 - eo(((ph - sum(s_[1] for s_ in secs[:cur_i])) / max(d, 0.1)) * 6)))
            self.ltext(img, f"{d:g}s", W / 2, H * 0.47, 46, False, o * 0.7, align="center")
            if ds: self.block(img, self.wrap(ds, 46, False, W * 0.8), H * 0.76, 46, False, o * 0.9, maxh=H * 0.14)
            return img
        return self._add(draw, D, kind="anatomy", meta=dict(count=len(secs)), **k)

    # ------------------------------------------------------------------ before / after
    def before_after(self, before, after, labels=("BEFORE", "AFTER"), dur=4.0, **k):
        """A slider that wipes from one picture to another and back."""
        def draw(u, n, f):
            W, H = self.W, self.H; A = self.bg(before, u, n, f, "still"); B = self.bg(after, u, n, f, "still"); o = self._io(u, n, 5, 5)
            p = 0.5 - 0.5 * np.cos(np.pi * 2 * clamp((u - 6) / max(n - 12, 1))) if False else eio(clamp((u - 8) / (n * 0.45))) if u < n * 0.6 else 1 - 0.0 * eio((u - n * 0.6) / (n * 0.3))
            xs = W * (0.08 + 0.84 * p); m = (jb.xx < xs)[..., None]; img = np.where(m, A, B)
            cv2.line(img, (int(xs), 0), (int(xs), H), (255, 255, 255), max(4, int(8 * self.U)), cv2.LINE_AA); cv2.circle(img, (int(xs), int(H / 2)), int(36 * self.U), (255, 255, 255), -1, cv2.LINE_AA)
            for j, (lab, cx) in enumerate(((labels[0], W * 0.2), (labels[1], W * 0.8))):
                self.card(img, cx - 130 * self.U, H * 0.07, cx + 130 * self.U, H * 0.07 + 76 * self.U, np.float32((20, 20, 24)), radius=38, op=0.8 * o); self.ltext(img, lab, cx, H * 0.07 + 38 * self.U, 38, True, o, jb.WHITE, align="center", maxw=240 * self.U)
            return img
        return self._add(draw, dur, kind="before_after", meta={}, **k)


    # ------------------------------------------------------------------ wire
    def _wire_shape(shape):
        import itertools
        if shape == "cube":
            V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]; E = [(i, j) for i, j in itertools.combinations(range(8), 2) if sum(a != b for a, b in zip(V[i], V[j])) == 1]
        elif shape == "pyramid":
            V = [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1), (0, -1.2, 0)]; E = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4), (3, 4)]
        elif shape == "cylinder":
            N = 28; V = [(np.cos(2 * np.pi * i / N), y, np.sin(2 * np.pi * i / N)) for y in (-0.9, 0.9) for i in range(N)]; E = [(i, (i + 1) % N) for i in range(N)] + [(N + i, N + (i + 1) % N) for i in range(N)] + [(i, N + i) for i in range(0, N, 2)]
        elif shape == "torus":
            U_, V_ = 28, 14; V = [((1.0 + 0.42 * np.cos(2 * np.pi * v / V_)) * np.cos(2 * np.pi * u / U_), 0.42 * np.sin(2 * np.pi * v / V_), (1.0 + 0.42 * np.cos(2 * np.pi * v / V_)) * np.sin(2 * np.pi * u / U_)) for u in range(U_) for v in range(V_)]
            E = [(u * V_ + v, u * V_ + (v + 1) % V_) for u in range(U_) for v in range(V_)] + [(u * V_ + v, ((u + 1) % U_) * V_ + v) for u in range(U_) for v in range(V_) if v % 2 == 0]
        else:                                                                    # sphere
            La, Lo = 10, 24; V = [(np.sin(np.pi * (a + 1) / (La + 1)) * np.cos(2 * np.pi * b / Lo), -np.cos(np.pi * (a + 1) / (La + 1)), np.sin(np.pi * (a + 1) / (La + 1)) * np.sin(2 * np.pi * b / Lo)) for a in range(La) for b in range(Lo)]
            E = [(a * Lo + b, a * Lo + (b + 1) % Lo) for a in range(La) for b in range(Lo)] + [(a * Lo + b, (a + 1) * Lo + b) for a in range(La - 1) for b in range(0, Lo, 2)]
        return np.float32(V), E
    def wire(self, shape="cylinder", label=None, dur=5.0, spin=1.0, **k):
        """A 3D wireframe drawn like a technical drawing: the edges draw themselves, then it turns slowly. shape: cube, pyramid, cylinder, torus, sphere.
        Best on the blueprint theme (white lines on blue) or on paper (ink lines)."""
        V, E = _wire_shape(shape)
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); ink = np.float32(self._ink); o = self._io(u, n, 6, 6); t = u / self.fps; S = min(W, H) * 0.30
            a, b = 0.5 + t * 0.55 * spin, 0.45 + 0.18 * np.sin(t * 0.7)
            Ry = np.float32([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]]); Rx = np.float32([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
            P = V @ Ry.T @ Rx.T; z = P[:, 2] + 4.2; sc = 4.2 / z; X = W / 2 + P[:, 0] * sc * S; Y = H * 0.46 + P[:, 1] * sc * S
            lay = np.zeros_like(img); prog = eo(u / max(n * 0.38, 4), 2); th = max(2, int(3.2 * self.U))
            for i, (p_, q_) in enumerate(E):
                g = clamp(prog * 1.6 - (i / len(E)) * 0.6)
                if g <= 0: continue
                x0, y0, x1, y1 = X[p_], Y[p_], X[p_] + (X[q_] - X[p_]) * g, Y[p_] + (Y[q_] - Y[p_]) * g; dep = clamp(1.25 - (z[p_] + z[q_]) / 2 / 6.5)
                cv2.line(lay, (int(x0), int(y0)), (int(x1), int(y1)), tuple(float(c) * (0.35 + 0.65 * dep) for c in ink), th, cv2.LINE_AA)
            glow = cv2.GaussianBlur(lay, (0, 0), 7 * self.U + 1); acc = np.float32(self._acc(1))
            img = img * (1 - np.clip(lay.max(2, keepdims=True) / 255.0, 0, 1) * o) + lay * o + glow * 0.5 * o * (1.0 if _lum(ink) > 120 else 0.0)
            for p_ in range(0, len(V), max(1, len(V) // 12)): cv2.circle(img, (int(X[p_]), int(Y[p_])), int(5 * self.U), tuple(float(c) for c in acc), -1, cv2.LINE_AA)
            if label: self.block(img, self.wrap(label, 64, True), H * 0.14, 64, True, eio((u - 6) / 10) * o, maxh=H * 0.14)
            return img
        return self._add(draw, dur, kind="wire", meta=dict(count=len(E)), **k)

    # ------------------------------------------------------------------ cta
    def cta(self, keyword, text="and I'll send you the link", lead="Comment", dur=4.0, **k):
        """The comment-keyword call to action: 'Comment KATANA and I'll send you the link'. The keyword types into a comment box, sends, and a DM badge pops."""
        kw = str(keyword).upper(); start = 18; per = 4
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); ink = np.float32(self._ink); o = self._io(u, n, 5, 6); a = np.float32(self._acc(1)); atx = np.float32((20, 20, 24)) if _lum(a) > 140 else jb.WHITE
            self.block(img, [lead], H * 0.27, 130, True, eio(u / 8) * o, scale=1 + 0.25 * (1 - eo(u / 8, 4)))
            bw, bh = W * 0.8, 120 * self.U; x0, y0 = (W - bw) / 2, H * 0.43; light = _lum(img[H // 2, W // 2]) > 140
            self.card(img, x0, y0, x0 + bw, y0 + bh, np.float32((236, 236, 240)) if light else np.float32((48, 46, 44)), radius=60, op=o * clamp(u / 6))
            typed = kw[:max(0, min(len(kw), (u - start) // per))]; sent = u > start + len(kw) * per + 14
            cur = "|" if (u // 7) % 2 == 0 and not sent else ""
            if not sent: self.ltext(img, (typed + cur) if typed or cur else "Add a comment...", x0 + 44 * self.U, y0 + bh / 2, 56, True, o, ink if typed else ink * 0.5, maxw=bw * 0.7)
            else: self.ltext(img, kw, x0 + 44 * self.U, y0 + bh / 2, 56, True, o * (1 - 0.5 * eio((u - start - len(kw) * per - 14) / 8)), ink)
            cx, cy = x0 + bw - 62 * self.U, y0 + bh / 2; cv2.circle(img, (int(cx), int(cy)), int(40 * self.U), tuple(float(c) for c in a), -1, cv2.LINE_AA)
            pts = np.int32([[cx - 12 * self.U, cy + 10 * self.U], [cx, cy - 14 * self.U], [cx + 12 * self.U, cy + 10 * self.U]]); cv2.polylines(img, [pts.reshape(-1, 1, 2)], False, tuple(float(c) for c in atx), max(3, int(5 * self.U)), cv2.LINE_AA)
            self.block(img, self.wrap(text, 58, False, W * 0.8), H * 0.62, 58, False, eio((u - 8) / 10) * o, maxh=H * 0.16)
            if sent:
                s = float(spring((u - start - len(kw) * per - 14) / 12, 1.8, 6)); r = 150 * self.U * max(s, 0.01); bx, by = W / 2, H * 0.78
                cv2.circle(img, (int(bx), int(by)), int(r), tuple(float(c) for c in a), -1, cv2.LINE_AA)
                if s > 0.5: self.ltext(img, "DM sent", bx, by, 52 * min(s, 1), True, 1.0, atx, align="center", maxw=r * 1.6)
            return img
        return self._add(draw, dur, kind="cta", meta=dict(count=len(kw), start=start, per=per), **k)


    # ------------------------------------------------------------------ shared drawing helpers for skits
    def _shade_box(self, img, cx, cy, w, h, color, radius=0.28, light=(-0.3, -0.5), op=1.0, tilt=0.0):
        """A softly lit rounded box (the clay / toy look): gradient from top-left light, a glossy highlight."""
        x0, y0, x1, y1 = int(cx - w / 2 - 6), int(cy - h / 2 - 6), int(cx + w / 2 + 6), int(cy + h / 2 + 6)
        xa, xb, ya, yb = max(x0, 0), min(x1, self.W), max(y0, 0), min(y1, self.H)
        if xb <= xa or yb <= ya: return
        gy, gx = np.mgrid[ya:yb, xa:xb].astype(np.float32); m = np.zeros((yb - ya, xb - xa), np.float32); r = int(min(w, h) * radius)
        rx0, ry0, rx1, ry1 = int(cx - w / 2) - xa, int(cy - h / 2) - ya, int(cx + w / 2) - xa, int(cy + h / 2) - ya
        cv2.rectangle(m, (rx0 + r, ry0), (rx1 - r, ry1), 1, -1); cv2.rectangle(m, (rx0, ry0 + r), (rx1, ry1 - r), 1, -1)
        for px, py in ((rx0 + r, ry0 + r), (rx1 - r, ry0 + r), (rx0 + r, ry1 - r), (rx1 - r, ry1 - r)): cv2.circle(m, (px, py), r, 1, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.2); nx, ny = (gx - cx) / (w / 2), (gy - cy) / (h / 2); d = np.clip(1 - (nx * nx + ny * ny) * 0.5, 0, 1)
        sh = 0.62 + 0.38 * np.clip(0.5 - 0.5 * (nx * light[0] + ny * light[1]) * 1.2, 0, 1) + 0.10 * d; hl = np.exp(-(((nx + 0.35) / 0.35) ** 2 + ((ny + 0.45) / 0.22) ** 2)) * 0.28
        col_ = np.float32(color)[None, None, :] * sh[..., None] + 255 * hl[..., None]; a = (m * op)[..., None]
        reg = img[ya:yb, xa:xb]; reg[:] = reg * (1 - a) + np.clip(col_, 0, 255) * a
    setattr(Film, "_shade_box", _shade_box)

    def _bokeh(self, f, base, n_=26, seed=3):
        """Out-of-focus lights over a dark colour: the depth-of-field backdrop."""
        W, H = self.W, self.H; img = np.broadcast_to(np.float32(base), (H, W, 3)).astype(np.float32).copy(); r = np.random.default_rng(seed); lay = np.zeros((H, W, 3), np.float32)
        for i in range(n_):
            x = (r.uniform(0, W) + 12 * np.sin(f / self.fps * 0.4 + i)) % W; y = r.uniform(0, H * 0.7); rad = r.uniform(0.025, 0.06) * W; c = np.float32((130, 220, 250)) * r.uniform(0.55, 1.0) if r.random() < 0.7 else np.float32((70, 170, 250)) * r.uniform(0.5, 0.95)
            cv2.circle(lay, (int(x), int(y)), int(rad), tuple(float(q) for q in c), -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 6 * self.U + 1); vig = np.clip(1 - 0.5 * (((jb.xx - W / 2) / (W * 0.7)) ** 2 + ((jb.yy - H / 2) / (H * 0.7)) ** 2), 0.3, 1)[..., None]
        return (img + lay * 0.55) * vig
    setattr(Film, "_bokeh", _bokeh)

    # ------------------------------------------------------------------ skit (two or three characters, one beat each)
    def _rpaste(self, img, fr, x0, y0, w, h, radius, op=1.0):
        """Paste picture fr (any size) into img at (x0, y0, w, h) with rounded corners."""
        x0, y0, w, h = int(x0), int(y0), int(w), int(h)
        if w < 4 or h < 4: return
        fr = cv2.resize(np.asarray(fr, np.float32), (w, h), interpolation=cv2.INTER_AREA); m = np.zeros((h, w), np.float32); r = int(min(radius * self.U, w / 2, h / 2))
        cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
        for px, py in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)): cv2.circle(m, (px, py), r, 1, -1, cv2.LINE_AA)
        ya, yb, xa, xb = max(y0, 0), min(y0 + h, self.H), max(x0, 0), min(x0 + w, self.W)
        if yb <= ya or xb <= xa: return
        a = (m[ya - y0:yb - y0, xa - x0:xb - x0] * op)[..., None]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + fr[ya - y0:yb - y0, xa - x0:xb - x0] * a
    setattr(Film, "_rpaste", _rpaste)

    def _skit_head(self, img, cx, cy, s, skin, hair, expr, t, talk):
        U = self.U; skc = np.float32(col(skin)); hc = np.float32(col(hair)); hy = cy - s * 0.04
        self._shade_box(img, cx, cy + s * 0.58, s * 1.18, s * 0.5, np.float32((52, 46, 50)), radius=0.3)                          # shoulders
        self._shade_box(img, cx, hy + s * 0.42, s * 0.22, s * 0.16, skc * 0.92, radius=0.2)                                       # neck
        self._shade_box(img, cx, hy - s * 0.12, s * 0.80, s * 0.74, hc, radius=0.28)                                              # back hair
        self._shade_box(img, cx, hy, s * 0.66, s * 0.62, skc, radius=0.22)                                                        # face
        self._shade_box(img, cx, hy - s * 0.30, s * 0.78, s * 0.20, hc, radius=0.3)                                               # fringe
        lid = {"sleepy": 0.45, "closed": 0.92}.get(expr, 0.0)
        for sx in (-1, 1):
            gx_, gy_ = cx + sx * s * 0.17, hy + s * 0.02; rr = int(s * 0.115); cv2.circle(img, (int(gx_), int(gy_)), rr, (250, 250, 250), -1, cv2.LINE_AA)
            px_ = gx_ + 3 * np.sin(t * 0.9); cv2.circle(img, (int(px_), int(gy_ + rr * 0.1)), int(rr * 0.42), (24, 22, 22), -1, cv2.LINE_AA); cv2.circle(img, (int(px_ - rr * 0.12), int(gy_ - rr * 0.1)), max(2, int(rr * 0.12)), (255, 255, 255), -1, cv2.LINE_AA)
            if lid:                                                                                                                # eyelids: skin colour over the top of the eye
                m = np.zeros(img.shape[:2], np.float32); cv2.circle(m, (int(gx_), int(gy_)), rr, 1, -1, cv2.LINE_AA); yy_ = np.arange(img.shape[0], dtype=np.float32)[:, None]; m *= (yy_ < gy_ - rr + 2 * rr * lid)
                img[:] = img * (1 - m[..., None]) + (skc * 0.97) * m[..., None]; cv2.line(img, (int(gx_ - rr), int(gy_ - rr + 2 * rr * lid)), (int(gx_ + rr), int(gy_ - rr + 2 * rr * lid)), (50, 40, 38), max(2, int(s * 0.008)), cv2.LINE_AA)
            cv2.circle(img, (int(gx_), int(gy_)), rr, (22, 20, 20), max(3, int(s * 0.016)), cv2.LINE_AA)
            tilt = {"flat": 0, "raised": 0, "angry": -0.14, "sad": 0.14, "sleepy": 0.04, "closed": 0.04}.get(expr, 0) * sx; by_ = gy_ - rr * 1.45 - (s * 0.03 if expr == "raised" else 0)
            cv2.line(img, (int(gx_ - rr * 0.9), int(by_ - tilt * s * 0.3)), (int(gx_ + rr * 0.9), int(by_ + tilt * s * 0.3)), (30, 26, 24), max(4, int(s * 0.02)), cv2.LINE_AA)
        cv2.line(img, (int(cx - s * 0.05), int(hy + s * 0.02)), (int(cx + s * 0.05), int(hy + s * 0.02)), (22, 20, 20), max(3, int(s * 0.01)), cv2.LINE_AA)
        mh = s * (0.015 + 0.04 * talk); self._shade_box(img, cx, hy + s * 0.24, s * 0.09, max(mh, 3), np.float32((70, 60, 190)), radius=0.4)
    setattr(Film, "_skit_head", _skit_head)

    def _skit_cube(self, img, cx, cy, s, color, glyph, t, talk, shadow=True):
        U = self.U; blink = 0.15 if (int(t * 2.2) % 5 == 0 and (t * 2.2) % 1 < 0.12) else 1.0; sq = 1 + 0.025 * talk; c = np.float32(col(color))
        if shadow:
            sh = np.zeros(img.shape[:2], np.float32); cv2.ellipse(sh, (int(cx), int(cy + s * 0.50)), (int(s * 0.46), int(s * 0.07)), 0, 0, 360, 1, -1); sh = cv2.GaussianBlur(sh, (0, 0), 14 * U + 2); img[:] = img * (1 - 0.55 * sh[..., None])
        for sx in (-0.2, 0.2): self._shade_box(img, cx + sx * s, cy + s * 0.42, s * 0.19, s * 0.22, c * 0.82, radius=0.3)
        self._shade_box(img, cx, cy, s * 0.82, s * 0.70 * sq, c, radius=0.30)
        if glyph:
            self.ltext(img, glyph, cx, cy + s * 0.02, s * 0.2 / U, True, 0.95, np.float32((255, 255, 255)), align="center")
        else:
            for sx in (-0.19, 0.19):
                ex, ey = cx + sx * s, cy - s * 0.02; eh = s * 0.15 * blink; self._shade_box(img, ex, ey, s * 0.07, eh, np.float32((22, 20, 20)), radius=0.5); cv2.circle(img, (int(ex), int(ey - eh * 0.22)), max(2, int(s * 0.011)), (255, 255, 255), -1, cv2.LINE_AA)
    setattr(Film, "_skit_cube", _skit_cube)

    def skit(self, who, line=None, label=None, pip=None, room="night", cube="#f58a3a", glyph=None, skin="#e9b68f", hair="#4a3426", expr="flat", view="close", notice=None, pip_h=0.35,
             pill=None, paper=None, extras=(), dim=None, shake=0.0, shot=None, cap=None, dur=None, **k):
        """One beat of a skit with up to three characters. who: "cube" (a toy bot; recolour with cube="#hex", put a symbol on its face with glyph=">_") or "head" (a person with big glasses).
        line: the caption under a coloured name pill (None = no caption). view: "close" (the character fills the frame) or "wide" (the person at a desk, a small bot on the shoulder,
        a monitor at the left that shows pip). pip: a picture path or a function (u, n, f) -> frame, shown as a rounded card at the top (pip_h = its height as a fraction of the frame).
        notice=("Dana (client)", "love it, can it feel warmer?") adds a phone-style banner (a third item is a reply shown under it). room: night (blue, bokeh), warm (brown) or desk (night with a desk). expr: flat, raised, angry, sad, sleepy, closed.
        paper="DESIGN\\n02" lays a sheet on the desk; extras=("bot",) adds a small purple terminal cube to a wide view. pill: name pill colour. shot=(offset_s, total_s): this scene is a slice of one longer continuous shot, so the slow camera push carries on across slices. cap=(from_s, to_s): the caption shows only in that window of the scene. shake: camera jitter in pixels (a typing, working look; 0 = steady). dim: room darkness (1.0 as drawn, default kinds.SKIT_DIM). label defaults to CLAUDE for a cube and YOU for a head."""
        assert who in ("cube", "head"), "who: cube or head"; assert view in ("close", "wide")
        label = label or ("CLAUDE" if who == "cube" else "YOU"); pil = np.float32(col(pill or (cube if who == "cube" else "#5b7bd5"))); pip_im = jb.art(pip) if isinstance(pip, str) else None; has_pip = pip_im is not None or callable(pip)
        D = dur or max(2.2, 0.55 + 0.085 * len((line or "x").split()) + 0.3)
        def draw(u, n, f):
            u0, n0 = ((shot[0] * self.fps, shot[1] * self.fps) if shot else (0, n)); W, H = self.W, self.H; U = self.U; t = (u + u0) / self.fps; o = 1.0 if self.exact else self._io(u, n, 3, 4); talk = max(0.0, np.sin(t * 17)) * (1 if (line and 3 < u < n - 6) else 0)
            base = {"night": np.float32((112, 46, 22)), "warm": np.float32((30, 48, 78)), "desk": np.float32((96, 38, 18))}[room]; img = self._bokeh(f, base, seed=9 if room == "warm" else 5)
            if room == "warm": img = img * 0.75 + np.float32((20, 40, 70)) * 0.25
            img = img * (SKIT_DIM if dim is None else dim)                                  # the room is dimmed; the characters and props are drawn on top, lit
            z = 1.0 + 0.04 * ((u + u0) / max(n0, 1)) + 0.05 * np.exp(-(u + u0) / 4); ink_w = np.float32((255, 255, 255))
            if view == "wide":
                cx, cy = W / 2 + 4 * np.sin(t * 1.3), H * 0.66
                self._shade_box(img, W * 0.50, H * 0.97, W * 1.15, H * 0.42, np.float32((44, 36, 46)), radius=0.12)                    # chair back
                for sx in (0.10, 0.90): self._shade_box(img, W * sx, H * 0.86, W * 0.26, H * 0.16, np.float32((58, 48, 60)), radius=0.35)  # armrests
                self._skit_head(img, cx, cy, W * 0.80 * z, skin, hair, expr, t, talk)
                self._skit_cube(img, W * 0.90, H * 0.78, W * 0.13, cube if who == "cube" else "#e0733a", None, t, 0, shadow=False) if "nobot" not in extras else None
                mon = pip if has_pip else None
                q = np.float32([[-0.04 * W, 0.52 * H], [0.19 * W, 0.555 * H], [0.19 * W, 0.78 * H], [-0.04 * W, 0.83 * H]]); cv2.fillConvexPoly(img, np.int32(q), (16, 14, 14), cv2.LINE_AA)
                if has_pip:
                    fr = (pip(u, n, f) if callable(pip) else pip_im); fr = cv2.resize(np.asarray(fr, np.float32), (400, 300)); M = cv2.getPerspectiveTransform(np.float32([[0, 0], [400, 0], [400, 300], [0, 300]]), q * 0.995 + np.float32([[3, 3], [-3, 3], [-3, -3], [3, -3]]) * U)
                    lay = cv2.warpPerspective(fr, M, (W, H)); mk = cv2.warpPerspective(np.ones((300, 400), np.float32), M, (W, H))[..., None]; img = img * (1 - mk) + lay * mk
                if "bot" in extras:
                    self._skit_cube(img, W * 0.13, H * 0.93, W * 0.30, "#4a3fd0", ">_", t, 0, shadow=False)
                if paper: self._paper(img, W * 0.30, H * 0.955, W * 0.2, paper, -0.12)
            else:
                cx, cy = W / 2 + 6 * np.sin(t * 1.3), (H * 0.50 if who == "head" else H * 0.50) + 6 * np.sin(t * 2.0)
                if room == "desk": img[int(H * 0.80):] = img[int(H * 0.80):] * 0.55 + np.float32((18, 38, 70)) * 0.45
                if who == "cube":
                    self._shade_box(img, W * 0.55, H * 0.86, W * 1.5, H * 0.46, np.float32((52, 42, 56)), radius=0.22); self._shade_box(img, W * 0.05, H * 0.45, W * 0.30, H * 0.9, np.float32((44, 36, 48)), radius=0.2)   # sofa
                    self._skit_cube(img, cx, cy + (H * 0.04 if room == "desk" else 0), W * (0.88 if room == "desk" else 0.86) * z, cube, glyph, t, talk)
                else: self._skit_head(img, cx, cy, W * 1.2 * z, skin, hair, expr, t, talk)
                if paper: self._paper(img, W * 0.80, H * 0.935, W * 0.38, paper, -0.06)
            if shake: img = cv2.warpAffine(img, np.float32([[1, 0, shake * U * (np.sin(f * 2.3) + np.sin(f * 5.9 + 1))], [0, 1, shake * U * (np.sin(f * 3.1 + 2) + np.sin(f * 7.3))]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            yy_ = (jb.yy / H)[..., None]; img = img * (1 - 0.30 * np.clip((yy_ - 0.60) / 0.40, 0, 1) ** 1.3)      # the room light falls off down the frame
            top = 0.0
            if has_pip and view == "close":
                pw, ph = W * 0.92, H * pip_h; px0, py0 = (W - pw) / 2, H * 0.037 - (1 - eo(u / 8, 3)) * (0 if self.exact else H * 0.3); fr = pip(u, n, f) if callable(pip) else pip_im
                self._rpaste(img, fr, px0, py0, pw, ph, 22, o)
            if has_pip and view == "wide": pw, ph = W * 0.92, H * pip_h; px0, py0 = (W - pw) / 2, H * 0.037; self._rpaste(img, pip(u, n, f) if callable(pip) else pip_im, px0, py0, pw, ph, 22, o)
            if notice:
                nw, nh = W * 0.80, H * (0.092 if len(notice) > 2 else 0.062); nx, ny = (W - nw) / 2 + W * 0.03, H * (0.052 if has_pip else 0.06) + (1 - eo(u / 6, 3)) * (0 if self.exact else -H * 0.1)
                self.card(img, nx, ny, nx + nw, ny + nh, np.float32((46, 42, 40)), radius=20, op=0.97 * o); cv2.circle(img, (int(nx + 38 * U), int(ny + nh * 0.35)), int(20 * U), (58, 112, 232), -1, cv2.LINE_AA)
                self.ltext(img, notice[0][:1], nx + 38 * U, ny + nh * 0.35, 26, True, 1.0, ink_w, align="center"); self.ltext(img, notice[0], nx + 76 * U, ny + nh * 0.30, 27, True, 1.0, ink_w, maxw=nw * 0.6); self.ltext(img, "now", nx + nw - 20 * U, ny + nh * 0.30, 22, False, 0.7, ink_w, align="right")
                self.ltext(img, notice[1], nx + 76 * U, ny + nh * (0.50 if len(notice) > 2 else 0.70), 24, False, 0.95, ink_w, maxw=nw - 100 * U)
                if len(notice) > 2: self.ltext(img, notice[2], nx + 76 * U, ny + nh * 0.78, 24, False, 0.95, np.float32((200, 200, 205)), maxw=nw - 100 * U)
            if line and (cap is None or cap[0] <= u / self.fps < cap[1]):
                if has_pip: ty = H * (0.037 + pip_h + 0.045); pill_y = ty; ly = ty + 0.027 * H + 0
                else: pill_y = H * 0.085; ly = pill_y
                wd = self._len(label, 28, True) + 40 * U; ph_ = 30 * U
                self.card(img, W / 2 - wd / 2, pill_y - ph_ * 0.5, W / 2 + wd / 2, pill_y + ph_ * 0.5 + 2 * U, pil, radius=6, op=o); self.ltext(img, label, W / 2, pill_y + 1.0 * U, 26, True, o, ink_w, align="center")
                lines = self.wrap(line, 44, True, W * 0.84); self.block(img, lines, pill_y + 30 * U + (len(lines) * 44 * U * 1.18) / 2 + 6 * U, 44, True, o, color=ink_w, shadow=0.7, maxh=H * 0.2, maxw=W * 0.88)
            return img
        return self._add(draw, D, kind="skit", meta=dict(who=who, line=bool(line), pip=has_pip, notice=bool(notice)), **k)

    def _paper(self, img, cx, cy, w, text, rot=0.0):
        U = self.U; h = w * 0.62; M = cv2.getRotationMatrix2D((cx, cy), np.degrees(rot), 1.0); pts = np.float32([[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2], [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]]); pts = (M[:, :2] @ pts.T).T + M[:, 2]
        cv2.fillConvexPoly(img, np.int32(pts), (232, 232, 236), cv2.LINE_AA); lines = text.split("\n")
        for i, l in enumerate(lines): self.ltext(img, l, cx - w * 0.36, cy - h * 0.2 + i * h * 0.38, w * 0.2 / U, True, 0.95, np.float32((50, 44, 42)))
    setattr(Film, "_paper", _paper)

    # ------------------------------------------------------------------ laptop (POV, with reflection)
    def laptop(self, media, pov="client paid $2,750 for this", dur=4.0, **k):
        """A laptop on a glossy dark desk, filmed from the front, with a mirror reflection below. media: a picture path or a function (u, n, f) -> frame (any size)
        that is shown on the screen. pov: the pill at the top-left with a cursor icon ("POV: ...")."""
        img0 = jb.art(media) if isinstance(media, str) else None
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; o = self._io(u, n, 5, 5); g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            bg = (np.float32((74, 70, 66)) * (1 - g) + np.float32((22, 20, 20)) * g) * np.ones((H, W, 1), np.float32); sw = W * 0.88; sh = sw * 0.60; cx, ytop = W / 2, H * 0.30
            frm = media(u, n, f) if callable(media) else img0; frm = cv2.resize(np.asarray(frm, np.float32), (int(sw * 0.94), int(sh * 0.90)), interpolation=cv2.INTER_AREA)
            scr = np.zeros((int(sh), int(sw), 3), np.float32); scr[:] = (18, 16, 16); oy, ox = int(sh * 0.05), int(sw * 0.03); scr[oy:oy + frm.shape[0], ox:ox + frm.shape[1]] = frm
            tl, tr_ = (cx - sw / 2, ytop), (cx + sw / 2, ytop); bl, br = (cx - sw / 2 * 0.985, ytop + sh), (cx + sw / 2 * 0.985, ytop + sh)
            M = cv2.getPerspectiveTransform(np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]), np.float32([tl, tr_, br, bl])); lay = cv2.warpPerspective(scr, M, (W, H), borderValue=(0, 0, 0)); mk = cv2.warpPerspective(np.ones((int(sh), int(sw)), np.float32), M, (W, H))[..., None]
            img = bg * (1 - mk) + lay * mk; base = np.int32([[cx - sw / 2 * 0.985, ytop + sh], [cx + sw / 2 * 0.985, ytop + sh], [cx + sw / 2 * 1.04, ytop + sh + H * 0.065], [cx - sw / 2 * 1.04, ytop + sh + H * 0.065]])
            cv2.fillConvexPoly(img, base, (30, 28, 28), cv2.LINE_AA); cv2.line(img, (int(cx - sw / 2 * 0.985), int(ytop + sh)), (int(cx + sw / 2 * 0.985), int(ytop + sh)), (70, 66, 64), max(2, int(3 * U)), cv2.LINE_AA)
            desk_y = int(ytop + sh + H * 0.065); refl = img[max(2 * desk_y - H, 0):desk_y][::-1].copy(); rh = min(refl.shape[0], H - desk_y)
            if rh > 0: fade = np.linspace(0.42, 0.0, rh, dtype=np.float32)[:, None, None]; rf = cv2.GaussianBlur(refl[:rh], (0, 0), 3 * U + 1); img[desk_y:desk_y + rh] = img[desk_y:desk_y + rh] * (1 - fade) + rf * fade
            if pov:
                wd = self._len(pov, 46, True) + 130 * U; x0, y0 = W * 0.06, H * 0.075; self.ltext(img, "POV: " + pov, x0 + 96 * U, y0, 46, True, o, jb.WHITE, maxw=W * 0.86 - 96 * U)
                cx_, cy_ = x0 + 42 * U, y0; cv2.circle(img, (int(cx_), int(cy_)), int(38 * U), (255, 255, 255), -1, cv2.LINE_AA); pts = np.int32([[cx_ - 12 * U, cy_ + 14 * U], [cx_ - 12 * U, cy_ - 16 * U], [cx_ + 16 * U, cy_ + 6 * U], [cx_ + 2 * U, cy_ + 6 * U]]); cv2.fillConvexPoly(img, pts, (20, 20, 20), cv2.LINE_AA)
            return img * (0.35 + 0.65 * o) if o < 1 else img
        return self._add(draw, dur, kind="laptop", meta={}, **k)


    # ------------------------------------------------------------------ notes (Apple Notes style ad)
    def notes(self, title, items, folder="Notes", dur=None, **k):
        """A notes-app screen that types itself: a bold title, then lines or a checklist. Items starting with "[x] " tick, "[ ] " stay open.
        The "Apple Notes ad" format: a plain note that quietly sells something."""
        rows = []
        for it in items:
            ck = None; s_ = str(it)
            if s_.startswith("[x] "): ck, s_ = True, s_[4:]
            elif s_.startswith("[ ] "): ck, s_ = False, s_[4:]
            rows.append((ck, s_))
        per = 3; t0 = 20 + len(title) * 3
        starts = []; acc = t0
        for ck, s_ in rows: starts.append(acc); acc += len(s_) * per + 14
        total = acc + 24
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; img = np.broadcast_to(np.float32((236, 246, 252)), (H, W, 3)).copy(); o = self._io(u, n, 4, 5); ink = np.float32((28, 28, 30)); yel = np.float32((10, 190, 245))
            self.ltext(img, "\u2039 " + folder, W * 0.05, H * 0.07, 46, True, 1.0, yel); self.ltext(img, "Done", W * 0.95, H * 0.07, 46, True, 1.0, yel, align="right")
            ty = H * 0.17; typed = title[:max(0, (u - 8) // 3)]; self.ltext(img, typed + ("|" if (u // 8) % 2 == 0 and len(typed) < len(title) + 1 and u < t0 else ""), W * 0.07, ty, 82, True, 1.0, ink, maxw=W * 0.86)
            self.ltext(img, "Today at 9:41", W * 0.07, ty + 70 * U, 32, False, 0.5, ink)
            y = H * 0.27; lh = min(H * 0.075, (H * 0.66) / max(len(rows), 1))
            for i, (ck, s_) in enumerate(rows):
                v = u - starts[i]
                if v < 0: continue
                typed = s_[:int(v // per) + 1]; x = W * 0.07
                if ck is not None:
                    cv2.circle(img, (int(x + 22 * U), int(y)), int(22 * U), tuple(float(q) for q in (yel if ck else np.float32((170, 170, 175)))), -1 if (ck and v > len(s_) * per) else max(3, int(4 * U)), cv2.LINE_AA)
                    if ck and v > len(s_) * per: cv2.polylines(img, [np.int32([[x + 11 * U, y], [x + 19 * U, y + 9 * U], [x + 33 * U, y - 9 * U]]).reshape(-1, 1, 2)], False, (255, 255, 255), max(3, int(5 * U)), cv2.LINE_AA)
                    x += 66 * U
                self.ltext(img, typed + ("|" if (u // 8) % 2 == 0 and len(typed) < len(s_) else ""), x, y, 52, False, o, ink * (0.45 if (ck and v > len(s_) * per + 8) else 1.0), maxw=W * 0.9 - x)
                y += lh
            return img
        return self._add(draw, dur or total / self.fps + 1.2, kind="notes", meta=dict(count=sum(len(s_) for _, s_ in rows) + len(title)), **k)

    # ------------------------------------------------------------------ review (social proof cards)
    def review(self, reviews, rating="4.9", count="2,431 reviews", badge="Product Hunt #1", dur=None, **k):
        """Social proof: review cards drop in one at a time with stars and a name, and a live badge with the rating. reviews: [("quote", "Name"), ...]."""
        N = len(reviews); step = max(self.beat * 2, self._snap(1.4))
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; img = self.bg(None, u, n, f); o = self._io(u, n, 5, 6); a = np.float32(self._acc(1)); ink = np.float32(self._ink)
            dot = 0.5 + 0.5 * np.sin(f * 0.25); cv2.circle(img, (int(W * 0.09), int(H * 0.075)), int(11 * U), (80, 220, 90) if dot > 0.3 else (50, 150, 60), -1, cv2.LINE_AA); self.ltext(img, "Live now", W * 0.09 + 28 * U, H * 0.075, 36, True, o, ink)
            self.block(img, [rating], H * 0.17, 150, True, eio(u / 8) * o, color=a, shadow=0, scale=1 + 0.2 * (1 - eo(u / 8, 4)), maxh=H * 0.14, maxw=W * 0.5); self._star(img, W / 2 + self._len(rating, 150, True) / 2 + 70 * U, H * 0.17, 52 * U, a, eio(u / 8) * o); self.ltext(img, count + "  \u00b7  " + badge, W / 2, H * 0.245, 38, False, o * 0.9, ink, align="center", maxw=W * 0.9)
            cur = min(max((u - 10) // step, -1), N - 1); cw = W * 0.86; ch = H * 0.15
            for i in range(cur + 1):
                v = u - 10 - i * step; slot = cur - i; y = H * 0.33 + slot * (ch + 24 * U) * 1.0
                if y > H * 0.95: continue
                s = float(spring(v / 14, 1.6, 6)); yy_ = y - (1 - min(s, 1.0)) * H * 0.2; card = np.float32((255, 255, 255)) if _lum(img[H // 2, W // 2]) < 200 or True else np.float32((40, 40, 40))
                self.card(img, W * 0.07, yy_, W * 0.07 + cw, yy_ + ch, card, radius=34, op=o * clamp(v / 5) * (1.0 if slot == 0 else 0.92))
                for j in range(5): self._star(img, W * 0.07 + 44 * U + j * 44 * U, yy_ + 36 * U, 17 * U, np.float32((40, 170, 250)), o * clamp(v / 5))
                q, by = reviews[i]; self.block(img, self.wrap(q, 40, True, cw * 0.88), yy_ + ch * 0.55, 40, True, o * clamp(v / 6), color=np.float32((28, 28, 30)), shadow=0, maxw=cw * 0.9, maxh=ch * 0.5)
                self.ltext(img, by, W * 0.07 + cw - 34 * U, yy_ + 36 * U, 32, False, o * clamp(v / 6) * 0.7, np.float32((90, 90, 95)), align="right", maxw=cw * 0.4)
            return img
        return self._add(draw, dur or (14 + N * step) / self.fps + 1.0, kind="review", meta=dict(count=N, step=step), **k)

    # ------------------------------------------------------------------ wrapped (recap story cards)
    def wrapped(self, stats, title="Your year", dur=None, **k):
        """A 'Wrapped' recap: one full-colour story card per stat, with story progress bars at the top. stats: [("12,480", "minutes listened"), ("#1", "Midnight City"), ...];
        a stat's first value may be a list to show a ranked list instead of a big number."""
        N = len(stats); seg = max(self.beat * 3, self._snap(1.7))
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; i = min(max(u, 0) // seg, N - 1); v = u - i * seg; c = self._fc(i); img = self._field(c); ink = self._ink; o = self._io(u, n, 3, 5)
            bw = (W * 0.9 - 8 * U * (N - 1)) / N
            for j in range(N):
                x0 = W * 0.05 + j * (bw + 8 * U); fill = 1.0 if j < i else (clamp(v / seg) if j == i else 0.0); cv2.rectangle(img, (int(x0), int(H * 0.04)), (int(x0 + bw), int(H * 0.04 + 8 * U)), tuple(float(q) * 0.35 + float(img[0, 0, b_]) * 0.65 for b_, q in enumerate(ink)), -1)
                cv2.rectangle(img, (int(x0), int(H * 0.04)), (int(x0 + bw * fill), int(H * 0.04 + 8 * U)), tuple(float(q) for q in ink), -1)
            big, lab = stats[i]; self.block(img, [title], H * 0.10, 50, False, o * 0.8, color=ink, shadow=0)
            if isinstance(big, (list, tuple)):
                for r_, name in enumerate(big[:5]):
                    g = eio((v - 4 - r_ * 4) / 8); self.ltext(img, str(r_ + 1), W * 0.12, H * 0.32 + r_ * H * 0.1, 84, True, g * o, ink * 0.55); self.ltext(img, str(name), W * 0.24 + 20 * U * (1 - g), H * 0.32 + r_ * H * 0.1, 66, True, g * o, ink, maxw=W * 0.66)
                self.block(img, self.wrap(lab, 52, False, W * 0.8), H * 0.86, 52, False, eio((v - 4) / 8) * o, color=ink, shadow=0)
            else:
                s_ = float(spring(v / 16, 1.4, 6)); self.block(img, [str(big)], H * 0.44, 300, True, clamp((v + 1) / 3) * o, color=ink, shadow=0, scale=0.6 + 0.4 * min(s_, 1.15), maxw=W * 0.9, maxh=H * 0.34)
                self.block(img, self.wrap(lab, 62, False, W * 0.8), H * 0.62, 62, False, eio((v - 6) / 8) * o, color=ink, shadow=0, maxh=H * 0.16)
            return img
        return self._add(draw, dur or seg * N / self.fps, kind="wrapped", meta=dict(seg=seg, count=N), **k)

    # ------------------------------------------------------------------ lyrics (karaoke)
    def lyrics(self, lines, per=2.0, **k):
        """Lyric / karaoke video: the lines sit stacked, the current one lights up word by word and the rest dim; the block scrolls as it goes."""
        N = len(lines); seg = max(self.beat * 2, int(round(per * self.fps / self.beat)) * self.beat)
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; img = self.bg(None, u, n, f); o = self._io(u, n, 6, 6); ink = np.float32(self._ink); a = np.float32(self._acc(1)); i = min(max(u, 0) // seg, N - 1); v = (u - i * seg) / seg
            sz = 78; lh = sz * 1.5 * U; cy = H * 0.5 - (i + eo(min(v * 4, 1))) * lh * 0 ; off = (i + eio(clamp(v * 5))) * lh
            for j in range(N):
                y = H * 0.5 + j * lh - off
                if y < -lh or y > H + lh: continue
                d = abs(j - (i + eio(clamp(v * 5)))); op = o * np.clip(1 - 0.28 * d, 0.1, 1.0)
                words = lines[j].split(); tot = sum(self._len(w + " ", sz, True) for w in words); x = (W - tot) / 2; prog = (v * 1.2 if j == i else (1.0 if j < i else 0.0)) * len(words)
                for w_i, w in enumerate(words):
                    ww = self._len(w + " ", sz, True); lit = clamp(prog - w_i); c = ink * (0.40 + 0.60 * lit) if j == i else (ink * 0.4 if j > i else ink * 0.6); self.ltext(img, w, x, y, sz, True, op, c); x += ww
            return img
        return self._add(draw, seg * N / self.fps + 0.5, kind="lyrics", meta=dict(seg=seg, count=N), **k)

    # ------------------------------------------------------------------ changelog (release notes)
    def changelog(self, version, items, title="What's new", dur=None, **k):
        """A release-notes video: a big version badge, then each change with its tag pill. items: [("NEW", "Dark mode"), ("FIX", "Login loop"), ("IMPROVED", "Faster sync")]."""
        N = len(items); step = max(self.beat, self._snap(0.9)); tags = {"NEW": "#2fbf71", "FIX": "#e5484d", "IMPROVED": "#3e63dd", "BETA": "#f5a524", "REMOVED": "#8b8d98"}
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; img = self.bg(None, u, n, f); o = self._io(u, n, 5, 6); ink = np.float32(self._ink)
            s = float(spring(u / 16, 1.5, 6)); bw, bh = 360 * U, 150 * U; a = np.float32(self._acc(1)); atx = np.float32((20, 20, 24)) if _lum(a) > 140 else jb.WHITE
            self.card(img, W / 2 - bw / 2 * min(s, 1.05), H * 0.12, W / 2 + bw / 2 * min(s, 1.05), H * 0.12 + bh * min(s, 1.05), a, radius=60, op=o)
            if s > 0.5: self.ltext(img, str(version), W / 2, H * 0.12 + bh / 2, 92, True, o, atx, align="center", maxw=bw * 0.85)
            self.block(img, [title], H * 0.12 + bh + 80 * U, 64, True, eio((u - 8) / 8) * o, maxh=H * 0.1)
            y0 = H * 0.42; lh = min(H * 0.11, (H * 0.5) / max(N, 1))
            for i, it in enumerate(items):
                tag, txt = it if isinstance(it, (tuple, list)) else ("NEW", it); v = u - 14 - i * step
                if v < 0: continue
                g = eio(v / 8); y = y0 + i * lh; tc = col(tags.get(str(tag).upper(), "#3e63dd")); wd = self._len(str(tag).upper(), 30, True) + 34 * U
                self.card(img, W * 0.07, y - 28 * U, W * 0.07 + wd, y + 28 * U, tc, radius=14, op=g * o); self.ltext(img, str(tag).upper(), W * 0.07 + wd / 2, y, 30, True, g * o, jb.WHITE, align="center")
                self.ltext(img, str(txt), W * 0.07 + wd + 30 * U + 20 * U * (1 - g), y, 54, True, g * o, ink, maxw=W * 0.93 - (W * 0.07 + wd + 30 * U))
            return img
        return self._add(draw, dur or (20 + N * step) / self.fps + 1.2, kind="changelog", meta=dict(count=N, step=step), **k)


    # ------------------------------------------------------------------ sprite (play a sprite sheet or turntable)
    def sprite(self, sheet, cols=None, rows=None, frames=None, fps=None, size=0.55, x=0.5, y=0.62, travel=False, flip=False, text=None, dur=3.0, shadow=True, **k):
        """Play a sprite sheet: a registered asset name (from the asset library, e.g. a Blender character) or an image path with transparency.
        cols, rows, frames, fps come from the asset when it has them. size is the character's height as a fraction of the shorter side; travel=True walks it across the frame."""
        meta = {}
        if not os.path.exists(str(sheet)):
            import assets; meta = assets.data(sheet); sheet = assets.path(sheet)
        cols, rows = cols or meta.get("cols", 1), rows or meta.get("rows", 1); frames = frames or meta.get("frames") or cols * rows; fps = fps or meta.get("fps", 12)
        im = cv2.imread(sheet, cv2.IMREAD_UNCHANGED)
        if im is None: raise FileNotFoundError(sheet)
        if im.shape[2] == 3: im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        ch, cw = im.shape[0] // rows, im.shape[1] // cols; cells = [im[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw].astype(np.float32) for i in range(frames)]
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); o = self._io(u, n, 4, 5); cell = cells[int(u * fps / self.fps) % frames]
            if flip: cell = cell[:, ::-1]
            hh = min(W, H) * size; k_ = hh / ch; px = W * (-0.15 + 1.3 * u / n) if travel else W * x; py = H * y
            M = np.float32([[k_, 0, px - cw * k_ / 2], [0, k_, py - ch * k_ / 2]]); pr = cv2.warpAffine(cell, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = pr[..., 3:4] / 255.0 * o
            if shadow:
                sh = np.zeros((H, W), np.float32); cv2.ellipse(sh, (int(px), int(py + ch * k_ * 0.46)), (int(cw * k_ * 0.32), int(ch * k_ * 0.05)), 0, 0, 360, 1, -1); sh = cv2.GaussianBlur(sh, (0, 0), 10 * self.U + 2)[..., None] * 0.35 * o; img = img * (1 - sh * (0.9 if _lum(self._ink) < 120 else 0.7))
            img = img * (1 - a) + pr[..., :3] * a
            if text: self.block(img, self.wrap(text, 62, True), H * 0.14, 62, True, eio((u - 4) / 8) * o, maxh=H * 0.2)
            return img
        return self._add(draw, dur, kind="sprite", meta=dict(count=int(dur)), **k)


    # ------------------------------------------------------------------ write (handwriting that writes itself)
    def write(self, text, style="marker", size=110, color=None, per=0.075, hold=1.0, dur=None, **k):
        """Text that writes itself, one line after another, in a hand-made medium: style "chalk" (grainy white strokes with dust), "marker" (solid ink with a wet tip) or "pencil" (fine graphite).
        The pen moves left to right along each line, a little unevenly; per = seconds per character. Best on chalkboard, whiteboard, dotgrid or paper themes."""
        lines = text.split("\n"); masks = []; sizes = []
        for ln in lines:
            m, sh = self.T(ln, size, True, 0, self.W * 0.88); cols = np.where(m.sum(0) > 0.5)[0]; x0, x1 = (int(cols.min()), int(cols.max())) if len(cols) else (0, 1); masks.append((m, x0, x1, max(len(ln), 1)))
        durs = [l[3] * per for l in masks]; total = sum(durs) + hold + 0.3
        def draw(u, n, f):
            W, H = self.W, self.H; U = self.U; img = self.bg(None, u, n, f); ink = _hexc(color) if color is not None else self._ink; o = self._io(u, n, 3, 5); t = u / self.fps; t0 = 0.25; gap = size * U * 1.32
            rng = np.random.default_rng(7); grain = _grain(H, W, style)
            for i, (m, x0, x1, nch) in enumerate(masks):
                prog = clamp((t - t0) / max(durs[i], 1e-3)); t0 += durs[i]
                if prog <= 0: continue
                cx = x0 + (x1 - x0 + 10) * (prog ** 0.92); yy = np.arange(m.shape[0], dtype=np.float32)[:, None]; edge = cx + 14 * np.sin(yy * 0.07 + i) + 8 * np.sin(yy * 0.19 + t * 9)
                xs = np.arange(W, dtype=np.float32)[None, :]; rev = np.clip((edge - xs) / 10.0, 0, 1); cy = H * 0.5 + (i - (len(masks) - 1) / 2) * gap
                y0 = int(cy - m.shape[0] / 2); ya, yb = max(y0, 0), min(y0 + m.shape[0], H)
                if yb <= ya: continue
                mm = (m * rev)[ya - y0:yb - y0]; gg = grain[ya:yb]
                if style == "chalk": a = mm * (0.55 + 0.45 * gg) ; img[ya:yb] = img[ya:yb] * (1 - a[..., None] * o) + ink * a[..., None] * o; halo = cv2.GaussianBlur(mm, (0, 0), 3 * U + 1) * 0.10; img[ya:yb] += halo[..., None] * ink * o
                elif style == "pencil": a = np.clip(mm * (0.45 + 0.55 * gg) * 0.95, 0, 1); img[ya:yb] = img[ya:yb] * (1 - a[..., None] * o) + (ink * 0.55 + 25) * a[..., None] * o
                else:
                    a = np.clip(mm, 0, 1); edge_d = np.clip(a - cv2.erode(a, np.ones((3, 3), np.uint8)), 0, 1); img[ya:yb] = img[ya:yb] * (1 - a[..., None] * 0.93 * o) + ink * a[..., None] * 0.93 * o - edge_d[..., None] * 18 * o
                    if 0 < prog < 1: tipy = cy + 4 * np.sin(t * 20); cv2.circle(img, (int(cx), int(tipy)), int(7 * U), (255, 255, 255), -1, cv2.LINE_AA)
            return img
        return self._add(draw, dur or total, kind="write", meta=dict(style=style, durs=durs, count=len(lines)), **k)

    # ------------------------------------------------------------------ sketch (an image drawn as ink lines, then coloured in)
    def sketch(self, image, text=None, ink="#14161a", lines=300, draw_for=0.62, dur=5.0, **k):
        """A picture that is drawn in front of you: its edges are traced into ink lines that draw themselves longest first, and then the colour floods in as loose blotches."""
        im = jb.art(image); ih, iw = im.shape[:2]; W, H = self.W, self.H; sc = max(W / iw, H / ih); fit = cv2.resize(im, (int(iw * sc) + 1, int(ih * sc) + 1))[(int(ih * sc) - H) // 2 if int(ih * sc) > H else 0:][:H, (int(iw * sc) - W) // 2 if int(iw * sc) > W else 0:][:, :W]
        if fit.shape[:2] != (H, W): fit = cv2.resize(fit, (W, H))
        g = cv2.GaussianBlur(cv2.cvtColor(fit, cv2.COLOR_BGR2GRAY), (0, 0), 1.6); ed = cv2.Canny(g, 40, 110); cs, _ = cv2.findContours(ed, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cs = sorted([c[:, 0, :] for c in cs if len(c) > 25], key=lambda c: -len(c))[:lines]; lens = np.array([len(c) for c in cs], np.float32); cum = np.concatenate([[0], np.cumsum(lens)]); tot = max(cum[-1], 1.0)
        def draw(u, n, f):
            U = self.U; bg = self.bg(None, u, n, f); o = self._io(u, n, 3, 6); p = clamp(u / (n * draw_for)); layer = np.zeros((H, W), np.float32); th = max(1, int(2.2 * U))
            for c, a0, a1 in zip(cs, cum[:-1] / tot, cum[1:] / tot):
                q = clamp((p * 1.15 - a0) / max(a1 - a0, 1e-4) * (0.45))   # lines start in order and each one grows while the next begins
                if q <= 0: continue
                k_ = max(2, int(len(c) * min(q * 2.2, 1.0))); pts = c[:k_].reshape(-1, 1, 2).astype(np.int32); cv2.polylines(layer, [pts], False, 1.0, th, cv2.LINE_AA)
            cp = clamp((u / n - draw_for * 0.7) / (1 - draw_for * 0.7)); nz = _blot(H, W); cov = np.clip((cp * 1.5 - nz) * 5, 0, 1)[..., None]; col = bg * (1 - cov) + fit.astype(np.float32) * cov
            img = col * (1 - layer[..., None] * 0.9) + _hexc(ink) * layer[..., None] * 0.9
            if text: self.block(img, self.wrap(text, 64, True), H * 0.9, 64, True, eio((u - n * 0.55) / 10) * o, maxh=H * 0.14)
            return img
        return self._add(draw, dur, kind="sketch", meta=dict(), **k)

    # ------------------------------------------------------------------ stamp (a rubber stamp that slams down)
    def stamp(self, text, sub=None, color="#d62828", angle=-8, dur=2.4, **k):
        """A rubber stamp: it comes down large, hits the paper with a thump and a small shake, and leaves rough, uneven ink (a double border, one word). APPROVED, SOLD OUT, FAKE, NEW."""
        from PIL import Image, ImageDraw, ImageFont
        W, H = self.W, self.H; U = self.U; fs = int(min(min(W, H) * 0.20, 0.78 * W / (len(text) * 0.66 + 0.9))); p, wt, ix = self.fb; ft = jb.font(p, fs, wt, ix); tw = int(ft.getlength(text)) + int(fs * 0.9); th = int(fs * 1.5) + (int(fs * 0.45) if sub else 0)
        im = Image.new("L", (tw + 40, th + 40), 0); d = ImageDraw.Draw(im); d.rounded_rectangle((8, 8, tw + 32, th + 32), radius=int(fs * 0.18), outline=255, width=max(4, int(fs * 0.06))); d.rounded_rectangle((8 + int(fs * 0.12), 8 + int(fs * 0.12), tw + 32 - int(fs * 0.12), th + 32 - int(fs * 0.12)), radius=int(fs * 0.12), outline=255, width=max(2, int(fs * 0.03)))
        d.text(((tw + 40) / 2, int(fs * 0.85) + 20), text, font=ft, fill=255, anchor="mm")
        if sub: d.text(((tw + 40) / 2, th - int(fs * 0.05) + 8), sub, font=jb.font(p, int(fs * 0.3), wt, ix), fill=255, anchor="mm")
        base = np.asarray(im, np.float32) / 255.0; rough = cv2.GaussianBlur(np.random.default_rng(3).standard_normal(base.shape).astype(np.float32), (0, 0), 1.2) * 0.6 + np.random.default_rng(4).standard_normal(base.shape).astype(np.float32) * 0.25
        base = np.clip(base * (0.85 + 0.15 * (rough > -0.35)) * (rough > -0.9), 0, 1); hit = 9
        def draw(u, n, f):
            img = self.bg(None, u, n, f); o = 1.0 if self.exact else self._io(u, n, 2, 6); k_ = base; s_ = 1 + 1.6 * (1 - eo(u / hit, 3)) if u < hit else 1.0; a_ = clamp(u / 4) if u < hit else 1.0
            if u < hit: cy_ = H * 0.46 - 120 * U * (1 - eo(u / hit, 3))
            else: cy_ = H * 0.46
            M = cv2.getRotationMatrix2D((k_.shape[1] / 2, k_.shape[0] / 2), angle, s_); M[0, 2] += W / 2 - k_.shape[1] / 2; M[1, 2] += cy_ - k_.shape[0] / 2
            if u >= hit: sh = 7 * U * np.exp(-(u - hit) / 3.0) * np.sin((u - hit) * 2.1); M[0, 2] += sh; M[1, 2] += sh * 0.6
            m = cv2.warpAffine(k_, M, (W, H), flags=cv2.INTER_LINEAR) * a_; ink = _hexc(color); m = m[..., None] * (0.93 if u >= hit else 0.5)
            img = img * (1 - m * (1 - ink / 255.0 * 0.95)); img = np.where(m > 0.02, img, img)
            if u >= hit and u < hit + 6: cv2.circle(img, (W // 2, int(cy_)), int(min(W, H) * 0.34 * eo((u - hit) / 6)), (255, 255, 255), max(2, int(3 * U)), cv2.LINE_AA) if False else None
            return img
        return self._add(draw, dur, kind="stamp", meta=dict(hit=hit), **k)

    for fn in (kinetic, highlight, stages, timeline, countdown, versus, product, chat, satisfying, stick, anatomy, before_after, wire, cta, skit, laptop, notes, review, wrapped, lyrics, changelog, sprite, write, sketch, stamp): setattr(Film, fn.__name__, fn)

NAMES = ("kinetic", "highlight", "stages", "timeline", "countdown", "versus", "product", "chat", "satisfying", "stick", "anatomy", "before_after", "wire", "cta", "skit", "laptop", "notes", "review", "wrapped", "lyrics", "changelog", "sprite", "write", "sketch", "stamp")

# sounds that match what each scene shows: (frame offset, sound, gain, duration, pitch)
def cues(film, sc):
    k, n, m, fps = sc["kind"], sc["n"], sc["meta"], film.fps; C = []
    if k == "kinetic": C += [(i * m["seg"], "pop", 0.32, None, 0.9 + 0.05 * (i % 5)) for i in range(m["count"])]
    elif k == "highlight": C += [(8 + i * m["step"], "tick", 0.2, None, 1 + 0.02 * (i % 6)) for i in range(m["count"])] + [(8 + m["count"] * m["step"] + 6, "sweep", 0.3, 0.4, 1.0)]
    elif k == "stages": C += [(i * m["seg"], "thud", 0.45, None, 1.0 - 0.04 * i) for i in range(m["count"])] + [(i * m["seg"] + 2, "pop", 0.2, None, 1 + 0.12 * i) for i in range(m["count"])]
    elif k == "timeline": C += [(8 + i * m["step"], "tick", 0.3, None, 1.0 + 0.04 * i) for i in range(m["count"])] + [(8 + i * m["step"] + 3, "pop", 0.2, None, 1.1) for i in range(m["count"])]
    elif k == "countdown": C += [(i * m["seg"], "thud", 0.6, None, 0.9 + 0.05 * i) for i in range(m["count"])] + [(i * m["seg"] + 2, "whoosh", 0.25, 0.3, 1) for i in range(m["count"])]
    elif k == "versus": C += [(0, "whoosh", 0.4, 0.5, 1), (8, "thud", 0.5, None, 1.0)] + [(14 + i * film.beat // 2, "pop", 0.22, None, 1 + 0.06 * (i % 4)) for i in range(m["count"])]
    elif k == "product": C += [(0, "sweep", 0.3, 0.7, 1), (14, "ding", 0.18, None, 1.0)] + [(18 + j * 8 + 3, "pop", 0.3, None, 1 + 0.1 * j) for j in range(m["count"])]
    elif k == "chat": C += [((m["start"] + i * m["step"]) + (int(m["step"] * 0.5) if w == "them" else 0), "pop" if w == "me" else "blip", 0.35, None, 1.2 if w == "me" else 1.0) for i, w in enumerate(m["who"])]
    elif k == "satisfying": C += [(i * film.beat * 2, "blip", 0.16, None, 1.0 + 0.08 * (i % 6)) for i in range(max(1, n // (film.beat * 2)))]
    elif k == "stick": C += [(0, "pop", 0.2, None, 1.0)] + ([(i * int(film.fps * 0.35), "tick", 0.18, None, 0.7) for i in range(int(n / (film.fps * 0.35)))] if m.get("action") in ("walk", "run") else [])
    elif k == "anatomy": C += [(4 + i * 3, "pop", 0.18, None, 1 + 0.08 * i) for i in range(m["count"])] + [(10, "sweep", 0.3, max(n - 24, 8) / fps, 1)]
    elif k == "wire": C += [(2, "sweep", 0.3, max(n * 0.38 / fps, 0.6), 1.0), (int(n * 0.38) + 2, "ding", 0.18, None, 1.0)]
    elif k == "cta": C += [(m["start"] + i * m["per"], "tick", 0.22, None, 1 + 0.03 * i) for i in range(m["count"])] + [(m["start"] + m["count"] * m["per"] + 14, "pop", 0.45, None, 1.3)]
    elif k == "skit": C += [(3, "pop", 0.35, None, 1.25 if m["who"] == "cube" else 0.85)]
    elif k == "laptop": C += [(0, "whoosh", 0.3, 0.5, 1), (n // 2, "blip", 0.15, None, 1.0)]
    elif k == "notes": C += [(20 + i * 6, "click", 0.10, None, 1) for i in range(min(m["count"], 60))]
    elif k == "review": C += [(10 + i * m["step"], "pop", 0.35, None, 1 + 0.06 * i) for i in range(m["count"])] + [(10, "ding", 0.15, None, 1.2)]
    elif k == "wrapped": C += [(i * m["seg"], "whoosh", 0.3, 0.35, 1) for i in range(m["count"])] + [(i * m["seg"] + 4, "thud", 0.4, None, 1.0) for i in range(m["count"])]
    elif k == "lyrics": C += [(i * m["seg"], "tick", 0.12, None, 1.0) for i in range(m["count"])]
    elif k == "changelog": C += [(0, "thud", 0.4, None, 1.0)] + [(14 + i * m["step"], "pop", 0.3, None, 1 + 0.05 * i) for i in range(m["count"])]
    elif k == "sprite": C += [(0, "pop", 0.3, None, 1.1)]
    elif k == "write": C += [(int(sum(m["durs"][:i]) * fps + 0.25 * fps), m["style"] if m["style"] != "chalk" else "chalk", 0.22, m["durs"][i], 1) for i in range(m["count"])]
    elif k == "sketch": C += [(4, "pencil", 0.22, n * 0.55 / fps, 1), (int(n * 0.5), "paper", 0.18, 0.8, 1), (n - 14, "pop", 0.2, None, 1.1)]
    elif k == "stamp": C += [(m["hit"], "stamp", 0.7, None, 0.9), (m["hit"] + 1, "paper", 0.18, 0.3, 1)]
    elif k == "before_after": C += [(8, "sweep", 0.4, n * 0.45 / fps, 1), (int(n * 0.45) + 8, "ding", 0.2, None, 1)]
    return C

# ---------------------------------------------------------------------------------------------- picture treatments applied to the finished frame
import looks
FX = ("vhs", "pixel") + tuple(looks.LOOKS)
def apply_fx(img, kind, f, U, fps):
    """Film(fx="vhs") or fx="pixel": a whole-film treatment applied after the look."""
    H, W = img.shape[:2]
    if isinstance(kind, (tuple, list)): kind, kw = kind[0], dict(kind[1])
    else: kw = {}
    if kind in looks.LOOKS: return looks.LOOKS[kind](img, f, U, fps, **kw)
    if kind == "vhs":
        sh = int(5 * U) + 1; out = img.copy(); out[..., 0] = np.roll(img[..., 0], sh, 1); out[..., 2] = np.roll(img[..., 2], -sh, 1)
        t = f / fps; y0 = int(((t * 0.28) % 1.0) * H); band = int(110 * U)
        for r in range(max(y0 - band, 0), min(y0 + band, H)):
            k = 1 - abs(r - y0) / band; out[r] = np.roll(out[r], int(30 * U * k * np.sin(r * 0.15 + f)), 0)
        out *= (1 - 0.16 * ((np.arange(H) % 3) == 0))[:, None, None]; out = cv2.GaussianBlur(out, (0, 0), 0.9 * U + 0.3)
        out += np.random.default_rng(f).normal(0, 7, (H, W, 1)).astype(np.float32); out[y0:y0 + int(6 * U)] += 40; return out
    if kind == "pixel":
        s = max(4, int(7 * U)); sm = cv2.resize(img, (max(W // s, 8), max(H // s, 8)), interpolation=cv2.INTER_AREA); sm = np.round(sm / 42.0) * 42.0
        return cv2.resize(sm, (W, H), interpolation=cv2.INTER_NEAREST)
    return img

# ---------------------------------------------------------------------------------------------- colour grades (applied after the look)
GRADES = ("teal_orange", "noir", "bleach", "sunset", "mint", "cross", "pastel", "night")
def apply_grade(img, name, strength=1.0):
    """Film(grade="teal_orange"): a colour grade on the whole finished picture. Strength 0..1 blends it with the original."""
    if name not in GRADES: return img
    x = np.clip(img, 0, 255) / 255.0; l = (x @ np.float32((0.114, 0.587, 0.299)))[..., None]; b, g, r = x[..., 0:1], x[..., 1:2], x[..., 2:3]
    sc = lambda v, k=1.0: v + k * (v - 0.5) * (1 - np.abs(2 * v - 1)) * 0.9          # S-curve, gentle
    if name == "teal_orange":
        sh = (1 - l) ** 1.5; hi = l ** 1.5; out = np.concatenate([b + 0.10 * sh - 0.12 * hi, g + 0.05 * sh - 0.02 * hi, r - 0.10 * sh + 0.12 * hi], 2); out = sc(out, 0.8)
    elif name == "noir":
        out = np.repeat(sc(l, 1.6), 3, 2); out[..., 0:1] += 0.025 * (1 - l)
    elif name == "bleach":
        d = np.repeat(l, 3, 2); out = sc(x * 0.55 + d * 0.45, 1.6)
    elif name == "sunset":
        out = np.concatenate([b * 0.82 + 0.05, g * 0.93 + 0.03, r * 1.05 + 0.02], 2); out = out + (l ** 2) * np.float32((-0.02, 0.0, 0.05)); out = sc(out, 0.5)
    elif name == "mint":
        out = np.concatenate([b * 0.96 + 0.02, g * 1.06 + 0.02, r * 0.92], 2)
    elif name == "cross":
        out = np.concatenate([1 - sc(1 - b, 0.9) * 0.9 + 0.04, sc(g, 0.7), sc(r, 1.1)], 2)
    elif name == "pastel":
        d = np.repeat(l, 3, 2); out = (x * 0.78 + d * 0.22) * 0.82 + 0.17
    else:   # night
        out = np.concatenate([b * 1.06 + 0.03, g * 0.95, r * 0.82], 2) * 0.9; out = sc(out, 0.7)
    out = np.clip(out, 0, 1) * 255.0
    return img * (1 - strength) + out * strength if strength < 1 else out.astype(np.float32)

# ---------------------------------------------------------------------------------------------- UI cards for skit(pip=...) and laptop(media=...)
# Each builder returns a function (u, n, f) -> an RGB-ish float32 BGR picture, drawn with Pillow at 1000x680. Wrap one in pip_done() to add the "Done" chip.
def _pf(size, bold=True):
    from PIL import ImageFont
    for p, ix in (("/System/Library/Fonts/Avenir Next.ttc", 8 if bold else 5), ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0), ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0)):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size, index=ix)
            except Exception: pass
    return ImageFont.load_default()

def _to_bgr(im): return np.asarray(im.convert("RGB"), np.float32)[..., ::-1].copy()

def pip_done(inner, seconds=4, label="Done"):
    """Wrap a card builder with a '✓ Done · 4s' chip at the bottom right (the 'an agent just finished this' look)."""
    from PIL import Image, ImageDraw
    def fn(u, n, f):
        img = inner(u, n, f); im = Image.fromarray(np.clip(img[..., ::-1], 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im); w, h = im.size; txt = "%s  ·  %ss" % (label, seconds); ft = _pf(int(h * 0.05)); tw = d.textlength(txt, font=ft) + h * 0.05
        x1, y1 = w - w * 0.03, h - h * 0.04; x0, y0 = x1 - tw - h * 0.07, y1 - h * 0.095; d.rounded_rectangle((x0, y0, x1, y1), radius=int(h * 0.05), fill=(12, 30, 20), outline=(60, 200, 110), width=max(2, int(h * 0.006))); cx_, cy_ = x0 + h * 0.055, (y0 + y1) / 2; d.line((cx_ - h * 0.016, cy_, cx_ - h * 0.004, cy_ + h * 0.014, cx_ + h * 0.02, cy_ - h * 0.014), fill=(90, 230, 140), width=max(3, int(h * 0.007))); d.text((x0 + h * 0.09, y0 + h * 0.018), txt, font=ft, fill=(90, 230, 140))
        return _to_bgr(im)
    return fn

def pip_slider():
    """A light card with two capsule toggles and a rainbow slider whose knob slides (a design-tool control)."""
    from PIL import Image, ImageDraw
    def fn(u, n, f):
        W, H = 1000, 680; im = Image.new("RGB", (W, H), (232, 234, 238)); d = ImageDraw.Draw(im); t = (np.sin(u * 0.12) + 1) / 2
        d.rounded_rectangle((100, 150, 330, 270), radius=60, fill=(246, 247, 250), outline=(210, 212, 218), width=4); d.ellipse((380, 150, 500, 270), fill=(246, 247, 250), outline=(214, 216, 222), width=4)
        bx0, bx1, by = 200, 800, 400; hsv = np.zeros((90, bx1 - bx0, 3), np.uint8); hsv[..., 0] = ((150 + np.linspace(0, 70, bx1 - bx0)) % 180).astype(np.uint8)[None, :]; hsv[..., 1] = 255; hsv[..., 2] = 255
        im.paste(Image.fromarray(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)), (bx0, by)); d.rounded_rectangle((bx0 - 20, by, bx0 + 40, by + 90), radius=45, fill=(150, 40, 220))
        kx = bx0 + (bx1 - bx0) * (0.72 + 0.2 * t); d.ellipse((kx - 52, by - 6, kx + 52, by + 98), fill=(250, 190, 40), outline=(255, 255, 255), width=8); d.ellipse((kx - 14, by + 30, kx + 14, by + 58), fill=(60, 40, 20))
        d.ellipse((60, 520, 170, 630), fill=(244, 245, 248), outline=(205, 207, 214), width=4); d.line((115, 548, 115, 602), fill=(40, 40, 44), width=8); d.line((88, 575, 142, 575), fill=(40, 40, 44), width=8)
        return _to_bgr(im)
    return fn

def pip_brand(name, style="dark"):
    """A made-up brand's hero card. style: dark (a dark panel in a green glow, a round mark), sky (blue sky, green hills, a round green bird), warm (cream with a big coloured name)."""
    from PIL import Image, ImageDraw
    def fn(u, n, f):
        W, H = 1000, 680; im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); b = np.sin(u * 0.15) * 4
        if style == "dark":
            for i in range(60): c = int(150 * (1 - i / 60)); d.rectangle((i, i, W - i, H - i), outline=(20, c + 40, 50))
            d.rounded_rectangle((90, 60, W - 90, H - 80), radius=40, fill=(10, 12, 12)); d.ellipse((W / 2 - 55, H / 2 - 95 + b, W / 2 + 55, H / 2 + 15 + b), fill=(40, 215, 100))
            for k in range(3): d.arc((W / 2 - 38 + k * 6, H / 2 - 75 + k * 20 + b, W / 2 + 38 - k * 6, H / 2 - 20 + k * 20 + b), 200, 340, fill=(10, 12, 12), width=7)
            d.text((W / 2, H / 2 + 80), name, font=_pf(54), fill=(235, 240, 238), anchor="mm")
        elif style == "sky":
            d.rectangle((0, 0, W, H), fill=(14, 14, 18)); sky = Image.new("RGB", (W, H)); d = ImageDraw.Draw(sky)
            for y in range(H): d.line((0, y, W, y), fill=(int(240 - 90 * y / H), int(190 + 30 * y / H), 120))
            d.ellipse((-200, H * 0.72, 700, H * 1.6), fill=(110, 210, 90)); d.ellipse((500, H * 0.8, 1300, H * 1.7), fill=(140, 225, 100)); d.text((70, 150), name, font=_pf(88), fill=(255, 255, 255)); d.text((70, 260), "Learn Spanish", font=_pf(74), fill=(255, 255, 255))
            bx, by = 720, 250 + b * 3; d.ellipse((bx - 120, by - 110, bx + 120, by + 130), fill=(120, 215, 40)); d.ellipse((bx - 70, by - 70, bx - 5, by - 5), fill=(255, 255, 255)); d.ellipse((bx + 5, by - 70, bx + 70, by - 5), fill=(255, 255, 255)); d.ellipse((bx - 40, by - 50, bx - 20, by - 25), fill=(30, 30, 30)); d.ellipse((bx + 25, by - 50, bx + 45, by - 25), fill=(30, 30, 30)); d.polygon([(bx - 22, by + 10), (bx + 22, by + 10), (bx, by + 45)], fill=(250, 170, 30)); sm = sky.resize((int(W * 0.86), int(H * 0.80))); im.paste(sm, (int(W * 0.07), int(H * 0.07))); d = ImageDraw.Draw(im)
        else:
            d.rectangle((0, 0, W, H), fill=(240, 236, 226)); d.text((W / 2, H / 2), name, font=_pf(150), fill=(200, 60, 40), anchor="mm")
        return _to_bgr(im)
    return fn

def pip_templates(highlight=None, speed=0, names=None, title="joyboy toolkit", sub="scenes, themes and music, ready to use", flips=None, flicker=None, drift=0):
    """A dark 'template library' panel: a header, a 3x3 grid of mini previews, an orange selection box that moves, and a label chip. speed=0 is calm; speed=1 flickers fast (the scrubbing look). drift=pixels per frame slides the tiles upwards (a library being scrolled). flicker=(from_s, to_s) re-draws the grid every frame in that window (the fast scrubbing look). flips=[seconds, ...] changes the whole grid and the selection exactly at those times (scene time), to match a reference frame by frame."""
    from PIL import Image, ImageDraw
    names = names or ["kinetic", "product", "chat", "stages", "timeline", "wrapped", "versus", "skit", "wire", "lyrics", "notes", "review"]
    pal = [(40, 44, 52), (60, 38, 40), (34, 56, 44), (52, 46, 70), (70, 60, 40), (30, 52, 72), (66, 66, 70), (80, 44, 60)]
    def fn(u, n, f):
        W, H = 1000, 680; nf = sum(1 for x in (flips or []) if u / 30.0 >= x); light = bool(flips) and nf % 2 == 1; im = Image.new("RGB", (W, H), (232, 233, 238) if light else (14, 15, 18)); d = ImageDraw.Draw(im); fl = int(u) if (flicker and flicker[0] <= u / 30.0 < flicker[1]) else 0; r = np.random.default_rng(nf * 7 + 3 + fl * 101 if flips else (int(u * (1 + 2 * speed)) if speed else 3))
        d.text((24, 22), title, font=_pf(46), fill=(240, 240, 240)); d.text((24 + d.textlength(title, font=_pf(46)) + 14, 40), "open source", font=_pf(22, False), fill=(150, 150, 160)); d.rounded_rectangle((W - 230, 20, W - 24, 66), radius=20, fill=(20, 48, 30)); d.text((W - 127, 43), "★ MIT licence", font=_pf(22), fill=(100, 230, 140), anchor="mm")
        d.text((24, 100), sub, font=_pf(26), fill=(235, 235, 235)); gx, gy, cw, ch = 24, 150, (W - 48 - 20) // 3, (H - 170 - 20) // 3; sel = (nf * 4 + 1) % 9 if flips else (int(((u * (0.9 + 5 * speed)) if speed else u * 0.12)) % 9 if highlight is None else highlight)
        yo_t = u * drift if drift else 0; sr = int(yo_t // (ch + 10)); yo = yo_t % (ch + 10); gim = Image.new("RGB", (W, H - gy), (232, 233, 238) if light else (14, 15, 18)); gd = ImageDraw.Draw(gim); sel_scr = sel
        for rr_ in range(-1, 4):
            for cc in range(3):
                i = rr_ * 3 + cc if rr_ >= 0 else -1; x, y = gx + cc * (cw + 10), rr_ * (ch + 10) - yo; ar = rr_ + sr; rg = np.random.default_rng((nf * 131 + ar * 17 + cc * 5 + 3 + fl * 101) % (2 ** 31))
                c = (tuple(int(v) for v in rg.integers(25, 235, 3)) if flips else pal[int(rg.integers(0, len(pal)))]) if (speed or flips) else pal[((ar * 3 + cc) * 3 + 1) % len(pal)]
                gd.rectangle((x, y, x + cw, y + ch), fill=c)
                for kk in range(int(rg.integers(2, 5))): xx = x + int(rg.integers(10, cw - 80)); yy = y + int(rg.integers(10, ch - 50)); gd.rounded_rectangle((xx, yy, xx + int(rg.integers(40, 140)), yy + int(rg.integers(14, 40))), radius=6, fill=tuple(int(min(255, v + 70)) for v in c))
                lab = names[(ar * 3 + cc + (nf if flips else (int(u) if speed else 0))) % len(names)]; gd.text((x + 8, y + ch - 24), lab, font=_pf(18, False), fill=(190, 190, 195))
                if rr_ >= 0 and rr_ * 3 + cc == sel_scr and not drift: gd.rectangle((x, y, x + cw, y + ch), outline=(250, 130, 40), width=7); tw = d.textlength(lab, font=_pf(34)); gd.rounded_rectangle((x + cw - tw - 36, y + ch - 52, x + cw, y + ch), radius=14, fill=(250, 130, 40)); gd.text((x + cw - tw - 18, y + ch - 44), lab, font=_pf(34), fill=(255, 255, 255))
                elif drift and rr_ == 1 and cc == 1: gd.rectangle((x, y, x + cw, y + ch), outline=(250, 130, 40), width=7); tw = d.textlength(lab, font=_pf(34)); gd.rounded_rectangle((x + cw - tw - 36, y + ch - 52, x + cw, y + ch), radius=14, fill=(250, 130, 40)); gd.text((x + cw - tw - 18, y + ch - 44), lab, font=_pf(34), fill=(255, 255, 255))
        im.paste(gim, (0, gy))
        return _to_bgr(im)
    return fn

def pip_wall(count=140, big="140+", sub="scenes, themes and sounds", scroll=0):
    """A dense mosaic of mini previews with a big number over it (the 'there are N more' reveal)."""
    from PIL import Image, ImageDraw
    def fn(u, n, f):
        W, H = 1000, 680; im = Image.new("RGB", (W, H), (14, 15, 18)); d = ImageDraw.Draw(im); r = np.random.default_rng(11); d.text((24, 22), "joyboy toolkit", font=_pf(46), fill=(240, 240, 240))
        cols, rows = 16, 9; cw, ch = (W - 40) / cols, (H - 120) / rows; mos = Image.new("RGB", (W, H), (14, 15, 18)); md = ImageDraw.Draw(mos)
        for i in range(cols):
            for j in range(rows):
                c = tuple(int(v) for v in r.integers(20, 200, 3)); x0, y0 = 20 + i * cw, 100 + j * ch; md.rectangle((x0 + 1, y0 + 1, x0 + cw - 1, y0 + ch - 1), fill=c)
        sh = int(u * scroll) % int(cw * 2) if scroll else 0; ma = np.roll(np.asarray(mos), -sh, axis=1); im.paste(Image.fromarray(ma).crop((0, 100, W, H)), (0, 100)); d = ImageDraw.Draw(im); d.text((24, 22), "joyboy toolkit", font=_pf(46), fill=(240, 240, 240))
        sc = 1 + 0.06 * np.sin(u * 0.2); d.text((W / 2, H / 2 + 20), big, font=_pf(int(210 * sc)), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(14, 15, 18)); d.text((W / 2, H / 2 + 150), sub, font=_pf(44), fill=(250, 130, 40), anchor="mm", stroke_width=4, stroke_fill=(14, 15, 18))
        return _to_bgr(im)
    return fn

def pip_seq(parts):
    """Switch cards during one scene: pip_seq([(0, card_a), (3.2, card_b)]) shows card_a, then card_b from 3.2 s into the scene."""
    def fn(u, n, f):
        cur = parts[0][1]
        for s_, c in parts:
            if u / 30.0 >= s_: cur = c
        return cur(u, n, f)
    return fn
