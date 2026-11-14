"""joyboy foley: the sounds of matter, made in code, and beds for rooms and machines.

Every visible action should have a sound that fits its material: chalk does not sound like marker, paper does not sound like glass. These are procedural
(filtered noise, modal tones, envelopes), so they cost nothing to install and land exactly on the frame they are given.

    film.skit(..., sfx=[(0.4, "stamp"), (1.0, "paper", 0.5)])           any scene: (seconds, name[, length in seconds])
    Film(..., bed="room")                                                a quiet bed under the whole film: room, ballast, air, tape, fan
    film.sound_layer(lambda s, duck: foley.bed(s, "ballast", 0, s.F, 0.04))   a bed with your own range and level

Names: chalk marker pencil paper page stamp tape shutter keys relay sonar glass beep knock squeak whirr degauss bell
Beds:  room ballast air tape fan

Sounds are created by Score.fx() (see score.py) for any name listed here; `make(score, name, dur, pitch)` returns the signal.
"""
import numpy as np
from scipy.signal import butter, lfilter

NAMES = ("chalk", "marker", "pencil", "paper", "page", "stamp", "tape", "shutter", "keys", "relay", "sonar", "glass", "beep", "knock", "squeak", "whirr", "degauss", "bell")
BEDS = ("room", "ballast", "air", "tape", "fan")

def _bp(s, x, lo, hi, o=2): b, a = butter(o, [lo / (s.sr / 2), min(hi, s.sr * 0.45) / (s.sr / 2)], "band"); return lfilter(b, a, x)

def make(s, name, dur=None, pitch=1.0):
    sr = s.sr; r = s.r
    if name == "chalk":                                    # a grainy drag: noise cut into grains, a few bright ones on top
        d = dur or 0.6; t = s.n(d); x = _bp(s, s.noise(len(t)), 1800, 7000); grains = (r.random(len(t)) < 0.35) * r.random(len(t)); env = np.clip(t * 25, 0, 1) * np.clip((d - t) * 25, 0, 1)
        return (x * (0.35 + 0.65 * grains) * env + _bp(s, s.noise(len(t)), 300, 900) * 0.15 * env) * 1.2
    if name == "marker":                                   # a felt tip: a squeak whose pitch wobbles with the hand, over a soft hiss
        d = dur or 0.5; t = s.n(d); f = (2300 + 400 * np.sin(2 * np.pi * 6 * t) + 600 * np.sin(2 * np.pi * 1.7 * t)) * pitch; sq = np.sin(2 * np.pi * np.cumsum(f) / sr) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)) ** 2
        env = np.clip(t * 30, 0, 1) * np.clip((d - t) * 30, 0, 1); return (sq * 0.35 + _bp(s, s.noise(len(t)), 2500, 8000) * 0.25) * env
    if name == "pencil":                                   # graphite on tooth: high, fine, scratchy
        d = dur or 0.5; t = s.n(d); x = _bp(s, s.noise(len(t)), 3500, 9000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 14 * t + 3 * np.sin(2 * np.pi * 2.3 * t)))); return x * np.clip(t * 40, 0, 1) * np.clip((d - t) * 40, 0, 1) * 0.9
    if name == "paper":                                    # a rustle: several short filtered bursts
        d = dur or 0.45; t = s.n(d); out = np.zeros(len(t))
        for _ in range(int(6 + d * 18)):
            i = int(r.integers(0, max(len(t) - 600, 1))); L = int(r.integers(300, 1500)); L = min(L, len(t) - i); seg = _bp(s, s.noise(L), 1200, 7500) * np.hanning(L) * r.uniform(0.3, 1.0); out[i:i + L] += seg
        return out * 0.9
    if name == "page":                                     # one page turned: a rising sweep and a settle
        t = s.n(dur or 0.7); x = t / t[-1]; return _bp(s, s.noise(len(t)), 800, 6500) * np.sin(np.pi * x) ** 1.4 * (0.6 + 0.4 * x) + _bp(s, s.noise(len(t)), 100, 400) * np.exp(-((x - 0.82) * 14) ** 2) * 0.5
    if name == "stamp":                                    # rubber on paper: a soft thump, a short slap
        t = s.n(0.35); return np.sin(2 * np.pi * (90 * pitch * t + 40 * (1 - np.exp(-t * 40)) / 40)) * np.exp(-t * 16) + s.lp(s.noise(len(t)), 2200) * np.exp(-t * 60) * 0.7
    if name == "tape":                                     # a cassette: a click, a short whirr of the motor
        t = s.n(0.5); click = s.noise(len(t)) * np.exp(-t * 400) * 0.8; motor = np.sin(2 * np.pi * (180 + 60 * np.exp(-t * 8)) * t) * np.exp(-t * 7) * 0.25; return click + motor + _bp(s, s.noise(len(t)), 900, 3000) * np.exp(-t * 14) * 0.2
    if name == "shutter":                                  # a camera: two clacks close together
        t = s.n(0.22); a = np.exp(-t * 250); b = np.exp(-np.clip(t - 0.07, 0, None) * 220) * (t > 0.07); return (_bp(s, s.noise(len(t)), 1500, 6000) * (a + 0.7 * b) + np.sin(2 * np.pi * 900 * t) * (a + b) * 0.2) * 0.9
    if name == "keys":                                     # typing: a quick run of clicks
        d = dur or 0.6; t = s.n(d); out = np.zeros(len(t)); n = max(3, int(d * 12))
        for k in range(n):
            i = max(0, int((k / n + r.uniform(-0.02, 0.03)) * len(t))); L = min(int(0.03 * sr), len(t) - i)
            if L > 20: tt = np.arange(L) / sr; out[i:i + L] += (s.noise(L) * np.exp(-tt * 260) * 0.7 + np.sin(2 * np.pi * (1800 + 700 * r.random()) * tt) * np.exp(-tt * 200) * 0.4) * r.uniform(0.6, 1.0)
        return out
    if name == "relay":                                    # a relay: a click, a clack
        t = s.n(0.12); return (s.noise(len(t)) * np.exp(-t * 500) + np.sin(2 * np.pi * 1100 * t) * np.exp(-t * 300) * 0.5) * 0.8 + (s.noise(len(t)) * np.exp(-np.clip(t - 0.05, 0, None) * 400) * (t > 0.05)) * 0.6
    if name == "sonar":                                    # a ping with two fading echoes
        t = s.n(dur or 2.0); f = 1250 * pitch; p = np.sin(2 * np.pi * f * t) * np.exp(-t * 5) * (1 - np.exp(-t * 600)); e1 = np.roll(p, int(0.28 * sr)) * 0.35; e2 = np.roll(p, int(0.62 * sr)) * 0.16; e1[:int(0.28 * sr)] = 0; e2[:int(0.62 * sr)] = 0; return p + e1 + e2
    if name == "glass":                                    # a tink: a few inharmonic partials
        t = s.n(1.2); f = 2400 * pitch; return sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (6 + 5 * k)) * a for k, a in ((1.0, 1.0), (2.76, 0.5), (5.4, 0.25))) * (1 - np.exp(-t * 900))
    if name == "beep":                                     # an instrument beep
        t = s.n(0.14); return np.sin(2 * np.pi * 1760 * pitch * t) * np.clip(t * 400, 0, 1) * np.clip((0.14 - t) * 400, 0, 1) * 0.7
    if name == "knock":                                    # knuckle on wood
        t = s.n(0.3); return np.sin(2 * np.pi * (180 * pitch) * t) * np.exp(-t * 28) + s.lp(s.noise(len(t)), 1200) * np.exp(-t * 80) * 0.6
    if name == "squeak":                                   # rubber on glass
        t = s.n(dur or 0.35); f = (1500 + 1400 * (t / t[-1]) ** 1.5) * pitch; return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.sin(np.pi * t / t[-1]) ** 0.8 * 0.5
    if name == "whirr":                                    # a small motor spinning up and down
        t = s.n(dur or 0.8); x = t / t[-1]; f = (120 + 520 * np.sin(np.pi * x) ** 1.2) * pitch; return (np.sin(2 * np.pi * np.cumsum(f) / sr) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / sr)) * np.sin(np.pi * x) * 0.3
    if name == "degauss":                                  # a CRT switching on: a heavy thump and a rising whine that settles
        t = s.n(1.4); thump = np.sin(2 * np.pi * (55 * t + 25 * (1 - np.exp(-t * 12)) / 12)) * np.exp(-t * 6); whine = np.sin(2 * np.pi * (6000 + 9000 * np.exp(-t * 3)) * t) * np.exp(-t * 2) * 0.05; return thump + whine
    if name == "bell":                                     # a desk bell
        t = s.n(1.6); f = 1568 * pitch; return sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + 2 * k)) * a for k, a in ((1.0, 1.0), (2.4, 0.55), (4.1, 0.3))) * (1 - np.exp(-t * 700))
    raise ValueError("unknown foley: " + name)

