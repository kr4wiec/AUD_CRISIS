"""
Logic for fetching RSS feeds, NLP-based location extraction, 
and severity scoring via keyword analysis.
"""
import hashlib
import logging
import time
import sys
from datetime import datetime
from typing import Tuple, Optional

import feedparser
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from sqlalchemy.orm import Session

from config import RSS_FEEDS, SEVERITY_KEYWORDS, NLP_MODEL_NAME, ANALYZER_SEVERITY_THRESHOLD
from database import CrisisEvent, get_db_session, LocationCache

# Configure logging for better observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CrisisAnalyzer:
    """
    Orchestrates the lifecycle of crisis data ingestion and analysis.
    """

    def __init__(self, db_session: Session = None):
        """
        Initializes NLP models and database connections.
        """
        self.db_session = db_session if db_session else get_db_session()

        try:
            self.nlp_model = spacy.load(NLP_MODEL_NAME)
        except:
            sys.exit(f"Something went wrong when loading {NLP_MODEL_NAME}. Try downloading it first.")

        self.geocoder = Nominatim(user_agent="aud_crisis_detector") # jak nie ma user_agent to prosi o podanie

    def get_coordinates(self, location_name: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Retrieves lat/lon for a location string, checking the local cache first.
        """
        if not location_name or location_name == "Unknown":
            return None, None

        # Sprawdz lokalny DB cache
        cached = self.db_session.query(LocationCache).filter_by(name=location_name).first()
        if cached:
            return cached.latitude, cached.longitude

        # Jak nie ma to wez od Nominatim
        try:
            location = self.geocoder.geocode(location_name, timeout=10)
            if location:
                new_cache = LocationCache(
                    name=location_name,
                    latitude=location.latitude,
                    longitude=location.longitude
                )
                self.db_session.add(new_cache)
                self.db_session.commit()
                return location.latitude, location.longitude
        except (GeocoderTimedOut, Exception) as e:
            logger.error(f"Geocoding error {e} for {location_name}.")

        return None, None

    def _generate_id(self, title: str) -> str:
        """Generates a unique MD5 hash for entry deduplication."""

        return hashlib.md5(title.encode('utf-8')).hexdigest()

    def extract_location(self, text: str) -> str:
        """Uses Spacy Named Entity Recognition (NER) to extract Geopolitical Entities (GPE)."""
        doc = self.nlp_model(text)
        locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
        res = locations[0] if locations else "Unknown"
        return res

    def get_severity_score(self, text: str, source_weight: float) -> Tuple[float, str]:
        """
        Calculates a score based on keywords and source reliability.
        Identifies the primary category based on the highest-weighted keyword.
        """
        text = text.lower()
        score = 0.0
        best_category = "General News"
        max_weight_found = 0

        for keyword, weight in SEVERITY_KEYWORDS.items():
            if keyword in text:
                score += weight
                if weight > max_weight_found:
                    max_weight_found = weight
                    best_category = keyword.capitalize()

        final_score = round(score * source_weight, 2)
        return final_score, best_category

    def scan_feed(self) -> int:
        """
        Main pipeline: Scans feeds, scores content, geocodes, and saves to DB.
        """
        new_event_counter = 0
        for source_name, config in RSS_FEEDS.items():
            logger.info(f"Scanning source - {source_name}")
            try:
                feed = feedparser.parse(config['url'])
                for entry in feed.entries:
                    entry_id = self._generate_id(entry.title) # na upartego można tego nie używać ale teoretycznie linki/RSS mogą być brzydkie, nie będzie dawało dobrych ID i nie będzie łapało duplikatów

                    # Jak istnieje to skipnij
                    if self.db_session.query(CrisisEvent).filter_by(id=entry_id).first():
                        continue

                    text = f"{entry.title} {entry.get('summary', '')}"
                    severity, category = self.get_severity_score(text, config['weight'])

                    # Severity filter
                    if severity > ANALYZER_SEVERITY_THRESHOLD: # domyślnie = 3
                        loc_name = self.extract_location(text)
                        lat, lon = self.get_coordinates(loc_name)

                        event = CrisisEvent(
                            id=entry_id,
                            title=entry.title,
                            source=source_name,
                            published_at=datetime.utcnow(),
                            severity_score=severity,
                            category=category,
                            link=entry.link,
                            location=loc_name,
                            latitude=lat,
                            longitude=lon
                        )
                        self.db_session.add(event)
                        new_event_counter += 1
                        time.sleep(1)  # Unikanie bana, musi być >1 s przerwy między callami

            except Exception as e:
                logger.error(f"Failed to process {source_name} with error {e}")

        self.db_session.commit()
        return new_event_counter

    def get_all_events(self):
        """Fetches all CrisisEvent objects from the database."""
        return self.db_session.query(CrisisEvent).all()