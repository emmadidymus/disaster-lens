import requests
from datetime import datetime
from app.database import SessionLocal, EONETEvent

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"


def fetch_eonet_events(days: int = 30, limit: int = 100):
    params = {
        "days": days,
        "limit": limit,
        "status": "open"
    }

    try:
        response = requests.get(EONET_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[EONET] Failed to fetch: {e}")
        return 0

    events = data.get("events", [])
    db = SessionLocal()
    saved = 0

    for event in events:
        event_id = event.get("id")
        if not event_id:
            continue

        # Skip if already in DB
        exists = db.query(EONETEvent).filter(EONETEvent.id == event_id).first()
        if exists:
            continue

        # Extract first geometry point
        geometries = event.get("geometry", [])
        lat, lon, event_date = None, None, None

        if geometries:
            geom = geometries[-1]  # most recent point
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            date_str = geom.get("date")
            if date_str:
                try:
                    event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass

        # Extract category
        categories = event.get("categories", [])
        category = categories[0].get("title") if categories else "Unknown"

        new_event = EONETEvent(
            id=event_id,
            title=event.get("title", "Untitled"),
            category=category,
            status=event.get("status", "open"),
            latitude=lat,
            longitude=lon,
            event_date=event_date,
        )
        db.add(new_event)
        saved += 1

    db.commit()
    db.close()
    print(f"[EONET] Saved {saved} new events.")
    return saved