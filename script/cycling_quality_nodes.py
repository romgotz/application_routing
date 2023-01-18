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
import osmnx as ox
import networkx as nx
from shapely import wkt

def cost_intersection_nosignalisation(movement,trafic):
    global inter_cost
    # basic_cost = 67
    # Tourner a droite
    if movement == 'droite':
        if trafic > 10000:
            inter_cost = 61
        else: 
            inter_cost = 0
    # Tourner a gauche
    elif movement == 'gauche':
        if trafic < 10000 and trafic > 5000:
            inter_cost = 66 
        elif trafic < 20000 and trafic > 10000:
            inter_cost = 147
        elif trafic > 20000:
            inter_cost = 372
        else:
            inter_cost = 0

    # Tout droit
    elif movement == 'tout_droit':
        if trafic < 10000 and trafic > 5000:
            inter_cost = 66 
        elif trafic < 20000 and trafic > 10000:
            inter_cost = 94
        elif trafic > 20000:
            inter_cost = 217
        else:
            inter_cost = 0  
    
    return inter_cost + basic_cost

def small_roundabout_cost(movement,trafic, maxspeed):
    global roundabout_cost
    roundabout_cost = 0
    global basic_cost
    basic_cost = 67
    # Tourner a droite
    if movement == 'droite':
        if maxspeed == 30:
            if trafic <= 10000 :
                roundabout_cost = 10
            elif trafic >= 10000 :
                roundabout_cost = 30 
        elif maxspeed == 50:
            if trafic <= 10000:
                roundabout_cost = 15
            elif trafic >= 10000:
                roundabout_cost = 45
        else: 
            roundabout_cost = 0
    # Tourner a gauche/tout droit
    elif (movement == 'gauche')|(movement=='tout_droit'):
        if maxspeed == 30:
            if trafic <= 10000 :
                roundabout_cost = 30
            elif trafic >= 10000 :
                roundabout_cost = 60 
        elif maxspeed == 50:
            if trafic <= 10000:
                roundabout_cost = 45
            elif trafic >= 10000:
                roundabout_cost = 90
        else: 
            roundabout_cost = 0  
    
    return roundabout_cost + basic_cost

# Different multipliers costs
# Sas_velo
def sas_mutliplier(sas_velo): 
    if sas_velo=='easy':
        cost_sas = 0.7
    elif sas_velo=='yes':
        cost_sas=0.8
    else:
        cost_sas=1
    return cost_sas

# preselection velo
def presel_velo_multiplier(presel_velo):
    if presel_velo=='easy':
        cost_presel_velo = 0.8
    elif presel_velo =='yes':
        cost_presel_velo =0.9
    else:
        cost_presel_velo=1
    return cost_presel_velo
# tag indirect
def tag_multiplier(tag_indirect):
    # Tourner a gauche indirect
    if tag_indirect=='yes':
        cost_tag = 0.8
    else:
        cost_tag=1
    return cost_tag
# tad_fr
def tad_multiplier(tad_fr):
    if tad_fr=='yes':
        cost_tad_fr = 0.9
    else:
        cost_tad_fr=1
    return cost_tad_fr

# Lanes
def lanes_multiplier(lanes, oneway):
    if oneway == 'True' or  oneway==1:
        if lanes >= 2:
            cost_lanes = 1.5
        else:
            cost_lanes=1
        return cost_lanes
    else:
        if lanes > 2:
            cost_lanes = 1.5
        else:
            cost_lanes=1
        return cost_lanes

# Tad VIM
def presel_vim_multiplier(presel_vim, bc_rouge):
    if (presel_vim=='yes') & (bc_rouge=='yes'):
        cost_tad_vim = 1.1
    elif presel_vim=='yes':
        cost_tad_vim=1.2
    else:
        cost_tad_vim=1
    return cost_tad_vim
    
# Tjm
def trafic_multiplier(trafic):
    if (trafic>10000) & (trafic <20000):
        cost_tjm = 1.1
    elif trafic >=20000:
        cost_tjm=1.3
    else:
        cost_tjm=1
    return cost_tjm
 

# define precision to keep in different calculs
precision = 3

fp_nodes = r'static/data/nodes_network_epsg32632.csv'
movement_fp = r'movement_intersection_complete_network.csv'

# 1. Downloading data
# Read the edges data ( one is shapefile, the other one is csv) ; have to specify encofing = utf-8 because there are some accents in the data
movement_df = pd.read_csv(movement_fp, encoding='utf-8', sep = ';')
nodes = pd.read_csv(fp_nodes, encoding='utf-8', sep=';')
# Keep only necesary columns
nodes_df = nodes[['osmid_original', 'y', 'x','geometry']]

# Prepare movement data 

print(movement_df.columns.values.tolist())

