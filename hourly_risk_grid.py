#!/usr/bin/env python3
"""
Hourly risk-grid refresh via POST.

Keeps LEWS risk cells up to date with fresh Open-Meteo weather so the
map and dashboard stay near real-time.

Usage (from repo root or backend/):

    python backend/scripts/hourly_risk_grid.py

    # one-shot regenerate
    python backend/scripts/hourly_risk_grid.py --once

Environment:
    BACKEND_URL                 default http://localhost:8000
    RISK_GRID_REFRESH_SECONDS   default 3600 (1 hour)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required. Install backend requirements first.", file=sys.stderr)
    sys.exit(1)

# Load shared .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    load_dotenv(root / "backend" / ".env", override=False)
except ImportError:
    pass


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
INTERVAL_SECONDS = int(os.getenv("RISK_GRID_REFRESH_SECONDS", "3600"))
# Grid builds take ~2-10 seconds for Uttarakhand (~1,534 H3 cells)
REQUEST_TIMEOUT = float(os.getenv("RISK_GRID_POST_TIMEOUT", "600"))


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{stamp}] {message}", flush=True)


def post_generate() -> dict:
    url = f"{BACKEND_URL}/risk-grid/generate"
    log(f"POST {url}")

    with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
        response = client.post(url)

    if response.status_code == 409:
        log("Generation already in progress — will retry next interval.")
        return {"status": "busy", "detail": response.text}

    response.raise_for_status()
    payload = response.json()
    log(
        f"OK — cells={payload.get('count')} "
        f"generated_at={payload.get('generated_at')}"
    )
    return payload


def run_loop(interval: int) -> None:
    log(
        f"Starting hourly risk-grid automation "
        f"(every {interval}s → {BACKEND_URL})"
    )

    while True:
        started = time.monotonic()
        try:
            post_generate()
        except httpx.HTTPError as exc:
            log(f"Request failed: {exc}")
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            log(f"Unexpected error: {exc}")

        elapsed = time.monotonic() - started
        sleep_for = max(0.0, interval - elapsed)
        log(f"Sleeping {sleep_for:.0f}s until next refresh...")
        time.sleep(sleep_for)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="POST /risk-grid/generate on an hourly schedule"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single POST and exit",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=INTERVAL_SECONDS,
        help="Seconds between POSTs (default: env or 3600)",
    )
    args = parser.parse_args()

    if args.once:
        try:
            post_generate()
        except httpx.HTTPError as exc:
            log(f"Request failed: {exc}")
            return 1
        return 0

    run_loop(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
