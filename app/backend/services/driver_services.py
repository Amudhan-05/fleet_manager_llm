from pathlib import Path
from backend.registry.trip_registry import TripRegistry

# Root path to trip data
DATA_ROOT = Path("app/data/trips")

# Singleton registry
_registry = TripRegistry(DATA_ROOT)


def list_trips(driver_id: str):
    """
    Return list of trip IDs for a driver
    """
    driver_dir = DATA_ROOT / driver_id

    if not driver_dir.exists():
        return []

    return [
        d.name
        for d in driver_dir.iterdir()
        if d.is_dir()
    ]


def analyze_trip(driver_id: str, trip_id: str):
    """
    Run full pipeline for ONE trip
    """
    print(f">>> DRIVER SERVICE: analyzing {driver_id}/{trip_id}")

    results = _registry.process_trip(driver_id, trip_id)

    if not results:
        return {
            "status": "empty",
            "message": "No valid trip data"
        }

    r = results[0]  # we already enforce single segment

    return {
        "status": "ok",
        "trip_id": trip_id,
        "window_index": r["window_index"],
        "severity": r["severity"],
        "summary": r["summary"],
        "coaching": r["coaching"]
    }


def analyze_trip_segment(driver_id: str, trip_id: str, segment_idx: int):
    return _registry.process_trip_segment(driver_id, trip_id, segment_idx)

def get_segment_count(driver_id: str, trip_id: str) -> int:
    return _registry.list_segments(driver_id, trip_id)

def get_segments(driver_id, trip_id):
    return _registry.list_segments(driver_id, trip_id)

def analyze_segment(driver_id, trip_id, segment_idx):
    return _registry.process_trip_segment(driver_id, trip_id, segment_idx)
