from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv
from requests import Response
from requests.exceptions import RequestException, SSLError
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

CWA_DATASET_ID = "F-A0010-001"
CWA_REST_ENDPOINT = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{CWA_DATASET_ID}"
CWA_FILEAPI_ENDPOINT = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{CWA_DATASET_ID}"
DEFAULT_CSV_PATH = Path("weather_data.csv")
DEFAULT_DB_PATH = Path("data.db")
WEATHER_TABLE_NAME = "TemperatureForecasts"
DB_COLUMNS = ["id", "regionName", "dataDate", "mint", "maxt", "avgTemp", "lat", "lon"]
APP_COLUMNS = ["region", "date", "min_temp", "max_temp", "avg_temp", "lat", "lon"]

load_dotenv()

REGION_METADATA: dict[str, dict[str, Any]] = {
    "北部地區": {
        "aliases": ["北部地區", "北部", "Northern"],
        "lat": 25.05,
        "lon": 121.53,
    },
    "中部地區": {
        "aliases": ["中部地區", "中部", "Central"],
        "lat": 24.15,
        "lon": 120.67,
    },
    "南部地區": {
        "aliases": ["南部地區", "南部", "Southern"],
        "lat": 22.63,
        "lon": 120.30,
    },
    "東北部地區": {
        "aliases": ["東北部地區", "東北部", "Northeastern"],
        "lat": 24.75,
        "lon": 121.75,
    },
    "東部地區": {
        "aliases": ["東部地區", "東部", "Eastern"],
        "lat": 23.99,
        "lon": 121.60,
    },
    "東南部地區": {
        "aliases": ["東南部地區", "東南部", "Southeastern"],
        "lat": 22.76,
        "lon": 121.15,
    },
}

MIN_TEMP_NAMES = {
    "MinT",
    "最低溫",
    "最低溫度",
    "最低氣溫",
    "最小溫度",
}

MAX_TEMP_NAMES = {
    "MaxT",
    "最高溫",
    "最高溫度",
    "最高氣溫",
    "最大溫度",
}

NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


