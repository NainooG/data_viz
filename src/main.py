import pandas as pd
import geopandas as gpd
import requests
from io import StringIO
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os
import folium



def custom_bivariate_classification(x, y):
    if pd.isna(x) or pd.isna(y):
        return np.nan

    # Custom thresholds for People_of_Color
    if x <= 20:
        x_class = 1
    elif x <= 40:
        x_class = 2
    else:
        x_class = 3

    # Custom thresholds for Access_Healthy_Foods
    if y <= 80:
        y_class = 1
    elif y <= 90:
        y_class = 2
    else:
        y_class = 3

    return str(x_class) + str(y_class)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'csv_files', 'Limited_Access_to_Healthy_Food.csv')

    food_desert = pd.read_csv(csv_path, dtype={"Census Tract": str})
    food_desert = food_desert[pd.to_numeric(food_desert['Census Tract'], errors='coerce').notnull()]
    food_desert['Census Tract'] = food_desert['Census Tract'].astype(float)

    url = "https://services8.arcgis.com/rGGrs6HCnw87OFOT/arcgis/rest/services/People_of_Color_v2/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
    response = requests.get(url)
    census_tracts = gpd.read_file(StringIO(response.text))

    census_tracts['Census_Tract'] = census_tracts['Census_Tract'].astype(float)

    joined_data = census_tracts.merge(food_desert, left_on='Census_Tract', right_on='Census Tract')

    joined_clean = joined_data.dropna(subset=['Score-Limited Access to Healthy Food Retailers'])
    joined_clean['People_of_Color'] = pd.to_numeric(joined_clean['Percent_People_of_Color'], errors='coerce')
    joined_clean['Access_Healthy_Foods'] = pd.to_numeric(joined_clean['Score-Limited Access to Healthy Food Retailers'],
                                                         errors='coerce')

    joined_clean['bi_class'] = joined_clean.apply(
        lambda row: custom_bivariate_classification(row['People_of_Color'], row['Access_Healthy_Foods']), axis=1
    )

    bivariate_colors = {
        '11': '#e8e8e8', '12': '#ace4e4', '13': '#5ac8c8',
        '21': '#dfb0d6', '22': '#a5add3', '23': '#5698b9',
        '31': '#be64ac', '32': '#8c62aa', '33': '#3b4994'
    }

    joined_clean['color'] = joined_clean['bi_class'].map(bivariate_colors)
    joined_clean = joined_clean.dropna(subset=['color'])

    # Convert to GeoJSON
    geojson_data = joined_clean.to_json()

    # Create a Folium map
    m = folium.Map(location=[47.5, -120], zoom_start=6)

    # Add the GeoJSON layer with the correct colors
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': feature['properties']['color'],
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7,
        }
    ).add_to(m)

    # Save the map to an HTML file
    m.save(os.path.join(base_dir, 'interactive_map.html'))

    # If running in a Jupyter notebook, you can display the map directly
    return m


if __name__ == "__main__":
    interactive_map = main()
    interactive_map  # Display in Jupyter Notebook if available
