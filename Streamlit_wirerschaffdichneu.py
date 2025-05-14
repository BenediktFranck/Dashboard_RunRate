import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

# Stil setzen
def set_custom_style():
    st.markdown("""
        <style>
            body {
                background-color: #111;
                color: white;
            }
            .metric-label {
                color: #ffcc00 !important;
            }
            .block-container {
                padding-top: 2rem;
            }
            .stDataFrame thead tr th {
                background-color: #222;
            }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()

# Logo einbinden
st.image("https://s3-eu-west-1.amazonaws.com/tpd/logos/5e74cb42193e490001227d3f/0x0.png", width=200)
st.title("💡 Run Rate Dashboard – ErschaffeDichNeu Edition")

# Daten laden
@st.cache_data(ttl=3600)
def load_data(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, parse_dates=["ContractStartDate", "BookingDate", "ContractEndDate"])
            df["MonthlyRevenue"] = df["BookedRevenue"] / df["ContractDurationMonths"]
            return df
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {e}")
            return pd.DataFrame()
    else:
        st.warning("Datei nicht gefunden: crm_data.csv")
        return pd.DataFrame()

# Datenpfad
data_path = "crm_data.csv"
df = load_data(data_path)

# Überprüfen, ob Daten geladen wurden
if not df.empty:
    today = pd.Timestamp.today()
    active = df[(df["ContractStartDate"] <= today) & (df["ContractEndDate"] >= today)]

    # KPIs
    run_rate = active["MonthlyRevenue"].sum() * 12
    st.markdown(f"### <span class='metric-label'>Aktuelle Run Rate (jährlich)</span>: **{run_rate:,.0f} €**", unsafe_allow_html=True)
    st.markdown(f"### <span class='metric-label'>Aktive Verträge</span>: **{len(active)}**", unsafe_allow_html=True)

    # Aktive Verträge anzeigen
    st.subheader("📋 Aktive Verträge")
    st.dataframe(active[["CustomerName", "ContractStartDate", "ContractEndDate", "BookedRevenue", "MonthlyRevenue"]])

    # Diagramm: Monatlicher Umsatz pro Kunde
    st.subheader("📈 Monatlicher Umsatz – Top Kunden")
    top_kunden = active.groupby("CustomerName")["MonthlyRevenue"].sum().sort_values(ascending=False).head(10)
    chart = alt.Chart(top_kunden.reset_index()).mark_bar().encode(
        x=alt.X("CustomerName:N", sort="-y"),
        y="MonthlyRevenue:Q",
        color=alt.value("#ffcc00")
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

    # Diagramm: Anzahl Verträge nach Startmonat
    st.subheader("📅 Vertragsstarts pro Monat")
    df["StartMonth"] = df["ContractStartDate"].dt.to_period("M").astype(str)
    starts_per_month = df["StartMonth"].value_counts().sort_index()
    st.line_chart(starts_per_month)

    # Diagramm: Verteilung gebuchter Umsätze
    st.subheader("💰 Verteilung gebuchter Umsätze")
    revenue_distribution = df.groupby("CustomerName")["BookedRevenue"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(revenue_distribution)

    # Interaktive Filteroption
    with st.expander("🔧 Filter: Vertragsstart-Zeitraum"):
        min_date = df["ContractStartDate"].min().date()
        max_date = df["ContractStartDate"].max().date()
        start, end = st.slider("Zeitraum wählen", min_value=min_date, max_value=max_date, value=(min_date, max_date))

        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        gefiltert = df[(df["ContractStartDate"] >= start_ts) & (df["ContractStartDate"] <= end_ts)]

        st.write(f"Anzahl Verträge im gewählten Zeitraum: **{len(gefiltert)}**")
        st.dataframe(gefiltert)
else:
    st.warning("Keine Daten verfügbar. Überprüfe den Dateipfad oder das Datenformat.")
