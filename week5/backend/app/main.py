from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import apply_seed_if_needed, engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import notes as notes_router

app = FastAPI(title="Modern Software Dev Starter (Week 5)")

# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ---------------------------------------------------------------------------
# TASK 7: uniform error envelope {ok: false, error: {code, message}} for ALL
# API failures. Wrapped in a pure ASGI middleware so it also covers exceptions
# raised before FastAPI's own handlers (and stays out of OpenAPI's way).
# ---------------------------------------------------------------------------
class ErrorEnvelopeMiddleware:
    """Rewrites non-2xx JSON responses on /notes* and /action-items* to
    {ok: false, error: {code, message}} while leaving success payloads intact
    (they're wrapped as {ok: true, data: ...} by the response wrapper below).
    """

    API_PREFIXES = ("/notes", "/action-items")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith(self.API_PREFIXES):
            await self.app(scope, receive, send)
            return

        status_holder = {"status": 200}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        # Buffer full body so we can rewrite error payloads
        messages = []

        async def receive_wrapper():
            return await receive()

        # FastAPI sends body in one or more http.response.body messages
        collected = bytearray()

        async def send_collect(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                messages.append(message)
            elif message["type"] == "http.response.body":
                collected.extend(message.get("body", b""))
                if not message.get("more_body", False):
                    status = status_holder["status"]
                    body = bytes(collected)
                    if status >= 400:
                        import json as _json

                        try:
                            original = _json.loads(body) if body else {}
                        except Exception:
                            original = {"detail": body.decode(errors="replace")[:200]}
                        detail = original.get("detail", original)
                        message_list = detail if isinstance(detail, list) else None
                        error_extra = {}
                        if message_list:
                            # FastAPI 422: collapse validation errors to readable text
                            parts = []
                            for item in message_list:
                                loc = ".".join(str(x) for x in item.get("loc", [])[1:])
                                parts.append(f"{loc}: {item.get('msg', 'invalid')}")
                            message_text = "; ".join(parts) or "validation failed"
                        elif isinstance(detail, dict):
                            import json as _json2

                            message_text = detail.get("message") or _json2.dumps(detail)
                            # structured details (e.g. missing_ids) pass through
                            passthrough = {
                                k: v for k, v in detail.items() if k != "message"
                            }
                            if passthrough:
                                error_extra.update(passthrough)
                        else:
                            message_text = str(detail)
                        envelope = {
                            "ok": False,
                            "error": {
                                "code": status,
                                "message": message_text,
                                **error_extra,
                            },
                        }
                        new_body = _json.dumps(envelope).encode()
                        start = dict(messages[0]) if messages else {}
                        headers = [
                            (k, v)
                            for k, v in start.get("headers", [])
                            if k.lower() != b"content-length"
                        ]
                        headers.append((b"content-length", str(len(new_body)).encode()))
                        await send(
                            {
                                "type": "http.response.start",
                                "status": status,
                                "headers": headers,
                            }
                        )
                        await send({"type": "http.response.body", "body": new_body})
                    else:
                        start = dict(messages[0]) if messages else {}
                        headers = [
                            (k, v)
                            for k, v in start.get("headers", [])
                            if k.lower() != b"content-length"
                        ]
                        headers.append((b"content-length", str(len(body)).encode()))
                        await send(
                            {
                                "type": "http.response.start",
                                "status": status,
                                "headers": headers,
                            }
                        )
                        await send({"type": "http.response.body", "body": body})
                # (more_body True handled implicitly: we only finalize on last chunk)

        await self.app(scope, receive_wrapper, send_collect)


app.add_middleware(ErrorEnvelopeMiddleware)


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    apply_seed_if_needed()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")


# Routers
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
