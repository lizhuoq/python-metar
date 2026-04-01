# python-metar

一个以英文 README 为主、同时提供中文文档的 Python 命令行工具，用于获取指定站点在过去一段时间内的 METAR 气象数据，并支持导出 CSV。

英文主文档： [README.md](README.md)

## 功能

- 按 ICAO 站点代码查询 METAR
- 支持指定过去时长（小时）
- 支持终端表格输出
- 支持仅输出原始 METAR 报文
- 支持导出 CSV 文件
- 使用 Python 标准库实现，无需额外第三方依赖

## 环境要求

- Python 3.9 及以上（推荐 3.12）

## 快速开始

在项目目录执行：

```bash
python fetch_metar.py --station ZBAA --hours 6
```

如果你的环境中 `python` 指向的不是目标解释器，请替换为完整路径，例如：

```bash
/home/zhuoqun/anaconda3/envs/metar/bin/python fetch_metar.py --station ZBAA --hours 6
```

## 参数说明

- `--station`：ICAO 站点代码，例如 `ZBAA`、`EGLC`、`KJFK`
- `--hours`：回溯小时数，例如 `3`、`6`、`24`
- `--raw-only`：仅输出原始 METAR 报文
- `--timeout`：HTTP 超时时间（秒），默认 `15`
- `--csv`：导出 CSV 文件路径，例如 `eglc_metar.csv`

## 使用示例

1. 查询过去 24 小时 METAR 并打印表格：

```bash
python fetch_metar.py --station EGLC --hours 24
```

2. 仅输出原始报文：

```bash
python fetch_metar.py --station EGLC --hours 24 --raw-only
```

3. 导出 CSV：

```bash
python fetch_metar.py --station EGLC --hours 24 --csv eglc_metar.csv
```

4. 导出 CSV 且仅输出原始报文：

```bash
python fetch_metar.py --station EGLC --hours 24 --csv eglc_metar.csv --raw-only
```

## CSV 字段

导出的 CSV 包含以下字段：

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

## 常见问题

1. 查询不到数据

- 请先确认站点代码是否正确
- 某些站点在部分时段可能没有观测数据

2. 网络错误或超时

- 可通过 `--timeout` 增加超时时间
- 确认当前网络可访问航空气象数据接口

## 数据来源

- API: https://aviationweather.gov/api/data/metar

## 许可证

可按你的项目需求补充（例如 MIT）。
