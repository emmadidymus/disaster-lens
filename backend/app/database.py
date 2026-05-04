from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./disaster_lens.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class EONETEvent(Base):
    __tablename__ = "eonet_events"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String)
    status = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    event_date = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String)
    title = Column(String)
    source = Column(String)
    url = Column(Text)
    published_at = Column(DateTime)
    content = Column(Text)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class CoverageScore(Base):
    __tablename__ = "coverage_scores"

    event_id = Column(String, primary_key=True)
    article_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")