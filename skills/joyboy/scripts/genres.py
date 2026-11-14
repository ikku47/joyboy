"""joyboy genres: twelve music styles, each with its own instruments, groove, harmony and melody.

    from genres import compose, pick_genre, GENRES
    g = pick_genre("upbeat", seed)               # a genre that suits the mood, chosen by the seed
    compose(score, frames_per_beat, g, seed, energy=1.0, key=None)

A genre is a table (tempo range, modes, chord progressions, 16-step drum grids, which layers play) plus a small
engine that turns it into music for the number of bars the film needs. Everything that is not fixed by the genre
comes from the seed: tempo, key, mode, progression, drum variant, the melody itself, where the breakdown falls.
Two films never get the same tune by accident, and the same film always gets the same music.

Genres: lofi, house, trap, synthwave, ambient, acoustic, funk, epic, phonk, afro, pop, techno.
"""
import numpy as np
from scipy.signal import butter, lfilter
from score import mf

MODES = dict(minor=[0, 2, 3, 5, 7, 8, 10], major=[0, 2, 4, 5, 7, 9, 11], dorian=[0, 2, 3, 5, 7, 9, 10], mixolydian=[0, 2, 4, 5, 7, 9, 10],
             phrygian=[0, 1, 3, 5, 7, 8, 10], lydian=[0, 2, 4, 6, 7, 9, 11])

# progressions are scale degrees (0 = I). Eight entries = two chords per bar.
MINOR_P = [[0, 5, 2, 6], [0, 3, 6, 2], [0, 6, 5, 6], [0, 2, 5, 4], [5, 2, 6, 0], [0, 0, 5, 6], [0, 4, 5, 3], [0, 5, 3, 6, 0, 5, 4, 4]]
MAJOR_P = [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 4, 3], [5, 3, 0, 4], [0, 2, 3, 4], [0, 4, 3, 0], [3, 4, 2, 5], [0, 4, 5, 2, 3, 0, 3, 4]]
JAZZ_P = [[1, 4, 0, 0], [0, 5, 1, 4], [2, 5, 1, 0], [0, 2, 3, 4], [1, 4, 0, 5]]

