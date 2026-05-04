from app.database import init_db, SessionLocal, EONETEvent, CoverageScore
from app.nlp.matcher import run_scoring

if __name__ == "__main__":
    init_db()
    run_scoring()

    db = SessionLocal()

    print("\n--- Forgotten disasters (lowest coverage) ---")
    low = (
        db.query(CoverageScore, EONETEvent)
        .join(EONETEvent, CoverageScore.event_id == EONETEvent.id)
        .order_by(CoverageScore.score.asc())
        .limit(8)
        .all()
    )
    for cs, ev in low:
        print(f"  score={cs.score:.3f} | articles={cs.article_count} | [{ev.category}] {ev.title}")

    print("\n--- Most covered events (highest coverage) ---")
    high = (
        db.query(CoverageScore, EONETEvent)
        .join(EONETEvent, CoverageScore.event_id == EONETEvent.id)
        .order_by(CoverageScore.score.desc())
        .limit(5)
        .all()
    )
    for cs, ev in high:
        print(f"  score={cs.score:.3f} | articles={cs.article_count} | [{ev.category}] {ev.title}")

    db.close()