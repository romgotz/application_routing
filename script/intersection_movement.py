"""
This algorithm takes a bike network from OSM, calculate the possible movement through intersections, and evaluate the safety of this intersection based on some criteria.
There are at least 2 necessary files
    - A file for the OSM nodes of the network containig : id, x/y position, degree, and some data from OSM (if its a traffic signal or a roundabout)
    - A file with the edges of the OSM network containing data about maxpseed (OSM), lanes (OSM) and trafic (added from another data) 

"""
import time
start_time = time.time()
import pandas as pd
import numpy as np 
import geopandas as gpd
from math import atan2, degrees, pi


def angle_btw_3points(x_anf,y_anf, x_in, y_in, x_ant, y_ant):
    """
    This function takes 3 points in the same row of a df and calculates the angle between them 
    """
    #.values(0) to have only the value without the index
    anf_x0, anf_y0 = x_anf, y_anf
    in_x0, in_y0 = x_in, y_in
    ant_x0, ant_y0 = x_ant, y_ant 

    
    anfx = anf_x0 - in_x0 
    anfy = anf_y0 - in_y0
    antx = ant_x0 - in_x0
    anty = ant_y0 - in_y0

    a = atan2(anfy, anfx)
    c = atan2(anty, antx)
    if a < 0: a += pi*2
    if c < 0: c += pi*2
    return degrees((pi*2 + c - a)) if a > c else degrees(c - a)

def angle_to_mvmt(angle):
    "Takes an angle (in degrees) and returns the associated movement through intersection (droite, gauche or tout_droit"
    if angle > 0 and angle < 165:
        return 'droite'
    elif angle > 195 and angle < 360:
        return 'gauche'
    else:
        return 'tout_droit'  


# define precision to keep in different calculs
precision = 3

# 1. Downloading data
# file path !!! To change and adapt with files online
fp_edges = r'C:/Users/romai/Desktop/memoire/Pre_processing/python/evaluation_cycling_quality/data/input/osm_complete_edges_nodp_complete_data_epsg32632.shp'
fp_nodes = r'C:/Users/romai/Desktop/memoire/Pre_processing/python/evaluation_cycling_quality/data/input/osm_complete_nodes_epsg32632.shp'
# read shp file
edges = gpd.read_file(fp_edges, encoding='utf-8')
nodes = gpd.read_file(fp_nodes, encoding='utf-8')

# keep necessary columns
nodes = nodes[['osmid', 'y', 'x', 'street_cou', 'lon', 'lat', 'elevation', 'highway', 'geometry']]

# Transform utf-8 in ascii : remove accents to avoid errors
cols = edges.select_dtypes(include=[object]).columns
edges[cols] = edges[cols].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))

# Some column types are not good, so change them. And also complete values for some columns
# u, v columns : saved as float, need to change into integers
# First round the value ups and downs if saved with decimals
edges['u'] = edges['u'].round()
edges['v'] = edges['v'].round()
# Then change the data types of the columns into int
cols = ['u', 'v']
edges[cols] = edges[cols].applymap(np.int64)
edges[cols] = edges[cols].applymap(np.int64)

# Change osmid values for nodes
nodes['osmid'] = nodes['osmid'].round()
col=['osmid']
nodes[col] = nodes[col].applymap(np.int64)


# Need to determine degree of each node
# Get u, v columns values and put them together
u_values = edges['u']
v_values = edges['v']
nodes_values = pd.concat([u_values, v_values])
# transform it into df (it is a serie for now)
nodes_degree = pd.DataFrame(nodes_values)
# define column name
nodes_degree = nodes_degree.rename(columns = {0:'osmid'})
# Count the occurence of each osmid node value
nodes_degree['degree'] = nodes_degree.groupby('osmid')['osmid'].transform('size')
# Remove duplicated rows
nodes_degree.drop_duplicates(inplace=True)

# Merge degree in original nodes df
nodes = pd.merge(nodes, nodes_degree, how='left', on=['osmid'])

# keep only nodes with degree value
nodes = nodes.loc[~(nodes['degree'].isna())]

"""
# Select nodes with degree 1
nodes_d1 = nodes.loc[nodes['degree']==1]
list_nodes_d1 = nodes_d1['osmid'].tolist()
print("There are %s nodes with degree 1" %len(list_nodes_d1))
# Remove edges for which v is a node with degree 1, cause it means it is a cul de sac. Is it necessary, maybe for visualisation 
cul_de_sac = directed_edges.loc[directed_edges['v'].isin(list_nodes_d1)]

# Keep only nodes with degree > 1 and remove edges with degree 1 as v
nodes = nodes.loc[nodes['degree']>1]
print(nodes.loc[nodes['osmid']==567931579])
directed_edges = directed_edges.loc[~(directed_edges['v'].isin(list_nodes_d1))]
"""

# Determine nodes that are intersections 
# To have nodes with degree = 4 that are intersections (keep crossings too)
nodes_d4 = nodes.loc[ (nodes['degree'] == 4) & ((nodes['highway'] == 'mini_roundabout') | (nodes['highway'] == 'traffic_signals') | (nodes['highway'] == 'crossing')) ]

