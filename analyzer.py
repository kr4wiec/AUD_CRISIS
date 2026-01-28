"""
Logic for fetching RSS feeds, NLP-based location extraction,
and severity scoring via keyword analysis.
"""
import hashlib
import logging
import time
import sys
from datetime import datetime, timedelta
from typing import Tuple, Optional

import feedparser
import spacy
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from sqlalchemy.orm import Session

from config import RSS_FEEDS, EVENT_CATEGORIES, SEVERITY_WEIGHTS, CONTEXT_KEYWORDS, NLP_MODEL_NAME, ANALYZER_SEVERITY_THRESHOLD
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

        self.geocoder = Nominatim(user_agent="aud_crisis_detector")

    def get_coordinates(self, location_name: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Retrieves lat/lon for a location string, checking the local cache first.
        """
        if not location_name or location_name == "Unknown":
            return None, None

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

    def detect_category(self, text: str) -> str:
        text = text.lower()
        scores = {}

        for category, keywords in EVENT_CATEGORIES.items():
            scores[category] = sum(1 for kw in keywords if kw in text)

        best_category = max(scores, key=scores.get)

        if scores[best_category] == 0:
            return "General"

        return best_category

    def compute_severity(self, title: str, text: str, source_weight: float) -> float:
        title = title.lower()
        text = text.lower()
        score = 0.0

        for kw, w in SEVERITY_WEIGHTS.items():
            if kw in text:
                score += w

        for kw, w in CONTEXT_KEYWORDS.items():
            if kw in text:
                score += w

        event_keywords_flat = [
            kw for kws in EVENT_CATEGORIES.values() for kw in kws
        ]

        if any(kw in title for kw in event_keywords_flat):
            score += 2

        victims_match = re.findall(
            r'(\d{1,4})\s*(dead|killed|ofiar|zabitych|rann|poszkodowanych|casualties|injured)',
            text
        )
        for num_str, _ in victims_match:
            try:
                num = int(num_str)
                if num >= 100:
                    score += 8
                elif num >= 20:
                    score += 5
                elif num >= 5:
                    score += 3
            except:
                pass

        return round(score * source_weight, 2)

    def cleanup_old_events(self, days: int = 30) -> int:
        """
         Removes outdated crisis events from the database based on a retention policy.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db_session.query(CrisisEvent)
            .filter(CrisisEvent.published_at < cutoff)
            .delete(synchronize_session=False)
        )

        self.db_session.commit()
        logger.info(f"Cleanup: removed {deleted} events older than {days} days")
        return deleted

    def extract_event_keywords(self, text: str):
        text = text.lower()
        out = []
        for category, kws in EVENT_CATEGORIES.items():
            for kw in kws:
                if kw in text:
                    out.append(kw)
        return list(set(out))

    def extract_free_keywords(self, text: str, top_k: int = 10):
        doc = self.nlp_model(text.lower())
        keywords = [
            token.lemma_
            for token in doc
            if token.pos_ in ("NOUN", "PROPN")
               and not token.is_stop
               and not token.like_url
               and not token.like_email
               and token.is_alpha
               and len(token) > 2
        ]
        return list(dict.fromkeys(keywords))[:top_k]

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
                    entry_id = self._generate_id(entry.title)

                    # Jak istnieje to skipnij
                    if self.db_session.query(CrisisEvent).filter_by(id=entry_id).first():
                        continue

                    text = f"{entry.title}, {entry.get('summary', '')} {entry.get('description', '')}"

                    event_keywords = self.extract_event_keywords(text)
                    free_keywords = self.extract_free_keywords(text)

                    category = self.detect_category(text)
                    severity = self.compute_severity(entry.title, text, config["weight"])

                    # ZMIANA / DODANE: obniżamy próg testowo + logujemy każde severity
                    logger.debug(f"Severity for '{entry.title[:60]}...': {severity:.1f} (source weight: {config['weight']})")

                    if severity > ANALYZER_SEVERITY_THRESHOLD:
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
                            longitude=lon,
                            event_keywords=event_keywords,
                            free_keywords=free_keywords
                        )
                        self.db_session.add(event)
                        new_event_counter += 1
                        time.sleep(1.1)  # ZMIANA / DODANE: 1.1 s → bezpieczniej przed Nominatim rate limit

            except Exception as e:
                logger.error(f"Failed to process {source_name} with error {e}")

        self.db_session.commit()
        self.cleanup_old_events(days=30)
        logger.info(f"Ingestion finished → added {new_event_counter} new events")
        return new_event_counter

    def get_all_events(self):
        """Fetches all CrisisEvent objects from the database."""
        return self.db_session.query(CrisisEvent).all()


if __name__ == "__main__":
    analyzer = CrisisAnalyzer()
    added = analyzer.scan_feed()
    print(f"Added {added} new situations.")