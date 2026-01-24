from typing import Dict, TypedDict
class SourceConfig(TypedDict):
    """Type definition for RSS feed configuration."""
    url: str
    weight: float

# analyzer.py
ANALYZER_SEVERITY_THRESHOLD = 3

# dashboard.py
DASHBOARD_SEVERITY_THRESHOLD = 7

# Database Uniform Resource Identifier
DB_URI = 'sqlite:///crisis_events.db'

# Moel used for extracting info
NLP_MODEL_NAME = "en_core_web_sm"

# Sources: RSS feeds with assigned impact weights
RSS_FEEDS: Dict[str, SourceConfig] = {
    "Reddit-WorldNews": {
        "url": "https://www.reddit.com/r/worldnews/new/.rss",
        "weight": 0.6
    },
    "Reddit-Disaster": {
        "url": "https://www.reddit.com/r/disaster/new/.rss",
        "weight": 0.6
    },
    "AlJazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "weight": 0.8
    },
    "BBC-World": {
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "weight": 0.9
    },
    "USGS-Quakes": {
        "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom",
        "weight": 1.0
    }
}

# Crisis Keywords with severity analysis
SEVERITY_KEYWORDS = {

    # Extreme Severity (9-10)
    "tsunami": 10, "nuclear": 10, "massacre": 10, "bombing": 10,
    "earthquake": 8, "hurricane": 8, "shooting": 9, "terror": 10,
    "explosion": 8, "wildfire": 9, "war": 11, "genocide": 10,

    # Moderate Severity (5-8)
    "flood": 7, "riot": 6, "strike": 6, "outbreak": 8, "typhoon": 8,
    "evacuation": 5, "casualty": 5, "clash": 4, "missing": 4,
    "arrest": 3, "cyberattack": 7, "landslide": 6,

    # Contextual (added to total score if existing)
    "massive": 2, "urgent": 2, "breaking": 1, "confirmed": 1,
    "deadly": 3, "thousands": 3, "emergency": 3, "catastrophic": 3,
    "death toll": 3, "state of emergency": 4, "millions": 5,
    "billions": 10
}