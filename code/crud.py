# crud.py
# PURPOSE: Demonstrate full CRUD operations on InfluxDB
# This is the core of the project - shows how InfluxDB handles each operation

from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.delete_api import DeleteApi

# ── Connection settings ───────────────────────────────────────────────────────
INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "mySecretToken123"
INFLUX_ORG    = "ist769org"
INFLUX_BUCKET = "smarthome"

# Create one shared client for all operations
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)


# ═══════════════════════════════════════════════════════════════
# CREATE - Write new data points to InfluxDB
# ═══════════════════════════════════════════════════════════════
def create_reading(room: str, temperature: float, humidity: float):
    """
    Write a single sensor reading to InfluxDB RIGHT NOW.

    InfluxDB data model:
      - measurement : like a table name  → "sensors"
      - tag         : indexed label      → room="bedroom"
      - field       : actual value       → temperature_f=71.5
      - time        : when it happened   → auto-set to now
    """
    print(f"\n── CREATE ──────────────────────────────────────")
    print(f"Writing new reading: room={room}, temp={temperature}°F, humidity={humidity}%")

    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = (
        Point("sensors")
        .tag("room", room)
        .tag("home_id", "home_001")
        .field("temperature_f", temperature)
        .field("humidity_pct", humidity)
        .time(datetime.now(timezone.utc), "s")
    )

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    print(f"✅ Created: {room} → temp={temperature}°F, humidity={humidity}%")


# ═══════════════════════════════════════════════════════════════
# READ - Query data using Flux query language
# ═══════════════════════════════════════════════════════════════
def read_latest(room: str = None):
    """
    Read the most recent sensor readings.
    Flux is InfluxDB's query language - functional and pipeline-based.

    Flux query structure:
      from(bucket: "smarthome")         ← which bucket to query
        |> range(start: -1h)            ← time window (last 1 hour)
        |> filter(fn: (r) => ...)       ← filter rows
        |> last()                       ← get most recent value
    """
    print(f"\n── READ (latest readings) ──────────────────────")

    # Build filter clause - optionally filter by room
    room_filter = f'|> filter(fn: (r) => r["room"] == "{room}")' if room else ""

    flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -24h)
        |> filter(fn: (r) => r["_measurement"] == "sensors")
        {room_filter}
        |> filter(fn: (r) => r["_field"] == "temperature_f" or r["_field"] == "humidity_pct")
        |> last()
    '''

    query_api = client.query_api()
    tables = query_api.query(flux_query, org=INFLUX_ORG)

    results = {}
    for table in tables:
        for record in table.records:
            room_name = record.values.get("room")
            field     = record.get_field()
            value     = record.get_value()
            time      = record.get_time()

            if room_name not in results:
                results[room_name] = {"time": time}
            results[room_name][field] = value

    if results:
        print(f"{'Room':<15} {'Temperature (°F)':<20} {'Humidity (%)':<15} {'Last Updated'}")
        print("-" * 70)
        for room_name, data in results.items():
            temp = data.get("temperature_f", "N/A")
            hum  = data.get("humidity_pct", "N/A")
            t    = data.get("time", "")
            print(f"{room_name:<15} {temp:<20} {hum:<15} {t}")
    else:
        print("No data found.")

    return results


def read_average_last_hour(room: str):
    """
    Read the average temperature for a room over the last hour.
    Shows aggregation - a key InfluxDB strength.
    """
    print(f"\n── READ (1-hour average for {room}) ────────────")

    flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "sensors")
        |> filter(fn: (r) => r["room"] == "{room}")
        |> filter(fn: (r) => r["_field"] == "temperature_f")
        |> mean()
    '''

    query_api = client.query_api()
    tables = query_api.query(flux_query, org=INFLUX_ORG)

    for table in tables:
        for record in table.records:
            avg = round(record.get_value(), 2)
            print(f"✅ Average temperature in {room} (last 1hr): {avg}°F")

    return tables


