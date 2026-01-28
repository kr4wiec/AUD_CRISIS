import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from analyzer import CrisisAnalyzer
from clustering import cluster_events, build_clustered_df

from config import DASHBOARD_SEVERITY_THRESHOLD

st.set_page_config(
    page_title="Global Crisis Detector",
    layout="wide"
)

def load_data(analyzer: CrisisAnalyzer) -> pd.DataFrame:
    """Converts DB events into a Pandas DataFrame for analysis."""
    events = analyzer.get_all_events()
    if not events:
        return pd.DataFrame()

    data = [{
        "Title": evnt.title,
        "Source": evnt.source,
        "Severity": evnt.severity_score,
        "Category": evnt.category,
        "Location": evnt.location,
        "Published": evnt.published_at,
        "Link": evnt.link,
        "latitude": evnt.latitude,  # y
        "longitude": evnt.longitude,  # x
        "EventKeywords": evnt.event_keywords,
        "FreeKeywords": evnt.free_keywords
    } for evnt in events]
    return pd.DataFrame(data)


def render_belt(df: pd.DataFrame):
    """Creates a scrolling HTML <marquee> for breaking news."""
    if df.empty:
        return

    high_sev = df[df['Severity'] > DASHBOARD_SEVERITY_THRESHOLD].sort_values('Published', ascending=False).head(
        10)  # take only rows where Severity > threshold, sort by newest first, keep only the top 10
    ticker_text = " | ".join([f"[{r['Category']}] {r['Title']}" for _, r in
                              high_sev.iterrows()])  # Jeden string np [Earthquake] Earthquake in Japan, [Shooting] Shooting in Texas -> [Earthquake] Earthquake in Japan | [Shooting] Shooting in Texas

    st.markdown(f"""
        <style>
        .marquee {{ width: 100%; line-height: 40px; background: #b22222; color: white;
                    white-space: nowrap; overflow: hidden; font-weight: bold; }}
        .marquee p {{ display: inline-block; padding-left: 100%; animation: mq 25s linear infinite; }}
        @keyframes mq {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
        </style>
        <div class="marquee"><p>{ticker_text}</p></div>
    """, unsafe_allow_html=True)


def render_severity_gauge(df: pd.DataFrame):
    """Renders a Plotly gauge showing average global severity."""
    val = df['Severity'].mean() if not df.empty else 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={'text': "Global Tension Index"},
        gauge={'axis': {'range': [0, 20]},
               'bar': {'color': "gray", 'thickness': 0.3},
               'steps': [{'range': [0, 6.67], 'color': "green"},
                         {'range': [6.67, 13.37], 'color': "orange"},
                         {'range': [13.37, 20], 'color': "red"}]}
    ))
    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main dashboard execution loop."""
    st.title("Global Crisis Detection Platform")
    analyzer = CrisisAnalyzer()
    df_raw = load_data(analyzer)

    # Sidebar
    with st.sidebar:
        st.header("CONTROLS")
        if st.button("Refresh"):
            analyzer.scan_feed()
            st.rerun()

        threshold = st.slider("Severity Threshold", 0.0, 20.0, 4.0)
        search = st.text_input("Filter Headline")

    if df_raw.empty:
        st.info("No data. Press ''Refresh'' button.")
        return

    # Filter Logic
    df = df_raw[
        (df_raw['Severity'] >= threshold) &
        (df_raw['Title'].str.contains(search, case=False))
        ].copy()

    clusters = cluster_events(df)
    clustered_df = build_clustered_df(clusters)

    render_belt(df)  # Czerwony pasek na górze

    c1, c2 = st.columns([1, 2])  # Layout
    with c1:
        render_severity_gauge(df_raw)  # Kolorowe kółeczko po lewej
    with c2:
        st.subheader("Global Crisis Map")
        fig_map = px.density_map(
            df.dropna(subset=['latitude']), lon="longitude", lat="latitude",
            z="Severity", radius=15, zoom=1, map_style="carto-darkmatter"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Crisis List")

    df_view = df[
        df["EventKeywords"].notna() & (df["EventKeywords"].str.len() > 0)
        ].drop(columns=["FreeKeywords"])

    st.data_editor(
        df_view.sort_values("Published", ascending=False),
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Link")
        }
    )

    st.subheader("Clustered Events")
    st.data_editor(
        clustered_df[clustered_df["N_reports"] > 1],
        hide_index=True
    )

if __name__ == "__main__":
    main()