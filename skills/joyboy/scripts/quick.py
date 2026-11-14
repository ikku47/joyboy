"""joyboy quick: describe a video as a list of scenes and get an MP4 with music (and narration) in one run.

    from quick import Film
    film = Film("spring-sale", size="portrait", mood="upbeat", palette=["#ff5a36", "#1b1b2f", "#ffd166"])
    film.intro("SPRING SALE", sub="this weekend only", logo="assets/logo.png")
    film.image("assets/shop.jpg", text="Everything in store", move="push")
    film.stat("40%", "off all shoes")
    film.outro("OPEN 9 TO 9", sub="12 Market Street", logo="assets/logo.png")
    film.render()

Run:  python film.py                 full quality
      JOYBOY_DRAFT=1 python film.py  half-size draft, several times faster (use this while iterating)
      python film.py sheet s.jpg 0 30 60 ...   contact sheet of frames

Scenes: intro, outro, title, image, clip, words, bullets, stat, bars, columns, line, donut, heatmap, icons, talk (a DiceBear character speaking, with lip sync), world shots (film.world(...).shot(...): a 3D low-poly place with people), map, web, window, slices, carousel, grid, tunnel, loader, lockcut, browser, quote, phone, crt, logo, end, custom.
Every scene takes dur (seconds), tr (transition into it: cut, fade, whip, white, zoom, wipe) and
pace (narration speed for the scene: 1.0 normal, 0.85 slow, 1.15 brisk, or "fit"), and\nnote (a small footnote on the scene, e.g. "sample data"), voice_at (seconds into the scene the narration starts), and\nvoice (narration text, or a path to a ready audio file; spoken with ElevenLabs if a key is set,\notherwise Piper, otherwise the system voice; the scene stretches to fit it).
Film options that keep videos from looking and sounding alike: look= (cinematic, soft, clean, punchy, warm, cool, vintage, none, or a dict of
strengths), music_seed=, key=, energy=, sfx= (level of the automatic sounds), mute= (sound names to leave out), air= (a wind bed).
Scene lengths snap to the music's beat so cuts land on beats. For anything a scene cannot do,
use film.custom(fn, dur) with fn(u, n, f) -> float32 BGR frame built from joyboy.py helpers.
"""
import os, sys, re, subprocess, wave, hashlib, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw
import joyboy as jb
from joyboy import eo, ei, eio, clamp, spring
from score import Score
import genres, themes, kinds, styles

SIZES = {"portrait": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080), "4:5": (1080, 1350)}
MOODS = {  # bpm, default transition, background colours, grain
    "cinematic": dict(bpm=90, tr="fade", grain=0.016), "upbeat": dict(bpm=120, tr="whip", grain=0.006),
    "calm": dict(bpm=75, tr="fade", grain=0.012), "tech": dict(bpm=112.5, tr="zoom", grain=0.008), "hype": dict(bpm=180, tr="cut", grain=0.006), "none": dict(bpm=120, tr="cut", grain=0.008)}
MOVES = {"push": lambda t: (1.04 + 0.12 * t, 0.5, 0.5, 0), "pull": lambda t: (1.18 - 0.14 * t, 0.5, 0.5, 0), "still": lambda t: (1.02, 0.5, 0.5, 0),
         "pan": lambda t: (1.14, 0.40 + 0.2 * t, 0.5, 0), "pan_left": lambda t: (1.14, 0.60 - 0.2 * t, 0.5, 0),
         "tilt_up": lambda t: (1.14, 0.5, 0.60 - 0.2 * eio(t), 0), "tilt_down": lambda t: (1.14, 0.5, 0.40 + 0.2 * eio(t), 0),
         "snap": lambda t: (1.08 + 0.4 * (1 - eo(t * 6, 4)) - 0.06 * t, 0.5, 0.5, 0), "parallax": lambda t: (1.1 + 0.06 * t, 0.5, 0.52, -14 + 28 * t)}

# Looks: how the finished picture is treated. Each value is a strength (0 = off, 1 = the classic film finish).
LOOKS = {
    "cinematic": dict(vignette=1.0, tint=1.0, fringe=1.0, contrast=1.0, streak=1.0, warmth=0.0, sat=1.0, glow=1.0, bloom=None, grain=None),   # dark corners, glow, grain: trailers, drama
    "soft":      dict(vignette=0.35, tint=0.4, fringe=0.3, contrast=0.5, streak=0.4, warmth=0.15, sat=1.0, glow=0.8, bloom=None, grain=0.006), # gentle, a little warm: stories, calm brands
    "clean":     dict(vignette=0.0, tint=0.0, fringe=0.0, contrast=0.3, streak=0.0, warmth=0.0, sat=1.0, glow=0.45, bloom=0.15, grain=0.0),    # true colours, no corners: apps, products, data, UI
    "punchy":    dict(vignette=0.25, tint=0.2, fringe=0.5, contrast=1.25, streak=0.8, warmth=0.0, sat=1.2, glow=1.0, bloom=None, grain=0.004), # strong contrast and colour: reels, offers, sport
    "warm":      dict(vignette=0.5, tint=0.3, fringe=0.4, contrast=0.7, streak=0.6, warmth=0.6, sat=1.05, glow=1.0, bloom=None, grain=0.010),  # golden: food, home, festivals, nostalgia
    "cool":      dict(vignette=0.5, tint=0.6, fringe=0.4, contrast=0.8, streak=0.5, warmth=-0.6, sat=0.95, glow=1.0, bloom=None, grain=0.010), # blue: tech, night, rain, winter
    "vintage":   dict(vignette=1.2, tint=0.5, fringe=1.4, contrast=0.6, streak=0.3, warmth=0.5, sat=0.7, glow=1.0, bloom=None, grain=0.030),   # faded, grainy: memories, retro
    "none":      dict(vignette=0.0, tint=0.0, fringe=0.0, contrast=0.0, streak=0.0, warmth=0.0, sat=1.0, glow=0.0, bloom=0.0, grain=0.0),      # the picture exactly as drawn
}
MOOD_LOOK = {"cinematic": "cinematic", "calm": "soft", "upbeat": "punchy", "tech": "clean", "hype": "punchy", "none": "clean"}

EMOTION = re.compile(r"\s*<(laugh|sigh|breath)>\s*")     # expression tags a line may carry for emotional voices
def untag(text):
    """A line without its expression tags, for captions and for voices that cannot act them."""
    return re.sub(r"\s+([.,!?])", r"\1", EMOTION.sub(" ", str(text))).strip()
SUPERTONIC_LANGS = set("en ko ja ar bg cs da de el es et fi fr hi hr hu id it lt lv nl pl pt ro ru sk sl sv tr uk vi".split())
_SUPERTONIC = None

def col(c):
    """'#rrggbb' or (b, g, r) -> float32 BGR."""
    if isinstance(c, str): c = c.lstrip("#"); return np.float32([int(c[4:6], 16), int(c[2:4], 16), int(c[0:2], 16)])
    return np.float32(c)

def _default_fonts():
    for path, bold, reg in (("/System/Library/Fonts/Avenir Next.ttc", 8, 5), ("/System/Library/Fonts/Helvetica.ttc", 1, 0)):
        if os.path.exists(path): return (path, None, bold), (path, None, reg)
    for b, r in (("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf")):
        if os.path.exists(b): return (b, None, 0), (r, None, 0)
    raise RuntimeError("no default font found; pass font=(path, weight, index) and font_bold=...")

