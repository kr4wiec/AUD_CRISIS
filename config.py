from typing import Dict, TypedDict
class SourceConfig(TypedDict):
    """Type definition for RSS feed configuration."""
    url: str
    weight: float

# analyzer.py
ANALYZER_SEVERITY_THRESHOLD = 4

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
    },
    "Reuters": {
        "url": "https://www.reuters.com/site-edition/international/rss",
        "weight": 0.95
    },
    "UN-News": {
        "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "weight": 1.0
    },
    "WHO": {
        "url": "https://www.who.int/rss-feeds/news-english.xml",
        "weight": 1.0
    },
    "TVN24": {
        "url": "https://tvn24.pl/najnowsze.xml",
        "weight": 0.8
    },
    "Onet": {
        "url": "https://wiadomosci.onet.pl/rss.xml",
        "weight": 0.75
    },

}

# Crisis Keywords with severity analysis
SEVERITY_KEYWORDS = {

    # Extreme Severity (9-10)
    "tsunami": 10, "nuclear": 10, "massacre": 10, "bombing": 10,
    "earthquake": 8, "hurricane": 8, "shooting": 9, "terror": 10,
    "explosion": 8, "wildfire": 9, "war": 6, "genocide": 10,
    "meltdown": 9, "suicide bombing": 10, "terrorist attack": 10,
    "civil war": 10, "mass shooting": 10, "school shooting": 9,

    # Moderate Severity (5-8)
    "flood": 7, "riot": 6, "strike": 6, "outbreak": 8, "typhoon": 8,
    "evacuation": 5, "casualty": 5, "clash": 4, "missing": 4,
    "arrest": 3, "cyberattack": 7, "landslide": 6, "kidnapping": 7,
    "violent protest": 5, "rescue": 6, "hostage": 7, "epidemic": 8,
    "pandemic": 8, "search and rescue": 6, "drought": 7,

    # Contextual (added to total score if existing)
    "massive": 2, "urgent": 2, "breaking": 1, "confirmed": 1,
    "deadly": 3, "thousands": 3, "emergency": 3, "catastrophic": 3,
    "death toll": 3, "state of emergency": 4, "millions": 5,
    "billions": 10, "minor": -2, "small": -2, "fatal": 3, "dozens": 1,
    "injured": 2, "no casualties": -3,
}

POLISH_BOOST = {
    "powódź": 7, "trzęsienie ziemi": 8, "huragan": 8, "pożar": 6,
    "pożar lasu": 8, "zamach": 10, "zamieszki": 6, "porwanie": 7,
    "uprowadzenie": 7, "epidemia": 8, "pandemia": 9, "katastrofa": 7,
    "ewakuacja": 6, "stan wyjątkowy": 6, "stan klęski żywiołowej": 7,
    "zaginięcie": 5,
}

SEVERITY_KEYWORDS.update(POLISH_BOOST)
