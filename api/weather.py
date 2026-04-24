from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from weather_service import fetch_weather_dataframe

CACHE_TTL_SECONDS = 1800
_CACHE_PAYLOAD: dict | None = None
_CACHE_TS = 0.0

load_dotenv()


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        global _CACHE_PAYLOAD, _CACHE_TS
        try:
            query = parse_qs(urlparse(self.path).query)
            selected_date = query.get("date", [""])[0].strip()

            api_key = os.getenv("CWA_API_KEY", "").strip()
            if not api_key:
                self._send_json(
                    400,
                    {"error": "Missing API key. Please set CWA_API_KEY in environment variables."},
                )
                return

            now = time.time()
            if _CACHE_PAYLOAD is None or (now - _CACHE_TS) > CACHE_TTL_SECONDS:
                dataframe = fetch_weather_dataframe(api_key=api_key)
                _CACHE_PAYLOAD = dataframe.to_dict(orient="records")
                _CACHE_TS = now

            records = _CACHE_PAYLOAD
            if selected_date:
                records = [row for row in records if str(row.get("date", "")) == selected_date]

            self._send_json(
                200,
                {
                    "count": len(records),
                    "cache_ttl_seconds": CACHE_TTL_SECONDS,
                    "data": records,
                },
            )
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
