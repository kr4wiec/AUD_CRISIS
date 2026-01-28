from datetime import timedelta
import pandas as pd

CORE_EVENT_KEYWORDS = {
    "plane crash",
    "aircraft crash",
    "earthquake",
    "flood",
    "explosion",
    "wildfire",
    "hurricane",
    "pandemic",
}

def jaccard(a, b):
    """Jaccard similarity for two lists of strings."""
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def titles_share_event(e1, e2):
    t1 = e1["Title"].lower()
    t2 = e2["Title"].lower()

    shared = set(e1["EventKeywords"]) & set(e2["EventKeywords"])
    shared_core = shared & CORE_EVENT_KEYWORDS

    return any(kw in t1 and kw in t2 for kw in shared_core)

def is_same_event(e1, e2, min_kw_sim=0.4, max_time_diff=timedelta(hours=1)):
    """
    Decides whether two events represent the same real-world event.
    Expects pandas Series with:
      - Keywords: list[str]
      - Category: str
      - Location: str
      - Published: datetime
    """

    if (e1["Location"] != "Unknown" and e2["Location"] != "Unknown" and e1["Location"] != e2["Location"]):
        if not titles_share_event(e1, e2): # allow override if titles clearly describe the same event
            return False

    if e1["Category"] != e2["Category"]:
        return False

    # similar keywords
    kw_sim = jaccard(e1["EventKeywords"], e2["EventKeywords"])
    if kw_sim < min_kw_sim:
        return False

    # Time
    time_diff = abs(e1["Published"] - e2["Published"])
    if time_diff > max_time_diff:
        return False

    return True


def cluster_events(df: pd.DataFrame):
    """
    Groups rows of df into clusters of same events.
    Returns list of clusters, each cluster is a list of rows.
    """
    clusters = []

    for _, row in df.iterrows():
        placed = False

        for cluster in clusters:
            if is_same_event(row, cluster[0]):
                cluster.append(row)
                placed = True
                break

        if not placed:
            clusters.append([row])

    return clusters


def build_clustered_df(clusters):
    """
    Builds an overview DataFrame from clusters.
    """
    rows = []

    for i, cluster in enumerate(clusters):
        rows.append({
            "EventID": i,
            "Title": cluster[0]["Title"],
            "Location": cluster[0]["Location"],
            "Category": cluster[0]["Category"],
            "MaxSeverity": max(e["Severity"] for e in cluster),
            "FirstSeen": min(e["Published"] for e in cluster),
            "LastSeen": max(e["Published"] for e in cluster),
            "N_reports": len(cluster),
            "Titles": [e["Title"] for e in cluster],
            "Links": [e["Link"] for e in cluster],
            "Keywords": list(set(
                kw for e in cluster for kw in e["EventKeywords"]
            ))
        })

    return pd.DataFrame(rows)
