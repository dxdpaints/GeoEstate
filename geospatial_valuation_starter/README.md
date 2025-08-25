# Geospatial Property Valuation — Starter Kit

This repo helps you build an end‑to‑end real‑estate **Geospatial Valuation Model**:
- Scrape listings (Playwright) →
- Geocode with **OpenStreetMap Nominatim API** (free) →
- Enrich with nearby amenities via **Overpass API** (OSM) →
- Engineer features and train ML (XGBoost) →
- Visualize & demo in **Streamlit**.

> ⚠️ Be respectful: check each website’s Terms of Service and `robots.txt`. Scrape slowly (sleep/retries). Use this for learning/portfolio, not for heavy crawling.

---

## 0) Quickstart

### Create & activate a virtual environment (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

### Try the sample pipeline (no scraping needed)
We included a tiny dataset at `sample/sample_properties.csv` so you can test geocoding + features without scraping first.

```bash
# 1) Geocode addresses with Nominatim (adds lat/lon; caches results)
python src/geocode_nominatim.py --in_csv sample/sample_properties.csv --out_csv data/processed/geocoded.csv --email YOUR_EMAIL@example.com

# 2) Fetch nearest schools & hospitals from Overpass and compute distances
python src/osm_overpass.py --in_csv data/processed/geocoded.csv --out_csv data/processed/enriched.csv --amenities school hospital

# 3) Train a quick baseline model
python src/train_model.py --in_csv data/processed/enriched.csv --target_col price_lakh

# 4) Launch demo app
streamlit run app/streamlit_app.py
```

---

## 1) Real-world Scraping (Playwright)

Use `src/scrape_magicbricks_playwright.py` with a **MagicBricks** (or similar) search URL.
**You must update the CSS selectors after inspecting the site with DevTools**, because sites change often.

Example (Bengaluru flats for sale search URL):
```
https://www.magicbricks.com/property-for-sale/residential-real-estate?City=bangalore
```

Run:
```bash
python src/scrape_magicbricks_playwright.py --url "YOUR_SEARCH_URL" --pages 3 --out_csv data/raw/listings_raw.csv
```

If a site blocks you:
- Reduce page count, add `--delay 3`
- Rotate User-Agent (already included)
- Consider scraping early mornings
- Or switch to another site (99acres, Housing.com) and update selectors in the parser.

---

## 2) Geocoding with Nominatim (Free OSM API)

We use Nominatim to convert address/locality → latitude/longitude. Respect limits:
- 1 request per second (we enforce sleep).
- Provide a **valid email** in the User-Agent for contact.
- Results are cached in `data/processed/geocode_cache.csv` to avoid re-hitting the API.

---

## 3) Amenities via Overpass API

Use `src/osm_overpass.py` to fetch nearby **amenities** (schools, hospitals, metro stations, etc.) per property.
We compute **distance to nearest** amenity for each type and append features like:
- `dist_school_m`, `dist_hospital_m`, `dist_metro_m`

---

## 4) Modeling

`src/train_model.py` trains a quick baseline regressor (XGBoost) and prints metrics (RMSE/R²). It saves the model to `models/model.pkl` and a feature importance PNG.

---

## 5) Streamlit App

`app/streamlit_app.py` lets you load the processed file and explore points on a map, then run the trained model to predict price for hypothetical inputs.

---

## Notes
- `geopandas` is not strictly required here (install can be heavy on Windows). We use `folium` for mapping.
- For scraping, **Playwright** is preferred over `requests+bs4` on JS sites.
- You can keep everything city-agnostic (Bengaluru, Mumbai, etc.).
