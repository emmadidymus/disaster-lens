import spacy
import requests
import re
from math import radians, sin, cos, sqrt, atan2
from app.database import SessionLocal, EONETEvent, NewsArticle, CoverageScore
from datetime import datetime

nlp = spacy.load("en_core_web_sm")


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def geocode_location(place: str) -> tuple:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "limit": 1}
        headers = {"User-Agent": "disaster-lens-app"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None


def extract_locations(text: str) -> list:
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]


def keyword_match(article: NewsArticle, event: EONETEvent) -> bool:
    text = f"{article.title} {article.content}".lower()
    # Strip punctuation from event title words before matching
    event_words = [re.sub(r'[^a-z]', '', w.lower()) for w in event.title.split() if len(w) > 4]
    event_words = [w for w in event_words if w]  # remove empty strings
    return any(word in text for word in event_words)


def article_matches_event(article: NewsArticle, event: EONETEvent, radius_km=1500) -> bool:
    if event.latitude is None or event.longitude is None:
        return keyword_match(article, event)

    text = f"{article.title} {article.content}"
    locations = extract_locations(text)

    for place in locations:
        lat, lon = geocode_location(place)
        if lat is None:
            continue
        dist = haversine_km(event.latitude, event.longitude, lat, lon)
        if dist <= radius_km:
            return True

    if not locations:
        return keyword_match(article, event)

    return False


def compute_coverage_score(event: EONETEvent, articles: list) -> float:
    if not articles:
        return 0.0

    article_count = len(articles)
    unique_sources = len(set(a.source for a in articles))
    source_diversity = min(unique_sources / 5, 1.0)

    recency_score = 0.0
    if event.event_date:
        for a in articles:
            if a.published_at:
                days_diff = abs((
                    a.published_at.replace(tzinfo=None) -
                    event.event_date.replace(tzinfo=None)
                ).days)
                recency_score += max(0, 1 - days_diff / 30)
        recency_score = min(recency_score / max(article_count, 1), 1.0)

    score = (
        0.5 * min(article_count / 10, 1.0) +
        0.3 * source_diversity +
        0.2 * recency_score
    )
    return round(score, 4)


def run_scoring():
    db = SessionLocal()
    events = db.query(EONETEvent).all()
    print(f"[SCORER] Scoring {len(events)} events...")

    for event in events:
        articles = db.query(NewsArticle).filter(NewsArticle.event_id == event.id).all()
        score = compute_coverage_score(event, articles)
        article_count = len(articles)

        existing = db.query(CoverageScore).filter(CoverageScore.event_id == event.id).first()
        if existing:
            existing.score = score
            existing.article_count = article_count
            existing.last_updated = datetime.utcnow()
        else:
            db.add(CoverageScore(
                event_id=event.id,
                article_count=article_count,
                score=score,
            ))

    db.commit()
    db.close()
    print("[SCORER] Done.")