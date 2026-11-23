# One-time setup on your own computer: turns a short user token from the Graph API Explorer into Page tokens that do not
# expire, saves them in credenciales/facebook.json (chmod 600) and uploads them to the FB_PAGES secret. Nothing is printed.
# usage: python3 -I scripts/fb_token.py        (asks hidden for the app ID, app secret and user token)
import getpass, json, os, subprocess, sys, urllib.parse, urllib.request

V = "v27.0"
NAMES = {"es": "Adentro TV", "en": "Inside TV"}
def get(path, **q):
    try:
        with urllib.request.urlopen(f"https://graph.facebook.com/{V}/{path}?" + urllib.parse.urlencode(q), timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: sys.exit(f"Facebook respondió {e.code}: {json.load(e).get('error', {}).get('message')}")

app_id = input("ID de la app: ").strip()
secret = getpass.getpass("Clave secreta de la app (no se verá): ").strip()
short = getpass.getpass("Token de usuario del Explorador (no se verá): ").strip()
long_user = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app_id, client_secret=secret, fb_exchange_token=short)["access_token"]
pages = get("me/accounts", fields="id,name,access_token,instagram_business_account{id,username}", access_token=long_user, limit=100).get("data", [])
out = {}
for lang, name in NAMES.items():
    p = next((p for p in pages if p["name"].strip().lower() == name.lower()), None)
    if not p: print(f"⚠ no encontré la página «{name}» (¿la marcaste al autorizar?)"); continue
    exp = get("debug_token", input_token=p["access_token"], access_token=f"{app_id}|{secret}")["data"].get("expires_at")
    out[lang] = {"id": p["id"], "name": p["name"], "token": p["access_token"]}
    ig = p.get("instagram_business_account")
    if ig: out[lang]["ig_id"] = ig["id"]
    print(f"✓ {name}: página {p['id']} · token {'sin caducidad' if not exp else 'caduca ' + str(exp)}"
          f" · Instagram {'@' + ig.get('username', '?') if ig else 'sin vincular'}")
if not out: sys.exit("no se guardó nada")
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
f = os.path.join(root, "credenciales", "facebook.json")
os.makedirs(os.path.dirname(f), exist_ok=True)
fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as o: json.dump(out, o)
subprocess.run(["gh", "secret", "set", "FB_PAGES"], input=json.dumps(out).encode(), cwd=root, check=True)
print("secreto FB_PAGES guardado en GitHub")
