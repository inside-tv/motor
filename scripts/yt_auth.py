# One-time YouTube OAuth for a desktop client (stdlib only): opens the browser, catches the redirect on localhost,
# exchanges the code (PKCE) and saves the refresh token. Other scripts call access_token() to get a fresh token.
# usage: python3 -I yt_auth.py <client_secret.json> <token_out.json>
import base64, hashlib, http.server, json, os, secrets, sys, threading, time, urllib.parse, urllib.request, webbrowser

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]

def _post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r: return json.load(r)

def access_token(secret_file, token_file):
    c = json.load(open(secret_file))["installed"]; tok = json.load(open(token_file))
    if tok.get("expires_at", 0) > time.time() + 60: return tok["access_token"]
    r = _post(c["token_uri"], {"client_id": c["client_id"], "client_secret": c["client_secret"], "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"})
    tok.update(access_token=r["access_token"], expires_at=time.time() + r["expires_in"])
    json.dump(tok, open(token_file, "w")); os.chmod(token_file, 0o600)
    return tok["access_token"]

def authorize(secret_file, token_file):
    c = json.load(open(secret_file))["installed"]
    verifier = secrets.token_urlsafe(64); state = secrets.token_urlsafe(16)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    got = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query)); got.update(q)
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write("<h2>Listo. Ya puedes cerrar esta pestaña.</h2>".encode())
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); redirect = f"http://127.0.0.1:{srv.server_port}"
    url = c["auth_uri"] + "?" + urllib.parse.urlencode({"client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    print("Abriendo el navegador. Si no se abre, copia esta URL:\n" + url, flush=True)
    webbrowser.open(url)
    t = threading.Thread(target=srv.handle_request); t.start(); t.join(timeout=600); srv.server_close()
    if got.get("state") != state or "code" not in got: sys.exit(f"Autorización fallida: {got.get('error', 'sin respuesta')}")
    r = _post(c["token_uri"], {"client_id": c["client_id"], "client_secret": c["client_secret"], "code": got["code"],
        "code_verifier": verifier, "redirect_uri": redirect, "grant_type": "authorization_code"})
    tok = {"refresh_token": r["refresh_token"], "access_token": r["access_token"], "expires_at": time.time() + r["expires_in"], "scope": r.get("scope")}
    json.dump(tok, open(token_file, "w")); os.chmod(token_file, 0o600)
    # confirm which channel we are connected to
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true", headers={"Authorization": "Bearer " + tok["access_token"]})
    ch = json.load(urllib.request.urlopen(req))["items"][0]
    print(f"Conectado al canal: {ch['snippet']['title']} ({ch['snippet'].get('customUrl', '')}) · {ch['statistics'].get('subscriberCount')} suscriptores · {ch['statistics'].get('videoCount')} videos")

if __name__ == "__main__":
    authorize(sys.argv[1], sys.argv[2])
