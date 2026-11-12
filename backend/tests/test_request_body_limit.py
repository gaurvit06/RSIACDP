import json
import unittest

from app.middleware import RequestBodyLimitMiddleware, RequestBodyTooLarge


def run_asgi(*, body_chunks=(), headers=(), path="/api/cases/upload", method="POST", limits=None, catch_body_overflow=False):
    messages = iter(body_chunks)
    sent = []
    inner_called = False

    async def receive():
        try:
            return next(messages)
        except StopIteration:
            return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    async def inner(scope, receive, send):
        nonlocal inner_called
        inner_called = True
        try:
            while True:
                message = await receive()
                if message["type"] != "http.request" or not message.get("more_body", False):
                    break
        except RequestBodyTooLarge:
            if not catch_body_overflow:
                raise
            await send({"type": "http.response.start", "status": 400, "headers": []})
            await send({"type": "http.response.body", "body": b"framework parser error", "more_body": False})
            return
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})

    scope = {"type": "http", "method": method, "path": path, "headers": list(headers)}
    app = RequestBodyLimitMiddleware(
        inner,
        limits=limits or {("POST", "/api/cases/upload"): 8},
        default_api_write_limit=8,
    )
    # The test ASGI app uses only immediate in-memory receive/send functions. Drive
    # its coroutine directly so this unit test needs no sockets or event loop.
    coroutine = app(scope, receive, send)
    try:
        coroutine.send(None)
    except StopIteration:
        pass
    else:
        self_error = AssertionError("test ASGI middleware unexpectedly performed asynchronous I/O")
        coroutine.close()
        raise self_error
    return sent, inner_called


class RequestBodyLimitTests(unittest.TestCase):
    def test_rejects_oversized_content_length_before_calling_app(self):
        sent, inner_called = run_asgi(
            headers=[(b"content-length", b"9")],
            body_chunks=[{"type": "http.request", "body": b"x" * 9, "more_body": False}],
        )
        self.assertFalse(inner_called)
        self.assertEqual(sent[0]["status"], 413)
        self.assertEqual(json.loads(sent[1]["body"])["detail"], "Request body exceeds the configured size limit")

    def test_counts_chunked_body_and_rejects_overflow(self):
        sent, inner_called = run_asgi(
            body_chunks=[
                {"type": "http.request", "body": b"12345", "more_body": True},
                {"type": "http.request", "body": b"6789", "more_body": False},
            ],
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 413)

    def test_rejects_streamed_overflow_even_when_declared_length_is_smaller(self):
        sent, inner_called = run_asgi(
            headers=[(b"content-length", b"4")],
            body_chunks=[
                {"type": "http.request", "body": b"12345", "more_body": True},
                {"type": "http.request", "body": b"6789", "more_body": False},
            ],
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 413)

    def test_rewrites_framework_parser_error_after_stream_overflow(self):
        sent, inner_called = run_asgi(
            body_chunks=[{"type": "http.request", "body": b"123456789", "more_body": False}],
            catch_body_overflow=True,
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 413)
        self.assertEqual(json.loads(sent[1]["body"])["detail"], "Request body exceeds the configured size limit")

    def test_allows_body_at_limit_and_ignores_non_api_routes(self):
        sent, inner_called = run_asgi(
            headers=[(b"content-length", b"8")],
            body_chunks=[{"type": "http.request", "body": b"12345678", "more_body": False}],
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 200)

        sent, inner_called = run_asgi(
            path="/health",
            headers=[(b"content-length", b"999")],
            body_chunks=[{"type": "http.request", "body": b"x", "more_body": False}],
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 200)

    def test_rejects_invalid_content_length(self):
        sent, inner_called = run_asgi(headers=[(b"content-length", b"many")])
        self.assertFalse(inner_called)
        self.assertEqual(sent[0]["status"], 400)

    def test_default_limit_covers_other_api_write_routes_but_not_non_api_paths(self):
        sent, inner_called = run_asgi(
            path="/api/auth/login",
            headers=[(b"content-length", b"9")],
            body_chunks=[{"type": "http.request", "body": b"x" * 9, "more_body": False}],
        )
        self.assertFalse(inner_called)
        self.assertEqual(sent[0]["status"], 413)

        sent, inner_called = run_asgi(
            path="/health",
            headers=[(b"content-length", b"999999")],
            body_chunks=[{"type": "http.request", "body": b"x", "more_body": False}],
        )
        self.assertTrue(inner_called)
        self.assertEqual(sent[0]["status"], 200)