def bed(s, name, f0, f1, g=0.05, duck=None):
    """A quiet continuous bed under frames f0..f1 of the score. room: air and distant movement; ballast: mains hum with starter ticks; air: a vent;
    tape: hiss with slow wow; fan: a low machine rotation."""
    t0 = s.t(f0); n = int(s.t(f1 - f0) * s.sr); tt = np.arange(n) / s.sr; env = np.clip(tt / 1.0, 0, 1) * np.clip((tt[-1] - tt) / 1.5, 0, 1)
    if name == "room": x = s.lp(s.noise(n), 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt)) + _bp(s, s.noise(n), 2500, 6500) * 0.04
    elif name == "ballast": x = (np.sin(2 * np.pi * 100 * tt) + 0.5 * np.sin(2 * np.pi * 200 * tt) + 0.3 * np.sin(2 * np.pi * 300 * tt) + 0.12 * np.sin(2 * np.pi * 500 * tt)) * 0.25 * (1 + 0.04 * np.sin(2 * np.pi * 0.3 * tt)) + s.lp(s.noise(n), 300) * 0.08
    elif name == "air": x = _bp(s, s.noise(n), 200, 1800) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * tt))
    elif name == "tape": wow = 1 + 0.004 * np.sin(2 * np.pi * 0.5 * tt); x = s.hp(s.noise(n), 3000) * 0.18 + np.sin(2 * np.pi * np.cumsum(60 * wow) / s.sr) * 0.05
    elif name == "fan": x = (np.sin(2 * np.pi * 48 * tt) * 0.5 + _bp(s, s.noise(n), 90, 500) * 0.6) * (1 + 0.05 * np.sin(2 * np.pi * 8 * tt))
    else: raise ValueError("unknown bed: " + name)
    if duck is not None:                                   # sit lower while a voice speaks
        i0 = int(t0 * s.sr); seg = duck[i0:i0 + n, 0] if getattr(duck, 'ndim', 1) == 2 else duck[i0:i0 + n]; x = x[:len(seg)] * seg; env = env[:len(seg)]
    s.add(s.dry, x * env, t0, g=g)
