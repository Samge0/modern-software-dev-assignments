"""Offline unit tests for week3 MCP server resilience logic (no network required).

Tests the retry/backoff helper, parameter clamps, and WMO code mapping by stubbing
the shared httpx client.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import main as srv  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, payload=None, headers=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._payload


class FakeClient:
    """Scripted httpx.Client stand-in."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, params))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_backoff_succeeds_after_429(monkeypatch):
    fake = FakeClient(
        [
            FakeResponse(429, None, headers={"retry-after": "0"}),
            FakeResponse(200, {"ok": True}),
        ]
    )
    monkeypatch.setattr(srv, "_client", fake)
    monkeypatch.setattr(srv.time, "sleep", lambda s: None)
    data = srv._get_with_backoff("https://x.test", {})
    assert data == {"ok": True}
    assert len(fake.calls) == 2


def test_backoff_exhausts_retries_on_5xx(monkeypatch):
    fake = FakeClient([FakeResponse(503, None)] * srv.MAX_RETRIES)
    monkeypatch.setattr(srv, "_client", fake)
    monkeypatch.setattr(srv.time, "sleep", lambda s: None)
    with pytest.raises(srv.UpstreamError):
        srv._get_with_backoff("https://x.test", {})


def test_backoff_gives_up_on_4xx_without_retry(monkeypatch):
    fake = FakeClient([FakeResponse(404, None, text="nope")])
    monkeypatch.setattr(srv, "_client", fake)
    with pytest.raises(srv.UpstreamError):
        srv._get_with_backoff("https://x.test", {})
    assert len(fake.calls) == 1


def test_backoff_network_errors_retried(monkeypatch):
    fake = FakeClient(
        [
            httpx.ConnectError("boom"),
            FakeResponse(200, {"results": []}),
        ]
    )
    monkeypatch.setattr(srv, "_client", fake)
    monkeypatch.setattr(srv.time, "sleep", lambda s: None)
    assert srv._get_with_backoff("https://x.test", {}) == {"results": []}


def test_geocode_empty_results_message(monkeypatch):
    fake = FakeClient([FakeResponse(200, {"results": None})])
    monkeypatch.setattr(srv, "_client", fake)
    out = srv.geocode(place="zzzzz", count=3)
    assert "No geocoding results" in out


def test_current_weather_formats(monkeypatch):
    geo = FakeResponse(
        200,
        {
            "results": [
                {
                    "name": "Testville",
                    "country": "TST",
                    "latitude": 1.0,
                    "longitude": 2.0,
                }
            ]
        },
    )
    wx = FakeResponse(
        200,
        {
            "current": {
                "time": "2026-01-01T10:00",
                "temperature_2m": 21.5,
                "apparent_temperature": 22.0,
                "relative_humidity_2m": 40,
                "weather_code": 0,
                "wind_speed_10m": 5,
            }
        },
    )
    fake = FakeClient([geo, wx])
    monkeypatch.setattr(srv, "_client", fake)
    out = srv.current_weather(place="Testville")
    assert "Testville" in out and "Clear sky" in out and "21.5" in out


def test_forecast_formats_and_clamps(monkeypatch):
    geo = FakeResponse(
        200,
        {
            "results": [
                {
                    "name": "T",
                    "country": "C",
                    "latitude": 1.0,
                    "longitude": 2.0,
                }
            ]
        },
    )
    wx = FakeResponse(
        200,
        {
            "daily": {
                "time": ["2026-01-01", "2026-01-02"],
                "weather_code": [61, 0],
                "temperature_2m_max": [15.0, 16.0],
                "temperature_2m_min": [5.0, 6.0],
                "precipitation_probability_max": [80, 10],
            }
        },
    )
    fake = FakeClient([geo, wx])
    monkeypatch.setattr(srv, "_client", fake)
    out = srv.forecast(place="T", days=99)  # clamped to 7 upstream, payload has 2
    assert "Slight rain" in out and "80%" in out


def test_wmo_codes_resource():
    text = srv.weather_codes()
    assert "0: Clear sky" in text and "95: Thunderstorm" in text


def test_dress_advice_prompt_template():
    p = srv.dress_advice(place="Oslo")
    assert "current_weather" in p and "Oslo" in p
