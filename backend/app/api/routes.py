from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal, EONETEvent, NewsArticle, CoverageScore
from typing import Optional

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/events")
def get_events(
    category: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    query = (
        db.query(EONETEvent, CoverageScore)
        .outerjoin(CoverageScore, EONETEvent.id == CoverageScore.event_id)
    )

    if category:
        query = query.filter(EONETEvent.category == category)
    if min_score is not None:
        query = query.filter(CoverageScore.score >= min_score)
    if max_score is not None:
        query = query.filter(CoverageScore.score <= max_score)

    results = query.limit(limit).all()

    return [
        {
            "id": ev.id,
            "title": ev.title,
            "category": ev.category,
            "status": ev.status,
            "latitude": ev.latitude,
            "longitude": ev.longitude,
            "event_date": ev.event_date.isoformat() if ev.event_date else None,
            "article_count": cs.article_count if cs else 0,
            "coverage_score": cs.score if cs else 0.0,
        }
        for ev, cs in results
    ]


@router.get("/events/forgotten")
def get_forgotten_events(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    results = (
        db.query(EONETEvent, CoverageScore)
        .outerjoin(CoverageScore, EONETEvent.id == CoverageScore.event_id)
        .order_by(CoverageScore.score.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": ev.id,
            "title": ev.title,
            "category": ev.category,
            "status": ev.status,
            "latitude": ev.latitude,
            "longitude": ev.longitude,
            "event_date": ev.event_date.isoformat() if ev.event_date else None,
            "article_count": cs.article_count if cs else 0,
            "coverage_score": cs.score if cs else 0.0,
        }
        for ev, cs in results
    ]


@router.get("/events/{event_id}")
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    ev = db.query(EONETEvent).filter(EONETEvent.id == event_id).first()
    if not ev:
        return {"error": "Event not found"}

    cs = db.query(CoverageScore).filter(CoverageScore.event_id == event_id).first()
    articles = db.query(NewsArticle).filter(NewsArticle.event_id == event_id).all()

    return {
        "id": ev.id,
        "title": ev.title,
        "category": ev.category,
        "status": ev.status,
        "latitude": ev.latitude,
        "longitude": ev.longitude,
        "event_date": ev.event_date.isoformat() if ev.event_date else None,
        "article_count": cs.article_count if cs else 0,
        "coverage_score": cs.score if cs else 0.0,
        "articles": [
            {
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ],
    }


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    rows = db.query(EONETEvent.category, func.count(EONETEvent.id)).group_by(EONETEvent.category).all()
    return [{"category": r[0], "count": r[1]} for r in rows]


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_events = db.query(EONETEvent).count()
    total_articles = db.query(NewsArticle).count()
    forgotten = db.query(CoverageScore).filter(CoverageScore.score == 0.0).count()
    covered = db.query(CoverageScore).filter(CoverageScore.score > 0.0).count()

    return {
        "total_events": total_events,
        "total_articles": total_articles,
        "forgotten_events": forgotten,
        "covered_events": covered,
    }