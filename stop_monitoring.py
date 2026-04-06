import requests
import json
import warnings
import psycopg2
import os
from datetime import datetime
from psycopg2 import OperationalError
import time

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

API_KEY = os.environ.get("API_KEY")
AGENCY = os.environ.get("AGENCY", "SF")
STOP_CODE = os.environ.get("STOP_CODE", "13911")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "muni")
DB_USER = os.environ.get("DB_USER", "muni")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "munipass")

def get_conn(retries=10, delay=2):
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print("Connected to Postgres")
            return conn
        except OperationalError as e:
            print(f"Postgres not ready (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)

    raise RuntimeError("Could not connect to Postgres after multiple attempts")


def fetch_predictions():
    response = requests.get(
        "http://api.511.org/transit/StopMonitoring",
        params={
            "api_key": API_KEY,
            "agency": AGENCY,
            "stopCode": STOP_CODE,
            "format": "json"
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

    if not response.text:
        print("Empty response")
        return None

    return json.loads(response.text.encode().decode("utf-8-sig"))

def store_predictions(conn, data):
    visits = data["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]
    fetched_at = datetime.utcnow()

    with conn.cursor() as cur:
        for visit in visits:
            journey = visit["MonitoredVehicleJourney"]
            call = journey["MonitoredCall"]

            cur.execute("""
                INSERT INTO stop_predictions
                (recorded_at, stop_code, line, direction, vehicle_id, aimed_arrival, expected_arrival, occupancy, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stop_code, vehicle_id, expected_arrival) DO NOTHING
            """, (
                visit.get("RecordedAtTime"),
                STOP_CODE,
                journey.get("LineRef"),
                journey.get("DirectionRef"),
                journey.get("VehicleRef"),
                call.get("AimedArrivalTime"),
                call.get("ExpectedArrivalTime"),
                journey.get("Occupancy"),
                fetched_at
            ))

        conn.commit()

    print(f"Stored {len(visits)} predictions at {fetched_at}")

def fetch_vehicle_positions():
    response = requests.get(
        "http://api.511.org/transit/VehicleMonitoring",
        params={
            "api_key": API_KEY,
            "agency": AGENCY,
            "format": "json"
        }
    )

    if response.status_code != 200:
        print(f"VehicleMonitoring error: {response.status_code}")
        return None

    if not response.text:
        return None

    return json.loads(response.text.encode().decode("utf-8-sig"))

def store_vehicle_positions(conn, data):
    delivery = data["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]
    if isinstance(delivery, list):
        delivery = delivery[0]
    vehicles = delivery.get("VehicleActivity", [])
    fetched_at = datetime.utcnow()

    with conn.cursor() as cur:
        count = 0
        for activity in vehicles:
            journey = activity.get("MonitoredVehicleJourney", {})
            location = journey.get("VehicleLocation", {})
            lat = location.get("Latitude")
            lon = location.get("Longitude")

            if lat is None or lon is None:
                continue

            cur.execute("""
                INSERT INTO vehicle_positions (vehicle_id, line, direction, latitude, longitude, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_id) DO UPDATE SET
                    line = EXCLUDED.line,
                    direction = EXCLUDED.direction,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    fetched_at = EXCLUDED.fetched_at
            """, (
                journey.get("VehicleRef"),
                journey.get("LineRef"),
                journey.get("DirectionRef"),
                float(lat),
                float(lon),
                fetched_at
            ))
            count += 1

        conn.commit()
    print(f"Stored {count} vehicle positions at {fetched_at}")

if __name__ == "__main__":
    conn = get_conn()

    data = fetch_predictions()
    if data:
        store_predictions(conn, data)
    else:
        print("No data fetched, skipping insert.")

    positions = fetch_vehicle_positions()
    if positions:
        store_vehicle_positions(conn, positions)
    else:
        print("No vehicle positions fetched, skipping insert.")

    conn.close()