def _first_key(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = NUMBER_PATTERN.search(value)
        if match:
            return float(match.group(0))
    return None


def _normalize_date(raw_value: Any) -> str | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", maxsplit=1)[0]
    if " " in text:
        text = text.split(" ", maxsplit=1)[0]
    return text


def _extract_time_temperature(time_item: dict[str, Any]) -> float | None:
    element_value = time_item.get("ElementValue")
    if isinstance(element_value, list):
        for element in element_value:
            if isinstance(element, dict):
                for key in (
                    "MinTemperature",
                    "MaxTemperature",
                    "Temperature",
                    "AirTemperature",
                    "ParameterName",
                    "Value",
                    "value",
                ):
                    if key in element:
                        parsed = _to_float(element[key])
                        if parsed is not None:
                            return parsed
                for raw in element.values():
                    parsed = _to_float(raw)
                    if parsed is not None:
                        return parsed
            else:
                parsed = _to_float(element)
                if parsed is not None:
                    return parsed

    parameter = time_item.get("Parameter")
    if isinstance(parameter, dict):
        for key in ("ParameterName", "Value", "value"):
            if key in parameter:
                parsed = _to_float(parameter[key])
                if parsed is not None:
                    return parsed

    return None


def _match_region_name(raw_name: str) -> str | None:
    candidate = raw_name.strip()
    if candidate in REGION_METADATA:
        return candidate
    for canonical_name, metadata in REGION_METADATA.items():
        for alias in metadata["aliases"]:
            if alias and alias in candidate:
                return canonical_name
    return None


def _iter_locations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records", {})
    locations_root = _first_key(records, ("Locations", "locations")) or []
    locations: list[dict[str, Any]] = []

    if isinstance(locations_root, list):
        for bucket in locations_root:
            if not isinstance(bucket, dict):
                continue
            entries = _first_key(bucket, ("Location", "location")) or []
            if isinstance(entries, list):
                locations.extend([entry for entry in entries if isinstance(entry, dict)])
    return locations


def _extract_daily_series(
    location_item: dict[str, Any], target_element_names: set[str]
) -> dict[str, list[float]]:
    weather_elements = _first_key(location_item, ("WeatherElement", "weatherElement")) or []
    series: dict[str, list[float]] = {}

    for weather_element in weather_elements:
        if not isinstance(weather_element, dict):
            continue

        element_name = _first_key(weather_element, ("ElementName", "elementName")) or ""
        if element_name not in target_element_names:
            continue

        time_values = _first_key(weather_element, ("Time", "time")) or []
        for time_item in time_values:
            if not isinstance(time_item, dict):
                continue
            date_key = _normalize_date(
                _first_key(time_item, ("DataTime", "dataTime", "StartTime", "startTime"))
            )
            temp_value = _extract_time_temperature(time_item)
            if date_key is None or temp_value is None:
                continue
            series.setdefault(date_key, []).append(temp_value)
    return series


def _request_endpoint_json(url: str, params: dict[str, Any], timeout: int) -> Response:
    try:
        return requests.get(url, params=params, timeout=timeout, verify=True)
    except SSLError:
        disable_warnings(InsecureRequestWarning)
        try:
            return requests.get(url, params=params, timeout=timeout, verify=False)
        except RequestException as exc:
            raise RuntimeError(f"Failed to connect CWA API after SSL fallback: {exc}") from exc
    except RequestException as exc:
        raise RuntimeError(f"Failed to connect CWA API: {exc}") from exc


def _is_resource_not_found(response: Response) -> bool:
    if response.status_code != 404:
        return False
    text = response.text or ""
    return "resource not found" in text.lower()


def _validate_payload(payload: dict[str, Any]) -> None:
    if "success" in payload:
        success_value = str(payload.get("success", "")).lower()
        if success_value not in {"true", "1"}:
            message = payload.get("message") or payload.get("result", {}).get("message")
            raise RuntimeError(f"CWA API returned unsuccessful response: {message or payload}")
        return

    cwa_root = payload.get("cwaopendata")
    if isinstance(cwa_root, dict):
        status = str(cwa_root.get("status", "")).lower()
        if status and status not in {"actual", "ok", "success"}:
            raise RuntimeError(f"CWA file API returned unexpected status: {cwa_root.get('status')}")
        return

    raise RuntimeError("Unexpected CWA payload format.")


def _request_forecast(api_key: str, timeout: int = 30) -> dict[str, Any]:
    params = {"Authorization": api_key, "format": "JSON"}

    response = _request_endpoint_json(CWA_REST_ENDPOINT, params=params, timeout=timeout)
    if _is_resource_not_found(response):
        response = _request_endpoint_json(CWA_FILEAPI_ENDPOINT, params=params, timeout=timeout)

    try:
        response.raise_for_status()
    except RequestException as exc:
        detail = ""
        if response.text:
            detail = f" | response: {response.text[:200]}"
        raise RuntimeError(f"CWA API request failed: {exc}{detail}") from exc

    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        raise RuntimeError("CWA API response is not valid JSON.") from exc

    _validate_payload(payload)
    return payload


def _extract_daily_series_from_fileapi(
    location_item: dict[str, Any], element_name: str
) -> dict[str, list[float]]:
    weather_elements = location_item.get("weatherElements", {})
    if not isinstance(weather_elements, dict):
        return {}

    element = _first_key(
        weather_elements,
        (element_name, element_name.lower(), element_name.upper()),
    )
    if not isinstance(element, dict):
        return {}

    daily_items = _ensure_list(_first_key(element, ("daily", "Daily")))
    series: dict[str, list[float]] = {}

    for item in daily_items:
        if not isinstance(item, dict):
            continue
        date_key = _normalize_date(_first_key(item, ("dataDate", "DataDate", "date", "Date")))
        temp_value = _to_float(
            _first_key(item, ("temperature", "Temperature", "value", "Value"))
        )
        if date_key is None or temp_value is None:
            continue
        series.setdefault(date_key, []).append(temp_value)
    return series


def _iter_fileapi_locations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cwa_root = payload.get("cwaopendata", {})
    if not isinstance(cwa_root, dict):
        return []

    resources = cwa_root.get("resources", {})
    if not isinstance(resources, dict):
        return []

    all_locations: list[dict[str, Any]] = []
    for resource in _ensure_list(resources.get("resource")):
        if not isinstance(resource, dict):
            continue
        data_node = _first_key(resource, ("data", "Data")) or {}
        agr_node = _first_key(data_node, ("agrWeatherForecasts", "AgrWeatherForecasts")) or {}
        forecasts = _first_key(agr_node, ("weatherForecasts", "WeatherForecasts")) or {}
        locations = _ensure_list(_first_key(forecasts, ("location", "Location")))
        all_locations.extend([item for item in locations if isinstance(item, dict)])
    return all_locations


def _build_rows_from_fileapi(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for location_item in _iter_fileapi_locations(payload):
        location_name = str(location_item.get("locationName", "")).strip()
        region_name = _match_region_name(location_name)
        if region_name is None:
            continue

        min_series = _extract_daily_series_from_fileapi(location_item, "MinT")
        max_series = _extract_daily_series_from_fileapi(location_item, "MaxT")
        daily_keys = sorted(set(min_series) | set(max_series))

        for date_key in daily_keys:
            min_values = min_series.get(date_key, [])
            max_values = max_series.get(date_key, [])
            rows.append(
                {
                    "region": region_name,
                    "date": date_key,
                    "min_temp": min(min_values) if min_values else None,
                    "max_temp": max(max_values) if max_values else None,
                }
            )
    return rows


def _build_rows_from_rest(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for location_item in _iter_locations(payload):
        location_name = str(_first_key(location_item, ("LocationName", "locationName")) or "")
        region_name = _match_region_name(location_name)
        if region_name is None:
            continue

        min_series = _extract_daily_series(location_item, MIN_TEMP_NAMES)
        max_series = _extract_daily_series(location_item, MAX_TEMP_NAMES)
        daily_keys = sorted(set(min_series) | set(max_series))

        for date_key in daily_keys:
            min_values = min_series.get(date_key, [])
            max_values = max_series.get(date_key, [])
            rows.append(
                {
                    "region": region_name,
                    "date": date_key,
                    "min_temp": min(min_values) if min_values else None,
                    "max_temp": max(max_values) if max_values else None,
                }
            )
    return rows


def _sort_app_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    sorted_df = dataframe.copy()
    sorted_df["date"] = sorted_df["date"].astype(str)
    sorted_df["region"] = pd.Categorical(
        sorted_df["region"],
        categories=list(REGION_METADATA.keys()),
        ordered=True,
    )
    sorted_df = sorted_df.sort_values(["date", "region"]).reset_index(drop=True)
    sorted_df["region"] = sorted_df["region"].astype(str)
    return sorted_df


def _normalize_app_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in APP_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized = normalized[APP_COLUMNS].copy()
    for column in ("min_temp", "max_temp", "avg_temp", "lat", "lon"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized["region"] = normalized["region"].astype(str)
    normalized["date"] = normalized["date"].astype(str)
    return _sort_app_dataframe(normalized)


def _to_storage_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    app_df = _normalize_app_dataframe(dataframe)
    storage_df = app_df.rename(
        columns={
            "region": "regionName",
            "date": "dataDate",
            "min_temp": "mint",
            "max_temp": "maxt",
            "avg_temp": "avgTemp",
        }
    )
    return storage_df[["regionName", "dataDate", "mint", "maxt", "avgTemp", "lat", "lon"]].copy()


def _from_storage_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(columns=APP_COLUMNS)
    app_df = dataframe.rename(
        columns={
            "regionName": "region",
            "dataDate": "date",
            "mint": "min_temp",
            "maxt": "max_temp",
            "avgTemp": "avg_temp",
        }
    )
    return _normalize_app_dataframe(app_df)


def _ensure_output_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _connect_sqlite(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_file = Path(db_path)
    _ensure_output_directory(db_file)
    return sqlite3.connect(db_file)


def initialize_weather_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect_sqlite(db_path) as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {WEATHER_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regionName TEXT NOT NULL,
                dataDate TEXT NOT NULL,
                mint REAL NOT NULL,
                maxt REAL NOT NULL,
                avgTemp REAL NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                UNIQUE(regionName, dataDate)
            )
            """
        )


def _build_weather_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    if "cwaopendata" in payload:
        rows = _build_rows_from_fileapi(payload)
    else:
        rows = _build_rows_from_rest(payload)

    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return dataframe

    dataframe["min_temp"] = pd.to_numeric(dataframe["min_temp"], errors="coerce")
    dataframe["max_temp"] = pd.to_numeric(dataframe["max_temp"], errors="coerce")
    dataframe = dataframe.dropna(subset=["min_temp", "max_temp"])

    dataframe = (
        dataframe.groupby(["region", "date"], as_index=False)
        .agg(min_temp=("min_temp", "min"), max_temp=("max_temp", "max"))
        .copy()
    )
    dataframe["avg_temp"] = (dataframe["min_temp"] + dataframe["max_temp"]) / 2
    dataframe["lat"] = dataframe["region"].map(lambda region: REGION_METADATA[region]["lat"])
    dataframe["lon"] = dataframe["region"].map(lambda region: REGION_METADATA[region]["lon"])
    return _normalize_app_dataframe(dataframe)


def fetch_raw_forecast_payload(api_key: str | None = None) -> dict[str, Any]:
    api_key = (api_key or os.getenv("CWA_API_KEY", "")).strip()
    if not api_key:
        raise ValueError(
            "CWA API key is missing. Please set CWA_API_KEY or pass --api-key explicitly."
        )
    return _request_forecast(api_key=api_key)


def fetch_weather_dataframe(api_key: str | None = None) -> pd.DataFrame:
    payload = fetch_raw_forecast_payload(api_key=api_key)
    dataframe = _build_weather_dataframe(payload)
    if dataframe.empty:
        raise RuntimeError("No target region temperature data was extracted from CWA response.")
    return dataframe


def dump_raw_payload_json(api_key: str | None = None) -> str:
    payload = fetch_raw_forecast_payload(api_key=api_key)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def dump_extracted_temperature_json(api_key: str | None = None) -> str:
    dataframe = fetch_weather_dataframe(api_key=api_key)
    extracted_records = _to_storage_dataframe(dataframe)[["regionName", "dataDate", "mint", "maxt"]]
    return json.dumps(extracted_records.to_dict(orient="records"), ensure_ascii=False, indent=2)


def save_weather_csv(
    output_path: str | Path = DEFAULT_CSV_PATH,
    api_key: str | None = None,
    dataframe: pd.DataFrame | None = None,
) -> pd.DataFrame:
    output = Path(output_path)
    _ensure_output_directory(output)
    weather_df = dataframe.copy() if dataframe is not None else fetch_weather_dataframe(api_key=api_key)
    weather_df = _normalize_app_dataframe(weather_df)
    weather_df.to_csv(output, index=False, encoding="utf-8-sig")
    return weather_df


def save_weather_sqlite(
    output_path: str | Path = DEFAULT_DB_PATH,
    api_key: str | None = None,
    dataframe: pd.DataFrame | None = None,
) -> pd.DataFrame:
    weather_df = dataframe.copy() if dataframe is not None else fetch_weather_dataframe(api_key=api_key)
    storage_df = _to_storage_dataframe(weather_df)
    initialize_weather_database(output_path)

    records = [
        (
            row.regionName,
            row.dataDate,
            float(row.mint),
            float(row.maxt),
            float(row.avgTemp),
            float(row.lat),
            float(row.lon),
        )
        for row in storage_df.itertuples(index=False)
    ]

    with _connect_sqlite(output_path) as connection:
        connection.execute(f"DELETE FROM {WEATHER_TABLE_NAME}")
        connection.executemany(
            f"""
            INSERT INTO {WEATHER_TABLE_NAME} (
                regionName, dataDate, mint, maxt, avgTemp, lat, lon
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

    return _normalize_app_dataframe(weather_df)


def save_weather_artifacts(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    db_path: str | Path = DEFAULT_DB_PATH,
    api_key: str | None = None,
) -> pd.DataFrame:
    weather_df = fetch_weather_dataframe(api_key=api_key)
    save_weather_csv(output_path=csv_path, dataframe=weather_df)
    save_weather_sqlite(output_path=db_path, dataframe=weather_df)
    return weather_df


def load_weather_csv(csv_path: str | Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame(columns=APP_COLUMNS)
    dataframe = pd.read_csv(path)
    return _normalize_app_dataframe(dataframe)


def load_weather_sqlite(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame(columns=APP_COLUMNS)

    initialize_weather_database(path)
    with _connect_sqlite(path) as connection:
        dataframe = pd.read_sql_query(
            f"""
            SELECT id, regionName, dataDate, mint, maxt, avgTemp, lat, lon
            FROM {WEATHER_TABLE_NAME}
            ORDER BY dataDate, id
            """,
            connection,
        )
    return _from_storage_dataframe(dataframe)


def get_available_regions(db_path: str | Path = DEFAULT_DB_PATH) -> list[str]:
    path = Path(db_path)
    if not path.exists():
        return []

    initialize_weather_database(path)
    with _connect_sqlite(path) as connection:
        rows = connection.execute(
            f"SELECT DISTINCT regionName FROM {WEATHER_TABLE_NAME}"
        ).fetchall()

    region_values = {str(row[0]) for row in rows}
    return [region for region in REGION_METADATA if region in region_values]


def list_all_region_names(db_path: str | Path = DEFAULT_DB_PATH) -> list[str]:
    return get_available_regions(db_path)


def load_region_forecast(region: str, db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame(columns=APP_COLUMNS)

    initialize_weather_database(path)
    with _connect_sqlite(path) as connection:
        dataframe = pd.read_sql_query(
            f"""
            SELECT id, regionName, dataDate, mint, maxt, avgTemp, lat, lon
            FROM {WEATHER_TABLE_NAME}
            WHERE regionName = ?
            ORDER BY dataDate, id
            """,
            connection,
            params=[region],
        )
    return _from_storage_dataframe(dataframe)


def load_central_region_forecast(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    return load_region_forecast("中部地區", db_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch 7-day agricultural weather forecast from CWA and save as CSV + SQLite."
    )
    parser.add_argument("--api-key", dest="api_key", help="CWA API authorization key")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_CSV_PATH),
        help=f"Output CSV path (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--db-output",
        default=str(DEFAULT_DB_PATH),
        help=f"Output SQLite path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Print the raw CWA JSON payload using json.dumps.",
    )
    parser.add_argument(
        "--show-extracted",
        action="store_true",
        help="Print extracted temperature records using json.dumps.",
    )
    args = parser.parse_args()

    if args.show_json:
        print(dump_raw_payload_json(api_key=args.api_key))
        return

    if args.show_extracted:
        print(dump_extracted_temperature_json(api_key=args.api_key))
        return

    dataframe = save_weather_artifacts(
        csv_path=args.output,
        db_path=args.db_output,
        api_key=args.api_key,
    )
    all_regions = list_all_region_names(args.db_output)
    central_region_df = load_central_region_forecast(args.db_output)

    print(f"Saved {len(dataframe)} rows to {Path(args.output).resolve()}")
    print(f"Saved {len(dataframe)} rows to {Path(args.db_output).resolve()}")
    print("All regions:", ", ".join(all_regions))
    print("Central region rows:")
    print(central_region_df.to_string(index=False))


if __name__ == "__main__":
    main()
