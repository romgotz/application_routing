from scipy import spatial
import numpy as np
import geopandas as gpd

nodes= gpd.read_file(r'static/data/osm_nodes_epsg32632.shp', encoding='utf-8')

nodes_epsg3857 = nodes.to_crs(epsg=3857)
# same for nodes osmid
nodes_epsg3857['osmid']  = nodes_epsg3857['osmid'].round()
nodes_epsg3857[['osmid']] = nodes_epsg3857[['osmid']].applymap(np.int64)
# Remove some columns
nodes_epsg3857.drop(columns=['field_1', 'Unnamed_ 0'], inplace=True)

for i in range(0, len(nodes_epsg3857)):
    point = nodes['geometry'][i]
    x = point.coords[0][0]
    y = point.coords[0][1]
    nodes.loc[nodes.index == i, 'x'] = x
    nodes.loc[nodes.index == i, 'y'] = y
# Keep only x,y coordinates
nodes_epsg3857 = nodes[['x', 'y']]
# Create multipoint from nodes_epsg3857
print(nodes_epsg3857.head(5))

kd_tree = spatial.KDTree(nodes_epsg3857)
print(kd_tree)

test_node = nodes.loc[nodes['osmid']==414238563]
X = np.array([test_node['x'].item()])
Y = np.array([test_node['y'].item()])
print("X : %s ; Y : %s", X,Y)
# Determine position and distance
dist, pos = kd_tree.query(np.array([X, Y]).T, k=1)
print("position: ", pos, "type : ", type(pos))
index = pos[0]
print("index:", index, "type: ", type(index))
closest_node = nodes_epsg3857.loc[nodes_epsg3857.index==index]
print(closest_node)
# node_osmid = nodes.loc[nodes.index == pos]['osmid']
# print("nodes osmid :", node_osmid)
print("dist: ", dist)

