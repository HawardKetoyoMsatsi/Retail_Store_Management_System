"""Web server: routes URLs to the functions in the other files."""
import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from catalog import add_item, delete_item, items, list_catalog, update_item
from config import WEB_DIR
from daily import get_daily, recent_daily, save_daily
from dashboard import dashboard, init_payload
from helpers import BadRequest, today
from purchases import add_purchases, delete_purchase, recent_purchases
from reconcile import reconcile
from settings import set_capital
from stocktake import get_stocktake, save_stocktake


def read_web_file(name):
    """Return (bytes, content-type) for a file in the web folder, or None."""
    safe = os.path.basename(name)  # no folder tricks
    path = os.path.join(WEB_DIR, safe)
    if not os.path.isfile(path):
        return None
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        return f.read(), ctype


# ------------------------------------------------------------- the routes
# Add a new feature by adding a line here that points to a function.
GET_ROUTES = {
    "/api/init": lambda q: init_payload(),
    "/api/dashboard": lambda q: dashboard(),
    "/api/purchases": lambda q: recent_purchases(),
    "/api/daily": lambda q: get_daily(q.get("date", today())),
    "/api/dailies": lambda q: recent_daily(),
    "/api/items": lambda q: items(),
    "/api/catalog": lambda q: list_catalog(),
    "/api/stocktake": lambda q: get_stocktake(q.get("date")),
    "/api/reconcile": lambda q: reconcile(q.get("date", today())),
}

POST_ROUTES = {
    "/api/purchases": add_purchases,
    "/api/daily": save_daily,
    "/api/stocktake": save_stocktake,
    "/api/capital": set_capital,
    "/api/catalog": add_item,
    "/api/catalog/update": update_item,
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def route(self, method):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path
        if method == "GET":
            if p == "/":
                return read_web_file("index.html")
            if p.startswith("/static/"):
                return read_web_file(p[len("/static/"):])
            if p in GET_ROUTES:
                return GET_ROUTES[p](q)
        elif method == "POST" and p in POST_ROUTES:
            return POST_ROUTES[p](self.read_json())
        elif method == "DELETE":
            m = re.fullmatch(r"/api/purchases/(\d+)", p)
            if m:
                return delete_purchase(int(m.group(1)))
            m = re.fullmatch(r"/api/catalog/(\d+)", p)
            if m:
                return delete_item(int(m.group(1)))
        return None

    def handle_any(self, method):
        try:
            res = self.route(method)
            if res is None:
                return self.send(404, {"error": "Not found"})
            if isinstance(res, tuple):  # a web file: (bytes, content-type)
                return self.send(200, res[0], res[1])
            self.send(200, res)
        except BadRequest as e:
            self.send(400, {"error": str(e)})
        except Exception as e:  # keep the server alive
            self.send(500, {"error": f"Server error: {e}"})

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")
    def do_DELETE(self): self.handle_any("DELETE")
