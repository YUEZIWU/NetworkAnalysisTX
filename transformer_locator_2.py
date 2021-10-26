import re, os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
# locate to data folder
data_folder_path = '/mnt/nfs/eguide/projects/networkAnalysis/Kenya/networkDesign_results/'
file_names = os.listdir(data_folder_path)
file_names = file_names[1000:1431]

# create a folder
output_dir = 'transformers_location'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# read the category
cate_file = pd.read_csv('wards_summary_mvlv_w_area_type.csv')

tx_locations_geodf = gpd.GeoDataFrame()
for i, name in enumerate(file_names):
    if i%10 ==0:
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
            mvs = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, sub_grid, "MV.shp"))
            # get points from lines and remove duplicated ones
            startpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[0]) for i,pt in mvs.iterrows()])
            endpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[-1]) for i,pt in mvs.iterrows()])
            points = startpts.append(endpts)
            result = gpd.GeoDataFrame(points,columns=['geometry'])
            result['id'] = mvs['pt1'].tolist() + mvs['pt2'].tolist()
            result = result.drop_duplicates()
            result['county'] = county
            result['ward'] = ward
            result['sub_grid'] = sub_grid
            result['area_cate'] = str(cate)
            pts_results = pts_results.append(result)
        except:
            pass
    pts_results.index = range(len(pts_results))
    tx_locations_geodf = tx_locations_geodf.append(pts_results)

tx_locations_geodf.to_file(os.path.join(output_dir, "gridmodel_tx_locations_2.gpkg"), driver="GPKG")
#tx_locations_geodf.to_file(os.path.join(output_dir, "gridmodel_tx_locations.shp"))