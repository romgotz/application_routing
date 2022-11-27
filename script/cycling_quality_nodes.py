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
def lanes_multiplier(lanes):
    if lanes>=2:
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

fp_nodes = r'data/input/osm_nodes_simplified_graphmethod.csv'
movement_fp = r'data/output/movement_intersection_infrastructure.csv'

# 1. Downloading data
# Read the edges data ( one is shapefile, the other one is csv) ; have to specify encofing = utf-8 because there are some accents in the data
movement_df = pd.read_csv(movement_fp, encoding='utf-8', sep = ';')
nodes_df_original = pd.read_csv(fp_nodes, encoding='utf-8', sep=';')
# Keep only necesary columns
nodes_df = nodes_df_original[['osmid_original', 'y', 'x','geometry']]

# print(movement_df.columns.values.tolist())
# ['field_1', 'id_in', 'x_in', 'y_in', 'id_anf', 'x_anf', 'y_anf', 'id_ant', 'x_ant', 'y_ant', 'key_anf_in', 'name_anf_in', 'highway_anf_in', 'oneway_anf_in', 'grade_anf_in', 'lanes_anf_in', 'maxspeed_anf_in', 'key_in_ant', 'name_in_ant', 'highway_in_ant', 'oneway_in_ant', 'grade_in_ant', 'lanes_in_ant', 'maxspeed_in_ant', 'DWV_mean', 'DTV_mean', 'MSP_mean', 'ASP_mean', 'angle', 'movement', 'sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection', 'Comment', 'Signalized_inter']


# print(movement_df['Comment'].value_counts(dropna=False))
# Some movements are actually not possible at signalized intersection, remove them
to_remove_list = ['move impossible','movement impossible', 'mov impossible', 'movement possible ?','no intersection','move impossible travaux', 'not intersection', 'no intersection move', 'move_impossible', 'move impossible ?','Move impossible', 'mouv impossible', 'not necessary']
# remove impossible moves
movement_df = movement_df.loc[~(movement_df['Comment'].isin(to_remove_list))] # remove impossible moves
# Change some column types
trafic_columns = ['DWV_mean', 'DTV_mean', 'MSP_mean', 'ASP_mean']
# Movement_df 
movement_df['x_in'] = pd.to_numeric(movement_df['x_in'].str.replace(',', '.'))
movement_df['y_in'] = pd.to_numeric(movement_df['y_in'].str.replace(',', '.'))
movement_df['DWV_mean'] = pd.to_numeric(movement_df['DWV_mean'].str.replace(',', '.'))
movement_df['DTV_mean'] = pd.to_numeric(movement_df['DTV_mean'].str.replace(',', '.'))
movement_df['MSP_mean'] = pd.to_numeric(movement_df['MSP_mean'].str.replace(',', '.'))
movement_df['ASP_mean'] = pd.to_numeric(movement_df['ASP_mean'].str.replace(',', '.'))

# Node_df
# For the nodes df, need to round x,y values 
nodes_df['x'] = nodes_df['x'].round(4)
nodes_df['y'] = nodes_df['y'].round(3)

# Select movement without intersection node osmid
movement_no_id = movement_df.loc[movement_df['id_in'].isna()]
# Merge btw two dfs to add osmid 
movement_no_id = pd.merge(movement_no_id, nodes_df, how='left', left_on=['x_in', 'y_in'], right_on=['x', 'y'])
# Keep necessary columns
movement_no_id = movement_no_id[['osmid_original', 'x', 'y']]

# Merging with original df
movement_df = pd.merge(movement_df, movement_no_id, how='left', left_on=['x_in', 'y_in'], right_on=['x', 'y'])
movement_df.loc[movement_df['id_in'].isna(), 'id_in'] = movement_df['osmid_original']
# Saving completed df
# movement_df.to_csv('data/output/movement_df_complete.csv', sep=';')
# print("The movement df without missing values for intersection node has been saved")

# Calculating cost for intersection movement

# print(movement_df.columns.values.tolist())
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
nodes_df = nodes_df_original[['osmid_original', 'highway']]
cost_df = pd.merge(cost_df, nodes_df, how='left', left_on=['id_in'], right_on=['osmid_original'])

