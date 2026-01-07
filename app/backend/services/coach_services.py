from backend.state.global_state import GLOBAL_STATE
from backend.state import global_state
from backend.registry.trip_registry import TripRegistry
from pathlib import Path

DATA_ROOT = Path("driving-coach-app\\app\\data\\trips")
_registry = TripRegistry(DATA_ROOT)

def get_driver_status(driver_id: str):
    """
    Return status info for a selected driver.
    """
    driver_dir = DATA_ROOT / driver_id
    if not driver_dir.exists():
        return None

    trips = list_trips(driver_id)

    return {
        "driver_id": driver_id,
        "online": driver_id in GLOBAL_STATE.active_drivers
    }

def list_drivers():
    if not DATA_ROOT.exists():
        return []

    return sorted(
        p.name for p in DATA_ROOT.iterdir() if p.is_dir()
    )


def list_trips(driver_id):
    driver_dir = Path("app/data/trips") / driver_id
    if not driver_dir.exists():
        return []
    return sorted([p.name for p in driver_dir.iterdir() if p.is_dir()])

def list_segments(driver_id, trip_id):
    return _registry.list_segments(driver_id, trip_id)

def analyze_segment(driver_id, trip_id, segment_idx):
    return _registry.process_trip_segment(driver_id, trip_id, segment_idx)

# def get_driver_status():
#     """
#     Returns dict:
#     {
#         driver_id: {
#             name: str,
#             online: bool,
#             last_seen: float
#         }
#     }
#     """
#     return GLOBAL_STATE.get_driver_status()
