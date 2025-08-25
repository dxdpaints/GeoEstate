import folium

def plot_properties(gdf, output_file="map.html"):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    for _, row in gdf.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=f"{row['address']}<br>Price: {row['price']}"
        ).add_to(m)
    m.save(output_file)
    print(f"Map saved to {output_file}")
