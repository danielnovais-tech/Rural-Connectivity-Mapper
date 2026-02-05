"""Analytics module for first-party event tracking.

This module provides privacy-aware analytics for tracking user interactions
and system metrics without relying on third-party services. All events are
logged locally to JSON Lines format.
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import time
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

# Application version - should match package version
APP_VERSION = "1.0.0-beta"

# Analytics data directory
ANALYTICS_DIR = Path("data/analytics")
EVENTS_FILE = ANALYTICS_DIR / "events.jsonl"

# Privacy settings
GEO_PRECISION_DECIMALS = 2  # Round lat/lon to 2 decimal places (~1km precision)


def ensure_analytics_directory():
    """Ensure analytics directory exists."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def safe_geo(latitude: float | None, longitude: float | None) -> dict[str, float] | None:
    """Convert precise coordinates to privacy-safe rounded coordinates.

    Rounds coordinates to 2 decimal places (~1km precision) to protect user privacy
    while still providing useful geographic insights.

    Args:
        latitude: Precise latitude coordinate
        longitude: Precise longitude coordinate

    Returns:
        Dict with rounded 'lat' and 'lon' keys, or None if inputs are None

    Example:
        >>> safe_geo(-23.5505199, -46.6333094)
        {'lat': -23.55, 'lon': -46.63}
    """
    if latitude is None or longitude is None:
        return None

    return {"lat": round(latitude, GEO_PRECISION_DECIMALS), "lon": round(longitude, GEO_PRECISION_DECIMALS)}


def generate_anonymous_user_id(session_id: str) -> str:
    """Generate a stable anonymous user ID from session ID.

    Creates a consistent hash-based ID that doesn't contain PII but remains
    stable for the session.

    Args:
        session_id: Session identifier (UUID)

    Returns:
        Anonymous user ID derived from session
    """
    # Use first 12 chars of session_id for brevity
    # In production, could use proper hashing with salt
    return f"anon_{session_id[:12]}"


def track_event(
    event_name: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    properties: Optional[Dict[str, Any]] = None,
    geo: Optional[Dict[str, float]] = None
) -> None:
    """Track an analytics event by appending to events.jsonl.

    Args:
        event_name: Name of the event (e.g., 'app_loaded', 'page_selected')
        session_id: Session identifier
        context: Context information (page, task, step, user_scenario)
        metrics: Numeric metrics (duration_ms, response_time_ms)
        properties: Event properties (provider_selected, cta, error_code)
        geo: Privacy-safe geographic coordinates (use safe_geo())
    """
    try:
        ensure_analytics_directory()

        event = {
            "event_name": event_name,
            "ts": datetime.now().isoformat(),
            "session_id": session_id,
            "anonymous_user_id": generate_anonymous_user_id(session_id),
            "app_version": APP_VERSION,
            "context": context or {},
            "metrics": metrics or {},
            "properties": properties or {},
        }

        # Only include geo if provided
        if geo:
            event["geo"] = geo

        # Append to JSON Lines file
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        logger.debug(f"Tracked event: {event_name}")

    except Exception as e:
        # Never fail the application due to analytics
        logger.error(f"Error tracking event {event_name}: {e}")


@contextmanager
def timed_event(
    event_name: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None,
    properties: Optional[Dict[str, Any]] = None,
    geo: Optional[Dict[str, float]] = None
):
    """Context manager to track events with duration measurement.

    Automatically measures the duration of the wrapped code block and
    includes it in the event metrics.

    Args:
        event_name: Name of the event
        session_id: Session identifier
        context: Context information
        properties: Event properties
        geo: Privacy-safe geographic coordinates

    Example:
        >>> with timed_event('recommendation_generated', session_id):
        ...     result = expensive_computation()
    """
    start_time = time()
    exception_occurred = False

    try:
        yield
    except Exception:
        exception_occurred = True
        raise
    finally:
        duration_ms = (time() - start_time) * 1000

        event_metrics = {"duration_ms": round(duration_ms, 2)}
        event_properties = properties or {}

        if exception_occurred:
            event_properties["error"] = True

        track_event(
            event_name=event_name,
            session_id=session_id,
            context=context,
            metrics=event_metrics,
            properties=event_properties,
            geo=geo,
        )


def read_events(limit: int | None = None) -> list:
    """Read analytics events from the events file.

    Args:
        limit: Maximum number of events to return (most recent first)

    Returns:
        List of event dictionaries
    """
    try:
        if not EVENTS_FILE.exists():
            return []

        events = []
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        # Return most recent first
        events.reverse()

        if limit:
            return events[:limit]
        return events

    except Exception as e:
        logger.error(f"Error reading events: {e}")
        return []


def compute_analytics_summary() -> dict[str, Any]:
    """Compute summary analytics from tracked events.

    Returns:
        Dictionary with computed metrics including:
        - Total events count
        - Unique sessions count
        - Event type counts
        - Time-to-recommendation metrics (median, p90)
        - CTR metrics if applicable
    """
    events = read_events()

    if not events:
        return {"total_events": 0, "unique_sessions": 0, "event_counts": {}, "time_to_recommendation": {}, "ctr": {}}

    # Basic counts
    unique_sessions = len(set(e["session_id"] for e in events))
    event_counts: dict[str, int] = {}
    for event in events:
        event_name = event["event_name"]
        event_counts[event_name] = event_counts.get(event_name, 0) + 1

    # Time-to-recommendation metrics
    recommendation_durations = [
        e["metrics"].get("duration_ms", 0)
        for e in events
        if e["event_name"] in ["recommendation_requested", "recommendation_api_called"]
        and "duration_ms" in e.get("metrics", {})
    ]

    time_to_recommendation = {}
    if recommendation_durations:
        sorted_durations = sorted(recommendation_durations)
        n = len(sorted_durations)
        time_to_recommendation = {
            "median_ms": sorted_durations[n // 2] if n > 0 else 0,
            "p90_ms": sorted_durations[int(n * 0.9)] if n > 0 else 0,
            "count": n,
        }

    # CTR calculation (example: cta_clicked / recommendation_rendered)
    cta_clicked = event_counts.get("cta_clicked", 0)
    recommendation_rendered = event_counts.get("recommendation_rendered", 0)

    ctr = {}
    if recommendation_rendered > 0:
        ctr = {
            "cta_clicked": cta_clicked,
            "recommendation_rendered": recommendation_rendered,
            "rate": round((cta_clicked / recommendation_rendered) * 100, 2),
        }

    return {
        "total_events": len(events),
        "unique_sessions": unique_sessions,
        "event_counts": event_counts,
        "time_to_recommendation": time_to_recommendation,
        "ctr": ctr,
    }
