# Publish a short as a Reel on the Facebook Page of its language (Graph API, 3 phases: start, upload, finish).
# Pages and tokens come from credenciales/facebook.json ({"es": {"id", "token"}, "en": {...}}), written by fb_token.py.
# usage: python3 -I fb_upload.py <es|en> <video.mp4> <meta.json>      → prints the Reel URL
import json, os, sys, time, urllib.parse, urllib.request

V = "v27.0"
lang, video, meta_f = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
page = json.load(open(os.path.join(HERE, "..", "credenciales", "facebook.json")))[lang]
meta = json.load(open(meta_f))

def call(url, data=None, headers=None, body=None):
    if data is not None: body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)
    except urllib.error.HTTPError as e:  # Graph errors explain themselves; never echo the token
        raise RuntimeError(f"Facebook respondió {e.code}: {e.read().decode()[:400]}")

def publish():
    G = f"https://graph.facebook.com/{V}/{page['id']}/video_reels"
    vid = call(G, {"upload_phase": "start", "access_token": page["token"]})["video_id"]
    size = os.path.getsize(video)
    call(f"https://rupload.facebook.com/video-upload/{V}/{vid}", body=open(video, "rb").read(),
         headers={"Authorization": f"OAuth {page['token']}", "offset": "0", "file_size": str(size)})
    # Facebook wants the title inside the text; hashtags already live in the description
    text = meta["title"].split(" #")[0] + "\n\n" + meta["description"]
    call(G, {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": text,
             "is_ai_generated": "true" if meta.get("ia_visual") else "false", "access_token": page["token"]})
    for _ in range(30):  # wait until it is processed so the URL works when we log it
        try: st = call(f"https://graph.facebook.com/{V}/{vid}?fields=status&access_token={urllib.parse.quote(page['token'])}").get("status", {})
        except RuntimeError: time.sleep(10); continue  # after "finish" the Reel is already out: a failed status check must not upload it again
        if st.get("video_status") in ("ready", "published") or st.get("publishing_phase", {}).get("status") == "complete": break
        if st.get("video_status") == "error": raise RuntimeError(f"Facebook no pudo procesar el video: {st}")
        time.sleep(10)
    return f"https://www.facebook.com/reel/{vid}"

for attempt in range(3):  # only the upload/finish steps are retried; once finished, status hiccups never re-post
    try: print(publish()); break
    except RuntimeError as e:
        print(e, file=sys.stderr)
        if attempt == 2: sys.exit("Facebook no pudo publicar el video tras 3 intentos")
        time.sleep(30)
