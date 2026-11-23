# Build one short of @adentro-tv in one language: narration (edge-tts, word times), Pixabay background clips (one per line),
# music bed ducked under the voice and two-pass loudnorm to -14 LUFS. Leaves <work>/timeline.json and <work>/audio.wav for render.js.
# usage: python3 montar.py <guion.json> <es|en> <work_dir> <ffmpeg> <music.mp3>
# guion.json: {"slug", "clips": [english search per line], "es": {"hook", "lineas": [...], "hi": [...]}, "en": {...}}
import json, os, subprocess, sys, urllib.parse, urllib.request, wave

gf, LANG, WD, FF, MUSIC = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(gf)); L = G[LANG]
os.makedirs(f"{WD}/voz", exist_ok=True); os.makedirs(f"{WD}/clips", exist_ok=True)
SR, LEAD, GAP, TAIL = 48000, 0.25, 0.16, 1.4
W, H, FPS = 1080, 1920, 30
CACHE = os.path.expanduser("~/.cache/adentro-clips"); os.makedirs(CACHE, exist_ok=True)
KEY = os.environ.get("PIXABAY_API_KEY", "")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) adentro-tv/1.0"}  # Pixabay answers 403 to urllib's default agent

def run(*a): subprocess.run(a, check=True)
def dur(p):
    with wave.open(p) as w: return w.getnframes() / w.getframerate()
assert len(L["lineas"]) == len(G["clips"]), "cada línea necesita su clip"

# ---- closing call to follow, spoken over the last clip. "Síguenos" works on YouTube and Facebook alike.
# The guion may bring its own "cierre" (e.g. when the topic really can save a life); otherwise one of these, fixed per slug.
CIERRES = {
    "es": ["Síguenos para no perderte lo que pasa dentro de tu cuerpo.",
           "Síguenos: un dato así puede ayudarte el día que más lo necesites.",
           "Síguenos y entiende a tu cuerpo antes de que te dé un susto."],
    "en": ["Follow for more of what happens inside your body.",
           "Follow us: a fact like this could help you the day you need it most.",
           "Follow and understand your body before it gives you a scare."],
}
cierre = L.get("cierre") or CIERRES[LANG][sum(map(ord, G.get("slug", ""))) % len(CIERRES[LANG])]

# ---- narration: one edge-tts call per line, laid end to end with short gaps ----
t, parts, words, lines, cta_start = LEAD, [], [], [], None
for i, text in enumerate(L["lineas"] + [cierre]):
    b = f"{WD}/voz/{i:02d}"
    if not os.path.exists(b + ".words.json"):
        run(sys.executable, f"{HERE}/voz.py", LANG, b, text)
    run(FF, "-v", "error", "-y", "-i", b + ".mp3", "-ac", "1", "-ar", str(SR), b + ".wav")
    d = dur(b + ".wav")
    for w in json.load(open(b + ".words.json")): words.append({"text": w["text"], "start": t + w["start"], "end": t + w["end"], "line": i})
    if i < len(L["lineas"]): lines.append({"start": t, "end": t + d})
    else: cta_start = t  # the closing line has no clip of its own: the last clip runs under it
    parts.append((t, b + ".wav")); t += d + GAP
DUR = t - GAP + TAIL

ins, fx = [], []
for k, (st, p) in enumerate(parts):
    ins += ["-i", p]; ms = int(st * 1000); fx.append(f"[{k}:a]adelay={ms}|{ms}[p{k}]")
