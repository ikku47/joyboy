"""joyboy ambience: background sound synthesized in NumPy (no recordings): fire, wind, rain, thunder, sea waves,
a stream, night crickets, street traffic and passing cars. Every sound is a stereo float array (n, 2) at `sr`.

    amb = Ambience(sr=44100, seed=7)
    bed = amb.fire(12.0)                      # 12 seconds of campfire
    layers = amb.for_world(place, time, weather, props, dur)     # the beds a world needs: [(name, array, gain), ...]
"""
import numpy as np
from scipy.signal import butter, sosfilt

class Ambience:
    def __init__(self, sr=44100, seed=7): self.sr = sr; self.r = np.random.default_rng(seed)
    # ----- building blocks -----
    def _f(self, kind, x, *fc, o=2): return sosfilt(butter(o, [min(f, self.sr * 0.45) / (self.sr / 2) for f in fc] if len(fc) > 1 else min(fc[0], self.sr * 0.45) / (self.sr / 2), kind, output="sos"), x)
    def lp(self, x, fc, o=2): return self._f("low", x, fc, o=o)
    def hp(self, x, fc, o=2): return self._f("high", x, fc, o=o)
    def bp(self, x, lo, hi, o=2): return self._f("band", x, lo, hi, o=o)
    def noise(self, n): return self.r.standard_normal(n)
    def brown(self, n): x = self.hp(np.cumsum(self.noise(n)), 25); return x / (np.abs(x).max() + 1e-9)
    def slow(self, n, rate, lo=0.0, hi=1.0):
        """A smooth random curve: new random values `rate` times a second, eased between."""
        k = int(n / self.sr * rate) + 3; v = self.r.uniform(lo, hi, k); x = np.arange(n) / self.sr * rate; i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f); return v[i] * (1 - f) + v[i + 1] * f
    def norm(self, x, rms): return x * (rms / (np.sqrt((x ** 2).mean()) + 1e-9))
    def pan(self, x, p): return np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], 1)
    def _put(self, out, sig, t, p=0.0, g=1.0):
        i = int(t * self.sr)
        if i >= len(out) or i < 0: return
        L = min(len(sig), len(out) - i); out[i:i + L] += self.pan(sig[:L], p) * g
    # ----- beds -----
    def fire(self, dur):
        """Campfire: a low breathing roar, a faint hiss, and crackles with the odd loud pop."""
        n = int(dur * self.sr); out = np.zeros((n, 2))
        for c in (0, 1): out[:, c] = self.norm(self.lp(self.brown(n), 320) * self.slow(n, 2.5, 0.55, 1.0), 0.05) + self.norm(self.bp(self.noise(n), 1800, 6500) * self.slow(n, 5, 0.15, 1.0), 0.008)
        for _ in range(self.r.poisson(dur * 13)):
            a = min(1.0, self.r.lognormal(-1.7, 0.9)); L = int(self.sr * self.r.uniform(0.002, 0.010) * (1 + 3 * a)); t = np.arange(L) / self.sr
            b = np.diff(self.noise(L + 1)) * np.exp(-t / (L / self.sr / 4))
            if a > 0.45: tk = np.arange(int(self.sr * 0.04)) / self.sr; th = np.sin(2 * np.pi * self.r.uniform(170, 330) * tk) * np.exp(-tk * 90) * 1.2; b = np.concatenate([b, np.zeros(max(len(th) - L, 0))]); b[:len(th)] += th
            self._put(out, b, self.r.uniform(0, dur), self.r.uniform(-0.5, 0.5), 0.16 * a)
        return out
    def wind(self, dur, strength=0.5, muffled=False):
        """Wind in gusts. muffled=True is the soft hush of a snowy or foggy place."""
        n = int(dur * self.sr); out = np.zeros((n, 2)); gust = self.slow(n, 0.13, 0.35, 1.0) ** 1.5
        for lo, hi, w in ((110, 380, 1.0), (380, 1000, 0.55), (1000, 2600, 0.0 if muffled else 0.22)):
            if not w: continue
            for c in (0, 1): out[:, c] += self.bp(self.noise(n), lo, hi) * self.slow(n, 0.3, 0.2, 1.0) ** 2 * w
        out *= gust[:, None]; return self.norm(out, 0.045 * (0.4 + strength))
    def rain(self, dur, heavy=0.5):
        """Steady rain with individual drops; heavy=1 is a downpour."""
        n = int(dur * self.sr); out = np.zeros((n, 2))
        for c in (0, 1): out[:, c] = self.bp(self.noise(n), 900, 9000) * self.slow(n, 0.5, 0.85, 1.0) + self.lp(self.noise(n), 450) * 0.5
        out = self.norm(out, 0.04 * (0.6 + 0.9 * heavy))
        for _ in range(int(dur * 45 * (0.5 + heavy))):
            L = int(self.sr * self.r.uniform(0.006, 0.016)); t = np.arange(L) / self.sr; f = self.r.uniform(1400, 5200)
            self._put(out, np.sin(2 * np.pi * f * t * (1 + 2 * t)) * np.exp(-t * 330), self.r.uniform(0, dur), self.r.uniform(-0.9, 0.9), self.r.uniform(0.01, 0.05))
        return out
    def waves(self, dur, period=8.0):
        """Sea waves: a swell that builds, breaks and hisses back down the sand."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; ph = (t / period + self.slow(n, 0.1, -0.08, 0.08)) % 1.0
        swell = np.where(ph < 0.35, (ph / 0.35) ** 2, np.exp(-(ph - 0.35) * 3.4)); out = np.zeros((n, 2))
        for c in (0, 1): out[:, c] = self.lp(self.noise(n), 850) * swell + self.bp(self.noise(n), 2000, 8000) * np.exp(-((ph - 0.44) / 0.19) ** 2) * 0.35 + self.lp(self.noise(n), 140) * 0.35
        return self.norm(out, 0.055)
    def stream(self, dur):
        """A stream or fountain: running water that bubbles."""
        n = int(dur * self.sr); out = np.zeros((n, 2))
        for fc in np.geomspace(500, 4200, 7):
            for c in (0, 1): out[:, c] += self.bp(self.noise(n), fc * 0.82, fc * 1.22) * self.slow(n, self.r.uniform(8, 19), 0.0, 1.0) ** 2
        for c in (0, 1): out[:, c] += self.bp(self.noise(n), 300, 2400) * 0.25
        return self.norm(out, 0.045)
    def crickets(self, dur, count=6):
        """Night insects: several crickets chirping at their own speeds."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; out = np.zeros((n, 2))
        for _ in range(count):
            f, pr, cr, ph = self.r.uniform(4000, 5300), self.r.uniform(26, 40), self.r.uniform(1.5, 2.7), self.r.uniform(0, 1)
            gate = self.lp(((np.sin(2 * np.pi * pr * t) > 0.1) & (((t * cr + ph) % 1.0) < 0.34)).astype(float), 500)
            out += self.pan(np.sin(2 * np.pi * f * t) * gate * self.slow(n, 0.2, 0.5, 1.0), self.r.uniform(-0.9, 0.9)) * self.r.uniform(0.04, 0.085)
        return out
    def traffic(self, dur, busy=0.6):
        """City bed: a low engine hum, the air of a street, and far-off horns."""
        n = int(dur * self.sr); out = np.zeros((n, 2))
        for c in (0, 1): out[:, c] = self.norm(self.lp(self.brown(n), 150) * self.slow(n, 0.2, 0.6, 1.0), 0.04) + self.norm(self.bp(self.noise(n), 200, 2000) * self.slow(n, 0.3, 0.5, 1.0), 0.012)
        for _ in range(self.r.poisson(dur * 0.22 * busy)):
            L = int(self.sr * self.r.uniform(0.18, 0.5)); t = np.arange(L) / self.sr; f = self.r.uniform(370, 480); e = np.clip(t / 0.02, 0, 1) * np.clip((L / self.sr - t) / 0.06, 0, 1)
            self._put(out, self.lp(np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * 1.26 * t), 1300) * e, self.r.uniform(0, dur), self.r.uniform(-0.8, 0.8), self.r.uniform(0.008, 0.02))
        return out
    # ----- single events -----
    def thunder(self, dur=6.0, near=0.6):
        """One thunderclap: an optional sharp crack, then a rumble that rolls away. Peak about 1."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; env = np.zeros(n)
        for ti, a in zip(np.sort(self.r.uniform(0, 2.4, 5)), self.r.uniform(0.4, 1.0, 5)): env += a * np.exp(-np.clip(t - ti, 0, None) * 1.3) * (t >= ti)
        x = self.lp(self.brown(n), 130, o=3) * env * np.exp(-t * 0.5) * 3; ck = int(0.3 * self.sr); x[:ck] += self.hp(self.noise(ck), 1200) * np.exp(-t[:ck] * 16) * 0.5 * near
        x /= np.abs(x).max() + 1e-9; return np.stack([x, np.roll(x, 300)], 1)
    def car_pass(self, direction=1, wet=False, dur=2.6):
        """A car driving past from one side to the other (direction 1 = left to right)."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; e = np.exp(-((t - dur / 2) / 0.42) ** 2)
        x = self.lp(self.noise(n), 650) + np.sin(2 * np.pi * np.cumsum(118 - 30 / (1 + np.exp(-(t - dur / 2) * 6))) / self.sr) * 0.35 + (self.bp(self.noise(n), 2500, 9000) * 0.7 if wet else 0)
        x = x * e; x /= np.abs(x).max() + 1e-9; p = np.clip((t - dur / 2) / 0.6, -1, 1) * direction * 0.9
        return np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], 1)
    def splash(self, dur=1.4):
        """Someone or something landing in water: a thud, a burst of spray, drops pattering back down."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; out = np.zeros((n, 2))
        thud = np.sin(2 * np.pi * (95 - 40 * t) * t) * np.exp(-t * 14) * 1.2
        for c in (0, 1): out[:, c] = thud + self.bp(self.noise(n), 350, 5200) * (np.exp(-t * 7) + 0.35 * np.exp(-((t - 0.28) / 0.16) ** 2)) * 0.9
        for _ in range(26):
            L = int(self.sr * 0.012); tt = np.arange(L) / self.sr; self._put(out, np.sin(2 * np.pi * self.r.uniform(1500, 4800) * tt * (1 + 2 * tt)) * np.exp(-tt * 300), self.r.uniform(0.35, dur - 0.1), self.r.uniform(-0.9, 0.9), self.r.uniform(0.05, 0.16))
        return out / (np.abs(out).max() + 1e-9)
    def slip(self, dur=0.5):
        """A cartoon slip: a quick falling whistle."""
        n = int(dur * self.sr); t = np.arange(n) / self.sr; f = 1500 * (320 / 1500) ** (t / dur); x = np.sin(2 * np.pi * np.cumsum(f) / self.sr) * np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
        return np.stack([x, x], 1)
    def step(self, wet=True):
        """One footstep on wet ground."""
        n = int(0.16 * self.sr); t = np.arange(n) / self.sr; x = self.lp(self.noise(n), 260) * np.exp(-t * 45) * 2 + (self.bp(self.noise(n), 900, 3800) * np.exp(-((t - 0.03) / 0.025) ** 2) * 0.5 if wet else 0)
        x /= np.abs(x).max() + 1e-9; p = self.r.uniform(-0.3, 0.3); return self.pan(x, p)
    def frogs(self, dur, count=5):
        """Frogs after rain: short croaks from several places."""
        n = int(dur * self.sr); out = np.zeros((n, 2))
        for _ in range(count):
            f, pan = self.r.uniform(260, 520), self.r.uniform(-0.9, 0.9); t0 = self.r.uniform(0, 3)
            while t0 < dur - 0.4:
                L = int(self.sr * self.r.uniform(0.16, 0.3)); t = np.arange(L) / self.sr; e = np.sin(np.pi * t / (L / self.sr)) ** 0.6 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * self.r.uniform(26, 38) * t)))
                self._put(out, self.lp(np.sign(np.sin(2 * np.pi * f * t)) + np.sin(2 * np.pi * f * 2.02 * t), 1700) * e, t0, pan, self.r.uniform(0.006, 0.014)); t0 += self.r.uniform(0.5, 3.5)
        return out
    # ----- what a world needs -----
    def for_world(self, place, time, weather, props, dur):
        """The beds for a world: [(name, stereo array, gain)]. Events (thunder, cars) are placed by the caller."""
        L = []; night = time == "night"; props = props or ()
        if "campfire" in props: L.append(("fire", self.fire(dur), 1.0))
        if weather == "snow" or place == "snowfield": L.append(("wind", self.wind(dur, 0.25, muffled=True), 0.8))
        elif weather == "fog": L.append(("wind", self.wind(dur, 0.2, muffled=True), 0.7))
        elif weather == "rain": L += [("rain", self.rain(dur, 0.5), 1.0), ("wind", self.wind(dur, 0.3), 0.6)]
        elif weather == "storm": L += [("rain", self.rain(dur, 1.0), 0.75), ("wind", self.wind(dur, 0.9), 0.75)]
        elif place != "street": L.append(("wind", self.wind(dur, 0.2), 0.5))
        if place == "beach": L.append(("waves", self.waves(dur), 1.0))
        if place == "street": L.append(("traffic", self.traffic(dur), 1.0))
        if place == "village" and weather in ("rain", "storm", "fog"): L.append(("frogs", self.frogs(dur), 1.0))
        if night and weather == "clear" and place in ("forest", "meadow", "beach", "village"): L.append(("crickets", self.crickets(dur), 1.0))
        return L
