import geopandas as gpd
import pandas as pd
import numpy as np
import re, os
from shapely.geometry import Point

data_folder_path = '/mnt/nfs/eguide/projects/networkAnalysis/Kenya/networkDesign_results/'
file_names = os.listdir(data_folder_path)
file_names = file_names

# create a folder
output_dir = 'transformers_location'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

str_locations_geodf = gpd.GeoDataFrame()
for i, name in enumerate(file_names):
    print(i, name)
    ward = re.split(r'_', name)[0]
    county = re.split(r'_', name)[1]
    sub_grid_list = os.listdir(os.path.join(data_folder_path, name))
    for sub_grid in sub_grid_list:
        try:
            sub_grid_strs = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, "{}.shp".format(sub_grid)))
            sub_grid_strs['county'] = county
            sub_grid_strs['ward'] = ward
            sub_grid_strs['sub_grid'] = sub_grid
            #print(sub_grid_strs)
            str_locations_geodf = str_locations_geodf.append(sub_grid_strs)
        except:
            pass
str_locations_geodf.index = range(len(str_locations_geodf))

str_locations_geodf.crs = {'init' :'epsg:32737'}
str_locations_geodf.to_file(os.path.join(output_dir, "kenya_structures.gpkg"), driver="GPKG")
