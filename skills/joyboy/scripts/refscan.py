"""joyboy refscan: measure a reference video so the new one can match it, then check the match.

    python refscan.py scan VIDEO [--out DIR]      shots, cut times, per-shot colours and motion, tempo, loudness, contact sheet, a timing skeleton
    python refscan.py check RENDER.mp4 REF.json   compare a finished render with the reference: score out of 100 and what differs

`scan` writes into DIR (default: ./reference/<video name>/):
    reference.json   everything measured (machine-readable)
    reference.md     the shot table to read, with a block for YOU to fill in: what is on screen in each shot, the words, the fonts, the motion
    contact.jpg      one picture per shot (with its time) - LOOK AT IT and describe each shot in reference.md
    shots/NN.jpg     the middle frame of every shot, full size, for looking closer
    skeleton.py      a film.py starting point with the same shot lengths, tempo and colours; replace the stubs with real scenes
What it measures is real (cut times, colours, camera movement, tempo, loudness). What is ON the screen (words, characters, what is drawn) it cannot read:
that is the part you describe by looking at contact.jpg and shots/, and write down in reference.md before writing any script.
Nothing is downloaded or uploaded; it only reads the file you give it.
"""
import os, sys, re, json, shutil, subprocess, tempfile, argparse, wave
import numpy as np, cv2

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path], capture_output=True, text=True)
    d = json.loads(out.stdout or "{}"); v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {}); a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    num, den = (v.get("r_frame_rate") or "30/1").split("/"); fps = float(num) / max(float(den), 1)
    return dict(width=v.get("width"), height=v.get("height"), fps=round(fps, 3), duration=float(d.get("format", {}).get("duration", v.get("duration", 0)) or 0), has_audio=a is not None)

def frames(path, step_fps=None):
    """Yield (index, time, small BGR frame) for every frame (or every n-th when step_fps is given). Small = 180 px wide."""
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 30; i = 0; every = max(1, int(round(fps / step_fps))) if step_fps else 1
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % every == 0:
            h, w = fr.shape[:2]; yield i, i / fps, cv2.resize(fr, (180, max(2, int(180 * h / w))), interpolation=cv2.INTER_AREA), fr
        i += 1
    cap.release()

def palette(img, k=4):
    px = cv2.resize(img, (48, 48)).reshape(-1, 3).astype(np.float32); crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 1.0)
    _, lab, cen = cv2.kmeans(px, k, None, crit, 2, cv2.KMEANS_PP_CENTERS); cnt = np.bincount(lab.flatten(), minlength=k); order = np.argsort(-cnt)
    return [("#%02x%02x%02x" % tuple(int(c) for c in cen[i][::-1]), round(float(cnt[i] / cnt.sum()), 2)) for i in order]

