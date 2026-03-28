#!/usr/bin/env python3

import argparse
import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_FILE = "vix-kicker-calculator.html"
CBOE_SETTLEMENT_URL = "https://www-api.cboe.com/us/futures/market_statistics/settlement/csv/?dt={dt}"


@lru_cache(maxsize=32)
def fetch_settlement_rows(settlement_date: str) -> list[dict[str, str]]:
    url = CBOE_SETTLEMENT_URL.format(dt=settlement_date)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv",
            "User-Agent": "vix-kicker-calculator/1.0",
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        payload = response.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(payload))
    return list(reader)


def latest_vx_settlement(symbol: str, as_of_date: str) -> dict[str, object]:
    start = datetime.strptime(as_of_date, "%Y-%m-%d").date()

    for lookback in range(0, 10):
        candidate = start - timedelta(days=lookback)
        candidate_str = candidate.isoformat()

        try:
            rows = fetch_settlement_rows(candidate_str)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise

        for row in rows:
            if row.get("Product") == "VX" and row.get("Symbol") == symbol:
                price_text = (row.get("Price") or "").strip().rstrip("*")
                return {
                    "symbol": symbol,
                    "quote": float(price_text),
                    "source_date": candidate_str,
                    "source_url": "https://www.cboe.com/markets/us/futures/market-statistics/settlement/futures/daily",
                }

    raise LookupError(f"No official Cboe VX settlement found for {symbol} on or before {as_of_date}.")


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
        params = urllib.parse.parse_qs(query)
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
