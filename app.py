# Import necessary modules for flask 
from flask import Flask, render_template, url_for, abort, request, jsonify
from markupsafe import escape
# importe python modules specific for own code
import json
import datetime
import math
import time
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox
import networkx as nx
import math
import timeit
from pyproj import Proj
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points

app = Flask(__name__)
app.debug = True


# Download file
# Edges file
dir_edges_list = gpd.read_file(r'static/data/edgelist_network.shp', encoding='utf-8')
# Nodes file
nodes = gpd.read_file(r'static/data/osm_nodes_epsg32632.shp', encoding='utf-8')
# Intersection cost file
cost_intersection = pd.read_csv(r'static/data/cost_intersection.csv', encoding='utf-8', sep=';')

# Change crs of edges and nodes to match with leaflet
dir_edges_list_epsg4326 = dir_edges_list.to_crs(epsg=4326)
nodes_epsg4326 = nodes.to_crs(epsg=4326)

# Change some columns types : somid for nodes and edges are often stored as float values, so change them into integers
dir_edges_list_epsg4326['u'] = dir_edges_list_epsg4326['u'].round()
dir_edges_list_epsg4326['v'] = dir_edges_list_epsg4326['v'].round()
# Then change the data types of the columns in integer64
cols = ['u', 'v']
dir_edges_list_epsg4326[cols] = dir_edges_list_epsg4326[cols].applymap(np.int64)
# Same for cost intersection
cost_intersection['id_in'].fillna(0, inplace=True) # Fill nan with 0, otherwise error raised
cost_intersection['id_in'] = cost_intersection['id_in'].round()
cost_intersection[['id_in']] = cost_intersection[['id_in']].applymap(np.int64)
# Put all costs into one column
cost_intersection['cost_movement'] = cost_intersection['Cost_unsignalized']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = cost_intersection['Cost_signalized']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = cost_intersection['cost_mini_roundabout']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = 0

# same for nodes osmid
nodes['osmid']  = nodes['osmid'].round()
nodes[['osmid']] = nodes[['osmid']].applymap(np.int64)
# Remove some columns
nodes.drop(columns=['field_1', 'Unnamed_ 0'], inplace=True)
# Create multipoint from nodes to find nearest nodes from defined orig/dest in leaflet



path = []
# Python functions necessary for routing
# Construct directed graph 
def construct_digraph(dir_edges_list, nodes_df):
    global G # define G as global so it is also defined outside of the function
    
    # Construct directed graph using networkx
    G = nx.from_pandas_edgelist(dir_edges_list, source='u', target='v', edge_attr=True, create_using=nx.DiGraph(), edge_key='key')
    # Define attributes for nodes in a df
    nodes_attr = nodes_df.set_index('osmid').to_dict(orient = 'index')
    # Set nodes attributes in the Graph 
    nx.set_node_attributes(G, nodes_attr)
    # Set crs attribute of the crs
    crs_gdf = str(dir_edges_list.crs)
    print(crs_gdf)
    G = nx.DiGraph(G, crs=crs_gdf)

    if ox.projection.is_projected("epsg:4326"):
        print("Graph is projected") # make sure crs params is defined
    else:
        print("Graph is not projected")
        # G = ox.project_graph(G, to_crs="epsg:4326")
 
    return G

# Find shortest path between two nodes using modified dijstra algorithm that includes intersection weight. There are 3 different functions (credit to Andrés Segura-Tinoco) 
# Returns the node with a minimum own distance
def get_min_node(nodes, weights):
    min_node = -1
    min_weigth = math.inf
    
    for n in nodes:
        w = weights[n]
        if w < min_weigth:
            min_node = n
            min_weigth = w
    
    return min_node

# A detailed version of the Dijkstra algorithm for directed graphs with edges with positive weights 
def get_dijkstra_dist(graph, source, intersection_cost, verbose=False):
    global in_cost, edge_cost  
    nodes = list(graph.nodes())
    edges = graph.edges()
    
    # Init distances
    dists = dict()
    for n in nodes:
        dists[n] = (0 if n == source else math.inf)
    # The path is a dict that contains each node and its predecessor for the shortest path
    paths = dict()
    for n in nodes:
        paths[n] = source
    
    # Greedy cycle
    v = source # begin with source node 
    while len(nodes):        
        nodes.remove(v)
        if verbose:
            print('>> curr node:', v, ', len:', len(nodes))
        
        # Update weights
        for w in nodes:
            if (v, w) in edges:
                edge_cost = nx.get_edge_attributes(G, "PD_DWV")[v,w]
                in_cost = 0
                if v in intersection_cost['id_in'].unique():
                    pred = paths[v] # get predecessor from current node
                    # Get the turn cost in the df
                    row_mov = intersection_cost.loc[(intersection_cost['id_anf']==pred) & (intersection_cost['id_in']== v) & (intersection_cost['id_ant'] == w)]
                    # get the cost value
                    if len(row_mov)!= 0:
                        in_cost = row_mov.iat[-1, -1]
                
                if dists[w] > dists[v] + edge_cost + in_cost:
                    dists[w] = dists[v] + edge_cost + in_cost
                    paths[w] = v
                    if verbose:
                        print('   v:', v, ', w:', w, ', weigth:', dists[w])
        
        # Get the node with a minimum own distance
        v = get_min_node(nodes, dists)
        if v == -1:
            break
        
    return { 'distances': dists, 'paths': paths }