def audio_info(path, work):
    wav = os.path.join(work, "a.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "22050", "-vn", wav], capture_output=True)
    if r.returncode or not os.path.exists(wav): return None
    w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; sr = w.getframerate(); w.close()
    if len(x) < sr: return None
    hop = 512; env = np.sqrt(np.convolve(x * x, np.ones(hop) / hop, "same")[::hop]); on = np.maximum(np.diff(env), 0); on = on - np.convolve(on, np.ones(20) / 20, "same"); on = np.maximum(on, 0)
    fr = sr / hop; lags = np.arange(int(fr * 60 / 190), int(fr * 60 / 65)); ac = np.array([np.dot(on[:-l], on[l:]) for l in lags]) if len(on) > lags.max() + 2 else np.zeros(len(lags))
    bpm = float(60 * fr / lags[int(np.argmax(ac))]) if ac.any() else None
    while bpm and bpm < 80: bpm *= 2
    while bpm and bpm > 170: bpm /= 2
    sp = np.abs(np.fft.rfft(x[:sr * 20])); f = np.fft.rfftfreq(min(len(x), sr * 20), 1 / sr); cen = float((sp * f).sum() / max(sp.sum(), 1e-9)); p2 = sp ** 2; low = float(p2[f < 150].sum() / max(p2.sum(), 1e-9))
    secs = [float(np.sqrt((x[int(i * sr):int((i + 1) * sr)] ** 2).mean())) for i in range(int(len(x) / sr))]
    conf = float(ac.max() / (ac.mean() + 1e-12)) if ac.any() else 0.0     # how rhythmic: about 1.5 for speech, 4.5 to 9 for music with a beat
    return dict(bpm=round(bpm, 1) if bpm else None, rhythm=round(conf, 2), rms=round(float(np.sqrt((x ** 2).mean())), 3), centroid_hz=round(cen), low_share=round(low, 2), loudness_per_second=[round(s, 3) for s in secs],
                character="bright" if cen > 3500 else "mid" if cen > 1800 else "dark/warm")

def analyze(path, work=None):
    """Measure a video. Returns a dict (see the module docstring)."""
    info = probe(path); work = work or tempfile.mkdtemp(prefix="jb-ref-"); prev = None; diffs = []; times = []; smalls = []; mot = []; fulls = {}
    for i, t, sm, full in frames(path):
        g = cv2.cvtColor(cv2.resize(sm, (64, 112)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean())); sh = cv2.phaseCorrelate(prev, g)[0]; mot.append((float(sh[0]), float(sh[1])))
        else: diffs.append(0.0); mot.append((0.0, 0.0))
        prev = g; times.append(t); smalls.append(sm)
    d = np.array(diffs); thr = max(float(np.median(d) + 6 * (np.median(np.abs(d - np.median(d))) + 0.4)), 12.0)
    cuts = [i for i in range(1, len(d)) if d[i] > thr and d[i] >= d[i - 1] and (i + 1 >= len(d) or d[i] >= d[i + 1])]
    bounds = [0] + cuts + [len(times)]; shots = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < 2: continue
        mid = (a + b) // 2; seg = smalls[a:b]; m = np.array(mot[a + 1:b]) if b - a > 1 else np.zeros((1, 2)); mdiff = d[a + 1:b] if b - a > 1 else np.zeros(1)
        flat = float(np.mean([s.std() for s in seg[::max(1, len(seg) // 6)]])); ps = palette(smalls[mid])
        move = "static" if mdiff.mean() < 2 else ("pan/scroll" if np.abs(m).mean() > 1.5 and mdiff.mean() < 14 else "busy motion")
        shots.append(dict(index=len(shots), start=round(times[a], 3), end=round(times[b - 1] + 1 / info["fps"], 3), duration=round(times[b - 1] + 1 / info["fps"] - times[a], 3), start_frame=a, end_frame=b, palette=ps, brightness=round(float(smalls[mid].mean()), 1),
                          motion=round(float(mdiff.mean()), 2), movement=move, flat_colour=bool(flat < 14), mid_frame=mid))
    a = audio_info(path, work) if info["has_audio"] else None
    cuts_t = [round(s["start"], 3) for s in shots[1:]]; dur = [s["duration"] for s in shots]
    return dict(file=os.path.abspath(path), **info, shots=shots, cut_times=cuts_t, average_shot=round(float(np.mean(dur)), 2) if dur else None, shortest_shot=min(dur) if dur else None, audio=a)

def scan(video, out):
    os.makedirs(os.path.join(out, "shots"), exist_ok=True); ref = analyze(video, out); cap = cv2.VideoCapture(video); picks = {s["mid_frame"]: s["index"] for s in ref["shots"]}; i = 0; thumbs = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i in picks:
            n = picks[i]; cv2.imwrite(os.path.join(out, "shots", "%02d.jpg" % n), fr, [cv2.IMWRITE_JPEG_QUALITY, 90]); h, w = fr.shape[:2]; th = cv2.resize(fr, (270, int(270 * h / w)))
            s = ref["shots"][n]; cv2.rectangle(th, (0, 0), (150, 24), (0, 0, 0), -1); cv2.putText(th, "#%d %.2fs %.1fs" % (n + 1, s["start"], s["duration"]), (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA); thumbs.append(th)
        i += 1
    if thumbs:
        cols = 6; hh = max(t.shape[0] for t in thumbs); rows = []
        for r in range(0, len(thumbs), cols):
            row = [cv2.copyMakeBorder(t, 0, hh - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in thumbs[r:r + cols]]
            while len(row) < cols: row.append(np.zeros_like(row[0]))
            rows.append(np.hstack(row))
        cv2.imwrite(os.path.join(out, "contact.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for s in ref["shots"]: s.pop("mid_frame", None); s.pop("start_frame", None); s.pop("end_frame", None)
    json.dump(ref, open(os.path.join(out, "reference.json"), "w"), indent=1)
    au = ref["audio"]; L = [f"# Reference: {os.path.basename(video)}", "", f"- {ref['width']}x{ref['height']}, {ref['fps']} fps, {ref['duration']:.2f} s, {len(ref['shots'])} shots (average {ref['average_shot']} s, shortest {ref['shortest_shot']} s)",
         (f"- Audio: about {au['bpm']} BPM, {au['character']} (spectral centre {au['centroid_hz']} Hz, low-end share {au['low_share']}), loudness {au['rms']}" if au else "- Audio: none"), f"- Cut times (s): {', '.join(str(c) for c in ref['cut_times']) or 'none (one continuous shot)'}", "",
         "## Shots (measured)", "", "| # | Start | Length | Colours | Movement | Flat colour field |", "|---|---|---|---|---|---|"]
    for s in ref["shots"]: L.append(f"| {s['index'] + 1} | {s['start']:.2f} | {s['duration']:.2f} | {' '.join(c for c, _ in s['palette'][:3])} | {s['movement']} ({s['motion']}) | {'yes' if s['flat_colour'] else 'no'} |")
    L += ["", "## What is on screen: YOU fill this in by looking at contact.jpg and shots/ (the scan cannot read pictures or words)", "",
          "| # | What is drawn (subject, layout, camera) | Words on screen, verbatim | Font style | Motion and transition into it | Sound at this moment |", "|---|---|---|---|---|---|"] + [f"| {s['index'] + 1} | TODO | TODO | TODO | TODO | TODO |" for s in ref["shots"]]
    L += ["", "## Overall (fill in)", "", "- Format name and the formula it uses: TODO", "- Hook (first second): TODO", "- Style: colour, type, texture, finish: TODO", "- What must be matched exactly: TODO", "- What may differ (the subject, the words): TODO", ""]
    open(os.path.join(out, "reference.md"), "w").write("\n".join(L))
    bpm = au["bpm"] if au and au["bpm"] else 120; sk = ['"""Timing skeleton from the reference scan: the same shot lengths, tempo and colours. Replace each stub with the real scene that matches the shot (see reference.md), keeping its length."""',
        "import os, sys", 'sys.path.insert(0, os.path.expanduser("~/joyboy/lib"))', "from quick import Film", "",
        f'film = Film("{re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(video))[0].lower()).strip("-") or "ref"}", size="{"portrait" if ref["height"] >= ref["width"] else "landscape"}", fps={int(round(ref["fps"])) or 30}, mood="none", bpm={int(round(bpm))}, loose=True)   # loose: no forced intro/outro, to match the reference exactly']
    for s in ref["shots"]:
        sk.append(f'film.title("shot {s["index"] + 1}", dur={s["duration"]:.2f}, bg="{s["palette"][0][0]}")   # {s["start"]:.2f}s  {s["movement"]}  colours {" ".join(c for c, _ in s["palette"][:3])}  -> replace with the real scene')
    sk += ["", "film.render()", ""]; open(os.path.join(out, "skeleton.py"), "w").write("\n".join(sk))
    return ref

def lab(hexc):
    c = np.uint8([[[int(hexc[5:7], 16), int(hexc[3:5], 16), int(hexc[1:3], 16)]]]); return cv2.cvtColor(c, cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)

def check(render, refjson, tol=0.15):
    """Compare a render with a reference.json. Returns (score, report lines)."""
    R = json.load(open(refjson)); N = analyze(render); rep = []; pts = 0.0; tot = 0.0
    def part(name, w, got, note): nonlocal pts, tot; pts += w * got; tot += w; rep.append("%-22s %3d/%d  %s" % (name, round(w * got), w, note))
    dur_err = abs(N["duration"] - R["duration"]) / max(R["duration"], 0.1); part("duration", 10, max(0, 1 - dur_err * 4), "%.2fs vs reference %.2fs" % (N["duration"], R["duration"]))
    cr, cn = R["cut_times"], N["cut_times"]; hit = sum(1 for c in cr if any(abs(c - x) <= tol for x in cn)); part("cut times", 30, hit / len(cr) if cr else (1.0 if not cn else 0.5), "%d of %d reference cuts matched within %.2fs; render has %d cuts" % (hit, len(cr), tol, len(cn)))
    extra = max(0, len(cn) - len(cr)); part("no extra cuts", 10, max(0, 1 - extra / max(len(cr), 1)), "%d extra" % extra if extra else "none")
    ds = []
    for s in R["shots"]:
        mid = (s["start"] + s["end"]) / 2; m = next((x for x in N["shots"] if x["start"] <= mid < x["end"]), None)
        if m: ds.append(float(np.linalg.norm(lab(s["palette"][0][0]) - lab(m["palette"][0][0]))))
    part("colour per shot", 25, max(0, 1 - (np.mean(ds) / 60 if ds else 1)), "average colour distance %.0f (0 = identical, above 40 = clearly different)" % (np.mean(ds) if ds else -1))
    mv = sum(1 for s in R["shots"] if (m := next((x for x in N["shots"] if x["start"] <= (s["start"] + s["end"]) / 2 < x["end"]), None)) and m["movement"] == s["movement"]); part("movement per shot", 10, mv / max(len(R["shots"]), 1), "%d of %d shots move the same way" % (mv, len(R["shots"])))
    ra, na = R.get("audio"), N.get("audio")
    if ra and ra.get("rhythm") is None and os.path.exists(R.get("file", "")):          # a reference scanned before the rhythm measure existed
        try: ra = dict(ra, rhythm=(audio_info(R["file"], tempfile.mkdtemp(prefix="jb-ref-")) or {}).get("rhythm"))
        except Exception: pass
    if ra and ra.get("rhythm") is not None and ra["rhythm"] < 3.0: rep.append("%-22s  -   not scored: the reference audio is not rhythmic (speech or ambience, beat strength %.1f); its 'tempo' means nothing" % ("tempo", ra["rhythm"]))
    elif ra and na and ra.get("bpm") and na.get("bpm"): e = abs(na["bpm"] - ra["bpm"]) / ra["bpm"]; part("tempo", 15, max(0, 1 - e * 5), "%.0f BPM vs reference %.0f" % (na["bpm"], ra["bpm"]))
    else: part("tempo", 15, 1.0 if not ra else 0.0, "no audio to compare" if not ra else "render has no measurable tempo")
    return round(100 * pts / tot), rep, N

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("video"); s.add_argument("--out")
    c = sub.add_parser("check"); c.add_argument("render"); c.add_argument("ref"); c.add_argument("--tol", type=float, default=0.15)
    x = ap.parse_args()
    if x.cmd == "scan":
        out = x.out or os.path.join("reference", re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(x.video))[0].lower()).strip("-")); ref = scan(x.video, out)
        print("scanned %s: %d shots, %.1fs%s -> %s" % (os.path.basename(x.video), len(ref["shots"]), ref["duration"], ", ~%s BPM" % ref["audio"]["bpm"] if ref["audio"] and ref["audio"]["bpm"] else "", out)); print("NEXT: look at %s/contact.jpg and fill in the table in reference.md before writing any script." % out)
    else:
        score, rep, N = check(x.render, x.ref, x.tol); print("accuracy %d/100" % score); print("\n".join(rep)); sys.exit(0 if score >= 80 else 1)
