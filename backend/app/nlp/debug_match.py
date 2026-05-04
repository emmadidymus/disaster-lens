from app.database import SessionLocal, EONETEvent, NewsArticle
from app.nlp.matcher import keyword_match, extract_locations, article_matches_event

if __name__ == "__main__":
    db = SessionLocal()

    # Get the Sparks Wildfire event
    event = db.query(EONETEvent).filter(EONETEvent.title.like("%Sparks%")).first()
    if not event:
        print("Event not found")
        db.close()
        exit()

    print(f"Event: {event.title}")
    print(f"Coords: lat={event.latitude}, lon={event.longitude}")
    print(f"Event words: {[w.lower() for w in event.title.split() if len(w) > 4]}")
    print()

    articles = db.query(NewsArticle).filter(NewsArticle.event_id == event.id).all()
    for a in articles:
        text = f"{a.title} {a.content}".lower()
        print(f"Article: {a.title}")
        print(f"Content snippet: {a.content[:150] if a.content else 'EMPTY'}")
        print(f"Keyword match: {keyword_match(a, event)}")
        print(f"Locations found: {extract_locations(a.title + ' ' + (a.content or ''))}")
        print(f"Full match: {article_matches_event(a, event)}")
        print()

    db.close()