GENRES = {
    "lofi": dict(bpm=(72, 86), modes=["dorian", "minor", "major"], progs=JAZZ_P, size=4, swing=0.24, cut="none", side=0.0, gain=1.0, desc="dusty jazz chords, vinyl crackle, lazy swung beat",
                 kick=["x.......x.x.....", "x.....x...x.....", "x..x....x.......", "x.......x..x...."], snare=["....x.......x...", "....x.......x..o"], hat=["x.x.x.x.x.x.x.x.", "x.xxx.x.x.xxx.x.", "x.x.x.xxx.x.x.x."],
                 layers=["keys", "bass", "lead", "vinyl"], lead=["bell", "keys"], rhythms=["x.....x...x.....", "..x.....x...x...", "x.......x..x...."]),
    "house": dict(bpm=(120, 126), modes=["minor", "dorian"], progs=MINOR_P, size=4, swing=0.0, cut="crash", side=0.65, gain=1.0, desc="four on the floor, offbeat bass, pumping chord stabs",
                  kick=["x...x...x...x..."], clap=["....x.......x..."], ohat=["..x...x...x...x."], hat=["x.xxx.xxx.xxx.xx", "xxxxxxxxxxxxxxxx"], perc=["..o...o..o...o.o"],
                  layers=["pad", "stab", "bass_roll", "lead", "drums_late"], lead=["pluck", "marimba"], rhythms=["x..x..x...x.x...", "..x.x...x..x.x..", "x.x.x.x.x.x.x.xx"]),
    "trap": dict(bpm=(130, 146), modes=["minor", "phrygian", "dorian"], progs=MINOR_P, size=3, swing=0.0, cut="boom", side=0.0, gain=1.0, desc="808 slides, rolling hats, bell melody, half-time snare",
                 kick=["x......x..x.....", "x.....x...x..x..", "x...........x.x."], clap=["........x......."], hat=["x.x.x.x.x.x.x.x.", "xxxxxxxxxxxxxxxx", "x.x.xxxxx.x.x.xx"],
                 layers=["pad", "808", "lead", "hatroll"], lead=["bell", "pluck"], rhythms=["x.....x...x.....", "x..x..x...x.x...", "x.x...x.x...x..."]),
    "synthwave": dict(bpm=(98, 110), modes=["minor", "dorian"], progs=MINOR_P, size=3, swing=0.0, cut="crash", side=0.25, gain=1.0, desc="neon arpeggios, gated snare, driving eighth-note bass",
                      kick=["x...x...x...x...", "x..x..x.x...x..."], snare=["....x.......x..."], hat=["..x...x...x...x."], layers=["pad", "arp", "bass_eighth", "lead", "gate"], lead=["saw", "bell"],
                      rhythms=["x.....x...x.....", "x..x....x..x...."]),
    "ambient": dict(bpm=60, modes=["lydian", "major", "dorian"], progs=MAJOR_P, size=4, swing=0.0, cut="none", side=0.0, gain=1.0, desc="slow evolving pads, a few sparse bells, no drums",
                    layers=["pad", "sparse", "air", "sub"], lead=["bell", "marimba"], rhythms=["x...............", "........x......."]),
    "acoustic": dict(bpm=(92, 106), modes=["major", "mixolydian"], progs=MAJOR_P, size=3, swing=0.06, cut="none", side=0.0, gain=1.0, desc="plucked guitar, shaker, soft kick and snaps, warm and hopeful",
                     kick=["x.....x.x.......", "x.......x.x....."], snap=["....x.......x..."], shaker=["xxxxxxxxxxxxxxxx", "x.xxx.xxx.xxx.xx"], layers=["guitar", "bass_pluck", "lead", "drums_late"], lead=["marimba", "whistle"],
                     rhythms=["x...x.x...x.x...", "..x...x.x.....x.", "x.x...x...x..x.."]),
    "funk": dict(bpm=(100, 112), modes=["dorian", "mixolydian"], progs=[[0, 3, 0, 4], [1, 4, 0, 0], [0, 0, 3, 4], [0, 5, 3, 4]], size=4, swing=0.10, cut="crash", side=0.0, gain=1.0, desc="slap bass, wah chord stabs, tight ghost-note drums, cowbell",
                 kick=["x..x..x...x.....", "x.....x..x.x...."], snare=["....x..o.o..x..o", "....x.o.....x..o"], hat=["xxxxxxxxxxxxxxxx", "x.xxx.xxx.xxx.xx"], layers=["stab", "bass_funk", "lead", "cowbell", "drums_late"],
                 lead=["pluck", "saw"], rhythms=["..x.x...x..x.x..", "x.x..x..x.x....x"]),
    "epic": dict(bpm=(78, 96), modes=["minor", "phrygian"], progs=MINOR_P, size=4, swing=0.0, cut="boom", side=0.0, gain=1.0, desc="trailer strings, taiko, brass, choir; builds and hits",
                 layers=["strings_ost", "choir", "taiko", "braam", "sub", "lead"], lead=["piano"], rhythms=["x...............", "x.......x......."]),
    "phonk": dict(bpm=(128, 142), modes=["phrygian", "minor"], progs=[[0, 0, 1, 0], [0, 5, 6, 0], [0, 1, 0, 6], [0, 6, 5, 6]], size=3, swing=0.05, cut="boom", side=0.0, gain=1.0, desc="drifting cowbell melody, distorted 808, vinyl dust",
                  kick=["x..x..x...x.....", "x.....x..x..x..."], clap=["....x.......x...", "....x.......x..x"], hat=["x.x.x.x.x.x.x.xx", "xxxxxxxxxxxxxxxx"], layers=["808_dirty", "cowbell_lead", "pad", "vinyl", "hatroll"], lead=["cowbell"],
                  rhythms=["x..x..x...x.x...", "x.x...x..x.x....", "x...x.x...x...x."]),
    "afro": dict(bpm=(100, 112), modes=["major", "mixolydian", "dorian"], progs=MAJOR_P, size=3, swing=0.08, cut="crash", side=0.0, gain=1.0, desc="tresillo percussion, marimba chords, rim-click groove",
                 kick=["x..x..x...x..x..", "x.....x..x..x..."], rim=["....x.x.....x..."], conga=["..x.x..x..x.x...", "x..x..x...x..x.."], shaker=["x.xxx.xxx.xxx.xx"], layers=["marimba_chords", "bass_pluck", "lead", "drums_late"],
                 lead=["bell", "marimba"], rhythms=["x..x..x...x..x..", "x.x..x..x.x.....", "..x..x..x..x.x.."]),
    "pop": dict(bpm=(112, 124), modes=["major", "mixolydian", "minor"], progs=MAJOR_P + MINOR_P[:3], size=3, swing=0.0, cut="crash", side=0.35, gain=1.0, desc="bright piano chords, pluck lead, claps and snaps: the clean promo sound",
                kick=["x.....x.x.......", "x...x...x...x...", "x..x....x..x...."], clap=["....x.......x..."], hat=["x.x.x.x.x.x.x.x.", "..x...x...x...x."], layers=["piano_pulse", "pad", "bass_eighth", "lead", "drums_late"],
                lead=["pluck", "bell", "marimba"], rhythms=["x..x..x...x.x...", "x.x.x...x.x.....", "..x.x.x.x.x.x..."]),
    "techno": dict(bpm=(126, 134), modes=["minor", "phrygian"], progs=[[0, 0, 0, 0], [0, 0, 1, 0], [0, 6, 0, 5], [0, 0, 5, 6]], size=3, swing=0.0, cut="whoosh", side=0.5, gain=1.0, desc="driving kick, rolling acid bass, hypnotic stabs",
                   kick=["x...x...x...x..."], hat=["..x...x...x...x."], ohat=["..x...x...x...x."], clap=["....x.......x..."], perc=["x.xx.x.xx.x.xx.x"], layers=["bass_acid", "stab_dark", "perc", "drums_late", "lead"], lead=["acid"],
                   rhythms=["x.xx.x.xx.x.xx.x", "x..x.x..x.x.x..x"]),
}
GENRES.update({
    "chiptune": dict(bpm=(124, 144), modes=["major", "minor", "mixolydian"], progs=MAJOR_P + MINOR_P[:4], size=3, swing=0.0, cut="crash", side=0.0, gain=1.0, desc="square and triangle voices, noise drums: an 8-bit game console score",
                     layers=["chip_arp", "chip_bass", "chip_drums", "lead"], lead=["chip"], rhythms=["x..x..x...x.x...", "x.x.x...x.x.x...", "x...x.x.x...x.x."]),
    "jazz": dict(bpm=(150, 176), modes=["major", "mixolydian", "dorian"], progs=JAZZ_P, size=4, swing=0.34, cut="none", side=0.0, gain=1.0, desc="1930s swing: stride piano, brushes and a clarinet or vibes lead",
                 layers=["stride", "brush", "lead"], lead=["clar", "vibes"], rhythms=["x..x..x...x.x...", "..x.x...x..x.x..", "x.x..x..x.x....x"]),
    "mallets": dict(bpm=(88, 104), modes=["major", "lydian", "mixolydian"], progs=MAJOR_P, size=3, swing=0.04, cut="none", side=0.0, gain=1.0, desc="tuned percussion: marimba, vibraphone, kalimba and a soft plucked bass, light and precise",
                    shaker=["x.xxx.xxx.xxx.xx"], layers=["marimba_chords", "bass_pluck", "lead", "drums_late"], lead=["vibes", "marimba", "bell"], rhythms=["x...x.x...x.x...", "x.x...x.x.....x.", "..x.x...x.x....."]),
    "citypop": dict(bpm=(100, 112), modes=["dorian", "major"], progs=[[1, 4, 0, 5], [0, 5, 1, 4], [3, 4, 2, 5], [1, 4, 0, 0]], size=4, swing=0.05, cut="crash", side=0.25, gain=1.0, desc="late-80s city pop: electric piano, slap bass, chorus guitar stabs, synth lead",
                    kick=["x..x..x...x..x..", "x...x..x..x....."], snare=["....x.......x..."], hat=["x.xxx.xxx.xxx.xx"], layers=["keys", "bass_funk", "stab", "lead", "drums_late"], lead=["saw", "vibes"], rhythms=["x..x..x...x.x...", "..x.x.x...x..x.."]),
    "counterpoint": dict(bpm=(80, 96), modes=["minor", "dorian"], progs=MINOR_P, size=3, swing=0.0, cut="none", side=0.0, gain=1.0, desc="two interlocking harpsichord lines, a canon over a slow pad: mechanical and precise",
                         layers=["pad", "lead", "canon"], lead=["harpsi"], rhythms=["x.x.x.xxx.x.x.x.", "x.xxx.x.x.xxx.x.", "x.x.xxx.x.x.xxx."]),
    "roomtone": dict(bpm=60, modes=["minor"], progs=MINOR_P, size=3, swing=0.0, cut="none", side=0.0, gain=1.0, desc="no tune at all: a room or machine hum with slow tape wobble, for films that carry on sound design alone",
                     layers=["hum"], lead=["bell"], rhythms=["x..............."]),
})
FOR_MOOD = {"cinematic": ["epic", "ambient", "synthwave", "phonk", "counterpoint"], "calm": ["lofi", "ambient", "acoustic", "mallets", "counterpoint"], "upbeat": ["pop", "house", "funk", "afro", "acoustic", "synthwave", "citypop", "chiptune", "mallets"],
            "tech": ["techno", "house", "synthwave", "trap", "pop", "chiptune", "counterpoint"], "hype": ["trap", "phonk", "techno", "house", "chiptune"]}

