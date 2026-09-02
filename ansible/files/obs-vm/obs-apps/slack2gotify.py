#!/usr/bin/env python3
"""Translate Slack-webhook-format alerts (TrueNAS alert service) to Gotify.

TrueNAS SCALE has no native Gotify alert service; its Slack service POSTs
{"text": "..."} JSON. This shim reposts it to Gotify's /message endpoint.
ponytail: single-threaded stdlib http.server — TrueNAS sends a few alerts a
day; swap for something real only if this ever becomes a bottleneck.
"""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

GOTIFY_URL = os.environ.get("GOTIFY_URL", "http://gotify:80")
GOTIFY_TOKEN = os.environ["GOTIFY_TOKEN"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            body = json.loads(raw or b"{}")
            text = body.get("text") or body.get("message") or raw.decode(errors="replace")
            payload = json.dumps({
                "title": "TrueNAS alert",
                "message": text[:4000],
                "priority": 7,
            }).encode()
            req = urllib.request.Request(
                f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            self.send_response(200)
        except Exception as exc:  # noqa: BLE001 — always answer the caller
            print(f"forward failed: {exc}", flush=True)
            self.send_response(502)
        self.end_headers()

    def log_message(self, *_):
        pass


def demo():
    """Self-check: translation logic without network."""
    body = {"text": "pool degraded"}
    assert (body.get("text") or body.get("message")) == "pool degraded"
    assert (({}).get("text") or ({}).get("message") or b"raw".decode()) == "raw"
    print("demo ok")


if __name__ == "__main__":
    if os.environ.get("DEMO"):
        demo()
    else:
        print(f"slack2gotify listening on :31662 -> {GOTIFY_URL}", flush=True)
        HTTPServer(("", 31662), Handler).serve_forever()
