import geopandas as gpd
import pandas as pd
import osmnx as ox
from shapely.geometry import Point

def geocode_addresses(df, address_col="address"):
    """Geocode addresses using OSM (Nominatim)."""
    geocoded = []
    for _, row in df.iterrows():
        try:
            loc = ox.geocode(row[address_col])
            geocoded.append(Point(loc[1], loc[0]))
        except Exception as e:
            print(f"Geocoding failed for {row[address_col]}: {e}")
            geocoded.append(Point(None, None))
    gdf = gpd.GeoDataFrame(df, geometry=geocoded, crs="EPSG:4326")
    return gdf

def compute_features(gdf):
    """Dummy feature engineering (extend later)."""
    gdf["road_density"] = [0.5, 0.8, 0.3, 0.6, 0.7]  # placeholder
    gdf["dist_metro"] = [200, 500, 1500, 800, 1000]  # placeholder
    gdf["greenery_index"] = [0.3, 0.2, 0.5, 0.4, 0.6]  # placeholder
    return gdf