_cache = {}

def pick_genre(mood, seed):
    c = FOR_MOOD.get(mood, list(GENRES)); return c[(seed // 7) % len(c)]

def tempo(genre, seed):
    b = GENRES[genre]["bpm"]; return b if isinstance(b, int) else b[0] + (seed // 11) % (b[1] - b[0] + 1)

# ---------------------------------------------------------------- instruments (all cached: same note, same sound)
def _memo(fn):
    def w(s, *a):
        k = (fn.__name__, s.sr) + a
        if k not in _cache: _cache[k] = fn(s, *a)
        return _cache[k]
    w.__name__ = fn.__name__; return w

@_memo
def pluck(s, m, dur=1.4, bright=0.5):                       # Karplus-Strong string: guitar, harp, pluck lead
    f = mf(m); D = max(int(s.sr / f), 8); n = int(dur * s.sr); x = np.zeros(n)
    x[:D] = s.lp(np.random.default_rng(int(m * 7)).standard_normal(D), 900 + 7000 * bright, 1) if D > 12 else np.random.default_rng(1).standard_normal(D)
    a = np.zeros(D + 2); a[0] = 1; a[D] = a[D + 1] = -0.4985; y = lfilter([1.0], a, x)
    return y / max(np.abs(y).max(), 1e-6) * np.clip((dur - np.arange(n) / s.sr) * 8, 0, 1)

@_memo
def supersaw(s, m, dur, att=0.01, rel=0.2, cut=3200, voices=5, spread=18):
    t = s.n(dur); sig = 0
    for k in range(voices):
        det = (k - (voices - 1) / 2) * spread / max(voices / 2, 1); sig = sig + 2 * ((mf(m) * 2 ** (det / 1200) * t + k * 0.37) % 1) - 1
    return s.lp(sig / voices, cut) * np.clip(t / att, 0, 1) * np.clip((dur - t) / rel, 0, 1)

@_memo
def pad(s, ms, dur, att=1.0, rel=1.2, cut=1400):             # slow, warm, detuned saws with a gentle swell
    t = s.n(dur); sig = 0
    for m in ms:
        for det in (-11, -4, 5, 12): sig = sig + 2 * ((mf(m) * 2 ** (det / 1200) * t + (m * 0.13 + det * 0.017) % 1) % 1) - 1
    sig = s.lp(sig, cut) / (len(ms) * 4)
    return sig * np.clip(t / att, 0, 1) * np.clip((dur - t) / rel, 0, 1) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * t))

@_memo
def s808(s, m, dur=0.6, glide=None, drive=2.2):
    t = s.n(dur); f = mf(m) * (1 + 1.6 * np.exp(-t * 55))
    if glide is not None: x = np.clip((t - dur * 0.55) / (dur * 0.4), 0, 1); f = f * (mf(glide) / mf(m)) ** (x * x * (3 - 2 * x))
    ph = 2 * np.pi * np.cumsum(f) / s.sr; sig = np.tanh(np.sin(ph) * drive) / np.tanh(drive)
    return sig * np.clip(t / 0.003, 0, 1) * np.exp(-t * 1.6) * np.clip((dur - t) / 0.06, 0, 1)

@_memo
def bass(s, m, dur=0.3, cut=900, sweep=9.0, sub=0.6):         # saw + square bass with a closing filter: acid, funk, house
    t = s.n(dur); f = mf(m); saw = 2 * ((f * t) % 1) - 1; sq = np.sign(np.sin(2 * np.pi * f * 0.5 * t))
    e = np.exp(-t * sweep); sig = s.lp(saw, cut) * (1 - e) + s.lp(saw, cut * 4.2) * e
    return (sig + sub * sq * 0.5) * np.clip(t / 0.004, 0, 1) * np.exp(-t * 3.0) * np.clip((dur - t) / 0.03, 0, 1)

@_memo
def acid(s, m, dur=0.16):
    t = s.n(dur); f = mf(m); saw = 2 * ((f * t) % 1) - 1; e = np.exp(-t * 16); sig = s.lp(saw, 500) * (1 - e) + s.lp(saw, 3600) * e
    return np.tanh(sig * 1.8) * np.clip(t / 0.003, 0, 1) * np.clip((dur - t) / 0.02, 0, 1)

@_memo
def marimba(s, m, dur=0.9):
    t = s.n(dur); f = mf(m); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.45 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 28)) * (1 - np.exp(-t * 900))

