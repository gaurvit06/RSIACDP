"""Privacy-oriented HTTP response middleware."""
from __future__ import annotations

import json


class RequestBodyTooLarge(Exception):
    """Raised before a request body larger than the configured cap is consumed."""


class RequestBodyLimitMiddleware:
    """Enforce bounded request bodies before FastAPI parses JSON or multipart forms."""

    def __init__(self, app, *, limits: dict[tuple[str, str], int], default_api_write_limit: int = 128 * 1024):
        self.app = app
        self.limits = {(method.upper(), path): limit for (method, path), limit in limits.items()}
        self.default_api_write_limit = default_api_write_limit
        if default_api_write_limit < 1 or any(limit < 1 for limit in self.limits.values()):
            raise ValueError("Request body limits must be positive")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "").upper()
        path = scope.get("path", "")
        limit = self.limits.get((method, path))
        if limit is None and path.startswith("/api/") and method in {"POST", "PATCH", "PUT"}:
            limit = self.default_api_write_limit
        if limit is None:
            await self.app(scope, receive, send)
            return

        content_lengths = [value for name, value in scope.get("headers", []) if name.lower() == b"content-length"]
        if content_lengths:
            try:
                if len(content_lengths) != 1:
                    raise ValueError
                declared_length = int(content_lengths[0])
                if declared_length < 0:
                    raise ValueError
            except ValueError:
                await self._respond(send, 400, "Invalid Content-Length")
                return
            if declared_length > limit:
                await self._respond(send, 413, "Request body exceeds the configured size limit")
                return

        consumed = 0
        overflowed = False
        response_started = False
        suppress_inner_response = False

        async def limited_receive():
            nonlocal consumed, overflowed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > limit:
                    overflowed = True
                    raise RequestBodyTooLarge
            return message

        async def track_send(message):
            nonlocal response_started, suppress_inner_response
            if suppress_inner_response:
                return
            if message["type"] == "http.response.start":
                if overflowed:
                    response_started = True
                    suppress_inner_response = True
                    await self._respond(send, 413, "Request body exceeds the configured size limit")
                    return
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, track_send)
        except RequestBodyTooLarge:
            if response_started:
                raise
            await self._respond(send, 413, "Request body exceeds the configured size limit")

    @staticmethod
    async def _respond(send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail}, separators=(",", ":")).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store, private"),
                    (b"pragma", b"no-cache"),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body, "more_body": False})


class ApiNoStoreMiddleware:
    """Prevent browsers and intermediary caches from retaining API payloads."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/api/"):
            await self.app(scope, receive, send)
            return

        async def send_no_store(message):
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in {b"cache-control", b"pragma", b"expires"}
                ]
                headers.extend(
                    [
                        (b"cache-control", b"no-store, private"),
                        (b"pragma", b"no-cache"),
                    ]
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_no_store)
