import requests
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select
from app.database import SessionLocal, EONETEvent, NewsArticle

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"


def clean(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9 ]', ' ', text).strip()


def build_query(event: EONETEvent) -> str:
    # Extract the location part (everything after first comma)
    parts = event.title.split(",")
    event_name = clean(parts[0].strip())
    location = clean(parts[1].strip()) if len(parts) > 1 else ""

    # Remove noisy prefixes
    for noise in ["Rx ", "rx ", "RX ", "Prescribed Fire", "Wildfire"]:
        event_name = event_name.replace(noise, "").strip()

    # If name is too short or mostly numeric, just use category + location
    if len(event_name) < 5 or sum(c.isdigit() for c in event_name) > 3:
        if location:
            return f"{event.category} {location}"
        return event.category

    # Use name + location for specificity
    if location:
        return f"{event_name} {location}"
    return event_name


def fetch_news_for_event(event: EONETEvent, db) -> int:
    query = build_query(event)

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  [NEWS] Failed for '{query}': {e}")
        return 0

    articles = data.get("articles", [])
    saved = 0

    for article in articles:
        url = article.get("url")
        if not url:
            continue

        exists = db.query(NewsArticle).filter(
            NewsArticle.event_id == event.id,
            NewsArticle.url == url
        ).first()
        if exists:
            continue

        published_at = None
        pub_str = article.get("publishedAt")
        if pub_str:
            try:
                published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except Exception:
                pass

        new_article = NewsArticle(
            event_id=event.id,
            title=article.get("title", ""),
            source=article.get("source", {}).get("name", ""),
            url=url,
            published_at=published_at,
            content=article.get("content") or article.get("description") or "",
        )
        db.add(new_article)
        saved += 1

    db.commit()
    return saved


def fetch_news_for_all_events(limit: int = 10):
    db = SessionLocal()

    events_with_news = select(NewsArticle.event_id).distinct().subquery()
    events = (
        db.query(EONETEvent)
        .filter(EONETEvent.id.notin_(events_with_news))
        .limit(limit)
        .all()
    )

    if not events:
        print("[NEWS] All events already have news articles.")
        db.close()
        return

    print(f"[NEWS] Fetching news for {len(events)} events...")
    total_saved = 0

    for event in events:
        query = build_query(event)
        print(f"  Querying: '{query}'")
        count = fetch_news_for_event(event, db)
        print(f"  Saved {count} articles.")
        total_saved += count

    db.close()
    print(f"[NEWS] Done. Total articles saved: {total_saved}")