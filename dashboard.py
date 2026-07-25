"""
Streamlit dashboard - reads from data/nifty.db (built by fetch_nse.py)
Run locally with: streamlit run dashboard.py
Deploy free at: https://share.streamlit.io (connect this GitHub repo)
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY Positioning Dashboard", layout="wide")

DB_PATH = "data/nifty.db"


@st.cache_data(ttl=300)
def load_table(name):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT * FROM {name}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


st.title("NIFTY Positioning Dashboard")
st.caption("Derived from free NSE option chain + participant-wise OI data")

oc = load_table("option_chain")
poi = load_table("participant_oi")

if oc.empty:
    st.warning("No option chain data yet. Run `python fetch_nse.py` to populate the database.")
else:
    latest_date = oc["date"].max()
    latest = oc[oc["date"] == latest_date]

    spot = latest["spot"].iloc[0]
    total_call_oi = latest["call_oi"].sum()
    total_put_oi = latest["put_oi"].sum()
    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 0
    resistance = latest.loc[latest["call_oi"].idxmax(), "strike"]
    support = latest.loc[latest["put_oi"].idxmax(), "strike"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NIFTY Spot", f"{spot:,.0f}")
    c2.metric("Put/Call Ratio", pcr, "put-heavy" if pcr > 1 else "call-heavy")
    c3.metric("Resistance (max call OI)", f"{resistance:,.0f}")
    c4.metric("Support (max put OI)", f"{support:,.0f}")

    st.subheader("Option Chain OI by Strike")
    fig = go.Figure()
    fig.add_bar(x=latest["strike"], y=latest["call_oi"], name="Call OI", marker_color="crimson")
    fig.add_bar(x=latest["strike"], y=latest["put_oi"], name="Put OI", marker_color="seagreen")
    fig.update_layout(barmode="group", template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("OI Change by Strike (build-up direction)")
    fig2 = go.Figure()
    fig2.add_bar(x=latest["strike"], y=latest["call_oi_chg"], name="Call OI Chg", marker_color="orange")
    fig2.add_bar(x=latest["strike"], y=latest["put_oi_chg"], name="Put OI Chg", marker_color="dodgerblue")
    fig2.update_layout(barmode="group", template="plotly_dark", height=350)
    st.plotly_chart(fig2, use_container_width=True)

if not poi.empty:
    st.subheader("Participant Net Positioning (FII / DII / Pro / Client)")
    st.caption("EOD data, ~1 trading day lag — this is a structural limit of free NSE data, not this dashboard.")
    latest_poi_date = poi["report_date"].max()
    poi_latest = poi[poi["report_date"] == latest_poi_date]
    st.dataframe(poi_latest, use_container_width=True)
else:
    st.info("No participant OI data yet — it publishes the morning after each trading day.")

st.divider()
st.caption("Data source: NSE India public APIs & daily reports. Educational use — not investment advice.")
