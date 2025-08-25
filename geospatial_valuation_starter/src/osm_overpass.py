"""
Fetch nearby amenities from OpenStreetMap Overpass API and compute nearest distances.

USAGE:
  python src/osm_overpass.py --in_csv data/processed/geocoded.csv --out_csv data/processed/enriched.csv --amenities school hospital metro --radius 2000
"""

import argparse, time, math, sys
from pathlib import Path
import requests
import pandas as pd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c  # meters

def overpass_around(lat, lon, key, value, radius):
    """
    Query nodes/ways/relations with [key=value] around (lat, lon) within radius (m).
    Returns list of dicts with name/lat/lon.
    """
    query = f"""
    [out:json][timeout:25];
    (
      node["{key}"="{value}"](around:{radius},{lat},{lon});
      way["{key}"="{value}"](around:{radius},{lat},{lon});
      relation["{key}"="{value}"](around:{radius},{lat},{lon});
    );
    out center;
    """
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
    r.raise_for_status()
    data = r.json()
    out = []
    for el in data.get("elements", []):
        name = (el.get("tags") or {}).get("name")
        if "lat" in el and "lon" in el:
            out.append({"name": name, "lat": el["lat"], "lon": el["lon"]})
        elif "center" in el:
            out.append({"name": name, "lat": el["center"]["lat"], "lon": el["center"]["lon"]})
    return out

def fetch_nearest(lat, lon, amenity, radius):
    # amenity synonyms: for 'metro' we approximate with railway=station having 'subway' or name contains 'Metro'
    if amenity.lower() == "metro":
        # Try railway=station and name ~ Metro
        query = f"""
        [out:json][timeout:25];
        (
          node["railway"="station"](around:{radius},{lat},{lon});
          way["railway"="station"](around:{radius},{lat},{lon});
          relation["railway"="station"](around:{radius},{lat},{lon});
        );
        out center;
        """
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        cands = []
        for el in elements:
            tags = el.get("tags") or {}
            name = tags.get("name","")
            if "metro" in name.lower() or tags.get("subway") == "yes" or tags.get("railway") == "station":
                if "lat" in el and "lon" in el:
                    cands.append({"name": name, "lat": el["lat"], "lon": el["lon"]})
                elif "center" in el:
                    cands.append({"name": name, "lat": el["center"]["lat"], "lon": el["center"]["lon"]})
        return cands
    else:
        return overpass_around(lat, lon, "amenity", amenity, radius)

def main(in_csv: str, out_csv: str, amenities: list, radius: int):
    df = pd.read_csv(in_csv)
    for col in ["lat","lon"]:
        if col not in df.columns:
            print(f"Missing column: {col}. Run geocoding first.", file=sys.stderr)
            return

    for amen in amenities:
        dist_col = f"dist_{amen}_m"
        name_col = f"nearest_{amen}_name"
        df[dist_col] = None
        df[name_col] = None

    for idx, row in df.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            continue
        lat, lon = float(row["lat"]), float(row["lon"])

        for amen in amenities:
            try:
                cands = fetch_nearest(lat, lon, amen, radius)
                if not cands:
                    continue
                # compute nearest
                best = None
                best_d = float("inf")
                for c in cands:
                    d = haversine(lat, lon, c["lat"], c["lon"])
                    if d < best_d:
                        best_d, best = d, c
                df.at[idx, f"dist_{amen}_m"] = best_d
                df.at[idx, f"nearest_{amen}_name"] = best.get("name")
            except Exception as e:
                print("Overpass error:", e, file=sys.stderr)
                time.sleep(2)
            time.sleep(1.0)  # be gentle to Overpass

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Saved enriched file -> {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--amenities", nargs="+", default=["school","hospital","metro"])
    ap.add_argument("--radius", type=int, default=2000)
    args = ap.parse_args()
    main(args.in_csv, args.out_csv, args.amenities, args.radius)
