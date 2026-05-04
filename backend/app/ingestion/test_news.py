from app.database import SessionLocal, NewsArticle, EONETEvent
from app.ingestion.news import fetch_news_for_all_events

if __name__ == "__main__":
    fetch_news_for_all_events(limit=10)

    db = SessionLocal()
    total = db.query(NewsArticle).count()
    print(f"\nTotal articles in DB: {total}")

    print("\nSample articles:")
    articles = db.query(NewsArticle).limit(5).all()
    for a in articles:
        event = db.query(EONETEvent).filter(EONETEvent.id == a.event_id).first()
        print(f"  Event: {event.title[:40] if event else 'unknown'}")
        print(f"  Article: {a.title[:60]}")
        print(f"  Source: {a.source}")
        print()
    db.close()