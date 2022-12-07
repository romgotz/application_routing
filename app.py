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
from scipy import spatial 
import math
import timeit
from pyproj import Proj, transform
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points

app = Flask(__name__)
app.debug = True


# 1. Download local data and prepare it 
# Edges file to build the graph 
dir_edges_list = gpd.read_file(r'static/data/edgelist_network.shp', encoding='utf-8')
# Nodes file to build the graph 
nodes = gpd.read_file(r'static/data/osm_nodes_epsg32632.shp', encoding='utf-8')
nodes_epsg3857_xy = pd.read_csv(r'static/data/nodes_xy_epsg3857.csv', sep=";", encoding='utf-8')
# Intersection cost file for the shortest path algorithm
cost_intersection = pd.read_csv(r'static/data/cost_intersection.csv', encoding='utf-8', sep=';')

# Remove uncessary column
nodes_epsg3857_xy.drop(columns=['Unnamed: 0'], inplace=True)
# Change some columns types. u/v columns are stored as float values, but need to be integers 
# Round float values 
dir_edges_list['u'] = dir_edges_list['u'].round()
dir_edges_list['v'] = dir_edges_list['v'].round()
# Change  data types to integer64
cols = ['u', 'v']
dir_edges_list[cols] = dir_edges_list[cols].applymap(np.int64)

# Do the same with nodes osmid 
# same for nodes osmid
nodes['osmid']  = nodes['osmid'].round()
nodes[['osmid']] = nodes[['osmid']].applymap(np.int64)
# Remove some unecessary columns
nodes.drop(columns=['field_1', 'Unnamed_ 0'], inplace=True)

# Create nodes and edges df with different crs
# epsg:4326 to match leaflet crs
dir_edges_list_epsg4326 = dir_edges_list.to_crs(epsg=4326)
nodes_epsg4326 = nodes.to_crs(epsg=4326)

# Epsg 3857 to have meters unit 
dir_edges_list_epsg3857 = dir_edges_list.to_crs(epsg=3857)
nodes_epsg3857 = nodes.to_crs(epsg=3857)

# Change column for intersection df 
cost_intersection['id_in'].fillna(0, inplace=True) # Fill nan with 0, otherwise error raised
cost_intersection['id_in'] = cost_intersection['id_in'].round()
cost_intersection[['id_in']] = cost_intersection[['id_in']].applymap(np.int64)
# Put all costs into one column
cost_intersection['cost_movement'] = cost_intersection['Cost_unsignalized']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = cost_intersection['Cost_signalized']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = cost_intersection['cost_mini_roundabout']
cost_intersection.loc[cost_intersection['cost_movement'].isna(), 'cost_movement'] = 0


def construct_kdTree(nodes_xy):
    """ Function that take nodes df containing x,y coordinates and construct a spatial KD_Tree that can be used to determine nearest node"""
    global kd_tree # Defines global so it can be used in the entire application code
    # Create the kd_tree (to find nearest node from localisation coordinates)
    kd_tree = spatial.KDTree(nodes_xy)
    return kd_tree

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
    print("crs gdf in construct graph function :", crs_gdf)
    G = nx.DiGraph(G, crs=crs_gdf)

    if ox.projection.is_projected(crs_gdf):
        print("Graph is projected in ", crs_gdf) # make sure crs params is defined
    else:
        print("Graph is not projected")
 
    return G

# Get nearest node in graph from the coordinates send from leaflet
def get_nearest_node(kdTree, x, y):
    # Define x,y coordinates as np array for ckdtree
    X = np.array([x])
    Y = np.array([y])
    # Determine position and distance
    dist, pos = kdTree.query(np.array([X, Y]).T, k=1)
    # Get value of the position (it is in a np.array)
    index = pos[0]
    closest_node = nodes_epsg3857.loc[nodes_epsg3857.index==index]
    closest_node_osmid = closest_node['osmid'].item()
    print("The closest node osmid is %s .And the dist is %s" %(closest_node_osmid, dist))

    return closest_node_osmid

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
def get_dijkstra_dist(graph, source,edge_weight, intersection_cost, verbose=False):
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
                edge_cost = nx.get_edge_attributes(G, edge_weight)[v,w]
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
def get_shortest_path(dwg, source, target, edge_weight, intersection_cost, verbose=False):
    # Validation
    if not source in dwg.nodes() or not target in dwg.nodes():
        print('Both the source and the target must exist in the graph.')
        return {}
    
    start_time = timeit.default_timer()
    print("The edge weight is", edge_weight)
    # Get the distance from 'source' to the other nodes
    sol = get_dijkstra_dist(dwg, source,edge_weight, intersection_cost, verbose)
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

