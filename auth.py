"""Login protection for the tracker apps. Standard library only.

The site password comes from the APP_PASSWORD environment variable on Render.
Changing it signs everyone out.
"""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qs, urlparse

COOKIE = "tracker_session"
SESSION_SECONDS = 12 * 60 * 60
MAX_FAILURES = 10
LOCK_SECONDS = 60
TEAM = "team"
MAX_LOGIN_BODY = 4096

_failures = {}


def _users():
    password = os.environ.get("APP_PASSWORD", "").strip()
    return {TEAM: password} if password else {}


def _signature(name, password, expires):
    key = hashlib.sha256(
        ("%s|%s|%s" % (os.environ.get("MONGO_URI", ""), name, password)).encode("utf-8")
    ).digest()
    return hmac.new(key, ("%s|%s" % (name, expires)).encode("utf-8"), hashlib.sha256).hexdigest()


def _make_token(name, password):
    expires = int(time.time()) + SESSION_SECONDS
    return "%s.%d.%s" % (name.encode("utf-8").hex(), expires, _signature(name, password, expires))


def _current_user(cookie_header):
    token = ""
    for part in (cookie_header or "").split(";"):
        key, _, value = part.strip().partition("=")
        if key == COOKIE:
            token = value
    try:
        name_hex, expires, sig = token.split(".")
        name = bytes.fromhex(name_hex).decode("utf-8")
        expires = int(expires)
    except ValueError:
        return None
    password = _users().get(name)
    if password is None or expires < time.time():
        return None
    if not hmac.compare_digest(sig.encode("utf-8"), _signature(name, password, expires).encode("utf-8")):
        return None
    return name


def _is_locked(name):
    record = _failures.get(name)
    if not record:
        return False
    count, since = record
    if time.time() - since > LOCK_SECONDS:
        _failures.pop(name, None)
        return False
    return count >= MAX_FAILURES


def _record_failure(name):
    if len(_failures) > 1000:
        _failures.clear()
    count, since = _failures.get(name, (0, time.time()))
    _failures[name] = (count + 1, since)


def _check_login(name, password):
    expected = _users().get(name)
    matches = hmac.compare_digest(
        password.encode("utf-8"), (expected or "\0").encode("utf-8")
    )
    return expected is not None and matches


# Added to each app's page: return to login when a session ends, and a log out button.
PAGE_SNIPPET = """<script>
(function(){
var f=window.fetch;
window.fetch=function(){return f.apply(this,arguments).then(function(r){if(r.status===401){location.href='/login';}return r;});};
document.addEventListener('DOMContentLoaded',function(){
var s=document.createElement('style');
s.textContent='@media print{#authLogout{display:none!important}}';
document.head.appendChild(s);
var form=document.createElement('form');
form.id='authLogout';form.method='post';form.action='/logout';
form.style.cssText='position:fixed;left:12px;bottom:12px;z-index:9999;margin:0';
form.innerHTML='<button type="submit" style="padding:7px 12px;border-radius:8px;border:1px solid #94a3b8;background:#fff;color:#334155;font:13px Tahoma,Arial,sans-serif;cursor:pointer">خروج / Log out</button>';
document.body.appendChild(form);
});
})();
</script>"""


def add_logout(html):
    return html.replace("<head>", "<head>" + PAGE_SNIPPET, 1)


def _login_page(app_name, message):
    note = '<p class="msg">%s</p>' % message if message else ""
    return """<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#f1f5f9;color:#1e293b;font-family:"Segoe UI",Tahoma,Arial,sans-serif;padding:16px}
form{background:#fff;width:100%%;max-width:360px;padding:28px;border-radius:12px;border:1px solid #e2e8f0}
h1{font-size:21px;margin:0 0 20px;text-align:center}
label{display:block;font-size:14px;margin:14px 0 6px}
input{width:100%%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;font-size:16px}
button{width:100%%;margin-top:22px;padding:12px;border:0;border-radius:8px;background:#1e293b;color:#fff;font-size:16px;cursor:pointer}
.msg{background:#fef2f2;color:#991b1b;padding:10px;border-radius:8px;font-size:14px;margin:0 0 8px;text-align:center}
</style></head><body>
<form method="post" action="/login">
<h1>%s</h1>%s
<label for="p">الرجاء إدخال كلمة المرور / Please enter your password</label>
<input id="p" name="password" type="password" autocomplete="current-password" required autofocus>
<button type="submit">دخول / Log in</button>
</form></body></html>""" % (app_name, app_name, note)


def protect(handler_class, app_name, cron_path=None):
    """Return a handler that requires login for everything except the login page.

    cron_path, if given, may instead be called with ?key=<CRON_KEY>.
    """

    class Protected(handler_class):
        def _reply(self, code, body, ctype, headers=()):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def _show_login(self, message="", code=200):
            self._reply(code, _login_page(app_name, message), "text/html; charset=utf-8")

        def _redirect(self, target, cookie=None):
            headers = [("Location", target)]
            if cookie:
                headers.append(("Set-Cookie", cookie))
            self._reply(303, "", "text/plain", headers)

        def _deny(self, path):
            if self.command == "GET" and not path.startswith("/api/"):
                self._redirect("/login")
            else:
                self._reply(401, json.dumps({"error": "login required"}), "application/json")

        def _allowed(self, path):
            if _current_user(self.headers.get("Cookie")):
                return True
            self._deny(path)
            return False

        def _handle_login(self):
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_LOGIN_BODY:
                self._show_login("بيانات غير صحيحة / Invalid request", 400)
                return
            form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
            name = TEAM
            password = form.get("password", [""])[0]
            if _is_locked(name):
                self._show_login(
                    "محاولات كثيرة، حاول بعد دقيقة / Too many attempts, try again in a minute",
                    429,
                )
                return
            if not _check_login(name, password):
                _record_failure(name)
                self._show_login("كلمة المرور غير صحيحة / Wrong password", 401)
                return
            _failures.pop(name, None)
            token = _make_token(name, password)
            cookie = "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=Lax" % (
                COOKIE, token, SESSION_SECONDS)
            self._redirect("/", cookie)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/login":
                self._show_login()
                return
            if cron_path and parsed.path == cron_path:
                expected = os.environ.get("CRON_KEY", "")
                given = parse_qs(parsed.query).get("key", [""])[0]
                if expected and hmac.compare_digest(
                    given.encode("utf-8"), expected.encode("utf-8")
                ):
                    handler_class.do_GET(self)
                else:
                    self._reply(403, json.dumps({"error": "forbidden"}), "application/json")
                return
            if self._allowed(parsed.path):
                handler_class.do_GET(self)

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/login":
                self._handle_login()
            elif path == "/logout":
                cookie = "%s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" % COOKIE
                self._redirect("/login", cookie)
            elif self._allowed(path):
                handler_class.do_POST(self)

        def do_PUT(self):
            path = urlparse(self.path).path
            if self._allowed(path):
                handler_class.do_PUT(self)

        def do_DELETE(self):
            path = urlparse(self.path).path
            if self._allowed(path):
                handler_class.do_DELETE(self)

    if not _users():
        print("WARNING: APP_PASSWORD is not set, so nobody can log in.", flush=True)
    return Protected
