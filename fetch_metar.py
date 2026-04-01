#!/usr/bin/env python3
"""Fetch historical METAR data for a given station and lookback duration.

Examples:
  python fetch_metar.py --station ZBAA --hours 12
  python fetch_metar.py --station KJFK --hours 6 --raw-only
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API_BASE = "https://aviationweather.gov/api/data/metar"
TIMEZONE_API_BASE = "https://timeapi.io/api/TimeZone/coordinate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get METAR observations for a station in the past N hours."
    )
    parser.add_argument(
        "--station",
        required=True,
        help="ICAO station code, e.g. ZBAA, KJFK",
    )
    parser.add_argument(
        "--hours",
        type=float,
        required=True,
        help="Lookback duration in hours, e.g. 3, 6, 24",
    )
    parser.add_argument(
        "--raw-only",
        action="store_true",
        help="Only print raw METAR lines",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15,
        help="HTTP timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        help="Export fetched records to CSV file path, e.g. metar.csv",
    )
    parser.add_argument(
        "--utc",
        action="store_true",
        help="Force output timestamps in UTC instead of auto-detected station timezone",
    )
    return parser.parse_args()


def fetch_metar(station: str, hours: float, timeout: float) -> list[dict]:
    if hours <= 0:
        raise ValueError("hours must be greater than 0")

    params = {
        "ids": station.upper(),
        "format": "json",
        "hours": f"{hours:g}",
    }
    url = f"{API_BASE}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except HTTPError as err:
        raise RuntimeError(f"HTTP error {err.code}: {err.reason}") from err
    except URLError as err:
        raise RuntimeError(f"Network error: {err.reason}") from err

    try:
        data = json.loads(body)
    except json.JSONDecodeError as err:
        raise RuntimeError("API returned invalid JSON") from err

    if not isinstance(data, list):
        raise RuntimeError("Unexpected API response format")

    # Sort by observation time so output is always chronological.
    def sort_key(item: dict) -> str:
        return str(item.get("obsTime") or item.get("obsTimeUtc") or "")

    return sorted(data, key=sort_key)


def parse_obs_time(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    if isinstance(value, str):
        if not value:
            return None
        try:
            if value.isdigit():
                return datetime.fromtimestamp(int(value), timezone.utc)
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def detect_timezone_name(records: list[dict], timeout: float) -> str:
    lat = None
    lon = None

    if records:
        first = records[0]
        lat = first.get("lat")
        lon = first.get("lon")

    if lat is None or lon is None:
        return "UTC"

    try:
        params = urlencode({"latitude": lat, "longitude": lon})
        url = f"{TIMEZONE_API_BASE}?{params}"
        with urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        tz_name = payload.get("timeZone") if isinstance(payload, dict) else None
        if isinstance(tz_name, str) and tz_name:
            return tz_name
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        pass

    return "UTC"


def fmt_local_time(value: object, tz_name: str) -> str:
    dt_utc = parse_obs_time(value)
    if dt_utc is None:
        return "-"

    try:
        local_dt = dt_utc.astimezone(ZoneInfo(tz_name))
        return f"{local_dt.strftime('%Y-%m-%d %H:%M')} {tz_name}"
    except ZoneInfoNotFoundError:
        return dt_utc.strftime("%Y-%m-%d %H:%M UTC")


def csv_local_time(value: object, tz_name: str) -> str:
    dt_utc = parse_obs_time(value)
    if dt_utc is None:
        return ""
    try:
        return dt_utc.astimezone(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M:%S")
    except ZoneInfoNotFoundError:
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S")


def print_results(records: list[dict], raw_only: bool, tz_name: str) -> None:
    if not records:
        print("No METAR records found for the given station/time range.")
        return

    if raw_only:
        for r in records:
            raw = r.get("rawOb") or r.get("raw_text")
            if raw:
                print(raw)
        return

    print(f"Total records: {len(records)}")
    time_col = f"Obs Time({tz_name})"
    print("-" * 112)
    print(
        f"{time_col:30} {'Flight Category':16} {'Wind':14} {'Vis':8} {'Temp/Dew':10} Raw METAR"
    )
    print("-" * 112)

    for r in records:
        obs_time = fmt_local_time(r.get("obsTime") or r.get("obsTimeUtc"), tz_name)
        category = r.get("flightCategory") or "-"
        wind = (
            f"{r.get('wdir', '-')}/{r.get('wspd', '-')}kt"
            if r.get("wdir") is not None or r.get("wspd") is not None
            else "-"
        )
        vis = r.get("visib") or r.get("visibility") or "-"
        temp = r.get("temp") if r.get("temp") is not None else "-"
        dewp = r.get("dewp") if r.get("dewp") is not None else "-"
        temp_dew = f"{temp}/{dewp}"
        raw = r.get("rawOb") or r.get("raw_text") or "-"

        print(
            f"{obs_time:30} {str(category):16} {str(wind):14} {str(vis):8} {temp_dew:10} {raw}"
        )


def write_csv(records: list[dict], csv_path: str, tz_name: str) -> None:
    fields = [
        "station",
        "obs_time",
        "timezone",
        "flight_category",
        "wind_dir_deg",
        "wind_speed_kt",
        "visibility",
        "temperature_c",
        "dewpoint_c",
        "altimeter_hpa",
        "raw_metar",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for r in records:
            writer.writerow(
                {
                    "station": r.get("icaoId") or r.get("station") or "",
                    "obs_time": csv_local_time(
                        r.get("obsTime") or r.get("obsTimeUtc"), tz_name
                    ),
                    "timezone": tz_name,
                    "flight_category": r.get("flightCategory") or "",
                    "wind_dir_deg": r.get("wdir") if r.get("wdir") is not None else "",
                    "wind_speed_kt": r.get("wspd") if r.get("wspd") is not None else "",
                    "visibility": r.get("visib") or r.get("visibility") or "",
                    "temperature_c": r.get("temp") if r.get("temp") is not None else "",
                    "dewpoint_c": r.get("dewp") if r.get("dewp") is not None else "",
                    "altimeter_hpa": r.get("altim") if r.get("altim") is not None else "",
                    "raw_metar": r.get("rawOb") or r.get("raw_text") or "",
                }
            )


def main() -> int:
    args = parse_args()

    try:
        records = fetch_metar(args.station, args.hours, args.timeout)
    except (ValueError, RuntimeError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    tz_name = "UTC" if args.utc else detect_timezone_name(records, args.timeout)

    if args.csv_path:
        try:
            write_csv(records, args.csv_path, tz_name)
            print(f"CSV exported: {args.csv_path}")
        except OSError as err:
            print(f"Error: failed to write CSV: {err}", file=sys.stderr)
            return 1

    print_results(records, args.raw_only, tz_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