# Show shortes path from source node to target node
def get_shortest_path(dwg, source, target, intersection_cost, verbose=False):
    # Validation
    if not source in dwg.nodes() or not target in dwg.nodes():
        print('Both the source and the target must exist in the graph.')
        return {}
    
    start_time = timeit.default_timer()
    
    # Get the distance from 'source' to the other nodes
    sol = get_dijkstra_dist(dwg, source, intersection_cost, verbose)
    paths = sol['paths']
    
    # Get shortest path from 'source' to 'target'
    ix = target
    path = [ix]
    while ix != source:
        ix = paths[ix]
        path.append(ix)
    path.reverse()
    
    weight = sol['distances'][target]
    
    # Elapsed time
    if verbose:
        elapsed = (timeit.default_timer() - start_time) * 1000
        print('>> elapsed time', elapsed, 'ms')
    
    return { 'path': path, 'weight': weight }


# 266194853
# 563683908
# Different app routes
# Index definition, main page of the application
@app.route('/', methods=["GET", "POST"])
def index():
    # Construct the graph when pages is reached
    construct_digraph(dir_edges_list_epsg4326, nodes_epsg4326)
    global path   
    # Receive lat/lon from geosearching
    if request.method == "POST":
        # Get the lat/lon of start and destination places
        latlngData = request.get_json()
        print(latlngData)
        orig_lon= latlngData['lon_dep']
        orig_lat = latlngData['lat_dep']
        dest_lon= latlngData['lon_dest']
        dest_lat = latlngData['lat_dest']

        # !!!! Need to add function to get the nearest node from the lon and latitude. It exists in OSMnx but it gives strange result, probably a problem of CRS. It alqys gives the same
        orig_node_id, dist_to_orig = ox.distance.nearest_nodes(G, X=orig_lon, Y=orig_lat, return_dist=True)
        print("Origin node-id: ", orig_node_id, "and distance:", dist_to_orig, "meters.")
        # Find the shortest path btw two nodes
        # path = get_shortest_path(G, start, target, cost_intersection, verbose=False)
        # print(path)
        # Send it to js

        # Fixed path to explore link with js
        # With orig = 573250847 (Avenue Louis-Vulliemin) and dest = 20934855 Avenue de Sevelin 
        path = {'path': [573250847, 414238563, 271298545, 266860949, 598462588, 266860951, 35296923, 253414467, 3788043897, 35296878, 561177254, 8168160545, 253414733, 7895322696, 561177082, 7895322694, 7895322693, 253402372, 7895322695, 3520685572, 1463796472, 280650, 767942317, 253402050, 253402053, 695205962, 253402054, 253413326, 5320029301, 3461418955, 8660575986, 8660575987, 1420431333, 334242852, 8050095192, 8050095193, 3111734118, 330630228, 3111734119, 253403391, 253267284, 5319971363, 253267286, 5319971358, 5319971360, 5319971362, 1577380107, 3578319815, 253421603, 565076120, 4553078980, 9140143640, 9751075316, 4553078971, 289638634, 698790746, 564315114, 20934855], 'weight': 7238.580999999999}
        nodes_path = path['path']
        # Define a df that will receive the edges and necessary data 
        # Specify the type of each column when creating the dataframe to avoid errors 
        params_to_keep = ['u', 'v','oneway', 'name', 'DWV_ALLE', 'MSP_ALLE', 'ASP_ALLE', 'grade', 'TC_DWV', 'TC_MSP', 'TC_ASP', 'Am_cycl', 'geometry']
        # edges_path = dir_edges_list[cols_to_keep]
        edges_df = dir_edges_list_epsg4326[params_to_keep]
        edges_df.drop(edges_df.index[:], inplace=True)
        print("edges_df length", len(edges_df))
        for i in range(0, len(nodes_path) - 1, 1):
            edge_u = nodes_path[i]
            edge_v = nodes_path[i+1]
            edge = dir_edges_list.loc[( dir_edges_list_epsg4326['u']==edge_u ) & (dir_edges_list_epsg4326['v']==edge_v)]
            edge = edge[params_to_keep]
            edges_df = pd.concat([edges_df, edge])

        edges_df = edges_df.sort_values(by=['TC_DWV'])
        # There still are duplicated edges, so remove them by keeping the one with the lowest TC
        edges_df.drop_duplicates(subset=['u', 'v'], inplace=True, ignore_index=True)
        # Have to tranform it into json 
        edges_geojson = edges_df.to_json()

        return edges_geojson
        


    # print("The shortest path algorithm is running")
    # start_time = time.time()
    # path = get_shortest_path(G,orig_node_id, dest_node_id, cost_intersection, verbose=False)
    # With orig = 573250847 (Avenue Louis-Vulliemin) and dest = 20934855 Avenue de Sevelin the result is
    # {'path': [573250847, 414238563, 271298545, 266860949, 598462588, 266860951, 35296923, 253414467, 3788043897, 35296878, 561177254, 8168160545, 253414733, 7895322696, 561177082, 7895322694, 7895322693, 253402372, 7895322695, 3520685572, 1463796472, 280650, 767942317, 253402050, 253402053, 695205962, 253402054, 253413326, 5320029301, 3461418955, 8660575986, 8660575987, 1420431333, 334242852, 8050095192, 8050095193, 3111734118, 330630228, 3111734119, 253403391, 253267284, 5319971363, 253267286, 5319971358, 5319971360, 5319971362, 1577380107, 3578319815, 253421603, 565076120, 4553078980, 9140143640, 9751075316, 4553078971, 289638634, 698790746, 564315114, 20934855], 'weight': 7238.580999999999}
    # It takes around 67 seconds..
    # print("The shortest path was found.  It took [seconds]", (time.time() - start_time) , "The path is \n", path)
    start  = request.args.get('start', "")
    target  = request.args.get('target', "")
    if start and target:
        start = int(start)
        target = int(target) # change string into integers
        path = get_shortest_path(G, start, target, cost_intersection, verbose=False)

    return render_template(
        'index.html', 
        path=path
    )

# Page about ot give details and supplementary information
@app.route('/about/')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run()