# To have nodes with degree = 2 that are intersections
nodes_d2 = nodes.loc[ (nodes['degree'] == 2) & ((nodes['highway'] == 'mini_roundabout') | (nodes['highway'] == 'traffic_signals') | (nodes['highway'] == 'crossing')) ]

# Remove nodes with degree = 0, 1, 2 or 4
nodes_1 = nodes.loc[ (nodes['degree']!=1) & (nodes['degree']!= 0) & (nodes['degree']!=2) & (nodes['degree']!=4) ]

# Put all subset of intersection nodes together 
frames = [nodes_1, nodes_d2, nodes_d4] 
nodes_intersection = pd.concat(frames)

print("\n The number of nodes that corrsepond to an intersection are", len(nodes_intersection))


# 4. Determining the movements possible at an intersection. Because the safety of bikers is dependant of the movement through the intersection.
 
# get unique values of osmid for the intersection nodes
intersection_nodes_array = pd.unique(nodes_intersection['osmid'])

# rest of the code was written with edges, so define edges as directed edges

# Prepare dataframe of edges by keeping only part of the data (about the trafic, oneways) 
edges_subset = pd.DataFrame([edges['key'], edges['osmid'], edges['name'], edges['highway'], edges['oneway'], edges['u'], edges['v'], edges['grade'], edges['lanes'], edges['maxspeed'], edges['DWV_ALLE'], edges['MSP_ALLE'], edges['ASP_ALLE']]).transpose()

# Another dataframe only containing nodes from and to 
edges_only_nodes = pd.DataFrame([edges['u'], edges['v']]).transpose()
cols = ['u', 'v']
edges_only_nodes[cols] = edges_only_nodes[cols].applymap(np.int64)

# Create df in which we will add the movement through an intersection, need to take the osmid of nodes and its x,y position to calculate the angle. IN = intersection node ; ANF = adjacent node from ; ANT = adjacent node to. The movement through an intersection is represented as ANF -> IN -> ANT
# Specify the type of each column when creating the dataframe to avoid errors 
variables = {'id_in': int(),'x_in':float(),'y_in':float(), 'id_anf':int(),'x_anf':float(), 'y_anf':float(), 'id_ant':int(), 'x_ant':float(), 'y_ant':float()}
movement_df = pd.DataFrame(variables, index=[])
# Take subset of data to test the code
# intersection_nodes_array = intersection_nodes_array[0:15]
for osmid in intersection_nodes_array: # iterates through every node being an intersection
    intersection_node = osmid
    # Select all edges in which intersection nodes appear
    selected_edges = edges_only_nodes.loc[ (edges_only_nodes['u'] == intersection_node) | (edges_only_nodes['v'] == intersection_node)]
    # Get unique id values of nodes 
    u = selected_edges['u'].unique().tolist()
    v = selected_edges['v'].unique().tolist()
    # Put two lists together
    u.extend(v)
    # Remove duplicate values
    u = [*set(u)]
    # Remove the intersection node (not necessary to have it for the permutation as it is always present in the movement through intersection)
    u.remove(intersection_node)
    # Get all permutations possible between the nodes connected to the intersections
    movements = list(itertools.permutations(u,2))
    # As the intersection node does not change for the movements, set values here to avoid doing it at every iteration 
    in_x = nodes_intersection[nodes_intersection['osmid'] == intersection_node]['x'].tolist()
    in_x[-1] # to access element of the list (there is only one element)
    in_y = nodes_intersection[nodes_intersection['osmid'] == intersection_node]['y'].tolist() 
    in_y[-1]
    # Add permutation in the movement dataframe
    for i in movements:
        # For each movement through intersection, store it in the dataframe with the y,x position of the nodes
        # Take the id from both nodes
        anf_id = i[0]
        ant_id = i[1]
        # Get x,y position for each node
        # anf node
        anf_x = nodes[nodes['osmid'] == anf_id]['x'].item()
        anf_y = nodes[nodes['osmid'] == anf_id]['y'].item()
        # ant node
        ant_x = nodes[nodes['osmid'] == ant_id]['x'].item()
        ant_y = nodes[nodes['osmid'] == ant_id]['y'].tolist()
        ant_y[-1]
        # Append all values in dataframe using concat (append is soon deprecated)
        row = pd.DataFrame({'id_in' : intersection_node, 'x_in': in_x, 'y_in' : in_y, 'id_anf' : anf_id,'x_anf': anf_x, 'y_anf' : anf_y, 'id_ant' : ant_id, 'x_ant':ant_x, 'y_ant':ant_y}, index=[0])
        movement_df = pd.concat([row,movement_df.loc[:]]) 


# Checking if the 1st part of the movement is possible (adjacent node from to the intersection node) and adds trafic data for this movement. Keep movement_df row only if the edge exists (u to v) in the edges_df 
movement_intersection_df = pd.merge(movement_df, edges, how='inner', left_on=['id_anf', 'id_in'], right_on=['u', 'v'])

