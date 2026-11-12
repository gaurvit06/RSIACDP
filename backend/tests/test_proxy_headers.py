import unittest

from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


def build_proxy_app():
    app = FastAPI()

    @app.get("/peer")
    def peer(request: Request):
        return {"client": request.client.host if request.client else None}

    return app


class ProxyTrustTests(unittest.TestCase):
    def test_untrusted_peer_cannot_spoof_forwarded_client_address(self):
        app = ProxyHeadersMiddleware(build_proxy_app(), trusted_hosts="127.0.0.1,::1")
        with TestClient(app, client=("198.51.100.10", 4321)) as client:
            response = client.get("/peer", headers={"X-Forwarded-For": "203.0.113.7"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["client"], "198.51.100.10")

    def test_configured_trusted_proxy_can_supply_forwarded_client_address(self):
        app = ProxyHeadersMiddleware(build_proxy_app(), trusted_hosts="127.0.0.1")
        with TestClient(app, client=("127.0.0.1", 4321)) as client:
            response = client.get("/peer", headers={"X-Forwarded-For": "203.0.113.7"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["client"], "203.0.113.7")


if __name__ == "__main__":
    unittest.main()
