from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DB_URI

Base = declarative_base()


class CrisisEvent(Base):
    """SQLAlchemy model representing a unique crisis event."""
    __tablename__ = 'events'

    id = Column(String, primary_key=True)  # MD5 hash of title
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    severity_score = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    location = Column(String, nullable=True)
    link = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    event_keywords = Column(JSON, nullable=True)
    free_keywords = Column(JSON, nullable=True)

    def __repr__(self) -> str: # lepsza printowalna reprezentacja DB
        return f"<CrisisEvent(title='{self.title[:10]} [...]', score={self.severity_score})>"


class LocationCache(Base):
    """Caches geocoding results to minimize external API latency."""
    __tablename__ = 'location_cache'

    name = Column(String, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

class FeedCache(Base):
    """
    Stores metadata of already processed RSS feed entries to prevent
    duplicate ingestion and repeated analysis of the same news items.
    """
    __tablename__ = 'feed_cache'

    entry_id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(String, nullable=True)

def get_engine():
    """Initializes the SQLite engine and creates tables if missing."""
    engine = create_engine(DB_URI)
    Base.metadata.create_all(engine)
    return engine

def get_db_session():
    """Creates and returns a new scoped database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()