#!/usr/bin/env python3
"""
Simple script to hit the quiz API endpoints repeatedly and print the output each time.
Reads the API URL from config.json.
"""

import json
import time
import urllib.request
import urllib.error

CONFIG_PATH = "config.json"
NUM_ROUNDS = 100

with open(CONFIG_PATH) as f:
    API = json.load(f)["apiBaseUrl"].rstrip("/")

ENDPOINTS = [
    ("GET",  f"{API}/submission/test@calpoly.edu", None),
    ("POST", f"{API}/submission/quiz", {"name": "Test", "email": "test@calpoly.edu", "uni": "csu", "submittedAt": "2026-01-01T00:00:00Z", "mcqAnswers": [], "correctAnswers": {}}),
    ("POST", f"{API}/submission/responses", {"name": "Test", "email": "test@calpoly.edu"}),
    ("POST", f"{API}/auth/send-code", {"email": "spam@calpoly.edu"}),
    ("POST", f"{API}/auth/verify-code", {"email": "spam@calpoly.edu", "code": "000000"}),
    ("POST", f"{API}/auth/refresh", {"refreshToken": "fake-token"}),
]


def hit(method, url, body):
    headers = {"Content-Type": "application/json"} if body else {}
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as ex:
        return 0, str(ex)


print(f"Target: {API}")
print(f"Rounds: {NUM_ROUNDS}  |  Endpoints: {len(ENDPOINTS)}")
print("=" * 80)

for i in range(1, NUM_ROUNDS + 1):
    print(f"\n--- Round {i}/{NUM_ROUNDS} ---")
    for method, url, body in ENDPOINTS:
        path = url.replace(API, "")
        start = time.time()
        status, resp_body = hit(method, url, body)
        elapsed = time.time() - start
        # truncate long responses
        preview = resp_body[:200] + ("..." if len(resp_body) > 200 else "")
        print(f"  [{status}] {method:4s} {path:<35s} ({elapsed:.2f}s) {preview}")

print("\n" + "=" * 80)
print("Done.")
