from __future__ import annotations

import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from weather_service import DEFAULT_CSV_PATH, load_weather_csv

DATA_PATH = Path(DEFAULT_CSV_PATH)


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
        try:
            query = parse_qs(urlparse(self.path).query)
            selected_date = query.get("date", [""])[0].strip()

            dataframe = load_weather_csv(DATA_PATH)
            if dataframe.empty:
                self._send_json(
                    503,
                    {
                        "error": "Cached weather data is not ready yet. Run the scheduled refresh job first."
                    },
                )
                return

            if selected_date:
                dataframe = dataframe[dataframe["date"].astype(str) == selected_date].copy()

            records = dataframe.to_dict(orient="records")
            last_updated = None
            if DATA_PATH.exists():
                last_updated = DATA_PATH.stat().st_mtime

            self._send_json(
                200,
                {
                    "count": len(records),
                    "data": records,
                    "data_source": "shared_csv_cache",
                    "last_updated_unix": last_updated,
                },
            )
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
