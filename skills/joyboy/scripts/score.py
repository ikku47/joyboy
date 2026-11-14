"""joyboy score: synthesize a film score and sound design in NumPy/SciPy, timed in frames.

    s = Score(total_frames, fps)
    s.add(s.wet, s.piano(69), s.t(128), pan=-0.2, g=0.16)     # wet bus gets reverb
    s.add(s.dry, s.boom(), s.t(512))                          # dry bus stays punchy (bass, drums)
    s.write("film.wav", sections=[(0, 128), (128, 512)])      # prints rms/peak per section

Notes are MIDI numbers (69 = A4). Gains are small (0.05-0.2 for tonal parts, up to 1.0 for the one big hit);
write() normalises and soft-limits, so balance matters more than absolute level.
"""
import wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve

def mf(m): return 440 * 2 ** ((m - 69) / 12)

class Score:
    def __init__(self, frames, fps=24, sr=44100, seed=3):
        self.F, self.fps, self.sr = frames, fps, sr
        self.N = int(frames / fps * sr) + sr // 2
        self.wet = np.zeros((self.N, 2)); self.dry = np.zeros((self.N, 2)); self.r = np.random.default_rng(seed)
    def t(self, frame): return frame / self.fps                 # frame -> seconds
    def n(self, dur): return np.arange(int(dur * self.sr)) / self.sr
    def add(self, bus, sig, t, pan=0.0, g=1.0):
        i = int(t * self.sr)
        if i < 0: sig = sig[-i:]; i = 0
        if i >= self.N: return
        L = min(len(sig), self.N - i); l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        bus[i:i + L, 0] += sig[:L] * l * g; bus[i:i + L, 1] += sig[:L] * r * g
    def lp(self, x, fc, o=2): b, a = butter(o, min(fc, self.sr * 0.45) / (self.sr / 2)); return lfilter(b, a, x)
    def hp(self, x, fc): b, a = butter(2, fc / (self.sr / 2), "high"); return lfilter(b, a, x)
    def noise(self, n): return self.r.standard_normal(n)

    # ----- tonal -----
    def piano(self, m, dur=3.5):
        t = self.n(dur); f = mf(m); s = 0
        for k in range(1, 8): s = s + np.sin(2 * np.pi * f * k * np.sqrt(1 + 0.0005 * k * k) * t) * np.exp(-t * (0.9 + 0.55 * k)) / k ** 1.5
        return s * (1 - np.exp(-t * 400)) * np.clip((dur - t) * 6, 0, 1)
    def keys(self, m, dur=3.4):                                  # soft electric piano
        t = self.n(dur); f = mf(m)
        s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t)
        return s * (1 - np.exp(-t * 180)) * np.exp(-t * 1.5) * (1 + 0.07 * np.sin(2 * np.pi * 4.6 * t))
    def bell(self, m, dur=2.2):                                  # music box / kalimba
        t = self.n(dur); f = mf(m)
        return (np.sin(2 * np.pi * f * t) * np.exp(-t * 4.2) + 0.28 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 13)) * (1 - np.exp(-t * 900))
    def strings(self, ms, dur, att=0.8, rel=0.8, cut=1800):      # detuned saw ensemble; short dur + att=0.01 = staccato
        t = self.n(dur); s = 0
        for m in ms:
            for det in (-9, 0, 8): s = s + 2 * ((mf(m) * 2 ** (det / 1200) * t + self.r.random()) % 1) - 1
        return self.lp(s, cut) * np.clip(t / att, 0, 1) * np.clip((dur - t) / rel, 0, 1) * (1 + 0.05 * np.sin(2 * np.pi * 5.3 * t)) / len(ms)
    def choir(self, ms, dur, att=1.0, rel=1.5):
        t = self.n(dur); s = 0
        for m in ms:
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t + m); f = mf(m)
            s = s + np.sin(2 * np.pi * f * t * vib) + 0.4 * np.sin(4 * np.pi * f * t * vib) + 0.18 * np.sin(6 * np.pi * f * t * vib)
        return s * np.clip(t / att, 0, 1) * np.clip((dur - t) / rel, 0, 1) / len(ms)
    def sub(self, m, dur, att=0.03, rel=0.6):                    # bass note under a chord (dry bus)
        return self.lp(self.strings([m - 12, m], dur, att, rel, 240), 240)
    def braam(self, m, dur=4.0):                                 # trailer brass
        t = self.n(dur); s = 0
        for mm in (m, m + 12, m + 19, m + 0.12, m + 12.1): s = s + 2 * ((mf(mm) * t + self.r.random()) % 1) - 1
        s = np.tanh(s * 1.4); out = np.zeros_like(s); nb = 16; seg = len(s) // nb
        for i in range(nb): out[i * seg:(i + 1) * seg] = self.lp(s, 250 + 1500 * np.exp(-i / 4.0))[i * seg:(i + 1) * seg]
        return out * np.clip(t / 0.04, 0, 1) * np.exp(-t * 0.7) * np.clip((dur - t) * 3, 0, 1)

    # ----- percussion and effects -----
    def taiko(self, g=1.0, f0=62):
        t = self.n(1.2)
        return (np.sin(2 * np.pi * (f0 * t + 28 * (1 - np.exp(-t * 22)) / 22 * 3)) * np.exp(-t * 5.5) + self.lp(self.noise(len(t)), 900) * np.exp(-t * 28) * 0.9) * g
    def kick(self):
        t = self.n(0.35); return np.sin(2 * np.pi * (48 * t + 6 * (1 - np.exp(-t * 30)))) * np.exp(-t * 11)
    def snare(self, dec=26):
        t = self.n(0.18); b, a = butter(2, [1800 / (self.sr / 2), 6500 / (self.sr / 2)], "band"); return lfilter(b, a, self.noise(len(t))) * np.exp(-t * dec)
    def hat(self): t = self.n(0.06); return self.hp(self.noise(len(t)), 6000) * np.exp(-t * 90)
    def boom(self):                                              # the big hit
        t = self.n(4.0)
        return np.tanh(np.sin(2 * np.pi * (34 * t + 9 * (1 - np.exp(-t * 9)))) * np.exp(-t * 1.5) * 1.6 + self.lp(self.noise(len(t)), 300) * np.exp(-t * 12) * 1.5)
    def crash(self, dur=3.5, dec=1.6): t = self.n(dur); return self.hp(self.noise(len(t)), 3500) * np.exp(-t * dec)
    def reverse_crash(self, dur=2.4): return self.crash(dur, 1.8)[::-1]      # place at t(hit) - dur
    def riser(self, dur):                                        # ends abruptly: place so it ends on the cut
        t = self.n(dur); x = t / dur
        return (self.hp(self.noise(len(t)), 1200) * x ** 2.5 * 0.7 + np.sin(2 * np.pi * np.cumsum(120 + 1400 * x ** 3) / self.sr) * x ** 2 * 0.3) * np.clip((dur - t) * 60, 0, 1)
    def whoosh(self, dur=0.45): t = self.n(dur); x = t / dur; return self.lp(self.hp(self.noise(len(t)), 300), 4000) * np.sin(np.pi * x) ** 2
    def click(self):                                             # key press / tick
        t = self.n(0.03); return self.noise(len(t)) * np.exp(-t * 300) + np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 220) * 0.5
    def roll(self, f0, f1, g0=0.10, g1=0.35):                    # accelerating snare roll between two frames
        tr, stp = float(f0), 5.0
        while tr < f1:
            t = self.n(0.12); self.add(self.dry, self.hp(self.noise(len(t)), 900) * np.exp(-t * 45), self.t(tr), pan=0.1, g=g0 + (g1 - g0) * (tr - f0) / max(f1 - f0, 1))
            tr += stp; stp = max(stp * 0.88, 1.0)

    # ----- scene sound effects (matched to what is happening on screen) -----
    def fx(self, name, dur=None, pitch=1.0):
        """Short sounds for on-screen actions: thud (something lands), pop (item appears), tick (counter step, letter),
        ding (count finished), blip (cell lights up), rise (bar grows), scribble (line being drawn), sweep (arc or wipe),
        shimmer (light tracing), whoosh (slide), click (key press)."""
        sr = self.sr
        if name == "thud": t = self.n(0.4); return np.sin(2 * np.pi * (70 * t + 30 * (1 - np.exp(-t * 30)) / 30 * 2)) * np.exp(-t * 14) + self.lp(self.noise(len(t)), 700) * np.exp(-t * 45) * 0.5
        if name == "pop": t = self.n(0.14); return np.sin(2 * np.pi * np.cumsum(420 * pitch + 900 * np.exp(-t * 45)) / sr) * np.exp(-t * 34)
        if name == "tick": t = self.n(0.035); return (np.sin(2 * np.pi * 1900 * pitch * t) * 0.7 + self.noise(len(t)) * 0.4) * np.exp(-t * 190)
        if name == "ding": t = self.n(1.6); f = 1568 * pitch; return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 6)) * np.exp(-t * 3.2) * (1 - np.exp(-t * 800))
        if name == "blip": t = self.n(0.09); return np.sin(2 * np.pi * 660 * pitch * t) * np.exp(-t * 40) * (1 - np.exp(-t * 900))
        if name == "rise": t = self.n(dur or 0.35); x = t / t[-1]; return np.sin(2 * np.pi * np.cumsum(180 * pitch + 520 * pitch * x ** 1.5) / sr) * np.sin(np.pi * x) ** 1.2 * 0.8
        if name == "scribble":
            t = self.n(dur or 1.0); x = t / t[-1]; b, a = butter(2, [1400 / (sr / 2), 5200 / (sr / 2)], "band")
            return lfilter(b, a, self.noise(len(t))) * (0.55 + 0.45 * np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 1.7 * t))) ** 2 * np.clip(x * 12, 0, 1) * np.clip((1 - x) * 12, 0, 1) * 1.6
        if name == "sweep": t = self.n(dur or 1.0); x = t / t[-1]; return (self.lp(self.hp(self.noise(len(t)), 500), 1500 + 3500 * x[-1]) * 0.8 + np.sin(2 * np.pi * np.cumsum(220 + 500 * x) / sr) * 0.25) * np.sin(np.pi * x) ** 1.5
        if name == "shimmer": t = self.n(dur or 1.5); x = t / t[-1]; return sum(np.sin(2 * np.pi * mf(m) * t * (1 + 0.002 * np.sin(11 * t + m))) for m in (86, 93, 98, 102)) * x ** 1.5 * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * 0.25
        if name == "whoosh": return self.whoosh(dur or 0.45)
        if name == "click": return self.click()
        import foley
        if name in foley.NAMES: return foley.make(self, name, dur, pitch)
        raise ValueError("unknown sound: " + name + " (also: " + ", ".join(foley.NAMES) + ")")

    # ----- ambience -----
    def wind(self, f0, f1, g=0.11):
        tt = np.arange(self.N) / self.sr
        w = self.lp(self.noise(self.N), 480) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * tt)) * np.clip((tt - self.t(f0)) / 2, 0, 1) * np.clip((self.t(f1) - tt) / 2, 0, 1)
        self.dry[:, 0] += w * g; self.dry[:, 1] += np.roll(w, 4000) * g
    def birdsong(self, f0, f1, count=14, g=0.018):
        for _ in range(count):
            t0 = self.r.uniform(self.t(f0), self.t(f1)); fr = self.r.uniform(2700, 4800); pan = self.r.uniform(-0.8, 0.8)
            for j in range(self.r.integers(2, 5)):
                tc = self.n(0.07)
                self.add(self.wet, np.sin(2 * np.pi * np.cumsum(fr + 900 * np.sin(np.pi * tc / 0.07) * (1 if j % 2 else -0.6)) / self.sr) * np.sin(np.pi * tc / 0.07) ** 2, t0 + j * 0.11, pan=pan, g=g)
    def hum(self, f0, f1, g=0.05):                               # mains hum for a CRT / machine
        t = self.n(self.t(f1 - f0)); e = np.clip(t / 0.3, 0, 1) * np.clip((t[-1] - t) * 3, 0, 1)
        self.add(self.dry, (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.25 * np.sin(2 * np.pi * 150 * t)) * e, self.t(f0), g=g)

    # ----- master -----
    def write(self, path, reverb=0.011, tail=3.2, drive=1.35, fade_out=2.2, sections=None):
        ti = self.n(tail)
        rev = np.stack([fftconvolve(self.wet[:, c], self.lp(np.random.default_rng(30 + c).standard_normal(len(ti)), 6000) * np.exp(-ti * 2.3), "full")[:self.N] for c in (0, 1)], 1)
        out = self.wet + self.dry + rev * reverb
        out /= max(np.abs(out).max(), 1e-9) / drive; out = np.tanh(out) / np.tanh(drive) * 0.92
        out = out[:int(self.F / self.fps * self.sr)]; fo = int(fade_out * self.sr)
        out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.4; out[:400] *= np.linspace(0, 1, 400)[:, None]
        for a, b in sections or [(0, self.F)]:
            seg = out[int(self.t(a) * self.sr):int(self.t(b) * self.sr)]
            if len(seg): print("frames %5d-%5d  rms %.3f  peak %.2f" % (a, b, np.sqrt((seg ** 2).mean()), np.abs(seg).max()))
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(self.sr); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