def read_time_range(room: str, hours_back: int = 6):
    """
    Read all readings for a room over a time range.
    Shows time-windowed queries - InfluxDB's core strength.
    """
    print(f"\n── READ (last {hours_back}h of data for {room}) ───────────")

    flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -{hours_back}h)
        |> filter(fn: (r) => r["_measurement"] == "sensors")
        |> filter(fn: (r) => r["room"] == "{room}")
        |> filter(fn: (r) => r["_field"] == "temperature_f")
        |> sort(columns: ["_time"], desc: false)
    '''

    query_api = client.query_api()
    tables = query_api.query(flux_query, org=INFLUX_ORG)

    count = 0
    for table in tables:
        for record in table.records:
            count += 1

    print(f"✅ Found {count} temperature readings for '{room}' in last {hours_back} hours")
    return count


# ═══════════════════════════════════════════════════════════════
# UPDATE - InfluxDB is append-only (time-series by design)
# The "update" pattern is to write a new corrected point
# ═══════════════════════════════════════════════════════════════
def update_reading(room: str, corrected_temp: float, corrected_humidity: float):
    """
    InfluxDB does NOT support in-place updates like SQL's UPDATE statement.
    This is BY DESIGN for time-series data - historical data should be immutable.

    The correct pattern: write a NEW point with the corrected value at current time.
    If you need to correct a historical point, you delete the old range and rewrite it.

    This is an important architectural concept to mention in your project!
    """
    print(f"\n── UPDATE (append-only pattern) ─────────────────")
    print(f"Note: InfluxDB is append-only. Writing corrected value as new point...")

    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = (
        Point("sensors")
        .tag("room", room)
        .tag("home_id", "home_001")
        .tag("corrected", "true")           # tag to mark this as a correction
        .field("temperature_f", corrected_temp)
        .field("humidity_pct", corrected_humidity)
        .time(datetime.now(timezone.utc), "s")
    )

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    print(f"✅ Correction written: {room} → temp={corrected_temp}°F, humidity={corrected_humidity}%")
    print(f"   Tagged with corrected=true for audit trail")


# ═══════════════════════════════════════════════════════════════
# DELETE - Remove data for a time range
# ═══════════════════════════════════════════════════════════════
def delete_range(room: str, hours_back: int = 1):
    """
    Delete all readings for a specific room in the last N hours.
    InfluxDB deletes by time range + optional tag filter predicate.
    """
    print(f"\n── DELETE ──────────────────────────────────────")
    print(f"Deleting last {hours_back} hour(s) of data for room: {room}")

    now   = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours_back)

    delete_api = client.delete_api()
    delete_api.delete(
        start=start,
        stop=now,
        predicate=f'_measurement="sensors" AND room="{room}"',
        bucket=INFLUX_BUCKET,
        org=INFLUX_ORG
    )

    print(f"✅ Deleted readings for '{room}' from {start.strftime('%H:%M')} to {now.strftime('%H:%M')} UTC")
    print(f"   Verifying deletion...")

    # Verify it's gone
    remaining = read_time_range(room, hours_back)
    if remaining == 0:
        print(f"✅ Confirmed: all {room} data deleted for that range")
    else:
        print(f"⚠️  {remaining} points still exist (may be outside range)")


# ═══════════════════════════════════════════════════════════════
# MAIN - Run all CRUD operations as a demo
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  InfluxDB CRUD Demo — IST769 Project")
    print("  Smart Home Sensor Database")
    print("=" * 60)

    # CREATE
    create_reading("garage", temperature=65.3, humidity=60.1)

    # READ - latest from all rooms
    read_latest()

    # READ - latest from one room
    read_latest(room="bedroom")

    # READ - average over last hour
    read_average_last_hour("living_room")

    # READ - time range query
    read_time_range("kitchen", hours_back=6)

    # UPDATE (append-only pattern)
    update_reading("bedroom", corrected_temp=70.0, corrected_humidity=48.0)

    # DELETE
    delete_range("garage", hours_back=1)

    print("\n" + "=" * 60)
    print("  ✅ All CRUD operations completed successfully!")
    print("  Open localhost:8086 to explore data in InfluxDB UI")
    print("=" * 60)

    client.close()