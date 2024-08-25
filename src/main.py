import pandas as pd
import geopandas as gpd
import requests
from io import StringIO
import folium
from folium.features import GeoJsonTooltip
from folium import Html, Element
import os


def custom_bivariate_classification(x, y):
    if pd.isna(x) or pd.isna(y):
        return None

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

    return f"{x_class}{y_class}"


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'csv_files', 'Limited_Access_to_Healthy_Food.csv')
    food_desert = pd.read_csv(csv_path, dtype={"Census Tract": str})
    food_desert = food_desert[pd.to_numeric(food_desert['Census Tract'], errors='coerce').notnull()]
    food_desert['Census Tract'] = food_desert['Census Tract'].astype(float)

    url = "https://services8.arcgis.com/rGGrs6HCnw87OFOT/arcgis/rest/services/People_of_Color_v2/FeatureServer/0/query"
    params = {
        'outFields': '*',
        'where': '1=1',
        'f': 'geojson'
    }
    response = requests.get(url, params=params)
    census_tracts = gpd.read_file(StringIO(response.text))
    census_tracts['Census_Tract'] = census_tracts['Census_Tract'].astype(float)

    joined_data = census_tracts.merge(food_desert, left_on='Census_Tract', right_on='Census Tract')
    joined_data = joined_data.dropna(
        subset=['Score-Limited Access to Healthy Food Retailers', 'Percent_People_of_Color'])

    joined_data['People_of_Color'] = pd.to_numeric(joined_data['Percent_People_of_Color'], errors='coerce')
    joined_data['Access_Healthy_Foods'] = pd.to_numeric(joined_data['Score-Limited Access to Healthy Food Retailers'],
                                                        errors='coerce')

    joined_data['bi_class'] = joined_data.apply(
        lambda row: custom_bivariate_classification(row['People_of_Color'], row['Access_Healthy_Foods']), axis=1
    )

    bivariate_colors = {
        '33': '#3b4994', '32': '#8c62aa', '31': '#be64ac',
        '23': '#5698b9', '22': '#a5add3', '21': '#dfb0d6',
        '13': '#5ac8c8', '12': '#ace4e4', '11': '#e8e8e8',
    }

    joined_data['color'] = joined_data['bi_class'].map(bivariate_colors)

    m = folium.Map(location=[47.5, -120], zoom_start=6, tiles='cartodbpositron')

    style_function = lambda feature: {
        'fillColor': feature['properties']['color'],
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.7,
    }

    tooltip = GeoJsonTooltip(
        fields=['Census_Tract', 'People_of_Color', 'Access_Healthy_Foods'],
        aliases=['Census Tract:', '% People of Color:', 'Limited Access Score:'],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """
    )

    folium.GeoJson(
        joined_data,
        style_function=style_function,
        tooltip=tooltip,
        name='Bivariate Choropleth'
    ).add_to(m)

    legend_html = create_bivariate_legend()
    legend_element = Element(legend_html)
    m.get_root().html.add_child(legend_element)

    folium.LayerControl().add_to(m)

    m.save('interactive_map_with_legend.html')

    return m


def create_bivariate_legend():
    legend_html = '''
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 150px;
        height: 150px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        ">
        <div style="text-align: center;">Bivariate Legend</div>
        <div style="display: flex;">
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div style="flex: 1;">High % POC</div>
                <div style="flex: 1;"></div>
                <div style="flex: 1;">Low % POC</div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div style="flex: 1; background-color: #3b4994;"></div>
                <div style="flex: 1; background-color: #8c62aa;"></div>
                <div style="flex: 1; background-color: #be64ac;"></div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div style="flex: 1; background-color: #5698b9;"></div>
                <div style="flex: 1; background-color: #a5add3;"></div>
                <div style="flex: 1; background-color: #dfb0d6;"></div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div style="flex: 1; background-color: #5ac8c8;"></div>
                <div style="flex: 1; background-color: #ace4e4;"></div>
                <div style="flex: 1; background-color: #e8e8e8;"></div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div style="flex: 1;">High Access</div>
                <div style="flex: 1;"></div>
                <div style="flex: 1;">Low Access</div>
            </div>
        </div>
    </div>
    '''
    return legend_html


if __name__ == "__main__":
    interactive_map = main()
    interactive_map  # If running in Jupyter Notebook, this will display the map
