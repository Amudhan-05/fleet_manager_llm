# backend/processing/scoring.py

"""
Driver scoring mechanism based on trip segment severities.
Calculates driver performance scores to help identify high-risk and safe drivers.
"""


def calculate_trip_score(segment_severities: list) -> dict:
    """
    Calculate a score for a single trip based on its segment severities.
    
    Args:
        segment_severities: List of dicts with "severity" key ("HIGH", "MEDIUM", "LOW")
    
    Returns:
        dict with trip_score, segment_breakdown, and risk_level
    """
    if not segment_severities:
        return {
            "trip_score": 100.0,
            "segment_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "risk_level": "SAFE"
        }
    
    high_count = sum(1 for seg in segment_severities if seg["severity"] == "HIGH")
    medium_count = sum(1 for seg in segment_severities if seg["severity"] == "MEDIUM")
    low_count = sum(1 for seg in segment_severities if seg["severity"] == "LOW")
    
    total_segments = len(segment_severities)
    
    # Scoring formula:
    # Start at 100 and deduct points for risky segments
    # HIGH severity: -5 points each
    # MEDIUM severity: -2 points each
    # LOW severity: 0 points
    trip_score = 100.0
    trip_score -= high_count * 5
    trip_score -= medium_count * 2
    
    # Ensure score stays between 0 and 100
    trip_score = max(0, min(100, trip_score))
    
    # Determine risk level - SIMPLIFIED: Only HIGH segments = High Risk
    if high_count > 0:
        risk_level = "HIGH_RISK"
    elif medium_count > 2 or trip_score < 70:
        risk_level = "MEDIUM_RISK"
    else:
        risk_level = "SAFE"
    
    return {
        "trip_score": round(trip_score, 1),
        "segment_count": total_segments,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "risk_level": risk_level
    }


def calculate_driver_score(all_trip_scores: list) -> dict:
    """
    Calculate an overall driver score based on all trip scores.
    
    Args:
        all_trip_scores: List of trip score dicts (from calculate_trip_score)
    
    Returns:
        dict with overall_score, trip_count, average_trip_score, and driver_rating
    """
    if not all_trip_scores:
        return {
            "overall_score": 100.0,
            "trip_count": 0,
            "average_trip_score": 100.0,
            "high_risk_trips": 0,
            "medium_risk_trips": 0,
            "safe_trips": 0,
            "driver_rating": "No Data"
        }
    
    trip_count = len(all_trip_scores)
    average_trip_score = sum(t["trip_score"] for t in all_trip_scores) / trip_count
    
    high_risk_count = sum(1 for t in all_trip_scores if t["risk_level"] == "HIGH_RISK")
    medium_risk_count = sum(1 for t in all_trip_scores if t["risk_level"] == "MEDIUM_RISK")
    safe_count = sum(1 for t in all_trip_scores if t["risk_level"] == "SAFE")
    
    # Overall score is weighted average, with emphasis on worst trips
    worst_trip = min(all_trip_scores, key=lambda x: x["trip_score"])["trip_score"]
    overall_score = (average_trip_score * 0.6 + worst_trip * 0.4)
    overall_score = round(overall_score, 1)
    
    # Assign driver rating
    if high_risk_count > 0:
        driver_rating = "High Risk"
    elif high_risk_count == 0 and medium_risk_count > trip_count // 2:
        driver_rating = "Needs Improvement"
    elif overall_score >= 85:
        driver_rating = "Excellent"
    elif overall_score >= 70:
        driver_rating = "Good"
    elif overall_score >= 50:
        driver_rating = "Fair"
    else:
        driver_rating = "Poor"
    
    return {
        "overall_score": overall_score,
        "trip_count": trip_count,
        "average_trip_score": round(average_trip_score, 1),
        "high_risk_trips": high_risk_count,
        "medium_risk_trips": medium_risk_count,
        "safe_trips": safe_count,
        "driver_rating": driver_rating
    }


def get_score_breakdown(trip_scores: list) -> dict:
    """
    Get a detailed breakdown of scoring statistics.
    
    Args:
        trip_scores: List of trip score dicts
    
    Returns:
        dict with detailed statistics for visualization
    """
    if not trip_scores:
        return {
            "total_segments": 0,
            "total_high": 0,
            "total_medium": 0,
            "total_low": 0,
            "high_percentage": 0.0,
            "medium_percentage": 0.0,
            "low_percentage": 0.0
        }
    
    total_segments = sum(t["segment_count"] for t in trip_scores)
    total_high = sum(t["high_count"] for t in trip_scores)
    total_medium = sum(t["medium_count"] for t in trip_scores)
    total_low = sum(t["low_count"] for t in trip_scores)
    
    if total_segments == 0:
        return {
            "total_segments": 0,
            "total_high": 0,
            "total_medium": 0,
            "total_low": 0,
            "high_percentage": 0.0,
            "medium_percentage": 0.0,
            "low_percentage": 0.0
        }
    
    return {
        "total_segments": total_segments,
        "total_high": total_high,
        "total_medium": total_medium,
        "total_low": total_low,
        "high_percentage": round(100 * total_high / total_segments, 1),
        "medium_percentage": round(100 * total_medium / total_segments, 1),
        "low_percentage": round(100 * total_low / total_segments, 1)
    }
