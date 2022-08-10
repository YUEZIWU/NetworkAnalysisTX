import re, os
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from datetime import datetime
now = datetime.now()
print('start_time', now)
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

# connection costs
mv_cap_m_costs = 25
lv_cap_m_costs = 10
tx_cap_m_costs = 2000

def drop_mvs_from_finalGrid(df1,df2):
    indices = df1[df1.pt1.isin(df2.pt1) & df1.pt2.isin(df2.pt2)].index
    df1.drop(indices, inplace=True)
    return df1

def find_dist(x1,y1,x2,y2):
    return np.sqrt( (x2 - x1)**2 + (y2 - y1)**2)

# modified DFS to find (1) all structures; (2) find the farest distance between tx and structure;
# (3) total LVs length of each transformer
def dfs(visited, graph, node, stpt, radTX, lvs_m):
    if node not in visited:
        # find find the farest distance between tx and structure
        try:
            if sum(graph.pt1==node) > 0:
                structure = graph.loc[graph.pt1==node, 'geometry'].iloc[0].coords[0]
            else:
                structure = graph.loc[graph.pt2==node, 'geometry'].iloc[0].coords[1]
            radTX.add(find_dist(stpt.x,stpt.y,structure[0],structure[1]))
        except:
            pass
        visited.add(node)
        neighbours = (graph.pt2[graph.pt1==node]).append(graph.pt1[graph.pt2==node])
        # + lv line length under this transformer
        lvs_m.update(graph.Length[(graph.pt1==node) | (graph.pt2==node)])
        for neighbour in neighbours:
            dfs(visited, graph, neighbour, stpt, radTX, lvs_m)

tx_locations_geodf = gpd.GeoDataFrame()
for i, name in enumerate(file_names):
    # if i%50 ==0:
    #     print(i, name) # print the process steps of the script
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
            mvs = gpd.GeoDataFrame()
            finalGrid = gpd.GeoDataFrame()
            sub_grid_cons = gpd.GeoDataFrame()
            result = gpd.GeoDataFrame()
            try:
                mvs = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, sub_grid, "MV.shp"))
                finalGrid = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, sub_grid, "FinalGrid.shp
                sub_grid_cons = gpd.read_file(os.path.join(data_folder_path, name, sub_grid, "{}.shp".format(sub_grid)))
            except:
                pass
            if len(mvs) > 0: # when there is mvs
                # get points from lines and remove duplicated ones
                startpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[0]) for i,pt in mvs.iterrows()])
                endpts = gpd.GeoSeries([Point(list(pt['geometry'].coords)[-1]) for i,pt in mvs.iterrows()])
                points =  startpts.append(endpts)
                result = gpd.GeoDataFrame(points,columns=['geometry'])
                result['id'] = mvs['pt1'].tolist() + mvs['pt2'].tolist()
                result = result.drop_duplicates()
                # total mvs costs
                mvs_costs_p_tx = np.sum(mvs['Length']) * mv_cap_m_costs / len(result)
                # find the structures connected to that transformer
                lvs = drop_mvs_from_finalGrid(finalGrid,mvs)
                result['NoStructure'] = None
                result['radTX'] = None
                result['connection_costs_p_str'] = None
                for tx_o_id in result['id']:
                    tx_id = -tx_o_id-100
                    ctpt = result.loc[result.id==tx_o_id, 'geometry'].item()
                    visited = set()
                    radTX = set()
                    lvs_m = set()
                    dfs(visited, lvs, tx_id, ctpt, radTX, lvs_m)
                    result.loc[result.id == tx_o_id, 'NoStructure'] = len(visited)-1
                    result.loc[result.id == tx_o_id, 'radTX'] = max(radTX)
                    connect_costs = sum(lvs_m) * lv_cap_m_costs + tx_cap_m_costs + mvs_costs_p_tx
                    result.loc[result.id == tx_o_id, 'connection_costs_p_str'] = connect_costs / (len(visited)-1)

            else: # when mvs is empty, choose the centriod as the transformer location
                points = gpd.GeoSeries(Point(np.mean(sub_grid_cons['geometry'].x), np.mean(sub_grid_cons['geometry'].y)))
                result = gpd.GeoDataFrame(points,columns=['geometry'])
                result['id'] = 0
                result['NoStructure'] = len(sub_grid_cons)

                radTX = set()
                for con_n, sub_grid_con in sub_grid_cons.iterrows():
                    radTX.add(find_dist(sub_grid_con['utm_x'], sub_grid_con['utm_y'], points.item().x, points.item().y))
                result['radTX'] = max(radTX)
                connect_costs = sum(finalGrid['Length']) * lv_cap_m_costs + tx_cap_m_costs
                result['connection_costs_p_str'] = connect_costs / len(sub_grid_cons)

            # Assign info.
            result['county'] = county
            result['ward'] = ward
            result['sub_grid'] = sub_grid
            result['area_cate'] = str(cate)
            pts_results = pts_results.append(result)
        except:
            print('no transformer found or errors', i, name, sub_grid)
            pass
    pts_results.index = range(len(pts_results))
    tx_locations_geodf = tx_locations_geodf.append(pts_results)
    if i%10 ==0:
        print(i, 'time:', datetime.now() - now) # print the process steps of the script
        now = datetime.now()

tx_locations_geodf = tx_locations_geodf.set_crs('epsg:32737', allow_override=True)
tx_locations_geodf.to_file(os.path.join(output_dir, "gridmodel_tx_locations_2.gpkg"), driver="GPKG")
