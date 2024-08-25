import pandas as pd
import geopandas as gpd
import requests
from io import StringIO
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os


def bivariate_classification(x, y):
    if pd.isna(x) or pd.isna(y):
        return np.nan

    if isinstance(x, (float, int)) and isinstance(y, (float, int)):
        if len(set([x, y])) < 3:
            return '22'
        try:
            x_class = pd.qcut([x], 3, labels=[1, 2, 3], duplicates='drop')[0]
            y_class = pd.qcut([y], 3, labels=[1, 2, 3], duplicates='drop')[0]
            return str(x_class) + str(y_class)
        except ValueError:
            return '22'
    else:
        return np.nan


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
        lambda row: bivariate_classification(row['People_of_Color'], row['Access_Healthy_Foods']), axis=1
    )

    bivariate_colors = {
        '11': '#e8e8e8', '12': '#ace4e4', '13': '#5ac8c8',
        '21': '#dfb0d6', '22': '#a5add3', '23': '#5698b9',
        '31': '#be64ac', '32': '#8c62aa', '33': '#3b4994'
    }

    joined_clean['color'] = joined_clean['bi_class'].map(bivariate_colors)

    # Remove rows where the color is NaN
    joined_clean = joined_clean.dropna(subset=['color'])

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    joined_clean.plot(ax=ax, color=joined_clean['color'], linewidth=0.1, edgecolor='white')
    ax.set_title('% People of Color and Limited Access To Healthy Foods in Washington State', fontsize=15)

    legend_labels = [
        ('#e8e8e8', 'Low People of Color, Low Limited Access'),
        ('#ace4e4', 'Low People of Color, Medium Limited Access'),
        ('#5ac8c8', 'Low People of Color, High Limited Access'),
        ('#dfb0d6', 'Medium People of Color, Low Limited Access'),
        ('#a5add3', 'Medium People of Color, Medium Limited Access'),
        ('#5698b9', 'Medium People of Color, High Limited Access'),
        ('#be64ac', 'High People of Color, Low Limited Access'),
        ('#8c62aa', 'High People of Color, Medium Limited Access'),
        ('#3b4994', 'High People of Color, High Limited Access')
    ]

    for color, label in legend_labels:
        ax.plot([], [], color=color, label=label)

    ax.legend(loc='lower left', frameon=False)

    plt.show()


if __name__ == "__main__":
    main()
