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
        "weight": 0.8
    },
    #"TVN24": {
        #"url": "https://tvn24.pl/najnowsze.xml",
        #"weight": 0.8
    #},
    #"Onet": {
        #"url": "https://wiadomosci.onet.pl/rss.xml",
        #"weight": 0.75
    #},

}

# Crisis Keywords with severity analysis
EVENT_CATEGORIES = {
    "Earthquake": ["earthquake", "aftershock", "tremor", "seismic", "magnitude", "richter"],
    "Flood": ["flood", "flooding", "inundation", "overflow", "submerged"],
    "Fire": ["fire", "wildfire", "blaze", "burning"],
    "Explosion": ["explosion", "blast", "detonation", "explosive"],
    "Shooting": ["shooting", "gunman", "shots fired", "firearm"],
    "Terrorism": ["terrorist attack", "suicide bombing", "terror", "extremist"],
    "War": ["civil war", "conflict", "battle", "fighting", "invasion"],
    "Epidemic": ["epidemic", "pandemic", "outbreak", "virus", "disease"],
    "Hurricane": ["hurricane", "typhoon", "cyclone", "storm"],
    "Cyber": ["cyberattack", "hack", "data breach", "ransomware"],
    "Protest": ["riot", "violent protest", "clash", "demonstration"],
    "Kidnapping": ["kidnapping", "hostage", "abduction"],
    "AirCrash": ["plane crash", "aircraft crash", "aviation accident", "airliner", "flight crash",
                 "crashed shortly after takeoff", "helicopter crash"],
}


SEVERITY_WEIGHTS = {
    # Extreme disasters
    "tsunami": 10,
    "nuclear": 10,
    "genocide": 10,
    "massacre": 10,
    "terrorist attack": 10,
    "suicide bombing": 10,

    # Physical disasters
    "earthquake": 8,
    "explosion": 8,
    "wildfire": 8,
    "hurricane": 8,
    "flood": 7,
    "landslide": 7,
    "air crash": 9,
    "plane crash": 9,

    # Human impact
    "dead": 3,
    "killed": 3,
    "fatal": 3,
    "injured": 2,
    "casualties": 3,
    "missing": 3,
    "evacuation": 4,
    "collapsed": 4,
    "destroyed": 4,

    # Escalators
    "massive": 2,
    "catastrophic": 3,
    "emergency": 3,
    "state of emergency": 4,
    "thousands": 3,
    "millions": 5,
    "critical": 3,
    "urgent": 2,
}

CONTEXT_KEYWORDS = {
    "catastrophic": 3,
    "deadly": 3,
    "state of emergency": 4,
    "thousands": 3,
    "millions": 5,
    "minor": -2,
    "small": -2,
    "no casualties": -3,
}

#POLISH_BOOST = {
    #"powódź": 7, "trzęsienie ziemi": 8, "huragan": 8, "pożar": 6,
    #"pożar lasu": 8, "zamach": 10, "zamieszki": 6, "porwanie": 7,
    #"uprowadzenie": 7, "epidemia": 8, "pandemia": 9, "katastrofa": 7,
    #"ewakuacja": 6, "stan wyjątkowy": 6, "stan klęski żywiołowej": 7,
    #"zaginięcie": 5,
#}

#SEVERITY_KEYWORDS.update(POLISH_BOOST)


