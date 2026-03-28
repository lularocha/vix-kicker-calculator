#!/usr/bin/env python3

import argparse
import json
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from vx_settlement_service import resolve_vx_settlement_query


ROOT = Path(__file__).resolve().parent
HTML_FILE = "vix-kicker-calculator.html"


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/vx-settlement":
            self.handle_vx_settlement(parsed.query)
            return

        if parsed.path in ("/", "/index.html"):
            self.path = f"/{HTML_FILE}"

        super().do_GET()

    def handle_vx_settlement(self, query: str):
        status, payload = resolve_vx_settlement_query(query)
        self.respond_json(payload, status=status)

    def respond_json(self, payload: dict[str, object], status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Serve the VIX kicker calculator locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Serving {HTML_FILE} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
