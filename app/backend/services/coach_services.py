from pathlib import Path
from backend.registry.trip_registry import TripRegistry
from backend.state.global_state import GLOBAL_STATE
from backend.processing.scoring import (
    calculate_trip_score,
    calculate_driver_score,
    get_score_breakdown
)

DATA_ROOT = Path("data/trips")
_registry = TripRegistry(DATA_ROOT)


def get_driver_status(driver_id: str):
    """
    Return status info for a selected driver.
    """
    driver_dir = DATA_ROOT / driver_id
    if not driver_dir.exists():
        return None


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
    
    driver_dir = DATA_ROOT / driver_id
    if driver_id.startswith("coach_"):
        raise ValueError("Coach ID passed as driver_id")
    if not driver_dir.exists():
        return []
    return sorted([p.name for p in driver_dir.iterdir() if p.is_dir()])

def list_segments(driver_id, trip_id):
    return _registry.list_segments(driver_id, trip_id)

def analyze_segment(driver_id, trip_id, segment_idx):
    return _registry.process_trip_segment(driver_id, trip_id, segment_idx)

def get_segment_severities(driver_id: str, trip_id: str):
    return _registry.list_segment_severities(driver_id, trip_id)


def get_trip_score(driver_id: str, trip_id: str) -> dict:
    """
    Calculate score for a single trip.
    
    Returns:
        dict with trip_score, segment_breakdown, and risk_level
    """
    try:
        segment_severities = get_segment_severities(driver_id, trip_id)
        trip_score = calculate_trip_score(segment_severities)
        return trip_score
    except Exception as e:
        return {"error": str(e), "trip_score": 0}


def get_driver_score(driver_id: str) -> dict:
    """
    Calculate overall driver score based on all trips.
    
    Returns:
        dict with overall_score, trip_count, average_trip_score, and driver_rating
    """
    try:
        trips = list_trips(driver_id)
        
        if not trips:
            return {
                "overall_score": 0,
                "trip_count": 0,
                "driver_rating": "No Data",
                "error": "No trips found for driver"
            }
        
        trip_scores = []
        for trip_id in trips:
            try:
                trip_score = get_trip_score(driver_id, trip_id)
                if "error" not in trip_score:
                    trip_scores.append(trip_score)
            except Exception as e:
                # Skip trips with errors
                print(f"Warning: Error processing trip {trip_id}: {e}")
                continue
        
        driver_score = calculate_driver_score(trip_scores)
        return driver_score
    except Exception as e:
        return {"error": str(e), "overall_score": 0}


def get_driver_score_breakdown(driver_id: str) -> dict:
    """
    Get detailed breakdown of driver's scores across all trips.
    
    Returns:
        dict with segment statistics and trip details
    """
    try:
        trips = list_trips(driver_id)
        trip_scores = []
        
        for trip_id in trips:
            try:
                trip_score = get_trip_score(driver_id, trip_id)
                if "error" not in trip_score:
                    trip_score["trip_id"] = trip_id
                    trip_scores.append(trip_score)
            except Exception as e:
                print(f"Warning: Error processing trip {trip_id}: {e}")
                continue
        
        breakdown = get_score_breakdown(trip_scores)
        breakdown["trips"] = trip_scores
        
        return breakdown
    except Exception as e:
        return {"error": str(e)}