class Film:
    def __init__(self, name, size="portrait", fps=30, mood=None, palette=None, font=None, font_bold=None, bpm=None, voice=None, voice_name=None, tts=None, lang="en", pace=1.0, bloom=None, out=None, loose=False, look=None, music_seed=None, key=None, energy=1.0, sfx=1.0, mute=(), air=False, genre=None, theme=None, fx=None, grade=None, mblur=False, exact=False, bed=None, style=None):
        st = styles.get(style) if style else {}                          # a style sets a whole look and sound; anything passed explicitly wins
        mood = mood or st.get("mood") or "cinematic"; theme = theme or st.get("theme"); fx = fx if fx is not None else st.get("fx"); grade = grade or st.get("grade"); genre = genre or st.get("genre"); bed = bed or st.get("bed"); look = look if look is not None else st.get("look"); self.style = style
        self.name, self.mood, self.fps = name, mood, fps; self.m = MOODS[mood]; self.draft = bool(os.environ.get("JOYBOY_DRAFT"))
        w, h = SIZES[size] if isinstance(size, str) else size
        if self.draft: w, h = w // 4 * 2, h // 4 * 2
        jb.init(w, h, fps); self.W, self.H, self.U = w, h, min(w, h) / 1080
        self.bed = bed
        if bed:
            import foley
            if bed not in foley.BEDS: sys.exit('joyboy: unknown bed %r; choose from %s' % (bed, ', '.join(foley.BEDS)))
        self.fx = fx; self.grade = grade; self.mblur = bool(mblur); self.exact = bool(exact)   # exact: scene lengths are exactly what is asked (no beat snapping), for matching a reference
        if grade and not callable(grade) and grade not in kinds.GRADES: sys.exit('joyboy: unknown grade %r; choose from %s' % (grade, ', '.join(kinds.GRADES)))
        if fx and not callable(fx) and (fx[0] if isinstance(fx, (tuple, list)) else fx) not in kinds.FX: sys.exit('joyboy: unknown fx %r; choose from %s' % (fx, ', '.join(kinds.FX)))
        self.theme = themes.resolve(theme); th = self.theme or {}; self.cur = 0; self._ink = jb.WHITE
        self.pal = [col(c) for c in (palette or th.get("pal") or ["#0b0b10", "#2f8ff5", "#e5261f", "#ff8a1f", "#7b3fe4"])]
        fb, fr = _default_fonts(); self.fb, self.fr = font_bold or font or th.get("font") or fb, font or th.get("font_reg") or fr
        if look is None and th: look = th["look"]
        if bloom is None and th: bloom = th["bloom"]
        self.music_seed = music_seed if music_seed is not None else int(hashlib.md5(name.encode()).hexdigest()[:6], 16)   # each video gets its own music; the same video always gets the same
        # genre: one of genres.GENRES, "classic" (the original three-arrangement score), or None = a genre that suits the mood, picked by the seed
        self.genre = None if (mood == "none" or genre == "classic") else (genre or genres.pick_genre(mood, self.music_seed))
        if self.genre and self.genre not in genres.GENRES: sys.exit("joyboy: unknown genre %r; choose from %s" % (self.genre, ", ".join(genres.GENRES)))
        if bpm is None and self.genre: bpm = genres.tempo(self.genre, self.music_seed)
        self.beat = max(1, round(fps * 60 / (bpm or self.m["bpm"]))); self.voice_name = voice_name or voice; self.tts = tts
        # look: a name from LOOKS, or a dict of strengths (optionally with "base": a look name to start from). None = the look that suits the mood.
        base = dict(LOOKS[(look.get("base") if isinstance(look, dict) else look) or MOOD_LOOK[mood]]); base.update({k_: v_ for k_, v_ in (look.items() if isinstance(look, dict) else ()) if k_ != "base"})
        self.look_name = ((look.get('base') if isinstance(look, dict) else look) or MOOD_LOOK[mood]) if not isinstance(look, dict) or look.get('base') else 'custom'
        self.ffgrain = os.environ.get("JOYBOY_FFGRAIN", "1") != "0"      # grain is added by the encoder, not drawn into every frame: much smaller files, faster
        self.fin = base; self.bloom = bloom if bloom is not None else (base["bloom"] if base["bloom"] is not None else 0.8)
        if base["grain"] is None: base["grain"] = self.m["grain"]
        self.key, self.energy, self.sfx, self.mute, self.air = key, float(energy), float(sfx), set(mute or ()), air
        self.scenes = []; self.layers = []; self.music_file = None; self.loose = loose; self.lang = (lang or "en").lower()[:2]; self.pace = pace; self.work = os.path.abspath("work"); os.makedirs(self.work, exist_ok=True)
        if self.bed:
            import foley
            self.layers.append(lambda s_, duck_: foley.bed(s_, self.bed, 0, s_.F, 0.05, duck_))   # a quiet room, machine or tape bed under the whole film
        self.out = out or os.path.abspath(os.path.join("work", name + "-draft.mp4") if self.draft else os.path.join("out", name + ".mp4")); os.makedirs(os.path.dirname(self.out), exist_ok=True)   # drafts stay in work/, out/ holds finished videos only

    # ---------- plumbing ----------
    def _add(self, draw, dur, tr=None, voice=None, kind="scene", meta=None, sfx=None, pace=None, note=None, voice_at=None, voice_as=None):
        """voice_as: a voice for this scene only (Supertonic F1-F5, M1-M5, a Piper name ...): one voice per character. exact films keep every scene's length and speak faster to fit."""
        voice_at = (0.08 if self.exact else 0.2) if voice_at is None else voice_at
        idx = len(self.scenes); draw0 = draw
        def draw(u, n, f): self.cur = idx; return draw0(u, n, f)
        pace = self.pace if pace is None else pace; vf = None; _vn = self.voice_name
        if voice_as: self.voice_name = voice_as
        if voice and (pace == "fit" or (self.exact and pace == self.pace)): pace = "fit"
        if voice and pace == "fit":      # keep the scene's length: speak as fast as needed (within natural limits) to fit it
            vf = self._say(voice, 1.0)
            mg = 0.12 if self.exact else 0.6
            if vf and vf[1] > dur - mg: vf = self._say(voice, min(1.5 if self.exact else 1.3, max(1.0, round(vf[1] / max(dur - mg, 0.3), 2))))
        elif voice: vf = self._say(voice, float(pace))
        self.voice_name = _vn
        if vf and not self.exact: dur = max(dur, vf[1] + 0.3 + voice_at)
        n = max(2, round(dur * self.fps)) if self.exact else max(self.beat * 2, round(dur * self.fps / self.beat) * self.beat)
        self.scenes.append(dict(draw=draw, n=n, tr=tr or self.m["tr"], voice=vf, kind=kind, meta=meta or {}, sfx=sfx or [], note=note, voice_at=voice_at, say=voice if (voice and not os.path.isfile(str(voice))) else ("(audio file) " + os.path.basename(str(voice)) if voice else ""), pace=pace)); return self
    def _say(self, text, pace=1.0):
        """Narration audio for a scene. `text` is the words to speak, or a path to an audio file already
        made (for example by an ElevenLabs MCP tool). Engines, in order: ElevenLabs (if ELEVENLABS_API_KEY
        is set), Piper (if installed with a voice in <workspace>/voices), the system voice (`say`).
        Supertonic, the emotional voice, is used first when the voice is one of its names (F1-F5, M1-M5) or
        Film(tts="supertonic"); it acts the tags <laugh>, <sigh> and <breath>, which every other engine skips.
        Film(tts="piper" | "elevenlabs" | "say" | "supertonic") puts that engine first.
        Cached in work/voice. Returns (wav path, seconds) or None."""
        import glob, json, urllib.request
        d = os.path.join(self.work, "voice"); os.makedirs(d, exist_ok=True); home = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy"))
        conv = lambda src, dst: subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ar", "44100", "-ac", "1", dst], check=True)
        dur = lambda p: (lambda w: (w.getnframes() / w.getframerate(), w.close())[0])(wave.open(p))
        if os.path.isfile(text) and text.lower().endswith((".wav", ".mp3", ".m4a", ".aiff", ".flac", ".ogg")):
            p = os.path.join(d, "file-" + hashlib.md5(os.path.abspath(text).encode()).hexdigest()[:12] + ".wav")
            if not os.path.exists(p): conv(text, p)
            return p, dur(p)
        plain = untag(text); st_voice = self.voice_name if self.voice_name and re.fullmatch(r"[FM][1-5]", str(self.voice_name)) else None
        def supertonic(out):
            global _SUPERTONIC
            if _SUPERTONIC is None:
                try: from supertonic import TTS
                except ImportError: raise RuntimeError("not installed; once: ~/joyboy/.venv/bin/python -m pip install supertonic")
                _SUPERTONIC = TTS(model="supertonic-3", model_dir=os.path.join(home, "voices", "supertonic"), auto_download=True)
            wav, _ = _SUPERTONIC.synthesize(text, voice_style=_SUPERTONIC.get_voice_style(voice_name=st_voice or "F1"), lang=self.lang, speed=1.05 * float(pace))
            _SUPERTONIC.save_audio(wav, out + ".s.wav"); conv(out + ".s.wav", out); os.remove(out + ".s.wav")
        key = os.environ.get("ELEVENLABS_API_KEY"); models = sorted(glob.glob(os.path.join(home, "voices", "*.onnx")))
        def eleven(out):
            vid = self.voice_name if self.voice_name and re.fullmatch(r"[A-Za-z0-9]{20}", self.voice_name) else os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
            rq = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}", data=json.dumps({"text": plain, "model_id": "eleven_multilingual_v2", "voice_settings": {"speed": float(min(max(pace, 0.7), 1.2))}}).encode(),
                                        headers={"xi-api-key": key, "Content-Type": "application/json", "accept": "audio/mpeg"})
            open(out + ".mp3", "wb").write(urllib.request.urlopen(rq, timeout=120).read()); conv(out + ".mp3", out); os.remove(out + ".mp3")
        def piper(out):
            pre = self.lang + "_"; mine = [x for x in models if os.path.basename(x).startswith(pre)]
            if not mine:   # no voice for this language yet: download one, once
                avail = [v for v in subprocess.run([sys.executable, "-m", "piper.download_voices"], capture_output=True, text=True).stdout.split() if v.startswith(pre)]
                if not avail: raise RuntimeError(f"Piper has no voice for language '{self.lang}'")
                pick = next((v for v in avail if self.voice_name and self.voice_name in v), None) or next((v for v in avail if v.endswith("medium")), avail[0])
                print(f"downloading Piper voice {pick} (one time)..."); subprocess.run([sys.executable, "-m", "piper.download_voices", "--download-dir", os.path.join(home, "voices"), pick], check=True, capture_output=True)
                mine = [os.path.join(home, "voices", pick + ".onnx")]
            m = next((x for x in mine if self.voice_name and self.voice_name in os.path.basename(x)), None) or next((x for x in mine if "lessac" in x), mine[0])
            subprocess.run([sys.executable, "-m", "piper", "-m", m, "-f", out + ".p.wav", "--length-scale", f"{1 / pace:.3f}", "--sentence-silence", f"{0.28 / pace:.2f}"], input=plain.encode(), check=True, capture_output=True); conv(out + ".p.wav", out); os.remove(out + ".p.wav")
        def system(out):
            v = self.voice_name if self.voice_name and self.lang == "en" else None
            if not v and self.lang != "en":   # pick a system voice that speaks the language
                v = next((l.split()[0] for l in subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout.splitlines() if re.search(r"\b%s[_-]" % self.lang, l)), None)
                if not v: raise RuntimeError(f"no system voice for language '{self.lang}'")
            subprocess.run(["say"] + (["-v", v] if v else []) + ["-r", str(int(175 * pace)), "-o", out + ".aiff", plain], check=True); conv(out + ".aiff", out); os.remove(out + ".aiff")
        engines = ([("elevenlabs", eleven)] if key else []) + ([("piper", piper)] if models or self.lang != "en" else []) + ([("say", system)] if shutil.which("say") else [])
        if (st_voice or self.tts == "supertonic") and self.tts in (None, "supertonic") and self.lang in SUPERTONIC_LANGS: engines = [("supertonic", supertonic)] + engines
        if self.tts: engines.sort(key=lambda e: e[0] != self.tts)      # the chosen engine first, the rest as fallbacks
        for name, fn in engines:
            p = os.path.join(d, name + "-" + hashlib.md5((text + str(self.voice_name) + self.lang + f"{pace:.2f}").encode()).hexdigest()[:12] + ".wav")
            if os.path.exists(p): return p, dur(p)
            try: fn(p); print("narration:", name); return p, dur(p)
            except Exception as e: print(f"narration: {name} failed ({str(e)[:80]}); trying the next voice")
        print("narration skipped: no voice engine available"); return None
    def sound_layer(self, fn):
        """Add your own sound to the mix: fn(score, duck) is called when the audio is built, after the music and effects.
        Place sound with score.add(score.dry, signal, seconds) or add a stereo array to score.dry; scenes carry their
        'start' and 'n' in frames; `duck` is 1.0 normally and lower while a voice speaks (multiply a bed by it).
        At that point the mix holds music and effects only (voices are added after), so a layer may also turn the music down."""
        self.layers.append(fn); return self
    def music(self, path):
        """Use an existing audio file instead of the generated score."""
        self.music_file = path; return self
    def T(self, txt, size, bold=True, track=0, maxw=None):
        p, wt, ix = self.fb if bold else self.fr
        return jb.tmask(txt, max(8, int(size * self.U)), p, wt, int(track * self.U), int(maxw or self.W * 0.86), ix)
    def wrap(self, txt, size, bold=False, maxw=None):
        p, wt, ix = self.fb if bold else self.fr; ft = jb.font(p, max(8, int(size * self.U)), wt, ix); maxw = maxw or self.W * 0.8; out = []
        for para in txt.split("\n"):
            line = ""
            for word in para.split():
                if line and ft.getlength(line + " " + word) > maxw: out.append(line); line = word
                else: line = (line + " " + word).strip()
            out.append(line)
        return out
    def _len(self, txt, size, bold):
        p, wt, ix = self.fb if bold else self.fr; return jb.font(p, max(8, int(size * self.U)), wt, ix).getlength(txt)
    ink = property(lambda self: self._ink)    # the text colour: white, or near-black on a light background (set by bg())
    def block(self, img, lines, cy, size, bold=True, op=1.0, gap=1.18, color=None, scale=1.0, shadow=0.4, track=0, stagger=0, u=0, maxw=None, maxh=None):
        """Centred multi-line text block around cy that always fits its container: one size factor is reduced
        until the widest line fits maxw (default 86% of the frame) and the block fits maxh (default 42% of the frame)."""
        color = self.ink if color is None else color
        if themes.lum(color) < 120: shadow = 0
        lines = [l for l in lines if l != ""] or [""]; mw = maxw or self.W * 0.86; mh = maxh or self.H * 0.42
        for _ in range(3):   # a line far too wide for the container: step the size down and re-wrap it, before any plain shrinking
            if max(self._len(l, size, bold) for l in lines) > mw * 1.25 and any(" " in l for l in lines):
                size *= 0.84; lines = [w_ for l in lines for w_ in self.wrap(l, size, bold, mw)]
        k = min(1.0, mw / max(max(self._len(l, size, bold) + track * self.U * max(len(l) - 1, 0) for l in lines), 1))
        k = min(k, mh / (len(lines) * size * self.U * gap)); size = max(size * k, 14)
        y = cy - (len(lines) - 1) * size * self.U * gap / 2
        for i, l in enumerate(lines):
            o = op * (clamp((u - i * stagger) / 6) if stagger else 1)
            jb.put(img, *self.T(l, size, bold, track, mw + 4), y + i * size * self.U * gap, o, color, shadow, scale)
        return len(lines) * size * self.U * gap / 2   # half the block height, to place things under it
    def L(self, text, size, track, cy, maxw=None):
        """Letter-by-letter text sized to fit the frame width."""
        mw = maxw or self.W * 0.86; w = self._len(text, size, True) + track * self.U * max(len(text) - 1, 0); k = min(1.0, mw / max(w, 1))
        return jb.letters(text, max(10, int(size * k * self.U)), self.fb[0], self.fb[1], int(track * k * self.U), cy)
    def ltext(self, img, txt, x, cy, size, bold=False, op=1.0, color=None, align="left", maxw=None):
        """Text at a position (left/right/center aligned), for labels. Shrinks to maxw when given."""
        color = self.ink if color is None else color
        if maxw: size = max(size * min(1.0, maxw / max(self._len(txt, size, bold), 1)), 10)
        p, wt, ix = self.fb if bold else self.fr; s = max(8, int(size * self.U)); ft = jb.font(p, s, wt, ix); w = int(ft.getlength(txt)) + 4
        im = Image.new("L", (w, int(s * 1.5)), 0); ImageDraw.Draw(im).text((2, s * 0.12), txt, font=ft, fill=255); m = np.asarray(im, np.float32) / 255 * op
        x0 = int(x - (w if align == "right" else w / 2 if align == "center" else 0)); y0 = int(cy - m.shape[0] / 2)
        xa, xb, ya, yb = max(x0, 0), min(x0 + w, self.W), max(y0, 0), min(y0 + m.shape[0], self.H)
        if xb <= xa or yb <= ya: return
        a = m[ya - y0:yb - y0, xa - x0:xb - x0, None]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + color * a
    def _head(self, img, title, u, o):
        if title: self.block(img, self.wrap(title, 76, True), self.H * 0.15, 76, True, eio(u / 8) * o, maxh=self.H * 0.13)
    def bg(self, spec, u, n, f, move="push", i=0):
        """Background: None (palette dark), '#hex'/colour, (top, bottom) gradient, or an image path."""
        W, H = self.W, self.H
        if spec is None and self.theme:                # a theme paints its own background; the text colour follows its brightness
            k_ = self.theme["bg"]; c = self.pal[self.cur % len(self.pal)] if k_ in ("field", "brutal") else self.pal[0]
            self._ink = col(self.theme["ink"]) if self.theme.get("ink") else (np.float32((20, 20, 24)) if themes.lum(c) > 140 else jb.WHITE)
            return themes.paint(k_, np.float32(c), f, self.fps, self.U, self.pal)
        if spec is None: spec = self.pal[0]
        if self.theme and not (isinstance(spec, str) and not spec.startswith("#")):
            c_ = col(spec) if not isinstance(spec, (tuple, list)) or len(spec) == 3 and np.isscalar(spec[0]) else col(spec[0]); self._ink = np.float32((20, 20, 24)) if themes.lum(c_) > 140 else jb.WHITE
        elif self.theme: self._ink = jb.WHITE
        if isinstance(spec, str) and not spec.startswith("#"):
            im = jb.art(spec); z, nx, ny, par = MOVES[move](u / max(n, 1)); z0 = max(1.0, H * im.shape[1] / (W * im.shape[0]))
            return jb.cam(im, z0 * z, nx, ny, f, par=par, wob=0)
        if isinstance(spec, (tuple, list)) and len(spec) == 2 and (isinstance(spec[0], str) or not np.isscalar(spec[0])):
            t = np.clip(jb.yy / H + 0.06 * np.sin(f / self.fps * 0.8), 0, 1)[..., None]; return col(spec[0]) * (1 - t) + col(spec[1]) * t
        c = col(spec); r2 = ((jb.xx - W / 2) / (W * 0.7)) ** 2 + ((jb.yy - H * 0.45) / (H * 0.7)) ** 2
        gl = self.fin["glow"]; return (c * (1 - 0.20 * gl + 0.34 * gl * np.exp(-r2 * 1.6))[..., None] + 6 * gl * np.exp(-r2 * 1.6)[..., None]).astype(np.float32)
    def _io(self, u, n, i=6, o=6): return eio(u / i) * (1 - eio((u - (n - o)) / o))

    # ---------- scenes ----------
    def title(self, text, sub=None, bg=None, dur=2.5, move="push", color=None, y=None, **k):
        """Big headline (use \\n for lines) that slams in, with an optional small line under it."""
        lines = text.split("\n"); size = 170 if max(len(l) for l in lines) <= 10 else 120
        def draw(u, n, f):
            img = self.bg(bg, u, n, f, move); sc = 1 + 0.35 * (1 - eo(u / 8, 4)) + 0.03 * u / n; op = clamp(u / 3) * (1 - eio((u - (n - 5)) / 5))
            cy = self.H * (y or (0.44 if sub else 0.48)); hh = self.block(img, lines, cy, size, True, op, color=col(color) if color else None, scale=sc)
            if sub: self.block(img, self.wrap(sub, 46), cy + hh + 66 * self.U, 46, False, maxh=self.H * 0.14, op=eio((u - 8) / 8) * (1 - eio((u - (n - 5)) / 5)))
            return img + 120 * np.exp(-u / 2.0)
        return self._add(draw, dur, kind="title", **k)
    def card(self, img, x0, y0, x1, y1, color, radius=28, op=1.0):
        """A rounded rectangle (panel, card, pill) drawn on img in place; radius in design pixels."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1); r_ = int(min(radius * self.U, (x1 - x0) / 2, (y1 - y0) / 2)); m = np.zeros((self.H, self.W), np.float32)
        cv2.rectangle(m, (x0 + r_, y0), (x1 - r_, y1), 1, -1); cv2.rectangle(m, (x0, y0 + r_), (x1, y1 - r_), 1, -1)
        for px, py in ((x0 + r_, y0 + r_), (x1 - r_, y0 + r_), (x0 + r_, y1 - r_), (x1 - r_, y1 - r_)): cv2.circle(m, (px, py), r_, 1, -1, cv2.LINE_AA)
        a = (m * op)[..., None]; img[:] = img * (1 - a) + col(color) * a
    icons_ready = lambda self, names: self._icons(names)               # pre-load icons used with put_icon in custom scenes
    mark = lambda self, path: self._mark(path)                         # logo contours for custom scenes (use with jb.dmask / jb.trace)
    head = lambda self, img, title, u, o=1.0: self._head(img, title, u, o)   # a fitted heading at the top of a custom scene
    text_width = lambda self, txt, size, bold=False: self._len(txt, size, bold)
    def image(self, path, text=None, move="push", dur=3.0, at="bottom", **k):
        """A still image with a camera move and an optional caption on a soft dark band."""
        def draw(u, n, f):
            img = self.bg(path, u, n, f, move)
            if text:
                band = (np.clip((jb.yy / self.H - 0.58) / 0.3, 0, 1) if at == "bottom" else np.clip((0.42 - jb.yy / self.H) / 0.3, 0, 1))[..., None]; img = img * (1 - 0.62 * band)
                self.block(img, self.wrap(text, 58, True), self.H * (0.82 if at == "bottom" else 0.17), 58, True, maxh=self.H * 0.22, op=self._io(u, n, 8), stagger=3, u=u - 4)
            return img
        return self._add(draw, dur, kind="image", **k)
    def clip(self, path, start=0.0, dur=3.0, text=None, **k):
        """A piece of an existing video, cropped to fill the frame."""
        d = os.path.join(self.work, "clips", hashlib.md5(f"{path}{start}{dur}{self.W}x{self.H}{self.fps}".encode()).hexdigest()[:12])
        if not os.path.exists(os.path.join(d, "done")):
            os.makedirs(d, exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur + 2), "-i", path, "-vf",
                            f"fps={self.fps},scale={self.W}:{self.H}:force_original_aspect_ratio=increase,crop={self.W}:{self.H}", "-q:v", "3", os.path.join(d, "%05d.jpg")], check=True)
            open(os.path.join(d, "done"), "w").close()
        cnt = len([x for x in os.listdir(d) if x.endswith(".jpg")])
        def draw(u, n, f):
            img = cv2.imread(os.path.join(d, "%05d.jpg" % (min(max(u, 0), cnt - 1) + 1))).astype(np.float32)
            if text:
                band = np.clip((jb.yy / self.H - 0.58) / 0.3, 0, 1)[..., None]; img = img * (1 - 0.62 * band)
                self.block(img, self.wrap(text, 58, True), self.H * 0.82, 58, True, maxh=self.H * 0.22, op=self._io(u, n, 8))
            return img
        return self._add(draw, dur, kind="clip", **k)
    def web(self, html, dur=4.0, text=None, clock=None, **k):
        """A web animation (GSAP and its plugins, SVG, CSS layouts) captured frame by frame and used as a scene.
        `html` is a page that exposes a paused timeline as window.tl (see web_template.html). Needs the web kit
        (node, Chrome, gsap) that setup.sh installs once; SYSTEM.md says whether it is ready."""
        home = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); kit = os.path.join(home, "web"); src = open(html).read()
        n = max(self.beat * 2, round(dur * self.fps / self.beat) * self.beat); secs = n / self.fps + 0.5
        tag = hashlib.md5(f"{src}{self.W}x{self.H}{self.fps}{secs}{clock}".encode()).hexdigest()[:12]; d = os.path.join(self.work, "web"); os.makedirs(d, exist_ok=True); mp4 = os.path.join(d, tag + ".mp4")
        if not os.path.exists(mp4):
            if not os.path.exists(os.path.join(kit, "node_modules", "gsap")): sys.exit("joyboy: the web kit is not installed; run setup.sh (needs node and a Chrome-family browser)")
            def lucide(mt):
                f_ = os.path.join(kit, "node_modules", "lucide-static", "icons", mt.group(1) + ".svg")
                if not os.path.exists(f_): sys.exit(f"joyboy: no Lucide icon named '{mt.group(1)}' (see {os.path.dirname(f_)})")
                return re.sub(r"<!--.*?-->", "", open(f_).read(), flags=re.S).strip()
            def ricon(mt): self._icons([mt.group(1)]); return open(os.path.join(home, "icons", mt.group(1).split("/")[-1] + ".svg")).read().replace('stroke="#ffffff"', 'stroke="currentColor"').replace('fill="#ffffff"', 'fill="currentColor"').replace('color:#ffffff', 'color:inherit')
            src2 = re.sub(r"\{\{icon:([\w/]+)\}\}", ricon, re.sub(r"\{\{lucide:([\w-]+)\}\}", lucide, src)).replace("{{GSAP}}", "file://" + os.path.join(kit, "node_modules", "gsap", "dist")).replace("{{GSS}}", "file://" + os.path.join(kit, "node_modules", "gss-lang", "lib")).replace("{{FONT_BOLD}}", "file://" + os.path.abspath(self.fb[0])).replace("{{FONT}}", "file://" + os.path.abspath(self.fr[0]))
            src2 = re.sub(r"\{\{PALETTE:(\d)\}\}", lambda mt: "#%02x%02x%02x" % tuple(int(v) for v in self.pal[int(mt.group(1)) % len(self.pal)][::-1]), src2)
            if "{{GSS}}" in src and not os.path.exists(os.path.join(kit, "node_modules", "gss-lang")): sys.exit("joyboy: gss-lang is not installed in the workspace (cd ~/joyboy/web && npm install gss-lang)")
            page = os.path.join(d, tag + ".html"); open(page, "w").write(src2)
            for a_ in os.listdir(os.path.dirname(os.path.abspath(html))):      # let the page reach files beside it
                if not os.path.exists(os.path.join(d, a_)) and a_ != os.path.basename(html):
                    try: os.symlink(os.path.join(os.path.dirname(os.path.abspath(html)), a_), os.path.join(d, a_))
                    except OSError: pass
            subprocess.run(["node", os.path.join(kit, "web_capture.mjs"), page, mp4, str(self.W), str(self.H), str(self.fps), f"{secs:.3f}"] + ([clock] if clock else []), check=True, cwd=kit)
        self.clip(mp4, 0, dur, text=text, **k); self.scenes[-1]["kind"] = "web"; return self
    def words(self, words, per=0.5, bgs=None, **k):
        """Kinetic type: one word per beat on alternating colour fields."""
        seg = max(self.beat, round(per * self.fps / self.beat) * self.beat); bgs = bgs or self.pal[1:] or self.pal
        def draw(u, n, f):
            i = min(max(u, 0) // seg, len(words) - 1); v = u - i * seg; c = col(bgs[i % len(bgs)]) if not isinstance(bgs[i % len(bgs)], np.ndarray) else bgs[i % len(bgs)]
            img = self.bg(tuple(c), v, seg, f); dark = float(c @ np.float32((0.114, 0.587, 0.299))) > 135
            self.block(img, words[i].split("\n"), self.H * 0.48, 230, True, clamp((v + 1) / 2), color=np.float32((20, 20, 24)) if dark else jb.WHITE, scale=1 + 0.45 * (1 - eo(v / 7, 4)), shadow=0 if dark else 0.3)
            return img + 90 * np.exp(-v / 1.6)
        return self._add(draw, seg * len(words) / self.fps, tr=k.pop("tr", "cut"), kind="words", meta=dict(seg=seg, count=len(words)), **k)
    def bullets(self, title, items, bg=None, dur=None, **k):
        """A heading with points that arrive one at a time (explainers, feature lists, steps). Sized to fit the frame."""
        def layout():
            k_ = 1.0
            while True:
                rows = [self.wrap(it, 64 * k_, False, self.W * 0.78) for it in items]; h = sum(len(r) * 64 * 1.3 + 30 for r in rows) * k_ * self.U
                if h <= self.H * 0.55 or k_ <= 0.5: return k_, rows
                k_ -= 0.04
        k_, rows = layout()
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); step = max(8, int((n * 0.6) / max(len(items), 1)))
            self.block(img, self.wrap(title, 84, True), self.H * 0.2, 84, True, eio(u / 8) * o, maxh=self.H * 0.16); y = self.H * 0.31 + max(0.0, self.H * 0.55 - sum(len(r_) * 64 * 1.3 + 30 for r_ in rows) * k_ * self.U) * 0.45
            for i, ls in enumerate(rows):
                v = u - 10 - i * step
                for l in ls:
                    jb.put(img, *self.T(l, 64 * k_, False), y + 14 * self.U * (1 - eo(v / 12)), eio(v / 8) * o, self.ink, 0.3 if themes.lum(self.ink) > 120 else 0); y += 64 * 1.3 * k_ * self.U
                y += 30 * k_ * self.U
            return img
        return self._add(draw, dur or 1.5 + 1.1 * len(items), kind="bullets", meta=dict(count=len(items)), **k)
    def _device(self, ph):
        """The phone body (titanium frame, side keys, dynamic island) at a given pixel height.
        Returns (body BGR float, body alpha, screen rect (x, y, w, h), screen mask, island mask). Design size 414 x 868."""
        s = ph / 868; pw = int(round(414 * s)); kx = int(np.ceil(5 * s)); Wd = pw + 2 * kx; SS = 3
        def rr(w, h, r, x=0, y=0, cw=None, chh=None):
            m = np.zeros(((chh or h) * SS, (cw or w) * SS), np.uint8); x, y, w, h, r = x * SS, y * SS, w * SS, h * SS, int(r * SS)
            cv2.rectangle(m, (x + r, y), (x + w - r, y + h), 255, -1); cv2.rectangle(m, (x, y + r), (x + w, y + h - r), 255, -1)
            for cx_, cy_ in ((x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)): cv2.circle(m, (cx_, cy_), r, 255, -1, cv2.LINE_AA)
            return cv2.resize(m, (cw or w // SS, chh or h // SS), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        yy_, xx_ = np.mgrid[0:ph, 0:pw].astype(np.float32); g = (xx_ * 0.643 + yy_ * 0.766); g = (g - g.min()) / (g.max() - g.min())
        stops = [0, 0.18, 0.5, 0.82, 1]; cols = [(0x74, 0x6e, 0x6f), (0x2e, 0x2a, 0x2a), (0x4d, 0x47, 0x48), (0x26, 0x23, 0x23), (0x6c, 0x66, 0x67)]
        body = np.stack([np.interp(g, stops, [c[i] for c in cols]) for i in range(3)], -1).astype(np.float32)
        outer = rr(pw, ph, 70 * s); hl = np.clip(outer - rr(pw - int(3 * s) - 1, ph - int(3 * s) - 1, 69 * s, int(1.5 * s) + 0, int(1.5 * s) + 0, pw, ph), 0, 1)
        ring = rr(pw - int(12 * s), ph - int(12 * s), 64 * s, int(6 * s), int(6 * s), pw, ph); inner = rr(pw - int(24 * s), ph - int(24 * s), 58 * s, int(12 * s), int(12 * s), pw, ph)
        body = body * (1 - 0.78 * (ring - inner)[..., None]) + 10 * (ring - inner)[..., None] * 0; body = body * (1 - (ring * 0.0)[..., None])
        body = body * (1 - (ring - inner)[..., None]) + np.float32((11, 10, 10)) * (ring - inner)[..., None]; body = body + hl[..., None] * 60
        sx, sy = int(round(13 * s)), int(round(13 * s)); sw, sh = pw - 2 * sx, ph - 2 * sy; smask = rr(sw, sh, 57 * s)
        iw, ih = int(124 * s), int(36 * s); island = rr(iw, ih, ih / 2 - 0.5, (sw - iw) // 2, int(11 * s), sw, sh)
        full = np.zeros((ph, Wd, 3), np.float32); al = np.zeros((ph, Wd), np.float32); full[:, kx:kx + pw] = body; al[:, kx:kx + pw] = outer
        for side, top, hh in ((0, 140, 34), (0, 205, 64), (0, 285, 64), (1, 240, 104)):
            x0 = 1 if side == 0 else kx + pw - 1; ya, yb = int(top * s), int((top + hh) * s); full[ya:yb, x0:x0 + kx] = (0x62, 0x5a, 0x5c); al[ya:yb, x0:x0 + kx] = np.maximum(al[ya:yb, x0:x0 + kx], 1.0)
        return full, al, (kx + sx, sy, sw, sh), smask, island
    def phone(self, screenshot, text=None, bg=None, dur=4.0, scroll=True, status=False, span=(0.0, 1.0), **k):
        """A phone with a screenshot inside (app and website demos). The device is the titanium frame with side keys and
        dynamic island. Tall screenshots scroll; short ones are scaled to cover. status=True adds a clock and battery."""
        shot = jb.art(screenshot); W, H = self.W, self.H; land = W > H
        ph = int(H * (0.84 if land else 0.68)); dev, al, (sx, sy, sw, sh), smask, island = self._device(ph); Wd = dev.shape[1]
        s = cv2.resize(shot, (sw, max(int(shot.shape[0] * sw / shot.shape[1]), 1)), interpolation=cv2.INTER_AREA)
        if s.shape[0] < sh: k2 = sh / s.shape[0]; s2 = cv2.resize(s, (int(sw * k2) + 1, sh)); x2 = (s2.shape[1] - sw) // 2; s = s2[:, x2:x2 + sw]
        dark = s[:int(54 * ph / 868)].mean() < 120
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); cx = int(W * (0.70 if land and text else 0.5)); cy = int(H * (0.5 if land else 0.57) + (1 - eo(u / 16, 3)) * H * 0.8)
            off = int(max(s.shape[0] - sh, 0) * (span[0] + (span[1] - span[0]) * (eio((u - 20) / max(n - 40, 1)) if scroll else 0))); scr = s[off:off + sh].astype(np.float32)
            scr = scr * (1 - island[..., None])
            d = dev.copy(); a_s = smask[..., None]; d[sy:sy + sh, sx:sx + sw] = d[sy:sy + sh, sx:sx + sw] * (1 - a_s) + scr * a_s
            x0, y0 = cx - Wd // 2, cy - ph // 2; ya, yb, xa, xb = max(y0, 0), min(y0 + ph, H), max(x0, 0), min(x0 + Wd, W)
            if yb > ya and xb > xa:
                shd = np.zeros((H, W), np.float32); shd[ya:yb, xa:xb] = al[ya - y0:yb - y0, xa - x0:xb - x0]
                img = img * (1 - 0.5 * cv2.GaussianBlur(np.roll(shd, int(24 * self.U), 0), (0, 0), 34 * self.U + 1)[..., None])
                a = al[ya - y0:yb - y0, xa - x0:xb - x0, None]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + d[ya - y0:yb - y0, xa - x0:xb - x0] * a
                if status:
                    c = jb.WHITE if dark else np.float32((33, 27, 17)); sc_ = ph / 868 / self.U
                    self.ltext(img, "9:41", x0 + sx + 44 * ph / 868, y0 + sy + 28 * ph / 868, 17 * sc_, True, 1.0, c)
                    bx, by = int(x0 + sx + sw - 56 * ph / 868), int(y0 + sy + 22 * ph / 868); cv2.rectangle(img, (bx, by), (bx + int(26 * ph / 868), by + int(12 * ph / 868)), tuple(float(v) for v in c), -1, cv2.LINE_AA)
            if text:
                ls = self.wrap(text, 64, True, W * (0.38 if land else 0.84)); o = self._io(u, n, 10)
                if land:
                    kk = min(1.0, H * 0.6 / (len(ls) * 64 * 1.25 * self.U))
                    for i, l in enumerate(ls): self.ltext(img, l, W * 0.07, H * 0.5 + (i - (len(ls) - 1) / 2) * 64 * kk * 1.25 * self.U, 64 * kk, True, o, maxw=W * 0.40)
                else: self.block(img, ls, H * 0.105, 64, True, o, maxh=H * 0.13)
            return img
        return self._add(draw, dur, kind="phone", **k)
    def _icons(self, names):
        """Make sure these react-icons icons are rendered and cached in <workspace>/icons (one browser launch for all)."""
        home = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); d = os.path.join(home, "icons"); kit = os.path.join(home, "web")
        miss = [n for n in names if not os.path.exists(os.path.join(d, n.split("/")[-1] + ".png"))]
        if miss:
            if not os.path.exists(os.path.join(kit, "node_modules", "react-icons")): sys.exit("joyboy: the icon kit is not installed; run setup.sh (needs node and a Chrome-family browser)")
            r = subprocess.run(["node", os.path.join(kit, "icon.mjs"), "render", d] + miss, cwd=kit, capture_output=True, text=True)
            if r.returncode: sys.exit("joyboy: " + (r.stderr.strip() or "icon render failed"))
        return d
    def icon(self, name):
        """Alpha mask (512 px, float 0..1) of a react-icons icon by its export name: 'LuRocket', 'FaWhatsapp', 'MdStorefront',
        'TbChartBar', 'SiShopify' ... Find names with: node ~/joyboy/web/icon.mjs search <word>."""
        im = cv2.imread(os.path.join(self._icons([name]), name.split("/")[-1] + ".png"), cv2.IMREAD_UNCHANGED)
        return im[..., 3].astype(np.float32) / 255
    def put_icon(self, img, name, cx, cy, size, color=jb.WHITE, op=1.0):
        """Draw an icon centred on (cx, cy), `size` pixels across, in any colour."""
        s_ = max(int(size), 2); m = cv2.resize(self.icon(name), (s_, s_), interpolation=cv2.INTER_AREA) * op; x0, y0 = int(cx - s_ / 2), int(cy - s_ / 2)
        xa, xb, ya, yb = max(x0, 0), min(x0 + s_, self.W), max(y0, 0), min(y0 + s_, self.H)
        if xb <= xa or yb <= ya: return
        a = m[ya - y0:yb - y0, xa - x0:xb - x0, None]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + np.float32(color) * a
    def icons(self, items, title=None, bg=None, dur=None, **k):
        """A grid of icons with labels that pop in one by one (features, services, benefits, steps).
        items = [(icon name, label), ...] or [(icon name, label, small line), ...]."""
        self._icons([it[0] for it in items]); nI = len(items)
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); self._head(img, title, u, o); land = W > H
            cols = min(nI, 4) if land else (1 if nI <= 3 else 2); rows = int(np.ceil(nI / cols)); x0, x1, y0, y1 = W * 0.08, W * 0.92, H * (0.26 if title else 0.14), H * 0.88
            cw, ch = (x1 - x0) / cols, (y1 - y0) / rows; r = min(cw * 0.26, ch * 0.24)
            for i, it in enumerate(items):
                cx, cy = x0 + cw * (i % cols + 0.5), y0 + ch * (i // cols + 0.5) - ch * 0.10; v = u - 8 - i * 6
                if v < 0: continue
                s_ = float(spring(v / self.fps * 1.7, 1.7, 5.5)); c = self._c(i)
                cv2.circle(img, (int(cx), int(cy)), int(r * s_) + 1, self._fade(c, o, img, cx, cy), -1, cv2.LINE_AA)
                self.put_icon(img, it[0], cx, cy, r * 1.15 * s_, color=np.float32((24, 22, 22)) if float(c @ np.float32((0.114, 0.587, 0.299))) > 165 else jb.WHITE, op=o)
                g = eio((v - 5) / 8) * o; self.ltext(img, it[1], cx, cy + r + 48 * U, 50, True, g, align="center", maxw=cw * 0.9)
                if len(it) > 2: self.ltext(img, it[2], cx, cy + r + 108 * U, 40, False, g * 0.85, align="center", maxw=cw * 0.9)
            return img
        return self._add(draw, dur or 2.0 + 0.5 * nI, kind="icons", meta=dict(count=nI), **k)
    # ----- people: illustrated characters from DiceBear, still or talking -----
    TALK = {"avataaars": (("twinkle", "default", "smile"), ("default", "closed", "happy"))}   # style: ((mouth closed, a little open, wide), (eyes open, blink, idle))
    def person(self, name, style="avataaars", seed=None, options=None, mouths=None, eyes=None, voice=None, tint="#f6e7dc"):
        """An illustrated character from DiceBear (dicebear.com), generated on this machine and cached in <workspace>/avatars.
        The same seed and options always give the same person; only the mouth and eyes change between frames.
        options = DiceBear options for the style (hair, skin, clothes ...; list them with: node ~/joyboy/web/avatar.mjs options <style>).
        mouths = (closed, a little open, wide) and eyes = (open, blink, idle) option names; built in for 'avataaars',
        pass them for any other style. voice = the voice this person speaks with (Piper voice name or ElevenLabs id).
        Returns a handle for talk(), face() and put_person()."""
        import json
        if style not in self.TALK and not (mouths and eyes): sys.exit(f"joyboy: pass mouths=(closed, half, wide) and eyes=(open, blink, idle) for the DiceBear style '{style}' (see: node ~/joyboy/web/avatar.mjs options {style})")
        mouths, eyes = tuple(mouths or self.TALK[style][0]), tuple(eyes or self.TALK[style][1]); opts = json.dumps(options or {}, sort_keys=True); seed = seed or name
        home = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); kit = os.path.join(home, "web")
        d = os.path.join(home, "avatars", style + "-" + hashlib.md5(f"{style}{seed}{opts}".encode()).hexdigest()[:10])
        if not all(os.path.exists(os.path.join(d, f"{name}__{m}__{e}.png")) for m in mouths for e in eyes):
            if not os.path.exists(os.path.join(kit, "node_modules", "@dicebear", "core")): sys.exit("joyboy: DiceBear is not installed; run setup.sh (needs node and a Chrome-family browser)")
            r = subprocess.run(["node", os.path.join(kit, "avatar.mjs"), "render", d, name, style, seed, opts, ",".join(dict.fromkeys(mouths)), ",".join(dict.fromkeys(eyes)), "1024"], cwd=kit, capture_output=True, text=True)
            if r.returncode: sys.exit("joyboy: " + (r.stderr.strip() or "avatar render failed"))
        return dict(name=name, dir=d, mouths=mouths, eyes=eyes, voice=voice, tint=tint, style=style, seed=seed, options=options or {})
    def face(self, person, mouth=None, eyes=None, h=None):
        """A person's picture as float BGRA (1024 px, or h pixels tall). mouth / eyes default to closed mouth, open eyes."""
        c = self.__dict__.setdefault("_faces", {}); k = (person["dir"], mouth or person["mouths"][0], eyes or person["eyes"][0])
        if k not in c:
            im = cv2.imread(os.path.join(k[0], f"{person['name']}__{k[1]}__{k[2]}.png"), cv2.IMREAD_UNCHANGED)
            if im is None: raise FileNotFoundError(f"no frame {k[1]}/{k[2]} for {person['name']}; add it to mouths= / eyes= in person()")
            c[k] = im.astype(np.float32)
        if not h: return c[k]
        h = max(int(h) // 2 * 2, 2)
        if k + (h,) not in c: c[k + (h,)] = cv2.resize(c[k], (h, h), interpolation=cv2.INTER_AREA)
        return c[k + (h,)]
    def put_person(self, img, person, cx, cy, h, mouth=None, eyes=None, op=1.0):
        """Draw a person on img (in place), h pixels tall, centred at (cx, cy). For custom scenes."""
        av = self.face(person, mouth, eyes, h); x0, y0 = int(cx - av.shape[1] / 2), int(cy - av.shape[0] / 2); xa, xb, ya, yb = max(x0, 0), min(x0 + av.shape[1], self.W), max(y0, 0), min(y0 + av.shape[0], self.H)
        if xb <= xa or yb <= ya: return
        part = av[ya - y0:yb - y0, xa - x0:xb - x0]; a = part[..., 3:4] / 255 * op; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + part[..., :3] * a
    def model(self, glb, **k):
        """A real 3D model file (GLB / glTF) drawn with 67.js: products, objects, vehicles, animated characters.
        Returns a Model; add camera shots with m.shot("turntable" | "orbit" | "push" | "pull" | "hero" | "low" | "top").
        See model3d.py and "3D models" in SKILL.md."""
        from model3d import Model
        return Model(self, glb, **k)
    def site(self, url, device="desktop"):
        """Download a real public website once and work with its parts: move to an element, light it, lift it, label it,
        click it. Returns a Site; add shots with s.shot(focus="words on the page", label=..., click=True).
        See sitekit.py and "Working with someone's website" in SKILL.md."""
        from sitekit import Site
        return Site(self, url, device)
    def world(self, place="forest", time="day", weather="clear", seed=1, props=(), people=(), extras=None):
        """A procedural low-poly 3D world for story scenes: a place, a time of day, weather, props and people (from person()).
        Returns a World; add camera shots with w.shot(cam, say=(person, "line")). See world.py and "Worlds" in SKILL.md."""
        from world import World
        return World(self, place=place, time=time, weather=weather, seed=seed, props=props, people=people, extras=extras)
    def _envelope(self, wav):
        """Loudness of a narration file per video frame (0..1), held for two frames so a mouth driven by it does not flicker."""
        w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32); hop = w.getframerate() // self.fps; w.close(); n = len(x) // hop
        if n < 2: return np.zeros(1, np.float32)
        e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)); e = e / (np.percentile(e, 95) + 1e-6)
        return np.repeat(np.maximum.reduceat(e, np.arange(0, n, 2)), 2)[:n].clip(0, 1.2)
    def talk(self, person, line, role=None, prop=None, bg=None, dur=3.0, at=0.5, caption=True, **k):
        """A person speaks `line`: their face in a rounded card, the mouth driven by the loudness of the narration, blinks,
        a small nod while speaking, a role label, and the line as a caption. `prop` = an image (screenshot, photo) shown in a
        window beside or above the speaker, panning slowly. Pass voice="file.mp3" to lip-sync to a ready recording instead."""
        say = k.pop("voice", line); pace = k.get("pace"); pace = self.pace if pace in (None, "fit") else pace
        old = self.voice_name; self.voice_name = person["voice"] or old
        try:
            vf = self._say(say, 1.0 if os.path.isfile(str(say)) else float(pace)); env = self._envelope(vf[0]) if vf else np.zeros(1, np.float32)
            W, H, U = self.W, self.H, self.U; land = W > H; v0 = int(at * self.fps); tint = col(person["tint"]); m0, m1, m2 = person["mouths"]; e_open, e_blink, e_idle = person["eyes"]
            def rr(w, h, r):
                m = np.zeros((h, w), np.float32); cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
                for px, py in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)): cv2.circle(m, (px, py), r, 1, -1, cv2.LINE_AA)
                return m
            cs = int((H * 0.56 if land else W * (0.60 if prop else 0.78))) // 2 * 2; ccx, ccy = (W * 0.27, H * 0.47) if land else (W / 2, H * (0.655 if prop else 0.47)); cm = rr(cs, cs, int(cs * 0.16))
            if prop:
                ww, wh = (int(W * 0.44) // 2 * 2, int(H * 0.52) // 2 * 2) if land else (int(W * 0.90) // 2 * 2, int(H * 0.36) // 2 * 2); sh = jb.art(prop); kk = max(ww / sh.shape[1], wh / sh.shape[0])
                page = cv2.resize(sh, (max(int(sh.shape[1] * kk), ww), max(int(sh.shape[0] * kk), wh)), interpolation=cv2.INTER_AREA).astype(np.float32); pm = rr(ww, wh, int(30 * U)); px0, py0 = (int(W * 0.50), int(H * 0.10)) if land else ((W - ww) // 2, int(H * 0.065))
            tw = W * (0.42 if land else 0.84); lines = self.wrap(untag(line), 50, True, tw) if caption else []
            def draw(u, n, f):
                img = self.bg(bg, u, n, f); o = self._io(u, n, 8, 8); t = u - v0; on = 0 <= t < len(env); lv = float(env[t]) if on else 0.0
                mouth = m0 if lv < 0.14 else m1 if lv < 0.6 else m2; eyes = e_blink if (u + 37) % 88 < 4 else (e_open if on else e_idle)
                if prop:
                    y0 = int(py0 - (1 - eo(u / 18, 3)) * H * 0.6); p_ = eio((u - 10) / max(n - 20, 1)); ox, oy = int((page.shape[1] - ww) * p_), int((page.shape[0] - wh) * p_ * 0.35); ya, yb = max(y0, 0), min(y0 + wh, H)
                    if yb > ya: a = pm[ya - y0:yb - y0, :, None] * o; img[ya:yb, px0:px0 + ww] = img[ya:yb, px0:px0 + ww] * (1 - a) + page[oy + ya - y0:oy + yb - y0, ox:ox + ww] * a
                s_ = min(float(spring(u / self.fps * 1.5, 1.4, 5.0)), 1.0); x0, y0 = int(ccx - cs / 2), int(ccy - cs / 2 + (1 - s_) * 60 * U)
                shd = np.zeros((H, W), np.float32); shd[y0:y0 + cs, x0:x0 + cs] = cm; img = img * (1 - 0.45 * o * cv2.GaussianBlur(np.roll(shd, int(22 * U), 0), (0, 0), 30 * U + 1)[..., None])
                card = np.empty((cs, cs, 3), np.float32); card[:] = tint; av = self.face(person, mouth, eyes, cs * 0.94)
                bob = int((4 + 7 * lv) * U * np.sin(u / 7.0)) if on else int(3 * U * np.sin(u / 16.0)); ax, ay = (cs - av.shape[1]) // 2, cs - av.shape[0] + int(8 * U) + bob
                ya, yb = max(ay, 0), min(ay + av.shape[0], cs); part = av[ya - ay:yb - ay]; a = part[..., 3:4] / 255; card[ya:yb, ax:ax + av.shape[1]] = card[ya:yb, ax:ax + av.shape[1]] * (1 - a) + part[..., :3] * a
                a = cm[..., None] * o; img[y0:y0 + cs, x0:x0 + cs] = img[y0:y0 + cs, x0:x0 + cs] * (1 - a) + card * a
                if role:
                    pw, ph = self._len(role, 38, True) + 80 * U, 74 * U; py = y0 + cs
                    self.card(img, ccx - pw / 2, py - ph / 2, ccx + pw / 2, py + ph / 2, self.pal[1 % len(self.pal)], radius=40, op=o); self.ltext(img, role, ccx, py, 38, True, o, align="center", maxw=pw * 0.86)
                if lines:
                    co = o * eio((t + 6) / 10)
                    if land:
                        cy_ = H * (0.80 if prop else 0.47); kk_ = min(1.0, H * (0.22 if prop else 0.6) / (len(lines) * 50 * 1.25 * U))
                        for i, l in enumerate(lines): self.ltext(img, l, W * 0.72, cy_ + (i - (len(lines) - 1) / 2) * 50 * kk_ * 1.25 * U, 50 * kk_, True, co * clamp((t + 6 - i * 5) / 6), align="center", maxw=tw)
                    else: self.block(img, lines, H * (0.885 if prop else 0.80), 50, True, co, maxh=H * 0.12, stagger=5, u=t + 6)
                return img
            k.setdefault("sfx", [(0.05, "pop")])
            return self._add(draw, dur, voice=say, voice_at=at, kind="talk", **k)
        finally: self.voice_name = old
    def stat(self, value, label=None, bg=None, dur=2.5, color=None, **k):
        """A big number that counts up ('40%', '$1.2M', '3x') with a label."""
        mt = re.match(r"^([^\d]*)([\d.,]+)(.*)$", str(value)); pre, num, suf = mt.groups() if mt else ("", "0", str(value))
        target = float(num.replace(",", "")); dec = len(num.split(".")[1]) if "." in num else 0
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); o = self._io(u, n, 4); v = target * eo(u / (n * 0.55), 3)
            s = f"{v:,.{dec}f}" if "," in num else f"{v:.{dec}f}"
            self.block(img, [pre + s + suf], self.H * 0.44, 280, True, o, color=col(color) if color else None, scale=1 + 0.06 * (1 - eo(u / 10)))
            if label: self.block(img, self.wrap(label, 56), self.H * 0.44 + 230 * self.U, 56, False, eio((u - 8) / 8) * o)
            return img
        return self._add(draw, dur, kind="stat", **k)
    def bars(self, data, title=None, bg=None, dur=4.0, unit="", **k):
        """Animated horizontal bar chart from {label: value}."""
        items = list(data.items()); mx = max(v for _, v in items) or 1
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6)
            if title: self.block(img, self.wrap(title, 76, True), H * 0.16, 76, True, eio(u / 8) * o)
            x0, x1 = W * 0.12, W * 0.88; rh = min(H * 0.56 / len(items), 150 * U); y = H * 0.30
            for i, (lab, v) in enumerate(items):
                g = eo((u - 8 - i * 4) / (n * 0.4), 3) * o; c = self.pal[1 + i % max(len(self.pal) - 1, 1)]
                self.ltext(img, str(lab), x0, y + rh * 0.2, 40, False, clamp(g * 3) * o, maxw=x1 - x0)
                bw = (x1 - x0) * v / mx * g; ya, yb = int(y + rh * 0.42), int(y + rh * 0.80)
                if bw > 2: img[ya:yb, int(x0):int(x0 + bw)] = c
                self.ltext(img, f"{v * min(g * 1.02, 1):,.0f}{unit}" if float(v).is_integer() else f"{v * min(g * 1.02, 1):,.1f}{unit}", x0 + bw + 14 * U, (ya + yb) / 2, 40, True, clamp(g * 3) * o)
                y += rh
            return img
        return self._add(draw, dur, kind="bars", meta=dict(count=len(items)), **k)
    def _c(self, i): return self.pal[1 + i % max(len(self.pal) - 1, 1)]
    def _fade(self, c, o, img, x, y):
        """Colour c faded toward whatever is behind it at (x, y), so shapes fade out into the background, not to black."""
        b_ = img[min(max(int(y), 0), self.H - 1), min(max(int(x), 0), self.W - 1)]; return tuple(float(q) * o + float(w) * (1 - o) for q, w in zip(c, b_))
    def columns(self, data, title=None, bg=None, dur=4.0, unit="", **k):
        """Animated vertical bar chart from {label: value}."""
        items = list(data.items()); mx = max(v for _, v in items) or 1
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); self._head(img, title, u, o)
            x0, x1, yb, yt = W * 0.12, W * 0.88, H * 0.74, H * 0.30; cw = (x1 - x0) / len(items)
            for i, (lab, v) in enumerate(items):
                g = eo((u - 8 - i * 4) / (n * 0.4), 3) * o; h = (yb - yt) * v / mx * g; xa, xb = int(x0 + cw * (i + 0.18)), int(x0 + cw * (i + 0.82))
                if h > 2: cv2.rectangle(img, (xa, int(yb - h)), (xb, int(yb)), tuple(float(q) for q in self._c(i)), -1, cv2.LINE_AA)
                val = v * min(g * 1.02, 1); self.ltext(img, (f"{val:,.0f}" if float(v).is_integer() else f"{val:,.1f}") + unit, (xa + xb) / 2, yb - h - 34 * U, 40, True, clamp(g * 3) * o, align="center")
                self.ltext(img, str(lab), (xa + xb) / 2, yb + 40 * U, 34, False, clamp(g * 3) * o, align="center", maxw=cw * 0.96)
            return img
        return self._add(draw, dur, kind="columns", meta=dict(count=len(items)), **k)
    def line(self, series, title=None, labels=None, bg=None, dur=4.0, unit="", **k):
        """Line chart that draws itself. series = [values] or {name: [values]}; labels = x-axis labels."""
        ser = series if isinstance(series, dict) else {"": list(series)}; allv = [v for vs in ser.values() for v in vs]; lo, hi = min(allv), max(allv); hi = hi if hi > lo else lo + 1
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); self._head(img, title, u, o)
            x0, x1, yb, yt = W * 0.12, W * 0.88, H * 0.72, H * 0.32; p = eio((u - 8) / (n * 0.5))
            for j in range(4): cv2.line(img, (int(x0), int(yb - (yb - yt) * j / 3)), (int(x1), int(yb - (yb - yt) * j / 3)), (70 * o, 70 * o, 78 * o), 1)
            for si, (name, vs) in enumerate(ser.items()):
                pts = np.float32([[x0 + (x1 - x0) * i / max(len(vs) - 1, 1), yb - (yb - yt) * (v - lo) / (hi - lo)] for i, v in enumerate(vs)])
                d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]; L = d[-1] * p; k2 = int(np.searchsorted(d, L)); sub = pts[:max(k2, 1)]
                if 0 < k2 < len(pts): t = (L - d[k2 - 1]) / max(d[k2] - d[k2 - 1], 1e-6); sub = np.vstack([sub, pts[k2 - 1] + (pts[k2] - pts[k2 - 1]) * t])
                c = self._fade(self._c(si), o, img, x0, yb)
                if len(sub) > 1:
                    glow = np.zeros((H, W), np.float32); cv2.polylines(glow, [np.int32(sub)], False, 1.0, int(18 * U) + 1, cv2.LINE_AA)
                    img += cv2.GaussianBlur(glow, (0, 0), 14 * U + 1)[..., None] * np.float32(c) * 0.5; cv2.polylines(img, [np.int32(sub * 8)], False, c, max(2, int(7 * U)), cv2.LINE_AA, 3)
                    cv2.circle(img, (int(sub[-1][0]), int(sub[-1][1])), int(13 * U) + 1, (250 * o, 252 * o, 250 * o), -1, cv2.LINE_AA)
                if p >= 1: self.ltext(img, (name + " " if name else "") + f"{vs[-1]:,g}{unit}", x1, pts[-1][1] - 46 * U, 38, True, eio((u - n * 0.55) / 8) * o, align="right")
            if labels:
                for i, lab in enumerate(labels): self.ltext(img, str(lab), x0 + (x1 - x0) * i / max(len(labels) - 1, 1), yb + 44 * U, 30, False, eio(u / 10) * o, align="center")
            return img
        return self._add(draw, dur, kind="line", meta=dict(count=len(ser)), **k)
    def donut(self, parts, title=None, center=None, bg=None, dur=4.0, **k):
        """Donut chart from {label: value} with a legend; `center` is optional text in the middle."""
        items = list(parts.items()); tot = sum(v for _, v in items) or 1
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); self._head(img, title, u, o); land = W > H
            cx, cy, r = int(W * (0.34 if land else 0.5)), int(H * (0.55 if land else 0.44)), int(min(W, H) * (0.24 if land else 0.27)); p = eo((u - 6) / (n * 0.45), 3); a0 = -90.0
            for i, (lab, v) in enumerate(items):
                sw = 360 * v / tot; a1 = min(a0 + sw, -90 + 360 * p)
                if a1 > a0: cv2.ellipse(img, (cx, cy), (r, r), 0, a0 + 1.2, a1 - 1.2, self._fade(self._c(i), o, img, cx, cy), int(r * 0.36), cv2.LINE_AA)
                a0 += sw
                lx, ly = (W * 0.62, H * 0.55 + (i - (len(items) - 1) / 2) * 70 * U) if land else (W * 0.24, cy + r * 1.38 + (i + 0.5) * 66 * U); g = eio((u - 14 - i * 4) / 8) * o
                cv2.circle(img, (int(lx), int(ly)), int(13 * U) + 1, self._fade(self._c(i), g, img, lx, ly), -1, cv2.LINE_AA)
                self.ltext(img, f"{lab}   {v / tot * 100:.0f}%", lx + 34 * U, ly, 40, False, g, maxw=W - lx - 60 * U)
            if center: self.ltext(img, center, cx, cy, 76, True, eio((u - 12) / 10) * o, align="center", maxw=r * 1.1)
            return img
        return self._add(draw, dur, kind="donut", meta=dict(count=len(items)), **k)
    def heatmap(self, grid, xlabels=None, ylabels=None, title=None, colors=None, values=False, bg=None, dur=4.0, **k):
        """Heat map from a 2D list of numbers; cells light up in a diagonal wave. colors = (low, high)."""
        G = np.array(grid, np.float32); R, Cn = G.shape; lo, hi = float(G.min()), float(G.max()); hi = hi if hi > lo else lo + 1
        c0, c1 = (col(colors[0]), col(colors[1])) if colors else (self.pal[0] * 0.6 + 26, self._c(0))
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = self.bg(bg, u, n, f); o = 1 - eio((u - (n - 6)) / 6); self._head(img, title, u, o)
            x0, x1, y0, y1 = W * (0.20 if ylabels else 0.10), W * 0.90, H * 0.27, H * (0.80 if xlabels else 0.84); cs = min((x1 - x0) / Cn, (y1 - y0) / R); gx = x0 + ((x1 - x0) - cs * Cn) / 2; gy = y0 + ((y1 - y0) - cs * R) / 2
            for r in range(R):
                if ylabels: self.ltext(img, str(ylabels[r]), gx - 16 * U, gy + cs * (r + 0.5), 30, False, eio(u / 10) * o, align="right")
                for c in range(Cn):
                    g = eo((u - 6 - (r + c) * 1.4) / 9, 3) * o
                    if g <= 0: continue
                    t = (G[r, c] - lo) / (hi - lo); cc = (c0 * (1 - t) + c1 * t) * g; h = cs * 0.46 * (0.4 + 0.6 * g); mx_, my_ = gx + cs * (c + 0.5), gy + cs * (r + 0.5)
                    cv2.rectangle(img, (int(mx_ - h), int(my_ - h)), (int(mx_ + h), int(my_ + h)), tuple(float(q) for q in cc), -1, cv2.LINE_AA)
                    if values and cs > 60 * U: self.ltext(img, f"{G[r, c]:g}", mx_, my_, min(34, cs / U * 0.3), True, g, align="center")
            if xlabels:
                for c in range(Cn): self.ltext(img, str(xlabels[c]), gx + cs * (c + 0.5), gy + cs * R + 30 * U, 28, False, eio(u / 10) * o, align="center")
            return img
        return self._add(draw, dur, kind="heatmap", meta=dict(count=R + Cn - 1), **k)
    def map(self, place, radius_km=2.0, pins=None, route=None, title=None, zoom="in", style=None, dur=5.0, **k):
        """A real street map (OpenStreetMap data, drawn in code) centred on a place name or (lat, lon).
        pins = [(label, place or (lat, lon)), ...] drop in one by one; route = [place or (lat, lon), ...] draws a line
        through the points (straight segments, not turn-by-turn); zoom = 'in', 'out' or 'still'."""
        import maps
        lat, lon = maps.geocode(place); M = maps.Map(lat, lon, radius_km); S = 2400 if not self.draft else 1400
        acc = self._c(0); st = dict(style or {}); base = self.pal[0]
        if style is None and float(base.mean()) < 110:   # tint the map with the film's dark base colour
            F3 = lambda v: tuple(float(q) for q in v); st = dict(land=F3(base * 0.9 + 8), building=F3(base * 0.9 + 30), park=F3(base * 0.7 + np.float32((40, 70, 30)) * 0.5), water=F3(base * 0.5 + np.float32((150, 95, 45)) * 0.5))
        base = M.render(S, st); P = [(lab, M.px(*maps.geocode(w), S)) for lab, w in (pins or [])]; R = np.float32([M.px(*maps.geocode(w), S) for w in (route or [])])
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; t = u / n; o = 1 - eio((u - (n - 6)) / 6)
            k0 = max(W, H) / S; z = {"in": 1.05 + 0.5 * eio(t), "out": 1.6 - 0.5 * eio(t), "still": 1.2}[zoom]; kk = k0 * z
            A = np.float32([[kk, 0, W / 2 - S / 2 * kk], [0, kk, H / 2 - S / 2 * kk]]); img = cv2.warpAffine(base, A, (W, H), flags=cv2.INTER_AREA if kk < 1 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            T = lambda q: (q[0] * kk + A[0, 2], q[1] * kk + A[1, 2])
            if len(R) > 1:
                pts = np.float32([T(q) for q in R]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]; L = d[-1] * eio((u - 10) / (n * 0.55)); j = int(np.searchsorted(d, L)); sub = pts[:max(j, 1)]
                if 0 < j < len(pts): sub = np.vstack([sub, pts[j - 1] + (pts[j] - pts[j - 1]) * (L - d[j - 1]) / max(d[j] - d[j - 1], 1e-6)])
                if len(sub) > 1:
                    gl = np.zeros((H, W), np.float32); cv2.polylines(gl, [np.int32(sub)], False, 1.0, int(22 * U) + 1, cv2.LINE_AA); img += cv2.GaussianBlur(gl, (0, 0), 16 * U + 1)[..., None] * acc * 0.6
                    cv2.polylines(img, [np.int32(sub * 8)], False, tuple(float(q) for q in acc), max(3, int(9 * U)), cv2.LINE_AA, 3); cv2.circle(img, (int(sub[-1][0]), int(sub[-1][1])), int(14 * U) + 1, (250, 252, 250), -1, cv2.LINE_AA)
            for i, (lab, q) in enumerate(P):
                v = u - 12 - i * 10
                if v < 0: continue
                x, y = T(q); s_ = float(spring(v / self.fps * 1.8, 1.8, 5.5)); y -= (1 - eo(v / 8, 3)) * 120 * U; r = 20 * U * s_
                pulse = (v % 40) / 40; cv2.circle(img, (int(x), int(y)), int(r + 60 * U * pulse) + 1, tuple(float(c) * (1 - pulse) * 0.7 + float(b) * (1 - (1 - pulse) * 0.7) for c, b in zip(acc, img[min(max(int(y), 0), H - 1), min(max(int(x), 0), W - 1)])), max(1, int(3 * U)), cv2.LINE_AA)
                cv2.circle(img, (int(x), int(y)), int(r) + 1, tuple(float(c) for c in acc), -1, cv2.LINE_AA); cv2.circle(img, (int(x), int(y)), int(r * 0.42) + 1, (250, 252, 250), -1, cv2.LINE_AA)
                if lab:
                    ft_w = self._len(lab, 34, True) + 40 * U; xa, ya = int(x - ft_w / 2), int(y - r - 78 * U); g = eio((v - 4) / 8) * o
                    cv2.rectangle(img, (xa, ya), (int(xa + ft_w), int(ya + 56 * U)), tuple(float(c) * g + float(b) * (1 - g) for c, b in zip((250, 252, 250), (40, 40, 44))), -1, cv2.LINE_AA)
                    self.ltext(img, lab, x, ya + 28 * U, 34, True, g, np.float32((24, 22, 22)), align="center")
            if title:
                band = np.clip(1 - jb.yy / (H * 0.3), 0, 1)[..., None]; img = img * (1 - 0.7 * band); self.block(img, self.wrap(title, 76, True), H * 0.11, 76, True, eio(u / 8) * o)
            self.ltext(img, "\u00a9 OpenStreetMap contributors", W - 18 * U, H - 26 * U, 22, False, 0.7, align="right")
            return img
        return self._add(draw, dur, kind="map", meta=dict(pins=len(P), route=len(R) > 1), **k)
    def quote(self, text, by=None, bg=None, dur=4.0, **k):
        """A quotation or testimonial, auto-wrapped."""
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); o = self._io(u, n, 10); ls = self.wrap(text, 74, True, self.W * 0.8); cy = self.H * 0.48; hq = len(ls) * min(74, self.H * 0.42 / (len(ls) * 1.18 * self.U)) * 0.6
            self.block(img, ["\u201c"], cy - (hq + 110) * self.U, 240, True, o * 0.5, color=self.pal[1 % len(self.pal)], shadow=0)
            self.block(img, ls, cy, 74, True, o, stagger=3, u=u)
            if by: self.block(img, [by], cy + (hq + 80) * self.U, 44, False, eio((u - 14) / 10) * (1 - eio((u - (n - 6)) / 6)))
            return img
        return self._add(draw, dur, kind="quote", **k)
    def capture(self, url, device="mobile"):
        """Full-length screenshot of a real public web page (cached). device = 'mobile' or 'desktop'.
        Use the result with phone() for a phone view or browser() for a desktop window."""
        home = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); d = os.path.join(home, "captures"); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, hashlib.md5((url + device).encode()).hexdigest()[:12] + f"-{device}.png")
        if not os.path.exists(p):
            r = subprocess.run(["node", os.path.join(home, "web", "page_capture.mjs"), url, p, device], cwd=os.path.join(home, "web"), capture_output=True, text=True)
            if not os.path.exists(p): sys.exit("joyboy: could not capture " + url + " " + r.stderr.strip()[:200])
        return p
    def browser(self, screenshot, url=None, text=None, bg=None, dur=5.0, scroll=True, span=(0.0, 1.0), **k):
        """A desktop browser window with a page inside (website tours). The page scrolls from top to bottom.
        `screenshot` is an image path, usually from capture(url, "desktop"); `url` is the address shown in the bar."""
        shot = jb.art(screenshot); W, H, U = self.W, self.H, self.U; land = W > H
        ww, wh = (int(W * 0.80), int(H * 0.74)) if land else (int(W * 0.92), int(H * 0.52)); bar = int(wh * (0.075 if land else 0.085)); ph_ = wh - bar
        page = cv2.resize(shot, (ww, max(int(shot.shape[0] * ww / shot.shape[1]), ph_)), interpolation=cv2.INTER_AREA)
        if page.shape[0] < ph_: page = cv2.copyMakeBorder(page, 0, ph_ - page.shape[0], 0, 0, cv2.BORDER_REPLICATE)
        m = np.zeros((wh, ww), np.float32); r_ = int(18 * U * (ww / (W * 0.8))) + 6; cv2.rectangle(m, (r_, 0), (ww - r_, wh), 1, -1); cv2.rectangle(m, (0, r_), (ww, wh - r_), 1, -1)
        for px, py in ((r_, r_), (ww - r_, r_), (r_, wh - r_), (ww - r_, wh - r_)): cv2.circle(m, (px, py), r_, 1, -1, cv2.LINE_AA)
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); x0 = (W - ww) // 2; y0 = int((H * (0.56 if text else 0.5) - wh / 2) + (1 - eo(u / 16, 3)) * H * 0.9)
            off = int(max(page.shape[0] - ph_, 0) * (span[0] + (span[1] - span[0]) * (eio((u - 24) / max(n - 50, 1)) if scroll else 0))); win = np.full((wh, ww, 3), (238, 236, 234), np.float32); win[bar:] = page[off:off + ph_]
            for i, c in enumerate(((86, 95, 255), (46, 188, 254), (64, 201, 40))): cv2.circle(win, (int(bar * (0.6 + i * 0.55)), bar // 2), max(3, int(bar * 0.17)), c, -1, cv2.LINE_AA)
            cv2.rectangle(win, (int(ww * 0.22), int(bar * 0.2)), (int(ww * 0.78), int(bar * 0.8)), (255, 255, 255), -1, cv2.LINE_AA)
            ya, yb = max(y0, 0), min(y0 + wh, H)
            if yb > ya:
                shd = np.zeros((H, W), np.float32); shd[ya:yb, x0:x0 + ww] = m[ya - y0:yb - y0]; img = img * (1 - 0.5 * cv2.GaussianBlur(np.roll(shd, int(26 * U), 0), (0, 0), 36 * U + 1)[..., None])
                a = m[ya - y0:yb - y0, :, None]; img[ya:yb, x0:x0 + ww] = img[ya:yb, x0:x0 + ww] * (1 - a) + win[ya - y0:yb - y0] * a
                if url and y0 + bar < H: self.ltext(img, url, W / 2, y0 + bar / 2, bar / U * 0.36, False, 1.0, np.float32((90, 84, 80)), align="center", maxw=ww * 0.5)
            if text: self.block(img, self.wrap(text, 64, True), H * (0.10 if land else 0.14), 64, True, self._io(u, n, 10), maxh=H * 0.15)
            return img
        return self._add(draw, dur, kind="browser", **k)
    def crt(self, lines, dur=4.0, **k):
        """An old terminal types `lines`, then blooms to white (use tr='white' on the next scene)."""
        def draw(u, n, f):
            t0, tl = 8, []
            for l in lines: tl.append((l, t0, 1.4)); t0 += int(len(l) * 1.4) + 8
            return jb.crt(u, tl, flash_at=n - 24)
        return self._add(draw, max(dur, (sum(len(l) for l in lines) * 1.4 + 8 * len(lines) + 40) / self.fps), tr=k.pop("tr", "cut"), kind="crt", meta=dict(lines=list(lines)), **k)
    def logo(self, mark, text=None, sub=None, style="trace", bg=None, dur=4.0, **k):
        """Logo reveal from an image of the logo (transparent PNG, or a flat logo on a plain background).
        style='trace': a line of light draws it on black, then it fills with a flash. style='pop': it springs in."""
        im = cv2.imread(mark, cv2.IMREAD_UNCHANGED)
        if im is None: raise FileNotFoundError(mark)
        if im.ndim == 3 and im.shape[2] == 4 and im[..., 3].min() < 200: msk = im[..., 3]
        else:
            g = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im; edge = np.r_[g[0], g[-1], g[:, 0], g[:, -1]].mean(); msk = 255 - g if edge > 127 else g
        C = jb.mark_contours((msk > 110).astype(np.float32)); mh = min(self.W, self.H) * 0.30; mx, my = self.W / 2, self.H * 0.42
        L = self.L(text, 62, 22, my + mh * 0.5 + 120 * self.U) if text else []
        cols = [tuple(c) for c in self.pal[1:]] or [(255, 255, 255)]
        def draw(u, n, f):
            t1 = int(n * 0.42) if style == "trace" else 0
            if u < t1: return jb.trace(C, eio((u - 2) / (t1 - 6)), u, mh, mx, my, cols)
            v = u - t1; z = 1 + 0.2 * (1 - eo(v / 14, 4)) + 0.03 * v / max(n - t1, 1); img = self.bg(bg, v, n - t1, f)
            s = z if style == "trace" else float(spring(v / self.fps * 1.6, 1.6, 5.0))
            if style == "trace": img = jb.impact(jb.shake(img, v), v, mx, my, cols)
            dm = jb.dmask(C, mh * max(s, 0.01), mx, my); a = dm[..., None]
            img = img * (1 - 0.2 * cv2.GaussianBlur(dm, (0, 0), 20 * self.U + 1)[..., None]); img = img * (1 - a) + jb.WHITE * a
            img = img + cv2.GaussianBlur(dm, (0, 0), 36 * self.U + 1)[..., None] * 255 * (0.05 + 0.6 * np.exp(-v / 10)) + (255 * np.exp(-v / 4.5) if style == "trace" else 0)
            if L: jb.put_letters(img, L, v - 14, max(1, min(4, int((n - t1 - 40) / max(len(L), 1)))))
            if sub: self.block(img, [sub], my + mh * 0.5 + 215 * self.U, 38, False, 0.9 * eio((v - 40) / 16), track=6)
            return img
        return self._add(draw, dur, tr=k.pop("tr", "cut" if style == "trace" else None), kind="logo", meta=dict(style=style, letters=len(L)), **k)
    def _mark(self, path):
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if im is None: raise FileNotFoundError(path)
        if im.ndim == 3 and im.shape[2] == 4 and im[..., 3].min() < 200: msk = im[..., 3]
        else:
            g = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im; edge = np.r_[g[0], g[-1], g[:, 0], g[:, -1]].mean(); msk = 255 - g if edge > 127 else g
        return jb.mark_contours((msk > 110).astype(np.float32))
    def _lockup(self, img, C, u, cy, mh):
        """Logo springing in at (centre, cy)."""
        dm = jb.dmask(C, mh * max(float(spring(u / self.fps * 1.6, 1.6, 5.0)), 0.01), self.W / 2, cy); a = dm[..., None]
        img = img * (1 - 0.2 * cv2.GaussianBlur(dm, (0, 0), 20 * self.U + 1)[..., None]); img = img * (1 - a) + jb.WHITE * a
        return img + cv2.GaussianBlur(dm, (0, 0), 36 * self.U + 1)[..., None] * 255 * (0.05 + 0.4 * np.exp(-u / 10))
    def intro(self, title, sub=None, logo=None, bg=None, dur=3.0, move="push", y=None, **k):
        """Opening card. Every video starts with one: the name or hook, an optional line, and the logo if there is one."""
        C = self._mark(logo) if logo else None; lines = title.split("\n"); size = 150 if max(len(l) for l in lines) <= 10 else 104
        def draw(u, n, f):
            img = self.bg(bg, u, n, f, move); o = 1 - eio((u - (n - 6)) / 6); mh_ = min(self.W, self.H) * 0.20; ly = self.H * (0.32 if self.H >= self.W * 1.2 else 0.25)
            cy = max(self.H * 0.56, ly + mh_ / 2 + 40 * self.U + min(len(lines) * size * self.U * 1.18, self.H * 0.42) / 2) if C is not None else self.H * 0.46
            if y: cy = self.H * y; ly = min(ly, cy - min(len(lines) * size * self.U * 1.18, self.H * 0.42) / 2 - mh_ / 2 - 40 * self.U)
            if C is not None: img = self._lockup(img, C, u, ly, mh_)
            d = 10 if C is not None else 0; sc = 1 + 0.3 * (1 - eo((u - d) / 9, 4)) + 0.03 * u / n
            hh = self.block(img, lines, cy, size, True, clamp((u - d) / 3) * o, scale=sc)
            if sub: self.block(img, self.wrap(sub, 46), cy + hh + 70 * self.U, 46, False, maxh=self.H * 0.14, op=eio((u - d - 10) / 10) * o)
            return img + 110 * np.exp(-max(u - d, 0) / 2.0) * (u >= d)
        return self._add(draw, dur, kind="intro", **k)
    def outro(self, text, sub=None, logo=None, bg=None, dur=3.5, y=None, **k):
        """Closing card. Every video ends with one: the logo if there is one, the closing words letter by letter, an optional line, fade out."""
        C = self._mark(logo) if logo else None; cy = self.H * (y or (0.58 if C is not None else 0.46))
        L = self.L(text, 80, 18, cy)
        def draw(u, n, f):
            img = self.bg(bg, u, n, f)
            if C is not None: img = self._lockup(img, C, u, cy - self.H * 0.22, min(self.W, self.H) * 0.24)
            jb.put_letters(img, L, u - (14 if C is not None else 4), max(1, min(3, int((n - 50) / max(len(L), 1)))), self.ink, 0.4 if themes.lum(self.ink) > 120 else 0)
            if sub: self.block(img, self.wrap(sub, 44), cy + 120 * self.U, 44, False, eio((u - 30) / 14))
            return img
        return self._add(draw, dur, kind="outro", meta=dict(letters=len(L), delay=14 if C is not None else 4), **k)
    def end(self, text, sub=None, bg=None, dur=3.0, **k):
        """Closing card: letters arrive one at a time, optional small line, fade out."""
        L = self.L(text, 88, 18, self.H * 0.46)
        def draw(u, n, f):
            img = self.bg(bg, u, n, f); jb.put_letters(img, L, u - 4, max(1, min(3, int((n - 40) / max(len(L), 1)))), self.ink, 0.4 if themes.lum(self.ink) > 120 else 0)
            if sub: self.block(img, self.wrap(sub, 44), self.H * 0.46 + 130 * self.U, 44, False, eio((u - 24) / 14))
            return img
        return self._add(draw, dur, kind="end", meta=dict(letters=len(L), delay=4), **k)
    # ----- reel scenes: logo-led, fast, graphic -----
    def _cover(self, path, f=0, z=1.06):
        im = jb.art(path); return jb.cam(im, max(1.0, self.H * im.shape[1] / (self.W * im.shape[0])) * z, 0.5, 0.5, f, wob=0)
    def window(self, mark, images, dur=5.0, **k):
        """The logo as a window: its outline lands on black, the images play through its shape on the beat,
        then it blows open into the full picture and the white logo springs back in."""
        C = self._mark(mark); cx, cy, mh = self.W / 2, self.H * 0.45, min(self.W, self.H) * 0.5
        def draw(u, n, f):
            t = u / n; img = self._cover(images[(u // self.beat) % len(images)], f)
            if t < 0.16: return jb.dmask(C, mh * (1 + 0.8 * (1 - eo(t / 0.16, 4))), cx, cy, stroke=5 * self.U)[..., None] * jb.WHITE * clamp(u / 3)
            s_ = 1.0 if t < 0.55 else 1 + 60 * ei((t - 0.55) / 0.22, 3)
            m = jb.dmask(C, mh * s_, cx, cy) if s_ < 40 else np.ones((self.H, self.W), np.float32); out = img * m[..., None]
            if t < 0.55: out += jb.dmask(C, mh, cx, cy, stroke=4 * self.U)[..., None] * 255 * 0.9
            v = u - int(n * 0.8)
            if v >= 0:
                dm = jb.dmask(C, mh * 0.62 * max(float(spring(v / self.fps * 1.6, 1.6, 5.0)), 0.01), cx, cy)[..., None]
                out = out * (1 - 0.25 * cv2.GaussianBlur(dm[..., 0], (0, 0), 22 * self.U + 1)[..., None]); out = out * (1 - dm) + jb.WHITE * dm + 200 * np.exp(-v / 3.0)
            return out
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="window", **k)
    def slices(self, images, count=6, dur=4.0, **k):
        """Vertical strips, each from a different image, slide in from top and bottom; the images march across the strips on the beat."""
        def draw(u, n, f):
            W, H = self.W, self.H; img = np.zeros((H, W, 3), np.float32); sw = W / count; shift = u // self.beat; cache = {}
            for i in range(count):
                j = (i + shift) % len(images)
                if j not in cache: cache[j] = self._cover(images[j], f)
                dy = int((1 - eo((u - i * 2) / 12, 3)) * H * (1 if i % 2 else -1) + ei((u - (n - 12) - i) / 10, 3) * H * (-1 if i % 2 else 1))
                xa, xb = int(i * sw), int((i + 1) * sw); col_ = np.roll(cache[j][:, xa:xb], dy, 0)
                if dy > 0: col_[:dy] = 0
                elif dy < 0: col_[dy:] = 0
                img[:, xa:xb] = col_
                if i: img[:, xa:xa + max(1, int(3 * self.U))] *= 0.25
            return img + 70 * np.exp(-(u % self.beat) / 2.0) * (u > 12)
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="slices", meta=dict(count=count), **k)
    def carousel(self, items, dur=4.0, **k):
        """Cards snap past one per beat with motion blur; the last one opens up to fill the frame.
        items = image paths, or react-icons names (drawn as coloured app-icon tiles)."""
        self._icons([it for it in items if not os.path.exists(it)]); S = int(min(self.W, self.H) * 0.5); gap = int(S * 1.25)
        def card(i, f):
            it = items[i]
            if os.path.exists(it): im = jb.art(it); k_ = S / min(im.shape[:2]); im = cv2.resize(im, (int(im.shape[1] * k_) + 1, int(im.shape[0] * k_) + 1)); y0, x0 = (im.shape[0] - S) // 2, (im.shape[1] - S) // 2; return im[y0:y0 + S, x0:x0 + S].astype(np.float32)
            c = np.full((S, S, 3), self._c(i), np.float32); m = cv2.resize(self.icon(it), (int(S * 0.56),) * 2, interpolation=cv2.INTER_AREA)[..., None]; o = (S - m.shape[0]) // 2
            c[o:o + m.shape[0], o:o + m.shape[0]] = c[o:o + m.shape[0], o:o + m.shape[0]] * (1 - m) + jb.WHITE * m; return c
        rm = np.zeros((S, S), np.float32); r_ = int(S * 0.2); cv2.rectangle(rm, (r_, 0), (S - r_, S), 1, -1); cv2.rectangle(rm, (0, r_), (S, S - r_), 1, -1)
        for px, py in ((r_, r_), (S - r_, r_), (r_, S - r_), (S - r_, S - r_)): cv2.circle(rm, (px, py), r_, 1, -1, cv2.LINE_AA)
        def draw(u, n, f):
            W, H = self.W, self.H; img = self.bg(None, u, n, f); nI = len(items); step = min(u // self.beat, nI - 1); v = u - step * self.beat
            pos = min(step - 1 + eo(v / (self.beat * 0.6), 4), nI - 1) if step else 0.0; vel = abs((1 - eo(v / (self.beat * 0.6), 4)) * 3) if step else 0
            for i in range(nI):
                x = int(W / 2 + (i - pos) * gap - S / 2); y = int(H * 0.46 - S / 2)
                if x >= W or x + S <= 0: continue
                xa, xb = max(x, 0), min(x + S, W); a = rm[:, xa - x:xb - x, None]; img[y:y + S, xa:xb] = img[y:y + S, xa:xb] * (1 - a) + card(i, f)[:, xa - x:xb - x] * a
            if vel > 0.15: img = cv2.blur(img, (int(vel * 60 * self.U) | 1, 1))
            z = u - (nI * self.beat + 4)
            if z > 0:
                kz = 1 + ei(z / max(n - nI * self.beat - 4, 1), 2) * (max(W, H) / S * 1.6); img = cv2.warpAffine(img, np.float32([[kz, 0, W / 2 * (1 - kz)], [0, kz, H * 0.46 * (1 - kz)]]), (W, H), flags=cv2.INTER_LINEAR)
            return img
        return self._add(draw, max(dur, (len(items) + 2) * self.beat / self.fps), kind="carousel", meta=dict(count=len(items)), **k)
    def grid(self, mark, dur=4.0, **k):
        """A wall of small logos; colour patterns ripple out from the centre on each beat, with zoom and tilt punches."""
        C = self._mark(mark); W, H = self.W, self.H; cols = 6 if W <= H else 10; ts = W // cols; rows = H // ts + 2
        tile = jb.dmask(C, ts * 0.62, W / 2, H / 2)[H // 2 - ts // 2:H // 2 - ts // 2 + ts, W // 2 - ts // 2:W // 2 - ts // 2 + ts]; wall = np.tile(tile, (rows, cols + 1))[:H, :W, None]
        ry, rx = np.mgrid[0:rows, 0:cols + 1]; dist = np.hypot(ry - (H / ts) / 2 + 0.5, rx - cols / 2 + 0.5); pal = np.stack(self.pal[1:] or self.pal); one = np.ones((ts, ts, 1), np.float32)
        def draw(u, n, f):
            b = u // self.beat; v = u % self.beat; idx = (np.floor(dist * (0.6 + 0.3 * (b % 3))) - b).astype(int) % len(pal)
            lit = np.clip((u / 4 - dist * 0.6), 0, 1)[..., None]; tc = np.kron(pal[idx] * lit, one)[:H, :W]; bgc = np.kron(pal[(idx + 2) % len(pal)] * 0.16 * lit, one)[:H, :W]; img = bgc * (1 - wall) + tc * wall
            z = 1.0 + 0.10 * np.exp(-v / 3.0) + 2.4 * ei((u - (n - 16)) / 16, 3); ang = (2.5 if b % 2 else -2.5) * np.exp(-v / 4.0)
            return cv2.warpAffine(img.astype(np.float32), cv2.getRotationMatrix2D((W / 2, H / 2), ang, z), (W, H), borderMode=cv2.BORDER_REFLECT_101)
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="grid", **k)
    def tunnel(self, mark, dur=4.0, **k):
        """Nested logo shapes in the palette colours rush outward like a tunnel, twisting and stepping on the beat."""
        C = self._mark(mark); pal = self.pal[1:] or self.pal
        def draw(u, n, f):
            W, H = self.W, self.H; img = np.zeros((H, W, 3), np.float32); ph = eo((u / self.beat) % 1, 2); base = min(W, H) * 0.10; b = u // self.beat
            for j in range(11, -1, -1):
                m = jb.dmask(C, base * 1.42 ** (j + ph), W / 2, H * 0.48, rot=0.10 * (j + ph) * np.sin(u * 0.03))[..., None]; img = img * (1 - m) + pal[(j - b) % len(pal)] * m * (0.55 + 0.45 * (j % 2))
            m = jb.dmask(C, base * 0.9, W / 2, H * 0.48)[..., None]; img = img * (1 - m) + jb.WHITE * m
            return (255 - img if (b % 4 == 3 and u % self.beat < 2) else img)
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="tunnel", **k)
    def loader(self, label="LOADING", done="READY", mark=None, dur=4.0, **k):
        """A glitchy loading screen: progress bar and percentage climbing to 100, equaliser bars, scan lines, colour split,
        then the closing word typed out with a cursor."""
        C = self._mark(mark) if mark else None
        def draw(u, n, f):
            W, H, U = self.W, self.H, self.U; img = np.full((H, W, 3), (16, 11, 10), np.float32); p = eio(u / (n * 0.68)); r = np.random.default_rng(u // 3)
            if C is not None: img += jb.dmask(C, min(W, H) * 0.26, W / 2, H * 0.30)[..., None] * 235
            x0, x1, y = int(W * 0.14), int(W * 0.86), int(H * 0.56); cv2.rectangle(img, (x0, y), (x1, y + int(16 * U)), (60, 52, 50), -1); cv2.rectangle(img, (x0, y), (int(x0 + (x1 - x0) * p), y + int(16 * U)), tuple(float(q) for q in self._c(0)), -1)
            self.ltext(img, f"{int(p * 100)}%", x1, y - 46 * U, 54, True, 1.0, align="right"); self.ltext(img, label if p < 1 else "", x0, y - 46 * U, 30, False, 0.75)
            for i in range(14):
                hh = (0.25 + 0.75 * r.random()) * H * 0.08 * (0.4 + 0.6 * (1 - p)); xa = int(x0 + (x1 - x0) * i / 14); cv2.rectangle(img, (xa, int(H * 0.70 - hh)), (xa + int((x1 - x0) / 14 * 0.6), int(H * 0.70)), tuple(float(q) * 0.8 for q in self._c(1)), -1)
            if p >= 1:
                v = u - int(n * 0.68); self.block(img, [done[:int(v / 2.2)] + ("_" if (v // 6) % 2 == 0 else " ")], H * 0.82, 84, True, 1.0, shadow=0, track=10)
            img = jb.scanlines(jb.chroma(img, 3 + 5 * (1 - p)), 0.22)
            return jb.glitch(img, f, 0.7) if (u % (self.beat * 4) < 3 and p < 1) else img
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="loader", meta=dict(done=len(done)), **k)
    def lockcut(self, images, per=3, mark_h=0.19, dur=4.0, **k):
        """Fast-cut reel where the logo never moves: every image must contain the same white logo; each is scaled and
        placed so the logo is the same size in the same spot, then they cut every `per` frames."""
        cx, cy, mh = self.W / 2, self.H * 0.42, self.H * mark_h; cache = {}
        def placed(i):
            if i not in cache:
                im = jb.art(images[i]); box = jb.detect_mark(im)
                if box is None: sys.exit(f"joyboy: no white logo found in {images[i]}")
                cache[i] = jb.lock(im, box, mh, cx, cy).astype(np.float32)
            return cache[i]
        def draw(u, n, f): return placed((u // per) % len(images)) + 60 * np.exp(-(u % per) / 1.2)
        return self._add(draw, dur, tr=k.pop("tr", "cut"), kind="lockcut", meta=dict(per=per), **k)
    def custom(self, fn, dur, **k):
        """Anything else: fn(u, n, f) returns a float32 BGR frame (H, W, 3) built with joyboy.py helpers."""
        return self._add(fn, dur, kind="custom", **k)

    # ---------- frames ----------
    def _layout(self):
        s = 0
        for sc in self.scenes: sc["start"] = s; s += sc["n"]
        self.total = s
    safe = property(lambda self: (int(self.W * 0.06), int(self.H * (0.14 if self.H >= self.W * 1.5 else 0.06)), int(self.W * (0.88 if self.H >= self.W * 1.5 else 0.94)), int(self.H * (0.78 if self.H >= self.W * 1.5 else 0.94))))   # (x0, y0, x1, y1) in px: keep words inside; Reels, TikTok and Shorts cover the top 14%, the bottom 22% and the right edge with their own buttons
    def frame(self, f):
        if not self.mblur: return self._frame1(f)
        a, b, c = self._frame1(max(f - 1, 0)).astype(np.float32), self._frame1(f).astype(np.float32), self._frame1(min(f + 1, self.total - 1)).astype(np.float32)   # a 3-tap shutter: fast movement smears like film
        return np.clip(0.25 * a + 0.5 * b + 0.25 * c, 0, 255).astype(np.uint8)
    def _frame1(self, f):
        i = max(j for j, sc in enumerate(self.scenes) if sc["start"] <= f); sc = self.scenes[i]; u = f - sc["start"]; n = sc["n"]
        img = np.asarray(sc["draw"](u, n, f), np.float32); tr = sc["tr"] if i else "cut"; W, H = self.W, self.H
        if sc["note"]:   # small footnote pill, e.g. "sample data"
            wn = self._len(sc["note"], 26, False) + 44 * self.U; y_ = H - 70 * self.U; img = img.copy()
            cv2.rectangle(img, (int(W / 2 - wn / 2), int(y_ - 24 * self.U)), (int(W / 2 + wn / 2), int(y_ + 24 * self.U)), (30, 28, 28), -1, cv2.LINE_AA); self.ltext(img, sc["note"], W / 2, y_, 26, False, 0.9, jb.WHITE, align="center", maxw=W * 0.8)
        if i and tr != "cut":
            pv = self.scenes[i - 1]; prev = lambda: np.asarray(pv["draw"](pv["n"] - 1, pv["n"], f), np.float32)
            if tr == "fade" and u < 10: a = eio((u + 1) / 11); img = prev() * (1 - a) + img * a
            elif tr == "whip" and u < 5: img = jb.whip(prev(), img, (u + 0.5) / 5)
            elif tr == "wipe" and u < 12:
                m = np.clip(((u + 1) / 12 * 1.3 - (jb.xx / W * 0.6 + jb.yy / H * 0.4)) * 8, 0, 1)[..., None]; img = prev() * (1 - m) + img * m
            elif tr == "zoom" and u < 10:
                z = 1 + 0.4 * (1 - eo(u / 10, 4)); img = cv2.warpAffine(img, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H), borderMode=cv2.BORDER_REFLECT_101) + 110 * np.exp(-u / 2.0)
            elif tr in ("iris", "bars", "doors", "pie") and u < 12: img = jb.wipe(prev(), img, eio((u + 1) / 12), tr)
            elif tr == "glitch" and u < 4: img = jb.glitch(img if u > 1 else prev(), f, 0.8)
            elif tr == "white": img = img + 255 * (1 - eo(u / 16, 2))
        if i + 1 < len(self.scenes) and self.scenes[i + 1]["tr"] == "white" and sc["kind"] != "crt": img = img + 255 * ei((u - (n - 8)) / 8, 2)
        fn = self.fin; img = jb.post(img, f, bloom=self.bloom, grain=0 if self.ffgrain else fn["grain"], vignette=fn["vignette"], tint=fn["tint"], fringe=fn["fringe"], contrast=fn["contrast"], streak=fn["streak"], warmth=fn["warmth"], sat=fn["sat"])
        if self.grade: img = self.grade(img, f, self.U, self.fps) if callable(self.grade) else kinds.apply_grade(img, self.grade)
        if self.fx: img = self.fx(img, f, self.U, self.fps) if callable(self.fx) else kinds.apply_fx(img, self.fx, f, self.U, self.fps)
        if f < 6 and not self.exact: img = img * eio((f + 1) / 7)
        if f > self.total - 14 and not self.exact: img = img * (1 - eio((f - (self.total - 14)) / 12))
        return np.clip(img, 0, 255).astype(np.uint8)

    # ---------- audio ----------
    def _score(self, path):
        s = Score(self.total, self.fps); b = self.beat; t = s.t; bars = range(0, self.total, 4 * b); mood = self.mood; nb = len(bars)
        if self.music_file:
            tmp = path + ".m.wav"; subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", self.music_file, "-t", str(self.total / self.fps + 1), "-ar", str(s.sr), "-ac", "2", tmp], check=True)
            w = wave.open(tmp); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768; w.close(); os.remove(tmp)
            s.dry[:min(len(x), s.N)] += x[:s.N] * 0.8
        elif self.genre:
            self.music_info = genres.compose(s, b, self.genre, self.music_seed, self.energy, self.key)
            if self.air: s.wind(0, self.total, 0.05)
        elif mood != "none":
            # Each video gets its own music: the seed picks the chord set, where the loop starts, the key and one of three
            # arrangements per mood. The same seed (by default made from the film's name) always gives the same music.
            sd = self.music_seed; var = sd % 3; rot = (sd // 3) % 4; pset = (sd // 12) % 3; E = self.energy
            tr_ = self.key if self.key is not None else ((sd // 36) % 5) - 2; T = lambda ch: tuple(m + tr_ for m in ch)
            if mood == "cinematic":
                P = [[(50, 57, 62, 65), (46, 53, 58, 62), (41, 53, 57, 60), (48, 55, 60, 64)], [(45, 52, 57, 60), (41, 48, 53, 57), (48, 55, 60, 64), (43, 50, 55, 59)], [(47, 54, 59, 62), (43, 50, 55, 59), (50, 57, 62, 66), (45, 52, 57, 61)]][pset]
                for k, f0 in enumerate(bars):
                    ch = T(P[(k + rot) % 4]); d = t(4 * b) + 0.9; lv = min(1, 0.5 + 0.15 * k) * E
                    s.add(s.dry, s.sub(ch[0], t(4 * b) + 0.2, 0.2, 0.4), t(f0), g=0.4 * lv)
                    if var == 0:                                   # strings and piano
                        s.add(s.wet, s.strings(ch, d, 0.8, 0.9, 1100 + 250 * min(k, 6)), t(f0) - 0.2, g=0.11 * lv)
                        for e in range(4): s.add(s.wet, s.piano(ch[(1, 2, 3, 2)[e]] + 12, 3), t(f0 + e * b), pan=0.2 * np.sin(e), g=0.13)
                    elif var == 1:                                 # choir and slow low piano
                        s.add(s.wet, s.choir(ch, d, 1.0, 1.4), t(f0) - 0.2, g=0.10 * lv)
                        for e in (0, 2): s.add(s.wet, s.piano(ch[1 + e // 2], 4), t(f0 + e * b), pan=-0.15 + 0.15 * e, g=0.17)
                    else:                                          # low strings with a pulsing figure on top
                        s.add(s.wet, s.strings(ch, d, 0.8, 0.9, 900), t(f0) - 0.2, g=0.07 * lv)
                        for e in range(8): s.add(s.wet, s.strings([ch[(0, 2, 1, 2, 3, 2, 1, 2)[e]] + 12], 0.2, 0.01, 0.12, 2600), t(f0 + e * b / 2), pan=0.3 * np.sin(e * 1.3), g=0.075 * lv)
            elif mood == "calm":
                P = [[(53, 57, 60, 64), (52, 55, 59, 62), (50, 53, 57, 60), (48, 52, 55, 59)], [(48, 55, 60, 64), (45, 52, 57, 60), (41, 48, 53, 57), (43, 50, 55, 59)], [(50, 57, 62, 66), (47, 54, 59, 62), (43, 50, 55, 59), (45, 52, 57, 61)]][pset]
                for k, f0 in enumerate(bars):
                    ch = T(P[(k + rot) % 4]); s.add(s.dry, s.sub(ch[0], t(4 * b), 0.05, 0.8), t(f0), g=0.3 * E)
                    if var == 0:                                   # electric piano chords with bells
                        for j_, m in enumerate(ch): s.add(s.wet, s.keys(m), t(f0) + j_ * 0.045, pan=-0.3 + 0.2 * j_, g=0.09 * E)
                        for e, m in ((0, ch[3] + 12), (1.5, ch[2] + 12), (2.5, ch[1] + 12)): s.add(s.wet, s.bell(m), t(f0 + e * b), pan=0.3 * np.sin(e + k), g=0.10 * E)
                    elif var == 1:                                 # piano arpeggio over soft strings
                        s.add(s.wet, s.strings(ch, t(4 * b) + 0.8, 1.0, 1.0, 1200), t(f0) - 0.2, g=0.05 * E)
                        for e in range(4): s.add(s.wet, s.piano(ch[(0, 2, 3, 1)[e]] + 12, 3.2), t(f0 + e * b), pan=0.25 * np.sin(e * 1.4 + k), g=0.14 * E)
                    else:                                          # music-box melody over a quiet choir
                        s.add(s.wet, s.choir(ch, t(4 * b) + 0.8, 1.2, 1.4), t(f0) - 0.2, g=0.05 * E)
                        for e, m in ((0, ch[2] + 12), (1, ch[3] + 12), (2, ch[1] + 12), (3, ch[2] + 12), (3.5, ch[3] + 12)): s.add(s.wet, s.bell(m), t(f0 + e * b), pan=0.3 * np.sin(e * 0.9 + k), g=0.11 * E)
                if self.air: s.wind(0, self.total, 0.06)
            else:                                                  # upbeat, tech, hype
                P = ([[(48, 55, 60, 64), (43, 55, 59, 62), (45, 57, 60, 64), (41, 53, 57, 60)], [(50, 57, 62, 66), (45, 57, 61, 64), (47, 59, 62, 66), (43, 55, 59, 62)], [(53, 60, 65, 69), (48, 60, 64, 67), (50, 62, 65, 69), (46, 58, 62, 65)]] if mood == "upbeat" else
                     [[(45, 52, 57, 60), (41, 53, 57, 60), (48, 55, 60, 64), (43, 55, 59, 62)], [(47, 54, 59, 62), (43, 55, 59, 62), (50, 57, 62, 66), (45, 57, 61, 64)], [(40, 52, 55, 59), (48, 55, 60, 64), (43, 55, 59, 62), (50, 57, 62, 66)]])[pset]
                div = 4 if mood == "tech" else 2; pat = [(1, 2, 3, 2, 1, 3, 2, 3), (1, 3, 2, 3, 1, 2, 3, 2), (3, 2, 1, 2, 3, 1, 2, 1)][var]
                for k, f0 in enumerate(bars):
                    ch = T(P[(k + rot) % 4]); drums = 0 < k < nb - 1 or nb < 3
                    s.add(s.wet, s.strings(ch, t(4 * b) + 0.3, 0.1, 0.4, 1600), t(f0), g=0.06)
                    for e in range(4 * div):
                        m = ch[pat[e % 8]] + 12; gg = 0.075 * (1.2 if e % div == 0 else 0.85) * E; pn = 0.4 * np.sin(e * 1.7)
                        if var == 1: s.add(s.wet, s.bell(m), t(f0 + e * b / div), pan=pn, g=gg * 1.25)             # plucked lead
                        else: s.add(s.wet, s.strings([m + (12 if var == 2 and e % 4 == 3 else 0)], 0.16, 0.005, 0.1, 3400), t(f0 + e * b / div), pan=pn, g=gg)
                    for e in ((0, 1, 2, 3, 4, 5, 6, 7) if var != 2 else (0, 1.5, 3, 4, 5.5, 7)): s.add(s.dry, s.sub(ch[0], 0.2, 0.005, 0.08), t(f0 + e * b / 2), g=(0.36 if drums else 0.2) * E)
                    if drums:
                        for e in range(4):
                            kick = (mood != "tech" or e % 2 == 0) if var == 0 else (e % 2 == 0) if var == 1 else True
                            if kick: s.add(s.dry, s.kick(), t(f0 + e * b), g=0.8 * E)
                            if e % 2: s.add(s.wet, s.snare(), t(f0 + e * b), pan=0.1, g=0.32 * E)
                        if var == 2: s.add(s.dry, s.kick(), t(f0 + 2.5 * b), g=0.6 * E)
                        for e in range(8): s.add(s.dry, s.hat(), t(f0 + e * b / 2), pan=-0.3, g=(0.10 if e % 2 else 0.06) * E * (1.3 if var == 1 and e % 2 else 1))
        fxg = self.sfx                                   # level of the automatic sounds (0 = none)
        acc = genres.GENRES[self.genre]["cut"] if self.genre else {"cinematic": "boom", "calm": "none"}.get(mood, "crash")   # how cuts are accented
        for i, sc in enumerate(self.scenes):           # accents on cuts
            if i == 0 or mood == "none" or self.music_file or fxg <= 0: continue
            if sc["tr"] in ("whip", "zoom", "wipe") and "whoosh" not in self.mute and acc != "none": s.add(s.wet, s.whoosh(), t(sc["start"]) - 0.22, g=0.4 * fxg)
            if acc == "boom" and "hit" not in self.mute:
                big = sc["kind"] in ("logo", "end", "outro") or i == len(self.scenes) - 1
                s.add(s.dry, s.boom() if big else s.taiko(), t(sc["start"]), g=(0.8 if big else 0.7) * fxg); s.add(s.wet, s.crash(3 if big else 1.6, 1.2 if big else 4), t(sc["start"]), g=(0.16 if big else 0.06) * fxg)
            elif acc == "crash" and "hit" not in self.mute: s.add(s.wet, s.crash(1.4, 4), t(sc["start"]), g=0.10 * fxg)
            if sc["kind"] == "logo" and sc["tr"] == "cut" and acc in ("boom", "crash") and "hit" not in self.mute:   # trace then hit
                hit = sc["start"] + int(sc["n"] * 0.42); s.add(s.wet, s.reverse_crash(1.5), t(hit) - 1.5, g=0.18 * fxg); s.add(s.dry, s.boom(), t(hit), g=0.9 * fxg); s.add(s.wet, s.crash(3.5, 1.1), t(hit), g=0.2 * fxg)
        for sc in self.scenes:                          # sounds that match what each scene shows
            for off, name, g, d, pt in self._cues(sc):
                if fxg > 0 and name not in self.mute and 0 <= off < sc["n"] + self.fps: s.add(s.wet, s.fx(name, d, pt), t(sc["start"] + off), pan=float(np.sin(off * 0.7)) * 0.3, g=g * fxg)
        duck = np.ones(s.N); voices = []
        for sc in self.scenes:
            if sc["voice"]:
                w = wave.open(sc["voice"][0]); v = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768; w.close(); a = int((t(sc["start"]) + sc["voice_at"]) * s.sr)
                duck[max(a - 4000, 0):a + len(v) + 8000] = 0.32; voices.append((v / max(np.abs(v).max(), 1e-6), t(sc["start"]) + sc["voice_at"]))
        if voices: k = np.ones(6000) / 6000; duck = np.convolve(duck, k, "same")[:, None]; s.wet *= duck; s.dry *= duck
        else: duck = np.ones((s.N, 1))
        for fn in self.layers: fn(s, duck)              # extra sound layers (ambience ...): music and effects are in place, voices are not yet
        for v, tt in voices: s.add(s.dry, v, tt, g=1.0 if (mood != "none" or self.music_file) else 0.8)
        s.write(path, fade_out=min(2.0, self.total / self.fps / 4), sections=[(sc["start"], sc["start"] + sc["n"]) for sc in self.scenes])

    def _cues(self, sc):
        """(frame offset, sound, gain, duration, pitch) for a scene, derived from what it animates. Extra cues can be
        passed to any scene as sfx=[(seconds, "pop"), (seconds, "scribble", duration), ...]."""
        k, n, m, fps = sc["kind"], sc["n"], sc["meta"], self.fps; C = []
        if k in ("title", "intro"): C.append((0 if k == "title" else 2, "thud", 0.5, None, 1))
        elif k == "words": C += [(i * m["seg"], "thud", 0.55, None, 1) for i in range(m["count"])]
        elif k == "stat": C += [(n * 0.55 * (j / 16) ** 1.7, "tick", 0.22, None, 1 + j * 0.02) for j in range(1, 16)] + [(n * 0.55, "ding", 0.28, None, 1)]
        elif k == "icons": C += [(8 + i * 6, "pop", 0.3, None, 1 + 0.07 * i) for i in range(m["count"])]
        elif k == "bullets": st = max(8, int(n * 0.6 / max(m["count"], 1))); C += [(10 + i * st, "pop", 0.3, None, 1 + 0.08 * i) for i in range(m["count"])]
        elif k in ("bars", "columns"): C += [(8 + i * 4, "rise", 0.16, n * 0.4 / fps * 0.8, 1 + 0.12 * i) for i in range(m["count"])] + [(8 + (m["count"] - 1) * 4 + n * 0.4 * 0.8, "pop", 0.25, None, 1.2)]
        elif k == "line": C += [(8, "scribble", 0.22, n * 0.5 / fps, 1), (8 + n * 0.5, "pop", 0.25, None, 1.3)]
        elif k == "donut": C += [(6, "sweep", 0.28, n * 0.45 / fps, 1), (6 + n * 0.45, "pop", 0.22, None, 1.2)]
        elif k == "heatmap": C += [(6 + d * 1.4, "blip", 0.13, None, 1 + 0.06 * d) for d in range(m["count"])]
        elif k == "map": C += ([(10, "scribble", 0.2, n * 0.55 / fps, 1)] if m["route"] else []) + [(12 + i * 10 + 5, "pop", 0.34, None, 0.9 + 0.1 * i) for i in range(m["pins"])]
        elif k in ("phone", "browser"): C.append((0, "whoosh", 0.35, 0.55, 1))
        elif k == "window": C += [(0, "thud", 0.5, None, 1), (n * 0.55, "sweep", 0.4, n * 0.22 / fps, 1), (n * 0.8, "thud", 0.6, None, 0.9)]
        elif k == "slices": C += [(i * 2, "whoosh", 0.22, 0.35, 1) for i in range(m["count"])] + [(n - 12, "whoosh", 0.3, 0.5, 1)]
        elif k == "carousel": C += [(i * self.beat, "whoosh", 0.3, 0.3, 1) for i in range(1, m["count"])] + [(m["count"] * self.beat + 4, "sweep", 0.35, 0.8, 1)]
        elif k == "grid": C += [(i * self.beat, "blip", 0.2, None, 1 + 0.1 * (i % 5)) for i in range(n // self.beat)] + [(n - 16, "sweep", 0.35, 0.6, 1)]
        elif k == "tunnel": C += [(i * self.beat, "rise", 0.14, self.beat / fps, 1 + 0.08 * (i % 4)) for i in range(n // self.beat)]
        elif k == "loader": C += [(n * 0.68 * (j / 20), "tick", 0.16, None, 1 + j * 0.02) for j in range(1, 20)] + [(n * 0.68, "ding", 0.3, None, 1)] + [(n * 0.68 + j * 2.2, "click", 0.16, None, 1) for j in range(m["done"])]
        elif k == "lockcut": C += [(i * m["per"], "tick", 0.14, None, 1) for i in range(n // m["per"])]
        elif k == "crt":
            t0 = 8
            for l in m["lines"]:
                C += [(t0 + i * 1.4, "click", 0.16, None, 1) for i, ch in enumerate(l) if ch != " "]; t0 += int(len(l) * 1.4) + 8
        elif k == "logo":
            t1 = int(n * 0.42) if m["style"] == "trace" else 0
            if t1: C.append((2, "shimmer", 0.3, t1 / fps, 1))
            else: C.append((0, "pop", 0.4, None, 0.8))
            C += [(t1 + 14 + j * 3, "tick", 0.10, None, 1) for j in range(m["letters"])]
        elif k in ("outro", "end"): C += [(m["delay"] + j * 2, "tick", 0.10, None, 1) for j in range(m["letters"])]
        C += kinds.cues(self, sc)
        for c in sc["sfx"]: C.append((c[0] * fps, c[1], 0.3, c[2] if len(c) > 2 else None, 1))
        return C
    def _write_script(self):
        """Write script.md beside film.py: the shot list with times, on-screen words, narration and files used.
        Rewritten on every render so it always matches the video. Anything under '## Notes' is kept."""
        def words(v):
            if isinstance(v, str): return [] if (os.path.exists(v) or v.startswith(("http", "#", "/")) or len(v) > 400) else [v.replace("\n", " / ")]
            if isinstance(v, dict): return [str(x) for x in v.keys() if isinstance(x, str)]
            if isinstance(v, (list, tuple)): return [w for x in v for w in words(x)]
            return []
        def files(v):
            if isinstance(v, str): return [v] if (os.path.exists(v) or v.startswith("http")) else []
            if isinstance(v, (list, tuple)): return [w for x in v for w in files(x)]
            return []
        notes = "- Brief, concept and decisions for this video go here (kept between renders).\n"
        if os.path.exists("script.md"):
            old = open("script.md").read()
            if "## Notes" in old: notes = old.split("## Notes", 1)[1].lstrip("\n") or notes
        mm = lambda fr: "%d:%04.1f" % (fr / self.fps // 60, fr / self.fps % 60)
        L = [f"# {self.name}: script", "", f"- Video: `{os.path.relpath(self.out)}`", f"- Length {self.total / self.fps:.1f} s, {self.W}x{self.H}, {self.fps} fps, mood `{self.mood}`, language `{self.lang}`" + (", own music" if self.music_file else ""),
             "- Made by `film.py`; this file is rewritten on every render.", "", "## Shot list", "", "| # | Time | Scene | On screen | Narration | In |", "|---|---|---|---|---|---|"]
        used = []
        for i, sc in enumerate(self.scenes):
            name, a, k = sc.get("call", (sc["kind"], (), {})); txt = [w for v in list(a) + [k.get(x) for x in ("text", "sub", "title", "label", "by", "done", "url")] for w in words(v)]
            used += [w for v in list(a) + list(k.values()) for w in files(v)]
            cell = lambda x: str(x).replace("|", "/").replace("\n", " ")
            L.append(f"| {i + 1} | {mm(sc['start'])}-{mm(sc['start'] + sc['n'])} | {name} | {cell('; '.join(dict.fromkeys(txt)))} | {cell(sc['say'])}" + (f" (pace {sc['pace']})" if sc["say"] and sc["pace"] not in (None, 1.0) else "") + f" | {sc['tr'] if i else 'fade in'} |")
        L += ["", "## Files used", ""] + ([f"- `{u}`" for u in dict.fromkeys(used)] or ["- none"]) + ["", "## Notes", "", notes.rstrip("\n"), ""]
        open("script.md", "w").write("\n".join(L))
    def _write_srt(self):
        """Narration as an .srt file beside the video (the words of each voiced scene, split into short cues across the time it is spoken)."""
        rows = []; n = 0
        ts = lambda s: "%02d:%02d:%02d,%03d" % (s // 3600, s % 3600 // 60, s % 60, int(round((s % 1) * 1000)))
        for sc in self.scenes:
            if not sc["voice"] or not sc["say"] or sc["say"].startswith("(audio file)"): continue
            txt = EMOTION.sub(" ", sc["say"]).strip(); t0 = sc["start"] / self.fps + sc["voice_at"]; d = sc["voice"][1]
            parts = [p_.strip() for p_ in re.split(r"(?<=[.!?,;:])\s+", txt) if p_.strip()]; chunks = []
            for p_ in parts:                                    # no cue longer than about 42 characters per line, two lines
                w = p_.split(); cur = ""
                for x in w:
                    if cur and len(cur) + len(x) > 60: chunks.append(cur); cur = x
                    else: cur = (cur + " " + x).strip()
                if cur: chunks.append(cur)
            tot = sum(len(c) for c in chunks) or 1; t = t0
            for c in chunks:
                dd = d * len(c) / tot; n += 1; rows.append("%d\n%s --> %s\n%s\n" % (n, ts(t), ts(t + dd), c)); t += dd
        if rows: open(os.path.splitext(self.out)[0] + ".srt", "w").write("\n".join(rows)); print("  captions: " + os.path.splitext(os.path.relpath(self.out))[0] + ".srt")
    READ_KINDS = ("title", "intro", "outro", "end", "highlight", "quote", "bullets", "stat", "timeline", "review", "changelog", "notes", "versus", "anatomy", "image", "clip", "phone", "browser", "product", "cta", "laptop", "icons")
    def _reading_check(self):
        """Can people read what is on screen? Rule: a scene needs about (letters / 16 + 1.0) seconds for its words. Warns for scenes that are shorter. Fast type scenes are exempt on purpose."""
        w = []
        def words(v):
            if isinstance(v, str): return [] if (os.path.exists(v) or v.startswith(("http", "#", "/")) or len(v) > 300) else [v]
            if isinstance(v, dict): return [str(x) for x in v.keys() if isinstance(x, str)] + [w_ for x in v.values() for w_ in words(x)]
            if isinstance(v, (list, tuple)): return [x for y in v for x in words(y)]
            return []
        for i, sc in enumerate(self.scenes):
            if sc["kind"] not in self.READ_KINDS: continue
            name, a, k = sc.get("call", (sc["kind"], (), {})); txt = [t for v in list(a) + [k.get(x) for x in ("text", "sub", "title", "label", "by", "done")] for t in words(v)]
            letters = sum(len(t) for t in txt if len(t) > 1)
            if letters < 12: continue
            need = letters / 16.0 + 1.0; have = sc["n"] / self.fps
            if sc["voice"]: need = max(need * 0.6, sc["voice"][1] + 0.4)
            if have < need * 0.85: w.append("scene %d (%s): %d letters in %.1f s; about %.1f s are needed to read them (shorten the words or lengthen the scene)" % (i + 1, name, letters, have, need))
        return w
    def _audio_check(self, wav):
        """Checks on the finished mix: real silences exist (a film at one level is flat), and the low end does not swamp everything else."""
        if not os.path.exists(wav): return []
        w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); sr = w.getframerate(); w.close()
        if ch == 2: x = x.reshape(-1, 2).mean(1)
        if len(x) < sr * 3: return []
        hop = int(0.05 * sr); n = len(x) // hop; r = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)); db = 20 * np.log10(r + 1e-9); quiet = db < db.max() - 34; runs = 0; c = 0
        for q_ in quiet:
            c = c + 1 if q_ else 0
            if c == 6: runs += 1
        out = []; dur = len(x) / sr
        if dur >= 20 and runs == 0 and self.mood != "none": out.append("no real silence in %.0f s: drop the music for a beat before the turn or the peak, then bring the next sound in hard" % dur)
        sp = np.abs(np.fft.rfft(x[:sr * 40])) ** 2; fr = np.fft.rfftfreq(min(len(x), sr * 40), 1 / sr); lo = sp[(fr >= 20) & (fr < 120)].sum(); hi = sp[(fr >= 120) & (fr < 6000)].sum() + 1e-9
        if lo / hi > 1.4: out.append("bass-heavy: the 20-120 Hz band carries %.1fx the energy of the rest; lower energy=, change key=, or pick another genre (small speakers will lose it)" % (lo / hi))
        return out
    WORLD_CAMS = ("wide", "full", "crane", "orbit", "two", "close", "over", "low", "top", "prop"); MODEL_CAMS = ("turntable", "orbit", "push", "pull", "hero", "low", "top")
    def _camera_check(self):
        """3D films must be shot like films: several different angles, an establishing or scale shot, no angle repeated for no reason. Returns warnings."""
        shots = []
        for sc in self.scenes:
            c = (sc.get("call") or ("",))[0]
            if c.startswith("world shot "): shots.append(("world", c[11:].split(":")[0]))
            elif c.startswith("model:"): shots.append(("model", c[6:]))
        if len(shots) < 3: return []
        w = []; names = [s[1] for s in shots]; kinds_ = {s[0] for s in shots}; known = {"world": self.WORLD_CAMS, "model": self.MODEL_CAMS}
        need = min(4, len(shots))
        if len(set(names)) < need:
            unused = [c for k_ in kinds_ for c in known[k_] if c not in names][:6]; w.append("only %d different angle(s) across %d 3D shots (%s); use at least %d. Not used yet: %s" % (len(set(names)), len(shots), ", ".join(dict.fromkeys(names)), need, ", ".join(unused)))
        rep = [names[i] for i in range(1, len(names)) if names[i] == names[i - 1] and names[i] not in ("two", "close", "over")]
        if rep: w.append("the same angle twice in a row (%s): change the angle, or hold one longer shot instead" % ", ".join(dict.fromkeys(rep)))
        if not any(n in ("wide", "crane", "orbit", "top", "low", "turntable", "hero") for n in names): w.append("no establishing or scale shot (wide, crane, orbit, top, low, hero): open or close on one")
        return w
    def _workflow_checks(self):
        """Before a render: the plan gate, and the variety check against recent videos. Prints, never blocks."""
        try:
            import plan as _plan, variety as _variety
            if os.path.exists("plan.md"):
                st = _plan.status("plan.md")
                if st["problems"]: print("plan: " + "; ".join(st["problems"]))
                else: print("plan: complete (research, toolkit match, gaps, variety and script are filled in)")
            else: print("plan: no plan.md in this folder; the workflow starts with `python lib/plan.py new <name>` (references/workflow.md)")
            for w_ in self._camera_check(): print("camera: " + w_)
            for w_ in self._reading_check(): print("reading: " + w_)
            for w_ in self._audio_check(os.path.join(self.work, self.name + ".wav")): print("audio: " + w_)
            fp = _variety.fingerprint(self)
            for w_ in _variety.check(fp): print("variety: " + w_)
            if not self.draft: _variety.record(fp)
        except Exception as e: print("workflow check skipped:", e)
    def _handoff(self):
        """After a finished render: make a small preview strip and print the facts the closing message needs,
        so the message can be short and exact. See "The final message" in SKILL.md."""
        if not os.path.exists(self.out): return
        secs = self.total / self.fps; shape = "tall" if self.H > self.W * 1.1 else "wide" if self.W > self.H * 1.1 else "square"; mb = os.path.getsize(self.out) / 1e6
        prev = os.path.join(self.work, self.name + "-preview.jpg"); n = 5 if shape == "tall" else 3; th = 480 if shape == "tall" else 270; tw = int(th * self.W / self.H) // 2 * 2
        try:   # one frame from the settled part of each scene (evenly chosen scenes when there are many), side by side
            idx = sorted(set(int(round(i * (len(self.scenes) - 1) / max(n - 1, 1))) for i in range(n))) if len(self.scenes) > n else list(range(len(self.scenes))); ims = []
            for i in idx:
                sc = self.scenes[i]; t_ = (sc["start"] + sc["n"] * 0.6) / self.fps; f_ = os.path.join(self.work, f".pv{i}.jpg")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t_:.3f}", "-i", self.out, "-frames:v", "1", "-vf", f"scale={tw}:{th}", "-q:v", "3", f_], check=True, capture_output=True)
                ims.append(cv2.copyMakeBorder(cv2.imread(f_), 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))); os.remove(f_)
            cv2.imwrite(prev, np.hstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 88])
        except Exception: prev = None
        sound = [x for x in ("music" if (self.mood != "none" or self.music_file) else "", "voice-over" if any(sc["voice"] for sc in self.scenes) else "") if x]
        print("\nREADY TO DELIVER"); print("video:   " + self.out); print(f"facts:   {secs:.0f} seconds, {shape} ({self.W}x{self.H}), " + (" and ".join(sound) if sound else "no sound") + f", {mb:.0f} MB")
        if prev: print("preview: " + prev)
        if os.path.exists("script.md"): print("script:  " + os.path.abspath("script.md"))
        print("open:    open " + json_quote(self.out))
    def render(self):
        if not self.loose:
            if not self.scenes or self.scenes[0]["kind"] not in ("intro", "title", "crt", "logo"):
                sys.exit("joyboy: the first scene must be a proper intro: film.intro(...) (title, crt and logo also count)")
            if len(self.scenes) < 2 or self.scenes[-1]["kind"] not in ("outro", "end", "logo"):
                sys.exit("joyboy: the last scene must be a proper outro: film.outro(...) (end and logo also count)")
        self._layout(); main = len(sys.argv) == 1;
        if sys.argv[1:2] in (["plan"], ["sheet"]):   # the scene list with start frames, for choosing sheet frames
            for sc in self.scenes: print("  %5d  %-9s %4.1fs  %s" % (sc["start"], sc.get("call", (sc["kind"],))[0], sc["n"] / self.fps, sc["tr"]))
            print("  %5d  end" % self.total)
            if sys.argv[1] == "plan": return
        wav = os.path.join(self.work, self.name + ".wav")
        if main:
            print(f"{self.name}: {len(self.scenes)} scenes, {self.total} frames, {self.total / self.fps:.1f}s, {self.W}x{self.H}" + (" (draft)" if self.draft else ""))
            for sc in self.scenes: print("  %5d  %-8s %4.1fs  %s" % (sc["start"], sc["kind"], sc["n"] / self.fps, sc["tr"]))
            self._score(wav); self._write_script(); self._write_srt(); self._workflow_checks()
            if getattr(self, "music_info", None): print("  music: %(genre)s, %(bpm)d bpm, %(mode)s" % self.music_info)
        jb.run(self.frame, self.total, self.out, audio=wav if os.path.exists(wav) else None, crf=28 if self.draft else 21, grain=(0 if self.draft else self.fin["grain"]) if self.ffgrain else 0)
        if main and not self.draft: self._handoff()

def json_quote(p):
    return '"' + p.replace('"', '\\"') + '"'

def _record(name, fn):
    """Remember how each scene was called, so script.md can list its words and files."""
    def wrapped(self, *a, **k):
        n0 = len(self.scenes); r = fn(self, *a, **k)
        for sc in self.scenes[n0:]:
            if name == "web" or "call" not in sc: sc["call"] = (name, a, {x: y for x, y in k.items() if x != "voice"})
        return r
    wrapped.__doc__ = fn.__doc__; wrapped.__name__ = name; wrapped.__wrapped__ = fn; return wrapped
kinds.install(Film)
def _asset(self, name, role="main"):
    """Path of a saved asset (character sheet, sprite sheet, 3D model ...) from the workspace asset library: film.image(film.asset("joybot-sheet"))."""
    import assets; return assets.path(name, role)
Film.asset = _asset
def _register_scene(cls, name, fn):
    """Add a scene method made for this project (see scaffold.py): it is recorded in script.md like every other scene."""
    setattr(cls, name, _record(name, fn))
Film.register_scene = classmethod(_register_scene)
def _extend(self, path):
    """Load a project-local extension file made with scaffold.py (new scenes, themes, effects): film.extend("local_hologram.py")."""
    import importlib.util
    path = os.path.abspath(path); spec = importlib.util.spec_from_file_location("jb_local_" + re.sub(r"\W", "_", os.path.basename(path)), path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if hasattr(mod, "install"): mod.install(Film)
    return self
Film.extend = _extend
SCENE_NAMES = ("intro", "outro", "title", "image", "clip", "web", "words", "bullets", "stat", "bars", "columns", "line", "donut", "heatmap", "icons", "map", "quote", "phone", "browser",
               "crt", "logo", "end", "window", "slices", "carousel", "grid", "tunnel", "loader", "lockcut", "talk", "custom") + kinds.NAMES   # every scene method; catalog.py lists them
TRANSITIONS = ("cut", "fade", "whip", "white", "zoom", "wipe", "iris", "bars", "doors", "pie", "glitch")
for _n in SCENE_NAMES:
    setattr(Film, _n, _record(_n, getattr(Film, _n)))
