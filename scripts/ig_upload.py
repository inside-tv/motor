# Publish a short as an Instagram Reel on the account linked to the Facebook Page of its language
# (Instagram API with Facebook Login, resumable upload: no public URL needed).
# Uses credenciales/facebook.json ({"es": {"token", "ig_id"}, ...}) written by fb_token.py.
# usage: python3 -I ig_upload.py <es|en> <video.mp4> <meta.json>      → prints the Reel URL
import json, os, sys, time, urllib.parse, urllib.request

V = "v27.0"
lang, video, meta_f = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
acc = json.load(open(os.path.join(HERE, "..", "credenciales", "facebook.json")))[lang]
if not acc.get("ig_id"): sys.exit(f"la página {lang} no tiene Instagram vinculado")
meta, tok, ig = json.load(open(meta_f)), acc["token"], acc["ig_id"]

def call(url, data=None, headers=None, body=None):
    if data is not None: body = urllib.parse.urlencode({**data, "access_token": tok}).encode()
    elif body is None: url += ("&" if "?" in url else "?") + "access_token=" + urllib.parse.quote(tok)
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)
    except urllib.error.HTTPError as e:  # never echo the token
        sys.exit(f"Instagram respondió {e.code}: {e.read().decode()[:400]}")

G = f"https://graph.facebook.com/{V}"
caption = (meta["title"].split(" #")[0] + "\n\n" + meta["description"])[:2200]
c = call(f"{G}/{ig}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": "true"})
call(c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{V}/{c['id']}", body=open(video, "rb").read(),
     headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(os.path.getsize(video))})
for _ in range(60):  # Instagram transcodes before it lets you publish
    st = call(f"{G}/{c['id']}?fields=status_code,status").get("status_code")
    if st == "FINISHED": break
    if st in ("ERROR", "EXPIRED"): sys.exit(f"Instagram no pudo procesar el video: {st}")
    time.sleep(10)
else: sys.exit("Instagram tardó demasiado en procesar el video")
mid = call(f"{G}/{ig}/media_publish", {"creation_id": c["id"]})["id"]
print(call(f"{G}/{mid}?fields=permalink").get("permalink") or f"publicado (id {mid})")