# Rename the columns added to take into account the from to
dict = {'key':'key_anf_in', 'name': 'name_anf_in', 'highway' : 'highway_anf_in', 'oneway':'oneway_anf_in', 'grade':'grade_anf_in',  'lanes': 'lanes_anf_in', 'maxspeed':'maxspeed_anf_in', 'DWV_ALLE':'DWV_ALLE_anf_in', 'MSP_ALLE':'MSP_ALLE_anf_in', 'ASP_ALLE':'ASP_ALLE_anf_in'}
movement_intersection_df.rename(columns=dict, inplace=True)

# Checking if the 2nd part of the movement is possible (from intersection node  to the adjacent node to) and adds trafic data for this movement. Keep movement_df row only if the edge exists (u to v) in the edges_df 
movement_intersection_df = pd.merge(movement_intersection_df, edges, how='inner', left_on=['id_in', 'id_ant'], right_on=['u', 'v'])

# Make sure that the columns are in the good data type (float) 
cast_to_type = {
    'DWV_ALLE_anf_in': float,
    'MSP_ALLE_anf_in': float,
    'ASP_ALLE_anf_in': float,
    'DWV_ALLE': float,
    'MSP_ALLE': float,
    'ASP_ALLE': float,
    }
movement_intersection_df = movement_intersection_df.astype(cast_to_type)

# Calculates the mean of traffic from the two edges present in the movement 
movement_intersection_df = movement_intersection_df.assign(DWV_mean = lambda x: ((x['DWV_ALLE'] + x['DWV_ALLE_anf_in']) / 2).round(precision))
movement_intersection_df = movement_intersection_df.assign(MSP_mean = lambda x: ((x['MSP_ALLE'] + x['MSP_ALLE_anf_in']) / 2).round(precision))
movement_intersection_df = movement_intersection_df.assign(ASP_mean = lambda x: ((x['ASP_ALLE'] + x['ASP_ALLE_anf_in']) / 2).round(precision))

# Rename again some columns
dict = {'key':'key_in_ant','name': 'name_in_ant', 'highway' : 'highway_in_ant', 'oneway':'oneway_in_ant', 'lanes': 'lanes_in_ant', 'maxspeed':'maxspeed_in_ant', 'grade':'grade_in_ant'}
movement_intersection_df.rename(columns=dict, inplace=True)

# Renmove unecessary columns
columns_to_remove = ['osmid_x','osmid_y','u_x','u_y', 'v_y','v_x','DWV_ALLE_anf_in', 'MSP_ALLE_anf_in', 'ASP_ALLE_anf_in','DWV_ALLE','MSP_ALLE', 'ASP_ALLE']
movement_intersection_df.drop(columns=columns_to_remove, inplace = True)

# 5. Determine angle and direction for each movement
# Calculate the angle between the 3 points for every row in movement_df
movement_intersection_df['angle'] = movement_intersection_df.apply(lambda x: angle_btw_3points(x["x_anf"], x["y_anf"], x["x_in"], x["y_in"], x["x_ant"], x["y_ant"]), axis = 1).round(3)
movement_intersection_df['movement'] = movement_intersection_df['angle'].apply(angle_to_mvmt)

# Saving the movement through intersection dataframe

print("\n The movements through intersection have been defined. There are ", len(movement_intersection_df), " defined movements")


columns_to_remove = ['service_x', 'junction_x', 'bridge_x', 'tunnel_x', 'speed_zone_x', 'Am_cycl_x', 'Am_Direct_x', 'Am_cycl_2_x', 'Am_Dir_2_x', 'DWV_PW_x', 'DWV_LI_x', 'DWV_LW_x', 'DWV_LZ_x', 'MSP_PW_x', 'MSP_LI_x', 'MSP_LW_x', 'MSP_LZ_x', 'ASP_PW_x', 'ASP_LI_x', 'ASP_LW_x', 'ASP_LZ_x', 'pour100_GW_x', 'geometry_x', 'length_y', 'grade_in_ant', 'service_y', 'junction_y', 'bridge_y', 'tunnel_y', 'speed_zone_y', 'Am_cycl_y', 'Am_Direct_y', 'Am_cycl_2_y', 'Am_Dir_2_y', 'DWV_PW_y', 'DWV_LI_y', 'DWV_LW_y', 'DWV_LZ_y', 'MSP_PW_y', 'MSP_LI_y', 'MSP_LW_y', 'MSP_LZ_y', 'ASP_PW_y', 'ASP_LI_y', 'ASP_LW_y', 'ASP_LZ_y', 'pour100_GW_y', 'geometry_y']

movement_intersection_df.drop(columns=columns_to_remove, inplace=True)

print(movement_intersection_df.head())

movement_intersection_df.to_csv('data/output/movement_intersection_complete_network.csv', sep=';')  

print("\n The movements through intersection have been defined. There are ", len(movement_intersection_df), " defined movements")

print("\n--- The program took %s seconds ---" % (time.time() - start_time))

