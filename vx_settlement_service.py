import csv
import io
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from functools import lru_cache


CBOE_SETTLEMENT_URL = "https://www-api.cboe.com/us/futures/market_statistics/settlement/csv/?dt={dt}"
SETTLEMENT_SOURCE_URL = "https://www.cboe.com/markets/us/futures/market-statistics/settlement/futures/daily"


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
                    "source_url": SETTLEMENT_SOURCE_URL,
                }

    raise LookupError(f"No official Cboe VX settlement found for {symbol} on or before {as_of_date}.")


def resolve_vx_settlement_query(query: str) -> tuple[int, dict[str, object]]:
    params = urllib.parse.parse_qs(query)
    symbol = (params.get("symbol") or [""])[0].strip()
    requested_date = (params.get("dt") or [date.today().isoformat()])[0].strip()

    if not symbol:
        return 400, {"error": "Missing required query parameter: symbol"}

    try:
        datetime.strptime(requested_date, "%Y-%m-%d")
    except ValueError:
        return 400, {"error": "Query parameter dt must be YYYY-MM-DD"}

    try:
        return 200, latest_vx_settlement(symbol, requested_date)
    except LookupError as exc:
        return 404, {"error": str(exc)}
    except Exception as exc:
        return 502, {"error": f"Cboe request failed: {exc}"}
