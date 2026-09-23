"""Week 3 — Custom MCP Server wrapping the Open-Meteo public APIs.

External APIs used (both free, no key required):
  - Geocoding:  https://geocoding-api.open-meteo.com/v1/search
  - Forecast:   https://api.open-meteo.com/v1/forecast

Transports:
  - STDIO (default):  python week3/server/main.py            (for Claude Desktop / Cursor)
  - HTTP + bearer auth: python week3/server/main.py --http   (extra credit: remote callable)

Tools (>=2 required by rubric):
  - geocode(place, count)          -> place candidates with lat/lon
  - current_weather(place)          -> resolve place then fetch current conditions
  - forecast(place, days)           -> daily forecast summary

Resources:
  - weather://codes                 -> WMO weather code legend

Prompts:
  - dress_advice(place)             -> user-facing prompt template for clothing advice

Resilience: timeouts on every call, retry with exponential backoff on 429/5xx,
graceful errors for empty results / network failures (returned as tool text, never
crashing the server). HTTP transport validates the Authorization bearer token from
MCP_HTTP_TOKEN and never forwards it upstream.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Logging: MUST go to stderr — stdout is reserved for the STDIO JSON-RPC stream.
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr,
    level=os.environ.get("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("weather-mcp")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = float(os.environ.get("MCP_HTTP_TIMEOUT", "10"))
MAX_RETRIES = int(os.environ.get("MCP_MAX_RETRIES", "3"))
USER_AGENT = "cs146s-week3-weather-mcp/1.0"

# Shared client (connection pooling); no auth headers — upstream needs none.
_client: httpx.Client | None = None


def _http() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
    return _client


class UpstreamError(RuntimeError):
    """Raised when the upstream API fails after retries."""


def _get_with_backoff(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """GET with retry/backoff on 429 & 5xx; raises UpstreamError on final failure."""
    last_error = "unknown error"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = _http().get(url, params=params)
        except httpx.HTTPError as exc:
            last_error = f"network error: {exc}"
            logger.warning("attempt %d/%d %s: %s", attempt, MAX_RETRIES, url, last_error)
        else:
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}"
                retry_after = resp.headers.get("retry-after")
                logger.warning("attempt %d/%d %s: %s (rate-limit/server error, will back off)",
                               attempt, MAX_RETRIES, url, last_error)
                # honor Retry-After when present, else exponential backoff
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.5 * (2 ** (attempt - 1))
                time.sleep(min(delay, 8.0))
                continue
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            break  # non-retryable client error
        if attempt < MAX_RETRIES:
            time.sleep(0.5 * (2 ** (attempt - 1)))
    raise UpstreamError(f"upstream request failed after {MAX_RETRIES} attempts: {last_error}")


WMO_CODES: Dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


# ---------------------------------------------------------------------------
# MCP server + tools
# ---------------------------------------------------------------------------
mcp = FastMCP("weather", instructions=(
    "Weather tools backed by Open-Meteo. Resolve place names with `geocode` first when "
    "you need coordinates; `current_weather` and `forecast` accept free-form place names "
    "and resolve them automatically."
))


@mcp.tool()
def geocode(place: str, count: int = 3) -> str:
    """Geocode a place name into candidate coordinates.

    Args:
        place: Place name (city, region) in English or local language.
        count: Max candidates to return (1-10).

    Returns:
        JSON array of candidates with name, country, latitude, longitude, timezone.
    """
    count = max(1, min(int(count), 10))
    try:
        data = _get_with_backoff(GEOCODING_URL, {
            "name": place, "count": count, "language": "en", "format": "json",
        })
    except UpstreamError as exc:
        return f"Error: {exc}"
    results: List[Dict[str, Any]] = data.get("results") or []
    if not results:
        return f"No geocoding results for '{place}'. Try a more common spelling or a nearby larger city."
    out = [
        {
            "name": r.get("name"),
            "country": r.get("country"),
            "admin1": r.get("admin1"),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "timezone": r.get("timezone"),
            "population": r.get("population"),
        }
        for r in results
    ]
    return json.dumps(out, ensure_ascii=False)


def _resolve_first(place: str) -> Dict[str, Any]:
    """Resolve a place name to the top geocoding hit; raise UpstreamError on none."""
    data = _get_with_backoff(GEOCODING_URL, {"name": place, "count": 1, "language": "en", "format": "json"})
    results = data.get("results") or []
    if not results:
        raise UpstreamError(f"no geocoding results for '{place}'")
    return results[0]


@mcp.tool()
def current_weather(place: str) -> str:
    """Get current weather conditions for a place (auto-geocoded).

    Args:
        place: Place name, e.g. "Beijing" or "Palo Alto".

    Returns:
        Human-readable current conditions (temperature, wind, humidity, weather).
    """
    try:
        loc = _resolve_first(place)
        data = _get_with_backoff(FORECAST_URL, {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "timezone": "auto",
        })
    except UpstreamError as exc:
        return f"Error: {exc}"
    cur = data.get("current") or {}
    code = cur.get("weather_code")
    desc = WMO_CODES.get(code, f"unknown code {code}")
    return (
        f"Current weather in {loc.get('name')}, {loc.get('country')} "
        f"(local time {cur.get('time')}):\n"
        f"- Condition: {desc}\n"
        f"- Temperature: {cur.get('temperature_2m')}°C (feels like {cur.get('apparent_temperature')}°C)\n"
        f"- Humidity: {cur.get('relative_humidity_2m')}%\n"
        f"- Wind: {cur.get('wind_speed_10m')} km/h"
    )


@mcp.tool()
def forecast(place: str, days: int = 3) -> str:
    """Get a daily weather forecast summary for a place (auto-geocoded).

    Args:
        place: Place name, e.g. "Beijing".
        days: Number of days (1-7).

    Returns:
        Per-day high/low, precipitation chance, and dominant condition.
    """
    days = max(1, min(int(days), 7))
    try:
        loc = _resolve_first(place)
        data = _get_with_backoff(FORECAST_URL, {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": days,
            "timezone": "auto",
        })
    except UpstreamError as exc:
        return f"Error: {exc}"
    daily = data.get("daily") or {}
    dates: List[str] = daily.get("time") or []
    if not dates:
        return f"Error: forecast API returned no daily data for '{place}'."
    lines = [f"{days}-day forecast for {loc.get('name')}, {loc.get('country')}:"]
    for i, date in enumerate(dates):
        code = daily.get("weather_code", [None] * len(dates))[i]
        desc = WMO_CODES.get(code, f"code {code}")
        tmax = daily.get("temperature_2m_max", [None] * len(dates))[i]
        tmin = daily.get("temperature_2m_min", [None] * len(dates))[i]
        pp = daily.get("precipitation_probability_max", [None] * len(dates))[i]
        lines.append(
            f"- {date}: {desc}, {tmin}~{tmax}°C, precipitation chance {pp}%"
        )
    return "\n".join(lines)


@mcp.resource("weather://codes")
def weather_codes() -> str:
    """WMO weather interpretation code legend used by Open-Meteo."""
    return "\n".join(f"{code}: {desc}" for code, desc in sorted(WMO_CODES.items()))


@mcp.prompt()
def dress_advice(place: str) -> str:
    """Prompt template: ask the assistant for clothing advice based on current weather."""
    return (
        f"First call the `current_weather` tool for {place}. Then, using the returned "
        f"temperature, condition, wind and humidity, recommend what to wear today in {place}. "
        "Keep it to 3 bullet points, practical, and mention rain gear if precipitation is likely."
    )


# ---------------------------------------------------------------------------
# HTTP transport with bearer-token auth (extra credit)
# ---------------------------------------------------------------------------
class _BearerAuthMiddleware:
    """ASGI middleware: require `Authorization: Bearer $MCP_HTTP_TOKEN` on every request.

    The token is validated locally and NEVER forwarded to upstream APIs (the shared
    httpx client sends no Authorization header at all).
    """

    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        expected = f"bearer {self.token}"
        if not secrets_compare(auth.lower(), expected):
            await self._send_json(send, 401, {"error": "unauthorized", "detail": "missing or invalid bearer token"})
            return
        await self.app(scope, receive, send)

    @staticmethod
    async def _send_json(send, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())],
        })
        await send({"type": "http.response.body", "body": payload})


def secrets_compare(a: str, b: str) -> bool:
    """Constant-time-ish comparison to avoid trivially timing-leaking the token."""
    import secrets as _secrets
    return _secrets.compare_digest(a.encode(), b.encode())


def main() -> None:
    parser = argparse.ArgumentParser(description="Weather MCP server (Open-Meteo)")
    parser.add_argument("--http", action="store_true", help="run HTTP transport with bearer auth instead of STDIO")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8137)
    args = parser.parse_args()

    if args.http:
        token = os.environ.get("MCP_HTTP_TOKEN", "")
        if not token:
            print("MCP_HTTP_TOKEN must be set for --http mode", file=sys.stderr)
            sys.exit(2)
        logger.info("starting HTTP MCP server on %s:%d (bearer auth enabled)", args.host, args.port)
        from mcp.server.sse import SseServerTransport  # streamable HTTP via SSE transport
        starlette_app = mcp.sse_app()  # FastMCP-built Starlette/SSE app
        app = _BearerAuthMiddleware(starlette_app, token)
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        logger.info("starting STDIO MCP server")
        mcp.run()  # defaults to stdio transport


if __name__ == "__main__":
    main()
