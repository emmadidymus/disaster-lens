from app.database import init_db, SessionLocal, EONETEvent
from app.ingestion.eonet import fetch_eonet_events

if __name__ == "__main__":
    init_db()
    count = fetch_eonet_events(days=30, limit=50)
    print(f"Fetched and saved: {count} events")

    db = SessionLocal()
    events = db.query(EONETEvent).limit(5).all()
    print("\nSample events in DB:")
    for e in events:
        print(f"  [{e.category}] {e.title} | lat={e.latitude}, lon={e.longitude} | {e.event_date}")
    db.close()