# Columns: [field_1, id_in, x_in, y_in, id_anf, x_anf, y_anf, id_ant, x_ant, y_ant, name_anf_in, oneway_anf_in, lanes_anf_in, highway_anf_in, maxspeed_anf_in, grade_anf_in, name_in_ant, oneway_in_ant, lanes_in_ant, highway_in_ant, maxspeed_in_ant, grade_in_ant, DWV_mean, angle, movement, sas, tag, tad_fr, tad_vim, bc_rouge, preselection, Comment, Signalized_inter]

# Make sure there is no movement with non existing nodes
nodes_id = nodes['osmid'].unique().tolist()
movement_df = movement_df.loc[(movement_df['id_in'].isin(nodes_id)) & (movement_df['id_ant'].isin(nodes_id)) & (movement_df['id_anf'].isin(nodes_id))]

nodes_ts = nodes.loc[(nodes['highway'] == 'traffic_signals')|(nodes['highway'] == 'crossing')]
nodes_ts_id = nodes_ts['osmid'].unique().tolist()


# If id_in is a trafic signal, update signalized intersection
movement_df.loc[movement_df['id_in'].isin(nodes_ts_id), 'Signalized_inter'] = 'yes'

# Calculating cost for intersection movement

# Explore repartition of different columns values
columns = ['sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection','Signalized_inter']
# Create new df for the cost
cost_df = movement_df 
# Some values in the column for sas are in fact preselection, so need to report those values in the good column
# Update those values in the correct column
cost_df.loc[cost_df['sas'] == 'presel easy', 'preselection'] = 'easy'
cost_df.loc[cost_df['sas'] == 'presel', 'preselection'] = 'yes'
# remove those values from sas columns
cost_df.loc[ (cost_df['sas'] == 'presel easy') | (cost_df['sas'] == 'presel'), 'sas'] = np.nan

# Some values are stored with capital letters, sometimes not ; remove capital letters to avoid errors
for i in columns:
    cost_df[i] = cost_df[i].str.lower()

# Calculate cost values

# Need to add column of nodes containing info about crossing, mini roundabout, etc
nodes_df = nodes[['osmid', 'highway']]
cost_df = pd.merge(cost_df, nodes_df, how='left', left_on=['id_in'], right_on=['osmid'])
# Add a value to categorize mini roundabout
cost_df.loc[cost_df['highway']=='mini_roundabout', 'Signalized_inter'] = 'm_ra'
# Add value to categorize unsignalised intersections
cost_df.loc[cost_df['Signalized_inter'].isna(), 'Signalized_inter'] = 'no'

# Some movements at Rue de la Barre are wronlgy stored as mini_roundabout in OSM
cost_df.loc[(cost_df['name_anf_in']=='Rue de la Barre')&(cost_df['Signalized_inter']=='m_ra'), 'Signalized_inter'] = 'no'
cost_df.loc[(cost_df['name_anf_in']=='Rue de la Barre')&(cost_df['Signalized_inter']=='m_ra'), 'highway'] = 'No'

# For mini roundabout
cost_df.loc[cost_df['highway'] == 'mini_roundabout', 'C_MR'] = cost_df.apply(lambda x: small_roundabout_cost(x['movement'], x['DWV_mean'],x['maxspeed_anf_in']), axis = 1)
# If the mini_roundabout is not between residential/living_street, add basic cost 
cost_df.loc[ (cost_df['highway'] == 'mini_roundabout') & ( (cost_df['highway_anf_in'].isin(['residential', 'living_street']) ) & (cost_df['highway_in_ant'].isin(['residential', 'living_street']) ) )  , 'C_MR'] = cost_df['C_MR'] - basic_cost 

# For signalized and unsignalized intersection

# Determine different cost multipliers for specific configurations for every movement
# cost_multiplier= cost_sas*cost_presel_velo* cost_tag*cost_tad*cost_lanes*cost_tad_vim*cost_tjm 
cost_df['M_SAS'] = cost_df['sas'].apply(sas_mutliplier)
cost_df['M_TAD_FR'] = cost_df['tad_fr'].apply(tad_multiplier)
cost_df['M_TAG'] = cost_df['tag'].apply(tag_multiplier)
# cost_df['M_LANES']  = cost_df['lanes_anf_in'].apply(lanes_multiplier)
cost_df['M_DWV'] = cost_df['DWV_mean'].apply(trafic_multiplier)
cost_df['M_TAD_VIM'] = cost_df.apply(lambda x : presel_vim_multiplier(presel_vim=x['tad_vim'], bc_rouge=x['bc_rouge']), axis=1)
cost_df['M_LANES'] = cost_df.apply(lambda x : lanes_multiplier(lanes=x['lanes_anf_in'], oneway=x['oneway_anf_in']), axis=1)
cols_multi = ['M_SAS', 'M_TAD_FR', 'M_TAG', 'M_LANES', 'M_DWV', 'M_TAD_VIM']
# Relace nan with 1 for those columns otherwise multiplication not possible
cost_df[cols_multi].fillna(1, inplace=True)
# Total multiplier 
cost_df['M_TOTAL'] = cost_df['M_SAS']*cost_df['M_TAD_FR']*cost_df['M_TAG']*cost_df['M_LANES']*cost_df['M_DWV']*cost_df['M_TAD_VIM']

