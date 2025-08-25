import pandas as pd
from src.features import geocode_addresses, compute_features
from src.model import train_model
from src.visualize import plot_properties

# Step 1: Load data
df = pd.read_csv("../data/sample_properties.csv")

# Step 2: Geocode
gdf = geocode_addresses(df)

# Step 3: Feature engineering
gdf = compute_features(gdf)
print(gdf.head())

# Step 4: Train model
model = train_model(gdf)

# Step 5: Visualization
plot_properties(gdf, output_file="../data/properties_map.html")
