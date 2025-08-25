import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import joblib
from pathlib import Path

st.set_page_config(page_title="Geospatial Valuation Demo", layout="wide")
st.title("🏙️ Geospatial Property Valuation — Demo")

st.markdown(
"""
Load a processed CSV (with `lat`, `lon`, distances like `dist_school_m`) and explore points on a map.
If `models/model.pkl` exists, you can run quick what‑if predictions.
"""
)

uploaded = st.file_uploader("Upload processed/enriched CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.write("Data preview:", df.head())

    # Map
    if {"lat","lon"}.issubset(df.columns):
        m = folium.Map(location=[df["lat"].median(), df["lon"].median()], zoom_start=11)
        mc = MarkerCluster().add_to(m)
        for _, r in df.dropna(subset=["lat","lon"]).iterrows():
            folium.Marker(
                location=[r["lat"], r["lon"]],
                popup=f"{r.get('title','(no title)')} | ₹{r.get('price_lakh','?')} L | {r.get('bhk','?')} BHK | {r.get('area_sqft','?')} sqft",
            ).add_to(mc)
        st_folium(m, width=900, height=500)

# Prediction
st.subheader("🔮 Quick What‑If Prediction")
if Path("models/model.pkl").exists():
    model = joblib.load("models/model.pkl")
    col1, col2, col3 = st.columns(3)
    bhk = col1.number_input("BHK", 1, 6, 2)
    area = col2.number_input("Area (sqft)", 200, 4000, 1000)
    dist_school = col3.number_input("Distance to nearest school (m)", 0, 5000, 800)
    dist_hosp = col1.number_input("Distance to nearest hospital (m)", 0, 5000, 1200)
    dist_metro = col2.number_input("Distance to nearest metro (m)", 0, 5000, 1500)
    # For demo, lat/lon default to median Bengaluru
    lat = 12.9716
    lon = 77.5946

    import numpy as np
    X = pd.DataFrame([{
        "bhk": bhk,
        "area_sqft": area,
        "lat": lat,
        "lon": lon,
        "dist_school_m": dist_school,
        "dist_hospital_m": dist_hosp,
        "dist_metro_m": dist_metro,
    }])
    if st.button("Predict Price (₹ Lakh)"):
        y = model.predict(X)[0]
        st.success(f"Estimated price: ₹ {y:.1f} Lakh")
else:
    st.info("Train a model first (see README), then restart the app.")
