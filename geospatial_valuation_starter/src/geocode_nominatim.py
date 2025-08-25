"""
Geocode addresses/localities using OpenStreetMap Nominatim.

USAGE:
  python src/geocode_nominatim.py --in_csv data/raw/listings_raw.csv --out_csv data/processed/geocoded.csv --email YOUR_EMAIL@example.com --addr_col address --city_col city

If you don't have scraped data yet, try the sample first:
  python src/geocode_nominatim.py --in_csv sample/sample_properties.csv --out_csv data/processed/geocoded.csv --email YOUR_EMAIL@example.com
"""

import argparse, time, csv, sys, os, math
from pathlib import Path
import requests
import pandas as pd

CACHE_PATH = Path("data/processed/geocode_cache.csv")

def load_cache():
    if CACHE_PATH.exists():
        return pd.read_csv(CACHE_PATH)
    return pd.DataFrame(columns=["query","lat","lon","display_name"])

def save_cache(df):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE_PATH, index=False)

def geocode(query: str, email: str, session: requests.Session) -> dict:
    base = "https://nominatim.openstreetmap.org/search"
    params = {"format":"json","q":query, "addressdetails":0, "limit":1}
    headers = {"User-Agent": f"geo-valuation-learner (contact: {email})"}
    r = session.get(base, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data:
        return {"lat": None, "lon": None, "display_name": None}
    d = data[0]
    return {"lat": float(d["lat"]), "lon": float(d["lon"]), "display_name": d.get("display_name")}

def main(in_csv: str, out_csv: str, email: str, addr_col: str, city_col: str):
    df = pd.read_csv(in_csv)
    cache = load_cache()

    # Build query string
    def build_query(row):
        parts = []
        if addr_col in row and pd.notna(row[addr_col]):
            parts.append(str(row[addr_col]))
        if city_col and city_col in row and pd.notna(row[city_col]):
            parts.append(str(row[city_col]))
        return ", ".join(parts) if parts else None

    df["geo_query"] = df.apply(build_query, axis=1)
    df["lat"] = None
    df["lon"] = None

    session = requests.Session()

    for idx, row in df.iterrows():
        q = row["geo_query"]
        if not q or (isinstance(q, float) and math.isnan(q)):
            continue

        # check cache
        cached = cache[cache["query"] == q]
        if len(cached):
            df.at[idx, "lat"] = float(cached.iloc[0]["lat"])
            df.at[idx, "lon"] = float(cached.iloc[0]["lon"])
            continue

        try:
            info = geocode(q, email, session)
            df.at[idx, "lat"] = info["lat"]
            df.at[idx, "lon"] = info["lon"]
            # update cache
            cache = pd.concat([cache, pd.DataFrame([{"query": q, "lat": info["lat"], "lon": info["lon"], "display_name": info["display_name"]}])], ignore_index=True)
            save_cache(cache)
        except Exception as e:
            print("Geocode error:", e, "for", q, file=sys.stderr)
        time.sleep(1.1)  # Nominatim polite rate limit

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Saved geocoded file -> {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--email", required=True, help="Your email to include in User-Agent per Nominatim policy")
    ap.add_argument("--addr_col", default="address", help="Column that holds address/locality")
    ap.add_argument("--city_col", default="city", help="City column (optional but recommended)")
    args = ap.parse_args()
    main(args.in_csv, args.out_csv, args.email, args.addr_col, args.city_col)
