import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

from vx_settlement_service import resolve_vx_settlement_query


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        status, payload = resolve_vx_settlement_query(parsed.query)
        self.respond_json(payload, status=status)

    def respond_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
