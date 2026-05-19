# InfluxDB Smart Home Sensor Network

A time-series database project that simulates smart-home sensor data and stores it in InfluxDB for querying, analysis, and dashboard visualization.

## Project Overview

This project simulates IoT-style sensor readings from multiple rooms in a smart home environment. The generated data includes temperature, humidity, and motion readings collected at fixed time intervals.

The goal of this project is to understand how time-series databases work and how InfluxDB can be used for sensor data, monitoring, and observability use cases.

## Tech Stack

- InfluxDB 2.7
- Python
- Docker Compose
- Grafana
- Flux Query Language
- InfluxDB Python Client

## Data Model

**Measurement**

```text
sensors
```

**Tags**

```text
room
home_id
```

**Fields**

```text
temperature_f
humidity_pct
motion
```

### Why tags and fields?

In InfluxDB, tags are indexed and useful for filtering/grouping data. Fields store the actual measured values.

For this project:

- `room` and `home_id` are tags because we often filter sensor data by room or home.
- `temperature_f`, `humidity_pct`, and `motion` are fields because they are the actual sensor readings.

## Project Structure

```text
influxdb-smart-home-sensor-network/
├── docker-compose.yml
├── code/
│   ├── data_gen.py
│   ├── crud.py
│   └── requirements.txt
├── data/
├── .gitignore
└── README.md
```

## Features

- Simulates smart-home sensor readings
- Stores time-series data in InfluxDB
- Uses measurements, tags, and fields correctly
- Demonstrates Python-based data insertion
- Demonstrates CRUD/query operations using the InfluxDB Python client
- Uses Flux queries for time-based analysis
- Can be connected to Grafana for dashboard visualization

## Workflow

```text
Python Data Generator
        ↓
InfluxDB Bucket
        ↓
Flux Queries
        ↓
Grafana Dashboard
```

## How to Run

### 1. Start InfluxDB using Docker

From the project root, run:

```bash
docker compose up -d
```

### 2. Install Python dependencies

```bash
cd code
pip install -r requirements.txt
```

### 3. Generate sensor data

```bash
python data_gen.py
```

### 4. Run CRUD/query operations

```bash
python crud.py
```

## Example Use Cases

This project represents a simplified version of real-world monitoring systems such as:

- Smart-home temperature monitoring
- Motion detection analytics
- IoT device telemetry
- Environmental monitoring dashboards
- Observability pipelines

## Key Learning

This project helped me understand:

- Time-series database design
- InfluxDB buckets, measurements, tags, and fields
- Why tags are used for filtering and fields are used for measured values
- Flux query syntax
- How IoT-style data can be stored and analyzed
- How Grafana can visualize time-series data
- How time-series databases differ from traditional relational databases

## Future Improvements

- Add Grafana dashboard screenshots
- Add alerting for abnormal temperature or humidity values
- Add more rooms and sensor types
- Add retention policies
- Add scheduled/continuous data generation
- Add Dockerized Python service for automatic sensor simulation

## Status

Core data generation and InfluxDB interaction scripts are completed. Dashboard screenshots and additional documentation will be added as future improvements.