@_memo
def whistle(s, m, dur=0.5):
    t = s.n(dur); vib = 1 + 0.006 * np.sin(2 * np.pi * 5.6 * t) * np.clip(t / 0.2, 0, 1); f = mf(m)
    return (np.sin(2 * np.pi * f * t * vib) + 0.12 * np.sin(4 * np.pi * f * t * vib)) * np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.15, 0, 1) * 0.8

@_memo
def brass(s, ms, dur=0.3, cut=2600):
    t = s.n(dur); sig = 0
    for m in ms:
        for det in (-7, 0, 7): sig = sig + 2 * ((mf(m) * 2 ** (det / 1200) * t + det * 0.01) % 1) - 1
    e = np.exp(-t * 7); sig = (s.lp(sig, cut) * (0.4 + 0.6 * e)) / (len(ms) * 3)
    return sig * np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.06, 0, 1)

@_memo
def clap(s):
    t = s.n(0.3); b, a = butter(2, [900 / (s.sr / 2), 3200 / (s.sr / 2)], "band"); x = lfilter(b, a, np.random.default_rng(5).standard_normal(len(t)))
    env = sum(np.exp(-np.clip(t - o, 0, None) * 220) * (t >= o) for o in (0, 0.011, 0.022)) * 0.5 + np.exp(-t * 20) * 0.7 * (t >= 0.03)
    return x * env

@_memo
def shaker(s, g=1.0):
    t = s.n(0.09); b, a = butter(2, [5200 / (s.sr / 2), 10000 / (s.sr / 2)], "band"); return lfilter(b, a, np.random.default_rng(6).standard_normal(len(t))) * np.sin(np.pi * np.clip(t / 0.09, 0, 1)) ** 1.5 * 1.2

@_memo
def ohat(s):
    t = s.n(0.32); return s.hp(np.random.default_rng(7).standard_normal(len(t)), 7000) * np.exp(-t * 13)

@_memo
def rim(s):
    t = s.n(0.08); return (np.sin(2 * np.pi * 1750 * t) * 0.6 + np.sin(2 * np.pi * 480 * t) * 0.5) * np.exp(-t * 70) + np.random.default_rng(8).standard_normal(len(t)) * np.exp(-t * 200) * 0.2

@_memo
def cowbell(s, pitch=1.0):
    t = s.n(0.4); x = np.sign(np.sin(2 * np.pi * 562 * pitch * t)) + np.sign(np.sin(2 * np.pi * 845 * pitch * t)); b, a = butter(2, [600 / (s.sr / 2), 2600 / (s.sr / 2)], "band")
    return lfilter(b, a, x) * np.exp(-t * 11) * 0.6

@_memo
def conga(s, hi=1):
    t = s.n(0.3); f = (330 if hi else 235) * (1 + 0.25 * np.exp(-t * 40)); return np.sin(2 * np.pi * np.cumsum(f) / s.sr) * np.exp(-t * 16) + s.hp(np.random.default_rng(9).standard_normal(len(t)), 1800) * np.exp(-t * 90) * 0.25

@_memo
def snap(s):
    t = s.n(0.12); b, a = butter(2, [1800 / (s.sr / 2), 5200 / (s.sr / 2)], "band"); return lfilter(b, a, np.random.default_rng(10).standard_normal(len(t))) * np.exp(-t * 55) + np.sin(2 * np.pi * 1250 * t) * np.exp(-t * 90) * 0.3

@_memo
def tkick(s, kind="punch"):                                   # kick variants: punch / soft / deep / hard
    t = s.n(0.42)
    if kind == "soft": return s.lp(np.sin(2 * np.pi * (52 * t + 5 * (1 - np.exp(-t * 28)))), 220) * np.exp(-t * 10)
    if kind == "deep": return np.sin(2 * np.pi * (44 * t + 9 * (1 - np.exp(-t * 18)))) * np.exp(-t * 6.5)
    if kind == "hard": return np.tanh(2.2 * np.sin(2 * np.pi * (55 * t + 14 * (1 - np.exp(-t * 36))))) * np.exp(-t * 9) + np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t * 400) * 0.25
    return np.sin(2 * np.pi * (50 * t + 7 * (1 - np.exp(-t * 30)))) * np.exp(-t * 11)

@_memo
def tsnare(s, kind="tight"):
    t = s.n(0.24); b, a = butter(2, [1700 / (s.sr / 2), 7000 / (s.sr / 2)], "band"); n_ = lfilter(b, a, np.random.default_rng(11).standard_normal(len(t)))
    if kind == "dusty": return s.lp(n_, 3800) * np.exp(-t * 22) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.3
    if kind == "gated": return n_ * (t < 0.16) * np.exp(-t * 8) + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 25) * 0.35
    return n_ * np.exp(-t * 28) + np.sin(2 * np.pi * 210 * t) * np.exp(-t * 35) * 0.4

@_memo
def thh(s, kind="tight"):
    t = s.n(0.07); return s.hp(np.random.default_rng(12).standard_normal(len(t)), 6500 if kind == "tight" else 4200) * np.exp(-t * (95 if kind == "tight" else 60))

@_memo
def chip(s, m, dur=0.2, duty=0.5, kind="sq"):                # console voices: a pulse wave or a triangle
    t = s.n(dur); f = mf(m); x = (2 * np.abs(2 * ((f * t) % 1) - 1) - 1) if kind == "tri" else np.where(((f * t) % 1) < duty, 1.0, -1.0)
    return x * np.clip(t / 0.003, 0, 1) * np.clip((dur - t) / 0.02, 0, 1) * (0.75 + 0.25 * np.exp(-t * 8)) * 0.5

