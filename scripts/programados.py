# Publish the shorts scheduled in datos/cola/programados.json once their time has come (Facebook and Instagram).
# Each item: {"carpeta": "2026-11-21_muela", "release": "v-2026-11-21-muela", "cuando": "2026-11-23T15:30:00-05:00",
#             "plataformas": ["facebook", "instagram"], "idiomas": ["es", "en"], "publicado": {"facebook_es": url, ...}}
# The videos come from the private release of the datos repo (GH_TOKEN + DATOS_REPO); urls and errors are written back.
# usage: python3 -I scripts/programados.py <datos_dir>
import datetime, json, os, subprocess, sys

DATOS = os.path.abspath(sys.argv[1]); HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(DATOS, "cola", "programados.json")
SCRIPT = {"facebook": "fb_upload.py", "instagram": "ig_upload.py"}
items = json.load(open(F)) if os.path.exists(F) else []
now = datetime.datetime.now(datetime.timezone.utc)
for it in items:
    if datetime.datetime.fromisoformat(it["cuando"]) > now: continue
    done = it.setdefault("publicado", {})
    todo = [(p, l) for p in it.get("plataformas", ["facebook", "instagram"]) for l in it.get("idiomas", ["es", "en"])
            if not str(done.get(f"{p}_{l}", "")).startswith("http")]
    if not todo: continue
    ent = os.path.join(DATOS, "produccion", it["carpeta"], "entrega")
    if not all(os.path.exists(f"{ent}/{l}.mp4") for _, l in todo):
        subprocess.run(["gh", "release", "download", it["release"], "-R", os.environ["DATOS_REPO"], "-D", ent, "-p", "*.mp4", "--clobber"], check=True)
    for p, l in todo:
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, SCRIPT[p]), l, f"{ent}/{l}.mp4", f"{ent}/{l}.json"], capture_output=True, text=True)
        out = (r.stdout.strip().splitlines() or [""])[-1] if r.returncode == 0 else "error: " + (r.stderr.strip() or r.stdout.strip())[-300:]
        done[f"{p}_{l}"] = out; print(it["carpeta"], p, l, out)
    json.dump(items, open(F, "w"), ensure_ascii=False, indent=1)