for i in cols_multi:
    repartition = cost_df[i].value_counts(dropna=False)
    print("For columns", i, "the number of movement with this configuration is\n", repartition)

# Calculate cost for signalized intersection
signalized_cost = 34
# Determine for all movements 
cost_df.loc[cost_df['Signalized_inter'] == 'yes', 'C_SIGNAL'] = cost_df['M_TOTAL']*(basic_cost+signalized_cost)
# If there is the possibility to turn right at red, do not have signalized_cost
cost_df.loc[(cost_df['Signalized_inter'] == 'yes') & (cost_df['tad_fr']=='yes'), 'C_SIGNAL'] = cost_df['M_TOTAL']*(basic_cost)

# Some movements are actually not possible at signalized intersection. Define a very high cost for this movement, so it will not be chosen in the shortest path algorithm.
impossible_moves = ['move impossible','movement impossible', 'mov impossible', 'movement possible ?','no intersection','move impossible travaux', 'not intersection', 'no intersection move', 'move_impossible', 'move impossible ?','Move impossible', 'mouv impossible', 'not necessary']
cost_df.loc[cost_df['Comment'].isin(impossible_moves), 'C_SIGNAL'] = 9999
cost_df.loc[cost_df['Comment'].isin(impossible_moves), 'Signalized_inter'] = 'impossible'

signalized = cost_df.loc[cost_df['Signalized_inter'] == 'yes']
print("The descriptive statistics for the signalized intersection is\n", signalized['C_SIGNAL'].describe())


# For unsignalised intersection
# Select them by removing signalized intersection and roundabouts. Only mulitply by the M_LANES
cost_df.loc[cost_df['Signalized_inter']=='no', 'C_UNSIGNAL'] =  cost_df.apply(lambda x : cost_intersection_nosignalisation(movement=x['movement'], trafic=x['DWV_mean']), axis=1)*cost_df['M_LANES']

# If the movement is in residential/living_street, no cost
cost_df.loc[(cost_df['Signalized_inter'] == 'no') & ( (cost_df['highway_anf_in'].isin(['residential', 'living_street']) ) & (cost_df['highway_in_ant'].isin(['residential', 'living_street']) ) )  , 'C_UNSIGNAL'] = 0 

unsignalized = cost_df.loc[cost_df['Signalized_inter']=='no']
print("The descriptive statistics for the unsignalised intersection is\n", unsignalized['C_UNSIGNAL'].describe())

# print(cost_df.columns.values.tolist())
# ['field_1', 'id_in', 'x_in', 'y_in', 'id_anf', 'x_anf', 'y_anf', 'id_ant', 'x_ant', 'y_ant', 'name_anf_in', 'oneway_anf_in', 'lanes_anf_in', 'highway_anf_in', 'maxspeed_anf_in', 'grade_anf_in', 'name_in_ant', 'oneway_in_ant', 'lanes_in_ant', 'highway_in_ant', 'maxspeed_in_ant', 'grade_in_ant', 'DWV_mean', 'angle', 'movement', 'sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection', 'Comment', 'Signalized_inter', 'osmid', 'highway', 'C_MR', 'M_SAS', 'M_TAD_FR', 'M_TAG', 'M_DWV', 'M_TAD_VIM', 'M_LANES', 'M_TOTAL', 'C_SIGNAL', 'C_UNSIGNAL']
cost_df = cost_df[['id_in', 'x_in', 'y_in', 'id_anf', 'id_ant', 'name_anf_in', 'name_in_ant', 'lanes_anf_in', 'highway_anf_in', 'highway_in_ant', 'DWV_mean', 'angle', 'movement', 'sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection', 'Comment', 'Signalized_inter', 'M_SAS', 'M_TAD_FR', 'M_TAG', 'M_DWV', 'M_TAD_VIM', 'M_LANES', 'M_TOTAL', 'C_SIGNAL', 'C_UNSIGNAL', 'C_MR']]

# Rename some columns 
# Rename some columns of movement_df
cols_rename_uv = {'Signalized_inter': 'type_inter'}
cost_df = cost_df.rename(columns=cols_rename_uv)

# Update value of type inter column so it is easier to understand
cost_df.loc[cost_df['type_inter']=='yes', 'type_inter'] = 'signalized'
cost_df.loc[cost_df['type_inter']=='no', 'type_inter'] = 'unsignalized'
# Define a new column with all cost 
cost_df['C_movement'] = cost_df['C_UNSIGNAL']
cost_df.loc[cost_df['C_movement'].isna(), 'C_movement'] = cost_df['C_MR']
cost_df.loc[cost_df['C_movement'].isna(), 'C_movement'] = cost_df['C_SIGNAL']


print("\n The costs for intersections have been calculated")