@_memo
def chipdrum(s, kind="snare"):                               # noise drums at console quality
    n = {"kick": 0.16, "snare": 0.14, "hat": 0.04}[kind]; t = s.n(n); r = np.random.default_rng(31).choice([-1.0, 1.0], len(t))
    if kind == "kick": return np.sin(2 * np.pi * np.cumsum(150 * np.exp(-t * 28) + 45) / s.sr) * np.exp(-t * 12)
    if kind == "snare": return (r * np.exp(-t * 26) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 40) * 0.4)
    return s.hp(r, 6000) * np.exp(-t * 90) * 0.6

@_memo
def clarinet(s, m, dur=0.5):                                  # a reedy tone: odd harmonics, a little vibrato after the attack
    t = s.n(dur); f = mf(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.25, 0, 1)); x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5, 7, 9))
    return s.lp(x, 3200) * np.clip(t / 0.04, 0, 1) * np.clip((dur - t) / 0.08, 0, 1) * 0.5

@_memo
def harpsi(s, m, dur=0.9):                                    # a harpsichord: a bright plucked string doubled an octave up, a quick decay
    return (pluck(s, m, dur, 0.95) + 0.35 * pluck(s, m + 12, dur, 0.95)) * 0.7

@_memo
def vibes(s, m, dur=2.0):                                     # a vibraphone: a sine with a slow tremolo and a quick overtone
    t = s.n(dur); f = mf(m); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.8) * (0.8 + 0.2 * np.sin(2 * np.pi * 5.5 * t)) + 0.22 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 6)) * (1 - np.exp(-t * 600))

# ---------------------------------------------------------------- engine
def _tone(rng, root, mode, d, base):
    sc = MODES[mode]; o, i = divmod(d, 7); return base + 12 * o + sc[i]

def _steps(p): return [i for i, ch in enumerate(p) if ch != "."]