fx.append("".join(f"[p{k}]" for k in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{DUR:.3f},"
          "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=100:makeup=1.5[v]")
run(FF, "-v", "error", "-y", *ins, "-filter_complex", ";".join(fx), "-map", "[v]", "-ar", str(SR), f"{WD}/narr.wav")

# ---- music bed under the voice, then -14 LUFS (two passes, linear) ----
mixfx = (f"[0:a]aformat=channel_layouts=stereo,asplit=2[v][sc];[1:a]atrim=0:{DUR:.3f},volume=0.14,afade=t=in:d=1,"
         f"afade=t=out:st={DUR - 2:.3f}:d=2[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[md];"
         "[v][md]amix=inputs=2:normalize=0:duration=first[mx]")
base = ["-i", f"{WD}/narr.wav", "-stream_loop", "-1", "-i", MUSIC, "-filter_complex"]
r = subprocess.run([FF, "-hide_banner", "-nostats", *base, mixfx + ";[mx]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True, check=True)
m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
run(FF, "-v", "error", "-y", *base, mixfx + f";[mx]{ln},aresample={SR}", "-ar", str(SR), f"{WD}/audio.wav")

# ---- background: one Pixabay clip per line (shared by both languages through the cache and clips.json) ----
FORMAT_TAGS = {"vertical", "smartphone video", "vertical video", "4k", "hd", "background", "stock footage"}
def search(q):
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": KEY, "q": q, "per_page": 40, "safesearch": "true", "order": "popular"})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA))).get("hits", [])
def rank(h, q):
    v = h["videos"].get("large") or h["videos"].get("medium") or {}
    tags = [x.strip().lower() for x in h.get("tags", "").split(",") if x.strip().lower() not in FORMAT_TAGS]
    rel = sum(max(0, 6 - next((i for i, x in enumerate(tags) if w in x), 6)) for w in q.lower().split())
    return (-rel, not (v.get("height", 0) > v.get("width", 1)), -(v.get("width") or 0))
def fetch(hit):
    v = hit["videos"]; f = next(v[k] for k in ("large", "medium", "small") if v.get(k, {}).get("url"))
    p = f"{CACHE}/{hit['id']}_{f['width']}.mp4"
    if not os.path.exists(p):
        with urllib.request.urlopen(urllib.request.Request(f["url"], headers=UA)) as r, open(p + ".part", "wb") as o: o.write(r.read())
        os.rename(p + ".part", p)
    return p

# the same clip choice for both languages: chosen once per guion and stored next to it
choice_f = os.path.join(os.path.dirname(os.path.abspath(gf)), "clips.json")
choice = json.load(open(choice_f)) if os.path.exists(choice_f) else []
credits, segs, used = [], [], {c["pixabay_id"] for c in choice}
for i, q in enumerate(G["clips"]):
    a = lines[i]["start"] if i else 0.0
    b = lines[i + 1]["start"] if i + 1 < len(lines) else DUR
    if i < len(choice): hit = {"id": choice[i]["pixabay_id"], "videos": choice[i]["videos"], "duration": choice[i]["dur"], "user": choice[i]["autor"], "pageURL": choice[i]["url"]}
    else:
        if not KEY: sys.exit("falta PIXABAY_API_KEY")
        hits = []
        for qq in dict.fromkeys([q, q.split()[-1], "human body"]):  # broaden the search before giving up
            hits = sorted([h for h in search(qq) if h["id"] not in used], key=lambda h: rank(h, qq))
            if hits:
                if qq != q: print(f"«{q}» sin clips en Pixabay: uso «{qq}»")
                break
        if not hits: sys.exit(f"Pixabay no tiene clips para «{q}»: cambia la búsqueda en el guion")
        hit = hits[0]; used.add(hit["id"])
        choice.append({"busqueda": q, "pixabay_id": hit["id"], "autor": hit.get("user"), "url": hit.get("pageURL"), "videos": hit["videos"], "dur": hit["duration"]})
    src, seg = fetch(hit), f"{WD}/clips/{i:02d}.mp4"
    start = max(0.0, min(1.0, hit["duration"] - (b - a)))
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
          f"zoompan=z='min(1+0.0009*on,1.1)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},eq=brightness=-0.04,format=yuv420p")
    run(FF, "-v", "error", "-y", "-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", src, "-t", f"{b - a:.3f}", "-vf", vf, "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", seg)
    segs.append(seg); credits.append({k: choice[i][k] for k in ("busqueda", "pixabay_id", "autor", "url")})
json.dump(choice, open(choice_f, "w"), ensure_ascii=False)
open(f"{WD}/clips/lista.txt", "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
run(FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WD}/clips/lista.txt", "-c", "copy", f"{WD}/bg.mp4")

# ---- captions: 1–3 words per chunk, broken at sentence ends ----
caps, cur = [], []
for k, w in enumerate(words):
    cur.append(w)
    nxt = words[k + 1] if k + 1 < len(words) else None
    if len(cur) == 3 or not nxt or nxt["line"] != w["line"] or nxt["start"] - w["end"] > 0.25:
        caps.append({"start": cur[0]["start"], "end": (nxt["start"] if nxt and nxt["line"] == w["line"] else w["end"] + 0.25), "words": cur}); cur = []
BRAND = {"es": ("ADENTRO TV", "Síguenos: Adentro TV"), "en": ("INSIDE TV", "Follow: Inside TV")}  # same text fits YouTube and Facebook
tl = {"duration": DUR, "lang": LANG, "hook": L["hook"], "hi": [h.lower() for h in L.get("hi", [])], "brand": BRAND[LANG][0], "cta": BRAND[LANG][1],
      "cta_start": cta_start,
      "bg": os.path.abspath(f"{WD}/bg.mp4"), "lines": lines, "captions": caps}
json.dump(tl, open(f"{WD}/timeline.json", "w"), ensure_ascii=False, indent=1)
json.dump(credits, open(f"{WD}/creditos.json", "w"), ensure_ascii=False, indent=1)
print(f"{LANG}: {DUR:.1f} s, {len(lines)} líneas, {len(caps)} subtítulos")
