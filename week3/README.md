# Week 3 — Custom MCP Server: Open-Meteo Weather

A Model Context Protocol server wrapping the real, public **Open-Meteo** APIs:

- Geocoding API — `https://geocoding-api.open-meteo.com/v1/search`
- Forecast API — `https://api.open-meteo.com/v1/forecast`

Both endpoints are free and key-less; the server adds timeouts, retry with
exponential backoff (honoring `Retry-After`) on 429/5xx, graceful error text on
network failures and empty results, and stderr-only logging (stdout stays clean
for the STDIO JSON-RPC stream).

## Prerequisites

- Python ≥ 3.10 with `mcp>=1.20,<2`, `httpx`, `uvicorn` (for HTTP mode)
- Outbound internet access to `*.open-meteo.com`

## Run locally (STDIO transport)

```bash
python week3/server/main.py            # STDIO JSON-RPC on stdin/stdout
```

Register in **Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["<abs-path>/week3/server/main.py"],
      "env": { "MCP_LOG_LEVEL": "INFO" }
    }
  }
}
```

Or point any MCP-aware IDE (Cursor etc.) at the same command.

### Example invocation flow (Claude Desktop)

1. Type: *“Geocode Beijing”* → client calls `geocode(place="Beijing", count=3)`
2. Type: *“What's the weather in Shanghai right now?”* → `current_weather(place="Shanghai")`
3. Type: *“Tokyo forecast for the next 3 days”* → `forecast(place="Tokyo", days=3)`

## Run remotely (HTTP transport + bearer auth — extra credit)

```bash
export MCP_HTTP_TOKEN="your-secret"
python week3/server/main.py --http --host 127.0.0.1 --port 8137
```

- Without `Authorization: Bearer <token>` → `401 {"error":"unauthorized"}`
- With a valid token → SSE MCP session (`GET /sse` + `POST /messages/?session_id=...`)
- The bearer token is validated in middleware and **never forwarded upstream**;
  Open-Meteo receives no credentials at all.

Verified locally:

```
$ curl http://127.0.0.1:8137/sse
{"error": "unauthorized", "detail": "missing or invalid bearer token"}
$ curl -H "Authorization: Bearer your-secret" http://127.0.0.1:8137/sse
event: endpoint
data: /messages/?session_id=69e80035e9dd49f69ce06ccb90940563
```

## Tool reference

| Tool | Parameters | Example output |
|---|---|---|
| `geocode` | `place: str`, `count: int = 3` (1–10) | JSON array of candidates with name/country/lat/lon/timezone |
| `current_weather` | `place: str` | `Current weather in Shanghai, China … Clear sky, 23.0°C (feels like 26.2°C), Humidity 81%, Wind 3.0 km/h` |
| `forecast` | `place: str`, `days: int = 3` (1–7) | Per-day condition, min~max °C, precipitation chance % |

Resource: `weather://codes` — WMO weather-code legend.
Prompt: `dress_advice(place)` — template that chains `current_weather` into clothing advice.

Error behaviour: every failure path returns human-readable `Error: …` text
(no server crash): unknown place, upstream timeout after 3 retries, HTTP 4xx,
empty forecast payloads.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `MCP_HTTP_TIMEOUT` | `10` | Upstream per-request timeout (seconds) |
| `MCP_MAX_RETRIES` | `3` | Retry budget for 429/5xx/network errors |
| `MCP_LOG_LEVEL` | `INFO` | stderr log verbosity |
| `MCP_HTTP_TOKEN` | — | Required for `--http` mode (bearer auth) |

## Tests

```bash
# offline unit tests (stubbed httpx, no network): retry/backoff, clamps, formatting
python -m pytest week3/tests/test_server.py -q

# live end-to-end over real STDIO + real Open-Meteo calls
python week3/tests/e2e_stdio.py
```

Last live run: 9/9 offline tests passed; e2e returned real data for Beijing
(geocode), Shanghai (23.0°C clear) and Tokyo (2-day drizzle forecast).