def compose(s, b, genre, seed, energy=1.0, key=None):
    """Write the whole score into `s` (a Score): `b` frames per beat, `genre` from GENRES, `seed` any integer."""
    G = GENRES[genre]; r = np.random.default_rng(seed + 101); E = float(energy); gain = G["gain"] * E
    root = 43 + (seed // 5) % 8 if key is None else 43 + (key % 12)
    mode = G["modes"][(seed // 3) % len(G["modes"])]; progs = G["progs"]; P = progs[(seed // 13) % len(progs)]; rot = (seed // 17) % len(P)
    bar = 4 * b; nb = max(1, int(np.ceil(s.F / bar))); step = b / 4; sw = G["swing"]; size = G["size"]; layers = set(G["layers"])
    bpb = 1 if len(P) <= 4 else 2                              # chords per bar
    def pick(key_, default=None):
        v = G.get(key_); return None if not v else v[(seed // 19 + len(key_)) % len(v)]
    pat = {k: pick(k) for k in ("kick", "snare", "clap", "hat", "ohat", "perc", "snap", "shaker", "rim", "conga")}
    kick_kind = {"citypop": "punch", "lofi": "soft", "house": "punch", "trap": "deep", "synthwave": "punch", "acoustic": "soft", "funk": "punch", "phonk": "hard", "afro": "soft", "pop": "punch", "techno": "hard"}.get(genre, "punch")
    snare_kind = {"lofi": "dusty", "synthwave": "gated"}.get(genre, "tight")
    lead_inst = G["lead"][(seed // 23) % len(G["lead"])]
    vel = lambda: float(r.uniform(0.82, 1.0))
    # ---- harmony per bar (list of chords, each a tuple of midi notes) and the matching bass root
    def chord_at(k, h):
        d = P[(k * bpb + h + rot) % len(P)]; return d, tuple(_tone(r, root, mode, d + 2 * i, root + 12) for i in range(size))
    # ---- sections: intro, a breakdown in the middle of long films, a lift at the end
    brk = int(nb * 0.55) if nb >= 10 else -1; rhythmic = bool(G.get("kick") or G.get("clap")); intro = 1 if nb >= 5 else 0
    # ---- melody: a 2-bar motif from the genre's rhythm templates, answered and varied every 4 bars
    def motif(salt):
        rr = np.random.default_rng(seed * 31 + salt); out = []
        for bi in range(2):
            rh = G["rhythms"][(seed // 29 + bi + salt) % len(G["rhythms"])]; pos = int(rr.integers(0, 5))
            for st in _steps(rh):
                pos = int(np.clip(pos + rr.choice([-2, -1, -1, 0, 1, 1, 2, 3]), -2, 9)); out.append((bi, st, pos, st % 4 == 0))
        return out
    A, B = motif(1), motif(2)
    def lead_note(m, t0, dur, g, pan):
        if lead_inst == "bell": s.add(s.wet, s.bell(m, 2.0), t0, pan=pan, g=g * 1.1)
        elif lead_inst == "keys": s.add(s.wet, s.keys(m, 1.6), t0, pan=pan, g=g * 0.9)
        elif lead_inst == "pluck": s.add(s.wet, pluck(s, m, 1.0, 0.7), t0, pan=pan, g=g * 1.25)
        elif lead_inst == "marimba": s.add(s.wet, marimba(s, m, 0.9), t0, pan=pan, g=g * 1.3)
        elif lead_inst == "whistle": s.add(s.wet, whistle(s, m + 12, max(dur, 0.35)), t0, pan=pan, g=g * 0.9)
        elif lead_inst == "saw": s.add(s.wet, supersaw(s, m, max(dur, 0.25), 0.01, 0.15, 3600, 5, 22), t0, pan=pan, g=g * 0.55)
        elif lead_inst == "piano": s.add(s.wet, s.piano(m, 3.5), t0, pan=pan, g=g * 1.1)
        elif lead_inst == "cowbell": s.add(s.dry, cowbell(s, 2 ** ((m - 72) / 12)), t0, pan=pan, g=g * 0.8)
        elif lead_inst == "acid": s.add(s.dry, acid(s, m, 0.14), t0, pan=pan, g=g * 0.9)
        elif lead_inst == "chip": s.add(s.wet, chip(s, m + 12, 0.2, 0.5), t0, pan=pan, g=g * 0.7)
        elif lead_inst == "clar": s.add(s.wet, clarinet(s, m, max(dur, 0.35)), t0, pan=pan, g=g * 1.1)
        elif lead_inst == "harpsi": s.add(s.wet, harpsi(s, m, 0.9), t0, pan=pan, g=g * 1.2)
        elif lead_inst == "vibes": s.add(s.wet, vibes(s, m, 2.0), t0, pan=pan, g=g * 1.0)
    # ---- sidechain envelope from the kicks (house, pop, techno, synthwave)
    pump = np.ones(s.N)
    def duck(sig, t0):
        i = int(t0 * s.sr)
        if i < 0: sig = sig[-i:]; i = 0
        L = min(len(sig), s.N - i)
        return sig[:L] * pump[i:i + L] if L > 0 else sig[:0]
    if G["side"] > 0:
        for k in range(nb):
            for e in range(4):
                i0 = int(s.t(k * bar + e * b) * s.sr); L = int(0.28 * s.sr)
                if i0 < s.N: seg = pump[i0:i0 + L]; seg *= 1 - G["side"] * np.exp(-np.arange(len(seg)) / s.sr * 11)
    def put(bus, sig, f, g, pan=0.0, side=False, off=0.0):
        t0 = s.t(f) + off
        if side: sig = duck(sig, t0)
        s.add(bus, sig, t0, pan=pan, g=g)
    def at(k, st): return k * bar + st * step + (sw * step if st % 2 else 0)
    # ---- the loop
    for k in range(nb):
        f0 = k * bar; lvl = 0.55 if k < intro else 1.0; inbrk = (k == brk); drums_on = rhythmic and not inbrk and not ("drums_late" in layers and k < intro)
        lvl *= min(1.0, 0.8 + 0.06 * k) if genre == "epic" else 1.0
        d0, c0 = chord_at(k, 0); bassroot = _tone(r, root, mode, d0, root - 12)
        if inbrk: lvl *= 0.6
        # pads and sustained layers
        for h in range(bpb):
            d, ch = chord_at(k, h); hf = f0 + h * (bar // bpb); hd = s.t(bar // bpb) + 0.25
            if "pad" in layers: put(s.wet, pad(s, ch, hd, 1.0, 1.0, 1300 + 120 * min(k, 8)), hf, 0.055 * lvl * gain, side=True, off=-0.15)
            if "strings_ost" in layers:
                for e in range(8 if not inbrk else 2): put(s.wet, s.strings([ch[(0, 2, 1, 2, 3, 2, 1, 2)[e % 8] % size] + 12], 0.2, 0.01, 0.12, 2400 + 200 * min(k, 6)), hf + e * b / 2 * (2 / bpb), 0.085 * lvl * gain, pan=0.3 * np.sin(e * 1.3 + k))
                put(s.wet, s.strings(ch, hd + 0.5, 0.7, 0.9, 900), hf, 0.07 * lvl * gain, off=-0.2)
            if "choir" in layers: put(s.wet, s.choir(ch, hd + 0.4, 1.0, 1.4), hf, 0.07 * lvl * gain * (0.6 if k < 2 else 1), off=-0.2)
            if "keys" in layers:
                for j, m in enumerate(ch): put(s.wet, s.keys(m, 3.0), hf, 0.085 * lvl * gain, pan=-0.3 + 0.2 * j, off=j * 0.045 + (0.02 if h else 0))
                if r.random() < 0.5 and k > 0: put(s.wet, s.keys(ch[1] + 12, 2.0), hf + 2.5 * b, 0.05 * lvl * gain, pan=0.3)
            if "piano_pulse" in layers:
                for e in range(0, 4, 2 if bpb == 1 else 4): put(s.wet, s.piano(ch[e % size] + 0, 2.6), hf + e * b * (2 / bpb) / 2, 0.11 * lvl * gain, pan=-0.1)
                for e in range(4): put(s.wet, s.piano(ch[(e + 1) % size] + 12, 2.2), hf + e * b, 0.08 * lvl * gain, pan=0.2 * np.sin(e + k))
            if "guitar" in layers:
                pattern = (0, 2, 1, 2, 0, 2, 1, 2) if (seed // 7) % 2 else (0, 1, 2, 1, 2, 1, 0, 1)
                for e in range(8): put(s.wet, pluck(s, ch[pattern[e] % size] + (0 if e % 4 == 0 else 12), 1.5, 0.45), hf + e * b / 2 * (2 / bpb) + 0, 0.15 * lvl * gain, pan=-0.2 + 0.1 * (e % 3), off=sw * 0.04 * (e % 2))
            if "marimba_chords" in layers:
                for e in (0, 1.5, 2.5, 3.5):
                    for j in range(size): put(s.wet, marimba(s, ch[j] + (12 if j else 0), 0.7), hf + e * b * (2 / bpb) / 2 * (1 if bpb == 1 else 1), 0.08 * lvl * gain, pan=-0.3 + 0.3 * j, off=j * 0.012)
            if "stab" in layers or "stab_dark" in layers:
                pts = (0.5, 1.5, 2.75, 3.5) if genre in ("house",) else (0, 0.75, 1.5, 2.5, 3.25) if genre == "funk" else (0.5, 1, 2.5, 3)
                for e in pts: put(s.wet, brass(s, ch if genre != "techno" else ch[:2], 0.18 if genre != "funk" else 0.14, 1800 if genre in ("house", "techno") else 2800), hf + e * b * (2 / bpb), 0.06 * lvl * gain * (0.7 if genre == "techno" else 1), pan=0.25 * np.sin(e * 3 + k), side=(genre in ("house", "techno")))
            if "arp" in layers:
                for e in range(16 // bpb): put(s.wet, supersaw(s, ch[(0, 1, 2, 1)[e % 4] % size] + 12 * (e // 4 % 2) + 12, 0.18, 0.004, 0.08, 4200, 3, 14), hf + e * step, 0.05 * lvl * gain, pan=0.4 * np.sin(e * 0.9), side=True)
            if "sub" in layers and genre in ("epic", "ambient"): put(s.dry, s.sub(ch[0] - 12, hd + 0.4, 0.3, 0.7), hf, 0.35 * lvl * gain)
        # bass
        bm = bassroot; ch0 = chord_at(k, 0)[1]
        if "bass" in layers and genre == "lofi":
            for e, dd in ((0, 0), (1.5, 0), (2.5, 7 if r.random() < 0.5 else 0)): put(s.dry, s.sub(bm + dd, s.t(b) * 1.2, 0.02, 0.2), f0 + e * b, 0.30 * lvl * gain)
        if "bass_roll" in layers and not inbrk:
            for e in range(16):
                if e % 4 != 0: put(s.dry, bass(s, bm + (0 if e % 4 != 3 else 12 if e % 8 == 7 else 7), 0.18, 700, 12), f0 + e * step, 0.36 * lvl * gain, side=True)
        if "bass_eighth" in layers and not inbrk:
            for e in range(8): put(s.dry, bass(s, bm + (12 if e % 4 == 3 else 0), 0.24, 800 if genre == "synthwave" else 1200, 7), f0 + e * b / 2, 0.36 * lvl * gain, side=True)
        if "bass_pluck" in layers and not inbrk:
            for e, dd in ((0, 0), (1.5, 0), (2, 7), (3, 5 if genre == "acoustic" else 0), (3.5, 0)):
                if e == 0 or r.random() < 0.8: put(s.dry, pluck(s, bm + 12 * (dd == 12) + (0 if dd != 7 else 7) - 12 * 0, 0.55, 0.15) * 0.8, f0 + e * b, 0.40 * lvl * gain)
        if "bass_funk" in layers and not inbrk:
            pb = (0, 3, 6, 8, 10, 12, 14) if (seed // 5) % 2 else (0, 2, 3, 6, 9, 10, 13)
            for e in pb: put(s.dry, bass(s, bm + (0, 0, 12, 7, 0, 10, 0, 12)[(e + k) % 8], 0.14, 1100, 11, 0.4), f0 + e * step + (sw * step if e % 2 else 0), 0.38 * lvl * gain)
        if "bass_acid" in layers and not inbrk:
            seq = [0, 0, 12, 0, 7, 0, 10, 12, 0, 0, 7, 0, 12, 0, 5, 10]
            for e in range(16):
                if (seed // 3 + e) % 5 != 0 or e % 4 == 0: put(s.dry, acid(s, bm + 12 + seq[(e + k * 3) % 16] * (1 if e % 3 else 0), 0.15), f0 + e * step, 0.30 * lvl * gain, side=True)
        if "808" in layers or "808_dirty" in layers:
            drive = 2.2 if "808" in layers else 5.0; seqf = ((0, 3.0, 0), (3, 1.0, 0)) if r.random() < 0.5 else ((0, 2.0, 0), (2.5, 1.5, 7))
            for e, ln, dd in seqf:
                nxt = bm + (7 if dd == 7 else (-5 if k % 2 else 0)); put(s.dry, s808(s, bm + 12, s.t(b) * ln, nxt + 12 if (k % 2 and e) else None, drive), f0 + e * b, 0.5 * lvl * gain)
        # cowbell lead for phonk, and the generic lead melody
        if "cowbell" in layers and genre == "funk":
            for e in (1.5, 3.5): put(s.dry, cowbell(s, 1.0), f0 + e * b, 0.05 * lvl * gain)
        if ("lead" in layers or "cowbell_lead" in layers) and not inbrk and (k >= intro or genre in ("epic",)):
            M = A if (k // 2) % 2 == 0 else B
            d, ch = chord_at(k, 0)
            for bi, st, p_, strong in M:
                if bi != k % 2: continue
                dd = d + p_ if not strong else d + 2 * int(round(p_ / 2))
                m = _tone(r, root, mode, dd, root + 24)
                if genre == "epic": m -= 5 if m > 82 else 0
                lead_note(m, s.t(at(k, st)), 0.4, 0.09 * lvl * gain, 0.35 * np.sin(st + k))
                if "canon" in layers: lead_note(m - 12, s.t(at(k, st) + 2 * b), 0.4, 0.075 * lvl * gain, -0.35 * np.sin(st + k))     # the same line again two beats later, an octave down
        if "sparse" in layers:                                      # ambient: a few bells from the scale, never on the beat
            for _ in range(2 if k % 2 == 0 else 1):
                dd = d0 + int(r.integers(0, 8)); put(s.wet, s.bell(_tone(r, root, mode, dd, root + 24), 3.5) if lead_inst == "bell" else marimba(s, _tone(r, root, mode, dd, root + 24), 1.4), f0 + float(r.uniform(0.3, 3.7)) * b, 0.10 * gain, pan=float(r.uniform(-0.7, 0.7)))
        # layers added for the console, swing, counterpoint and room-tone genres
        sec_step = s.t(step)
        if "chip_arp" in layers and not inbrk:
            for e in range(16): put(s.wet, chip(s, ch0[(0, 1, 2, 1)[e % 4] % size] + 12 * (1 + (e // 4) % 2), sec_step * 0.9, 0.25), f0 + e * step, 0.05 * lvl * gain, pan=0.3 * np.sin(e))
        if "chip_bass" in layers and not inbrk:
            for e in range(8): put(s.dry, chip(s, bm + (12 if e % 4 == 3 else 0), 0.22, 0.5, "tri"), f0 + e * b / 2, 0.20 * lvl * gain)
        if "chip_drums" in layers and not inbrk and k >= intro:
            for st in range(16):
                if st in (0, 6, 10): put(s.dry, chipdrum(s, "kick"), at(k, st), 0.5 * gain)
                if st in (4, 12): put(s.dry, chipdrum(s, "snare"), at(k, st), 0.32 * gain)
                if st % 2 == 0: put(s.dry, chipdrum(s, "hat"), at(k, st), 0.16 * gain)
        if "stride" in layers and not inbrk:
            for e in range(4):
                if e % 2 == 0: put(s.dry, s.piano(bm + (7 if e == 2 else 0), 1.2), f0 + e * b, 0.16 * lvl * gain)
                else:
                    for m_ in ch0[:3]: put(s.wet, s.piano(m_ + 0, 0.9), f0 + e * b + (sw * step if e == 3 else 0), 0.07 * lvl * gain, pan=0.1)
        if "brush" in layers and not inbrk:
            for st in (0, 4, 6, 8, 12, 14): put(s.dry, thh(s, "soft"), at(k, st), 0.10 * gain, pan=-0.2)
            for st in (4, 12): put(s.wet, tsnare(s, "dusty"), at(k, st), 0.10 * gain)
            put(s.dry, tkick(s, "soft"), f0, 0.3 * gain)
        if "hum" in layers:
            n_ = int(s.t(bar) * s.sr); tt = np.arange(n_) / s.sr; wow = 1 + 0.003 * np.sin(2 * np.pi * (0.4 + 0.05 * k) * tt)
            x = (np.sin(2 * np.pi * np.cumsum(100 * wow) / s.sr) + 0.5 * np.sin(2 * np.pi * np.cumsum(200 * wow) / s.sr) + 0.25 * np.sin(2 * np.pi * np.cumsum(300 * wow) / s.sr)) * 0.5 + s.lp(s.noise(n_), 500) * 0.2; s.add(s.dry, x, s.t(f0), g=0.07 * gain)
        # drums
        if drums_on:
            for st in range(16):
                t_ = at(k, st); g_ = vel()
                def hit(name, sig, gg, pan=0.0, bus=None, side=False):
                    P_ = pat.get(name)
                    if P_ and P_[st] != ".": put(s.dry if bus is None else bus, sig, t_, gg * (1.25 if P_[st] == "X" else 0.45 if P_[st] == "o" else 1.0) * g_ * gain, pan=pan)
                hit("kick", tkick(s, kick_kind), {"trap": 1.0, "phonk": 0.95, "techno": 1.0, "house": 1.0}.get(genre, 0.85))
                hit("snare", tsnare(s, snare_kind), 0.24, 0.1, s.wet)
                hit("clap", clap(s), 0.19 if genre not in ("trap", "phonk") else 0.3, 0.05, s.wet)
                hit("hat", thh(s, "tight" if genre not in ("lofi",) else "soft"), 0.048 if genre != "lofi" else 0.05, -0.3)
                hit("ohat", ohat(s), 0.045, 0.3)
                hit("perc", rim(s) if genre in ("house", "afro") else cowbell(s, 1.3) if genre == "techno" else rim(s), 0.05, 0.4)
                hit("snap", snap(s), 0.22, 0.1, s.wet)
                hit("shaker", shaker(s), 0.07 if genre != "afro" else 0.08, -0.4)
                hit("rim", rim(s), 0.13, 0.3)
                if pat.get("conga") and pat["conga"][st] != ".": put(s.dry, conga(s, 1 if st % 3 else 0), t_, 0.22 * g_ * gain, pan=0.3 if st % 3 else -0.3)
            if "gate" in layers:
                for e in (1, 3): put(s.wet, tsnare(s, "gated"), f0 + e * b, 0.18 * gain)
            if "hatroll" in layers and k % 2 == 1:                  # trap / phonk: hat roll at the end of every second bar
                for e in range(8): put(s.dry, thh(s, "tight"), f0 + 3 * b + e * b / 8, (0.04 + 0.012 * e) * gain, pan=-0.2)
        if "taiko" in layers:
            hits = (0, 2, 3) if k % 2 == 0 else (0, 1.5, 2.5, 3.5)
            for e in hits: put(s.dry, s.taiko(0.9 if e == 0 else 0.55, 58 if k % 2 else 62), f0 + e * b, (0.55 if e == 0 else 0.32) * lvl * gain)
        if "braam" in layers and k % 4 == 0 and k > 0: put(s.wet, s.braam(root - 12 + _tone(r, root, mode, d0, 0) % 12, 3.0), f0, 0.14 * gain)
        if "vinyl" in layers:
            n_ = int(s.t(bar) * s.sr); tt = np.arange(n_) / s.sr; imp = (r.random(n_) < 18 / s.sr) * r.uniform(0.2, 1.0, n_)
            cr = s.hp(imp, 1800) * 0.9 + s.hp(s.noise(n_), 4000) * 0.015; s.add(s.dry, cr, s.t(f0), g=0.12 * (1.0 if genre == "lofi" else 0.8))
        if "air" in layers:
            n_ = int(s.t(bar) * s.sr); x = s.lp(s.noise(n_), 700) * np.sin(np.pi * np.arange(n_) / n_) ** 2; s.add(s.wet, x, s.t(f0), g=0.05)
        # lifts: a riser and reverse crash into every fourth bar, a fill on the last beat before it
        if (k % 4 == 3 or k == nb - 2) and k + 1 < nb and genre not in ("ambient", "lofi", "acoustic") :
            s.add(s.wet, s.riser(s.t(2 * b)), s.t(f0 + 2 * b), g=0.16 * gain)
            if rhythmic and drums_on and genre not in ("epic",):
                for e in range(4): put(s.wet, tsnare(s, snare_kind), f0 + 3 * b + e * b / 4, (0.12 + 0.05 * e) * gain)
        if k == brk + 1 and brk > 0: s.add(s.wet, s.crash(2.5, 1.4), s.t(f0), g=0.2 * gain)
    return dict(genre=genre, root=root, mode=mode, bars=nb, bpm=round(s.fps * 60 / b))
