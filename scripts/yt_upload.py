# Upload one video to YouTube with the Data API (resumable upload, stdlib only), optionally scheduled, then set its thumbnail.
# usage: python3 -I yt_upload.py <client_secret.json> <token.json> <video.mp4> <meta.json>
# meta.json: {"title", "description", "tags": [], "categoryId": "28", "publishAt": "2026-10-24T17:00:00Z" | null,
#             "privacy": "private"|"unlisted"|"public", "thumbnail": "miniatura.jpg" | null, "synthetic": true}
# With publishAt the video stays private and YouTube publishes it at that time (UTC).
# Prints the video id and URL. Unaudited API projects get every upload locked as private by YouTube.
import json, os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_auth import access_token

secret, token, video, meta_f = sys.argv[1:5]
meta = json.load(open(meta_f))
tok = access_token(secret, token)
status = {"privacyStatus": "private" if meta.get("publishAt") else meta.get("privacy", "private"),
          "selfDeclaredMadeForKids": False, "containsSyntheticMedia": bool(meta.get("synthetic", True))}
if meta.get("publishAt"): status["publishAt"] = meta["publishAt"]
body = {"snippet": {"title": meta["title"][:100], "description": meta.get("description", "")[:5000], "tags": meta.get("tags", []),
                    "categoryId": meta.get("categoryId", "28"), "defaultLanguage": "es", "defaultAudioLanguage": "es"}, "status": status}

size = os.path.getsize(video)
init = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    data=json.dumps(body).encode(), method="POST",
    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
             "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
try:
    session = urllib.request.urlopen(init).headers["Location"]
except urllib.error.HTTPError as e:
    sys.exit(f"Error al iniciar la subida: {e.code} {e.read().decode()[:500]}")

# send the file in 8 MB chunks; on a dropped connection, ask the server how much it has and resume from there
CHUNK, sent = 8 * 1024 * 1024, 0
with open(video, "rb") as f:
    while True:
        f.seek(sent); data = f.read(CHUNK); end = sent + len(data) - 1
        req = urllib.request.Request(session, data=data, method="PUT",
            headers={"Authorization": f"Bearer {tok}", "Content-Length": str(len(data)), "Content-Range": f"bytes {sent}-{end}/{size}"})
        try:
            r = urllib.request.urlopen(req); res = json.load(r); break
        except urllib.error.HTTPError as e:
            if e.code != 308: sys.exit(f"Error al subir: {e.code} {e.read().decode()[:500]}")
            rng = e.headers.get("Range"); sent = int(rng.split("-")[1]) + 1 if rng else 0
            print(f"  {sent * 100 // size} %", flush=True)

vid = res["id"]
print(f"Subido: {vid} · https://youtu.be/{vid} · estado: {res['status'].get('privacyStatus')} {res['status'].get('publishAt', '')}")
if meta.get("thumbnail"):
    th = meta["thumbnail"] if os.path.isabs(meta["thumbnail"]) else os.path.join(os.path.dirname(os.path.abspath(meta_f)), meta["thumbnail"])
    req = urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", data=open(th, "rb").read(),
        method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"})
    try: urllib.request.urlopen(req); print("Miniatura puesta.")
    except urllib.error.HTTPError as e: print(f"Miniatura no aplicada: {e.code} {e.read().decode()[:300]}")
