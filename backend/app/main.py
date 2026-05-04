from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.api.routes import router
from app.ingestion.eonet import fetch_eonet_events
from app.ingestion.news import fetch_news_for_all_events
from app.nlp.matcher import run_scoring
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Disaster Lens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


def refresh_data():
    print("[SCHEDULER] Refreshing data...")
    fetch_eonet_events(days=30, limit=100)
    fetch_news_for_all_events(limit=20)
    run_scoring()
    print("[SCHEDULER] Done.")


@app.on_event("startup")
def startup():
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data, "interval", minutes=30)
    scheduler.start()


@app.get("/")
def root():
    return {"message": "Disaster Lens API is running"}