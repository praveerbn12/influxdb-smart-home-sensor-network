# data_gen.py
# PURPOSE: Generate fake smart home sensor data and write it to InfluxDB
# This simulates 3 rooms with temperature + humidity sensors
# Data is written for the past 24 hours (one reading every 5 minutes)

import random
from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ── Connection settings (must match docker-compose.yml) ──────────────────────
INFLUX_URL   = "http://localhost:8086"
INFLUX_TOKEN = "mySecretToken123"
INFLUX_ORG   = "ist769org"
INFLUX_BUCKET = "smarthome"

# ── Rooms in our smart home ───────────────────────────────────────────────────
ROOMS = ["bedroom", "living_room", "kitchen"]

# ── Base values per room (realistic ranges) ───────────────────────────────────
ROOM_PROFILES = {
    "bedroom":     {"temp_base": 68.0, "humidity_base": 50.0},
    "living_room": {"temp_base": 72.0, "humidity_base": 45.0},
    "kitchen":     {"temp_base": 75.0, "humidity_base": 55.0},
}

def generate_sensor_data():
    """
    Generate 24 hours of sensor readings (every 5 minutes = 288 points per room)
    Total: 288 x 3 rooms = 864 data points
    """
    points = []
    now = datetime.now(timezone.utc)

    # Go back 24 hours, step every 5 minutes
    for minutes_ago in range(0, 24 * 60, 5):
        timestamp = now - timedelta(minutes=minutes_ago)

        for room in ROOMS:
            profile = ROOM_PROFILES[room]

            # Add small random variation to base values
            temperature = round(profile["temp_base"] + random.uniform(-3.0, 3.0), 2)
            humidity    = round(profile["humidity_base"] + random.uniform(-5.0, 5.0), 2)

            # Kitchen gets hotter during "meal times" (7-9am, 12-1pm, 6-8pm)
            hour = timestamp.hour
            if room == "kitchen" and hour in [7, 8, 12, 18, 19]:
                temperature += random.uniform(2.0, 6.0)

            # Build an InfluxDB Point
            # measurement = table name ("sensors")
            # tag         = indexed metadata (room name) - used for filtering
            # field       = actual measurement values (temp, humidity)
            # time        = timestamp of the reading
            point = (
                Point("sensors")
                .tag("room", room)
                .tag("home_id", "home_001")
                .field("temperature_f", round(temperature, 2))
                .field("humidity_pct", round(humidity, 2))
                .time(timestamp, "s")
            )
            points.append(point)

    return points


def write_data():
    """Connect to InfluxDB and write all generated points"""
    print("Connecting to InfluxDB...")

    # Create client connection
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

    # Write API - SYNCHRONOUS means wait for confirmation before continuing
    write_api = client.write_api(write_options=SYNCHRONOUS)

    print("Generating sensor data...")
    points = generate_sensor_data()
    print(f"Generated {len(points)} data points across {len(ROOMS)} rooms")

    print("Writing data to InfluxDB...")
    write_api.write(
        bucket=INFLUX_BUCKET,
        org=INFLUX_ORG,
        record=points
    )

    print(f"✅ Successfully wrote {len(points)} points to bucket '{INFLUX_BUCKET}'")
    print("Rooms:", ", ".join(ROOMS))
    print("Fields: temperature_f, humidity_pct")
    print("Time range: last 24 hours")

    client.close()


if __name__ == "__main__":
    write_data()