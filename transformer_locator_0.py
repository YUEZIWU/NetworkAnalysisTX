import re, os
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
# locate to data folder
data_folder_path = '/mnt/nfs/eguide/projects/networkAnalysis/Kenya/networkDesign_results/'
file_names = os.listdir(data_folder_path)
file_names = file_names[0:500]

# create a folder
output_dir = 'transformers_location'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# read the category
cate_file = pd.read_csv('wards_summary_mvlv_w_area_type.csv')

tx_locations_geodf = gpd.GeoDataFrame()
for i, name in enumerate(file_names):
    if i%50 ==0:
        print(i)
    pts_results = gpd.GeoDataFrame()
    ward = re.split(r'_', name)[0]
    county = re.split(r'_', name)[1]
    sub_grid_list = os.listdir(os.path.join(data_folder_path, name))
    if len(cate_file[(cate_file['ward'].str.lower()==ward.lower())&(cate_file['county'].str.lower()==county.lower())])>0:
        cate = cate_file[(cate_file['ward'].str.lower()==ward.lower())&
                         (cate_file['county'].str.lower()==county.lower())].area_type.values[0]
    else:
        cate = None
    for sub_grid in sub_grid_list:
        try:
            mvs = None
            result = gpd.GeoDataFrame()
            mvs = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, sub_grid, "MV.shp"))
            if len(mvs) > 0: # when there is mvs
                # get points from lines and remove duplicated ones
                startpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[0]) for i,pt in mvs.iterrows()])
                endpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[-1]) for i,pt in mvs.iterrows()])
                points =  startpts.append(endpts)
                result = gpd.GeoDataFrame(points,columns=['geometry'])
                result['id'] = mvs['pt1'].tolist() + mvs['pt2'].tolist()
                result = result.drop_duplicates()
            else: # when mvs is empty, choose the centriod as the transformer location
                sub_grid_cons = None
                sub_grid_cons = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, "{}.shp".format(sub_grid)))
                points = gpd.GeoSeries(Point(np.mean(sub_grid_cons['geometry'].x), np.mean(sub_grid_cons['geometry'].y)))
                result = gpd.GeoDataFrame(points,columns=['geometry'])
                result['id'] = 0 # !!! action may be needed
            # Assign info.
            result['county'] = county
            result['ward'] = ward
            result['sub_grid'] = sub_grid
            result['area_cate'] = str(cate)
            pts_results = pts_results.append(result)
        except:
            print('no transformer found: ', name, sub_grid)
            pass
    pts_results.index = range(len(pts_results))
    tx_locations_geodf = tx_locations_geodf.append(pts_results)

tx_locations_geodf.crs = {'init' :'epsg:4326'}
tx_locations_geodf.to_file(os.path.join(output_dir, "gridmodel_tx_locations_0.gpkg"), driver="GPKG")
#tx_locations_geodf.to_file(os.path.join(output_dir, "gridmodel_tx_locations.shp"))