# print(cost_df.columns.values.tolist())
# ['field_1', 'id_in', 'x_in', 'y_in', 'id_anf', 'x_anf', 'y_anf', 'id_ant', 'x_ant', 'y_ant', 'key_anf_in', 'name_anf_in', 'highway_anf_in', 'oneway_anf_in', 'grade_anf_in', 'lanes_anf_in', 'maxspeed_anf_in', 'key_in_ant', 'name_in_ant', 'highway_in_ant', 'oneway_in_ant', 'grade_in_ant', 'lanes_in_ant', 'maxspeed_in_ant', 'DWV_mean', 'DTV_mean', 'MSP_mean', 'ASP_mean', 'angle', 'movement', 'sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection', 'Comment', 'Signalized_inter', 'osmid_original_x', 'x', 'y', 'osmid_original_y', 'highway']

cols_to_keep = ['id_anf','id_in', 'id_ant', 'name_anf_in', 'lanes_anf_in', 'maxspeed_anf_in', 'name_in_ant', 'DWV_mean', 'DTV_mean', 'MSP_mean', 'ASP_mean', 'angle', 'movement', 'sas', 'tag', 'tad_fr', 'tad_vim', 'bc_rouge', 'preselection', 'Signalized_inter', 'highway']
cost_df  = cost_df[cols_to_keep]

# For mini roundabout
cost_df.loc[cost_df['highway'] == 'mini_roundabout', 'cost_mini_roundabout'] = cost_df.apply(lambda x: small_roundabout_cost(x['movement'], x['DWV_mean'],x['maxspeed_anf_in']), axis = 1)

# For signalized and unsignalized intersection
# Determine different cost multipliers for specific configurations for every movement
# cost_multiplier= cost_sas*cost_presel_velo* cost_tag*cost_tad*cost_lanes*cost_tad_vim*cost_tjm 
cost_df['sas_multi'] = cost_df['sas'].apply(sas_mutliplier)
cost_df['tad_fr_multi'] = cost_df['tad_fr'].apply(tad_multiplier)
cost_df['tag_multi'] = cost_df['tag'].apply(tag_multiplier)
cost_df['lanes_multi']  = cost_df['lanes_anf_in'].apply(lanes_multiplier)
cost_df['trafic_multi'] = cost_df['DWV_mean'].apply(trafic_multiplier)
cost_df['tad_vim_multi'] = cost_df.apply(lambda x : presel_vim_multiplier(presel_vim=x['tad_vim'], bc_rouge=x['bc_rouge']), axis=1)
cols_multi = ['sas_multi', 'tad_fr_multi' ,'tag_multi', 'lanes_multi', 'trafic_multi', 'tad_vim_multi']
# Relace nan with 1 for those columns otherwise multiplication not possible
cost_df[cols_multi].fillna(1, inplace=True)
# Total multiplier 
cost_df['total_multi'] = cost_df['sas_multi']*cost_df['tad_fr_multi']*cost_df['tag_multi']*cost_df['lanes_multi']*cost_df['trafic_multi']*cost_df['tad_vim_multi']

for i in cols_multi:
    repartition = cost_df[i].value_counts(dropna=False)
    print("For columns", i, "the number of movement with this configuration is\n", repartition)

# Calculate cost for signalized intersection
global basic_cost
basic_cost = 67
signalized_cost = 34
cost_df.loc[cost_df['Signalized_inter'] == 'yes', 'Cost_signalized'] = cost_df['total_multi']*(basic_cost+signalized_cost)

# For unsignalised intersection
# Select them by removing signalized intersection and roundabouts
cost_df.loc[ ~(cost_df['Signalized_inter']=='yes') | (cost_df['highway'] == 'mini_roundabout'), 'Cost_unsignalized'] =  cost_df.apply(lambda x : cost_intersection_nosignalisation(movement=x['movement'], trafic=x['DWV_mean']), axis=1)*cost_df['total_multi'] 

# select movement with specific configurations 
# Replace 1 value by nan
cost_df.loc[cost_df['total_multi']==1, 'total_multi'] = np.nan
print("There are",len(cost_df.loc[~(cost_df['total_multi'].isna())]), "movements in intersection that are with dangerous configurations")

# See descriptive statistics for the calculated costs
print("The descriptive statistics for the mini roudabout  is\n", cost_df['cost_mini_roundabout'].describe())
print("The descriptive statistics for the unsignalised intersection is\n", cost_df['Cost_unsignalized'].describe())
print("The descriptive statistics for the signalised intersection is\n", cost_df['Cost_signalized'].describe())
print("The descriptive statistics for the cost multiplier is\n", cost_df['total_multi'].describe())


cost_df.to_csv('data/output/cost_intersection.csv', sep=';')  

print("\n The costs for intersections have been calculated")

print("\n--- The program took %s seconds ---" % (time.time() - start_time))

