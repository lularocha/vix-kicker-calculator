import json
import urllib.parse
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler

from run import latest_vx_settlement


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        symbol = (params.get("symbol") or [""])[0].strip()
        requested_date = (params.get("dt") or [date.today().isoformat()])[0].strip()

        if not symbol:
            self.respond_json({"error": "Missing required query parameter: symbol"}, status=400)
            return

        try:
            datetime.strptime(requested_date, "%Y-%m-%d")
        except ValueError:
            self.respond_json({"error": "Query parameter dt must be YYYY-MM-DD"}, status=400)
            return

        try:
            payload = latest_vx_settlement(symbol, requested_date)
        except LookupError as exc:
            self.respond_json({"error": str(exc)}, status=404)
            return
        except Exception as exc:
            self.respond_json({"error": f"Cboe request failed: {exc}"}, status=502)
            return

        self.respond_json(payload)

    def respond_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
