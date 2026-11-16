"""
RETAIL STORE MANAGER: start here.

Run:   python app.py
Open:  http://localhost:8000   (it opens automatically)
"""
import os
import threading
import webbrowser
from http.server import ThreadingHTTPServer

from config import DB_PATH, PORT
from database import init_db
from server import Handler


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Retail Store Manager running at {url}  (Ctrl+C to stop)")
    print(f"Data file: {DB_PATH}")
    if not os.environ.get("NO_BROWSER"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
