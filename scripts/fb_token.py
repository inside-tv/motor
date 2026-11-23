# One-time setup on your own computer: turns a short user token from the Graph API Explorer into Page tokens that do not
# expire, saves them in credenciales/facebook.json (chmod 600) and uploads them to the FB_PAGES secret. No token is printed.
# The long-lived user token and app credentials stay in credenciales/facebook_app.json so the script can run again with --reusar.
# usage: python3 -I scripts/fb_token.py [--reusar]
import getpass, json, os, subprocess, sys, urllib.parse, urllib.request

V = "v27.0"
PAGES = {"es": ("Adentro TV", "adentrotv.es"), "en": ("Inside TV", "insidetv.en")}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CRED = os.path.join(ROOT, "credenciales")

def get(path, **q):
    try:
        with urllib.request.urlopen(f"https://graph.facebook.com/{V}/{path}?" + urllib.parse.urlencode(q), timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: sys.exit(f"Facebook respondió {e.code} en {path}: {json.load(e).get('error', {}).get('message')}")

def save(name, data):
    os.makedirs(CRED, exist_ok=True)
    fd = os.open(os.path.join(CRED, name), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as o: json.dump(data, o)

if "--reusar" in sys.argv:
    app = json.load(open(os.path.join(CRED, "facebook_app.json")))
else:
    app = {"id": input("ID de la app: ").strip(), "secret": getpass.getpass("Clave secreta de la app (no se verá): ").strip()}
    short = getpass.getpass("Token de usuario del Explorador (no se verá): ").strip()
    app["user_token"] = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app["id"],
                            client_secret=app["secret"], fb_exchange_token=short)["access_token"]
    save("facebook_app.json", app)
tok = app["user_token"]

granted = [p["permission"] for p in get("me/permissions", access_token=tok).get("data", []) if p.get("status") == "granted"]
print("permisos concedidos:", ", ".join(granted) or "ninguno")
pages = get("me/accounts", fields="id,name,username,access_token,instagram_business_account{id,username}", access_token=tok, limit=100).get("data", [])
print("páginas que ve la app:", ", ".join(f"{p['name']} ({p.get('username') or p['id']})" for p in pages) or "ninguna")

out = {}
for lang, (name, user) in PAGES.items():
    p = next((p for p in pages if p.get("username") == user or p["name"].strip().lower() == name.lower()), None)
    if not p: print(f"⚠ no encontré la página «{name}»"); continue
    exp = get("debug_token", input_token=p["access_token"], access_token=f"{app['id']}|{app['secret']}")["data"].get("expires_at")
    out[lang] = {"id": p["id"], "name": p["name"], "token": p["access_token"]}
    ig = p.get("instagram_business_account")
    if ig: out[lang]["ig_id"] = ig["id"]
    print(f"✓ {name}: página {p['id']} · token {'sin caducidad' if not exp else 'caduca ' + str(exp)}"
          f" · Instagram {'@' + ig.get('username', '?') if ig else 'sin vincular'}")
if not out: sys.exit("no se guardó nada")
save("facebook.json", out)
subprocess.run(["gh", "secret", "set", "FB_PAGES"], input=json.dumps(out).encode(), cwd=ROOT, check=True)
print("secreto FB_PAGES guardado en GitHub")
