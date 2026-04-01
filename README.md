# python-metar

An English-first Python CLI tool for fetching historical METAR weather data for a given station and exporting results to CSV.

Chinese documentation: [README.zh-CN.md](README.zh-CN.md)

## Features

- Fetch METAR by ICAO station code
- Query data for a user-defined lookback window (hours)
- Render terminal-friendly output
- Print raw METAR lines only
- Export records to CSV
- Implemented with Python standard library only (no third-party dependencies)

## Requirements

- Python 3.9+ (3.12 recommended)

## Quick Start

Run in the project directory:

```bash
python fetch_metar.py --station ZBAA --hours 6
```

If your `python` command does not point to the target interpreter, use the full path instead:

```bash
/home/zhuoqun/anaconda3/envs/metar/bin/python fetch_metar.py --station ZBAA --hours 6
```

## Arguments

- `--station`: ICAO station code, for example `ZBAA`, `EGLC`, `KJFK`
- `--hours`: Lookback duration in hours, for example `3`, `6`, `24`
- `--raw-only`: Print raw METAR lines only
- `--timeout`: HTTP timeout in seconds, default `15`
- `--csv`: Export CSV file path, for example `eglc_metar.csv`

## Examples

1. Query last 24 hours and print terminal output:

```bash
python fetch_metar.py --station EGLC --hours 24
```

2. Print raw METAR lines only:

```bash
python fetch_metar.py --station EGLC --hours 24 --raw-only
```

3. Export CSV:

```bash
python fetch_metar.py --station EGLC --hours 24 --csv eglc_metar.csv
```

4. Export CSV and print raw lines:

```bash
python fetch_metar.py --station EGLC --hours 24 --csv eglc_metar.csv --raw-only
```

## CSV Columns

Exported CSV includes:

- `station`
- `obs_time_utc`
- `flight_category`
- `wind_dir_deg`
- `wind_speed_kt`
- `visibility`
- `temperature_c`
- `dewpoint_c`
- `altimeter_hpa`
- `raw_metar`

## FAQ

1. No records returned

- Confirm the station code is correct.
- Some stations may not have observations in certain periods.

2. Network error or timeout

- Increase timeout with `--timeout`.
- Ensure your network can access the aviation weather API.

## Data Source

- API: https://aviationweather.gov/api/data/metar

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