# Opening page of the app. It constructs the graph used fro
@app.route('/')
def opening_page():
    construct_digraph(dir_edges_list=dir_edges_list_epsg3857, nodes_df=nodes_epsg3857)
    construct_kdTree(nodes_xy=nodes_epsg3857_xy)
    return render_template('index.html')

path = []
# Different app routes
# Index definition, main page of the application
@app.route('/', methods=["GET", "POST"])
def get_itineraries():
    global path
    # Receive data for the routing from js file
    if request.method == "POST":
        # Get data necessary for routing : settings and lat/lng
        routingData = request.get_json()
        # Determine settings from checkboxes
        settings = routingData['Settings']
        # Different trafic values according to checkboxes, by default it is DWV
        # HP_matin = ASP
        if ('HP_matin' in settings):
            # Determine the names of the coloumns to take into account
            trafic_col = 'MSP_ALLE'
            tc_col = 'TC_MSP'
            pd_col = 'PD_MSP'
        # HP_soir = ASP
        elif ('HP_soir' in settings):
            trafic_col = 'ASP_ALLE'
            tc_col = 'TC_ASP'
            pd_col = 'PD_ASP'
        # DWV (by default) 
        else:
            trafic_col = 'DWV_ALLE'
            tc_col = 'TC_DWV'
            pd_col = 'PD_DWV'
        # For the intersections and vae 
        if ('intersections' in settings ):
            cost_inter = True
        if('vae' in settings):
            vae = True
        # Now the lat/lng data 
        # Project the lat/lng in epsg3857 to have meters
        outProj = Proj('epsg:3857')
        inProj = Proj('epsg:4326')
        orig_lat = routingData['lat_dep']
        orig_lon= routingData['lon_dep']
        dest_lat = routingData['lat_dest']
        dest_lon= routingData['lon_dest']
        orig_lat, orig_lon = transform(inProj,outProj,orig_lat,orig_lon)
        dest_lat, dest_lon = transform(inProj,outProj,dest_lat, dest_lon)
        # print("After projecting into epsg:3857. Orig_lat: %s ; Orig_lon : %s ;  Dest_lat: %s; Dest_lon : %s" %(orig_lat, orig_lon, dest_lat, dest_lon))
        start = get_nearest_node(kdTree=kd_tree, x=orig_lat, y=orig_lon)
        target = get_nearest_node(kdTree=kd_tree, x=dest_lat, y=dest_lon)

        print("Determining the shortest path. It might take a moment")
        start_time = time.time()
        path = get_shortest_path(dwg=G,source=start,target=target,edge_weight=pd_col,intersection_cost = cost_intersection, verbose=False)
        print("The shortest path was found. It took [seconds]", (time.time() - start_time) , "The path is \n", path)
        # Fixed path to go quicker
        path = [266860942, 414238563, 573250847, 418016472, 602689559, 267510221, 602689574, 573250900, 8790226568]
        # Determine the edges corresponding to the nodes in the path
        nodes_path = path# ['path']
        # Define a df that will receive the edges and necessary data 
        params_to_keep = ['u', 'v','oneway', 'name', 'grade', 'Am_cycl', trafic_col, pd_col, tc_col, 'geometry']
        # Take the edges from df with crs = epsg:4326 to match leaflet 
        edges_df = dir_edges_list_epsg4326[params_to_keep]
        edges_df.drop(edges_df.index[:], inplace=True)
        for i in range(0, len(nodes_path) - 1, 1):
            edge_u = nodes_path[i]
            edge_v = nodes_path[i+1]
            edge = dir_edges_list_epsg4326.loc[( dir_edges_list_epsg4326['u']==edge_u ) & (dir_edges_list_epsg4326['v']==edge_v)]
            edge = edge[params_to_keep]
            edges_df = pd.concat([edges_df, edge])

        edges_df = edges_df.sort_values(by=[tc_col])
        # There still are duplicated edges, so remove them by keeping the one with the lowest TC
        edges_df.drop_duplicates(subset=['u', 'v'], inplace=True, ignore_index=True)
        # Have to tranform it into json 
        edges_geojson = edges_df.to_json()

        return edges_geojson

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