"""
This algorithm takes a bikeway network and evaluates according to some criteria. It requires two files representing the network : the edges and the nodes. The edges must contain columns about :
    - start node
    - end node 
    - length of edge
    - cycling infrastructure
    - way of the cycling infra
    - the trafic 
    - the maxspeed
    - the slope
    - the % of aquatic and green areas
    - the number of lanes
    
    
Written by Romain Götz in September 2022
"""

from math import exp
import pandas as pd
import numpy as np
import scipy 
import geopandas as gpd
import osmnx as ox
from shapely import wkt
from shapely.geometry import Point, LineString, Polygon
import math
import fiona
import seaborn as sns 
import matplotlib.pyplot as plt


import time

start_time = time.time()

# Defining the functions for links

# Gradient cost function
def gradient_cost(gradient):
    return 417*gradient*(gradient + 0.04)

# Green and aquatic areas benefit function
def green_water_benefit(surface_aquaticgreen):
    # if there is a value for the surface
    if surface_aquaticgreen >= 0:
        return 0.1 - 0.1 / (0.01 + exp(0.05*surface_aquaticgreen))
    else: # otherwie return 0
        return 0

# Cost function for dangerous configurations
# Cost for rate of heavy vehicles
def HV_cost(heavy_vehicles):

    if heavy_vehicles >= 8:
        heavy_vehicles_cost = 0.2
    else:
        heavy_vehicles_cost = 0

    return heavy_vehicles_cost

# Trafic, speed and cycling infrastructure costs
# Bike and trafic without any infrastructure 
def bike_30km(traffic):
    return 0.011*exp(0.00018*traffic) + 0.889

def bike_40km(traffic):
    return 0.011*exp(0.00025*traffic) + 1.180

def bike_50km(traffic):
    return 0.011*exp(0.00025*traffic) + 1.280

def bike_60km(traffic):
    return 0.011*exp(0.00025*traffic) + 1.380

def bike_80km(traffic):
    return 0.011*exp(0.00025*traffic) + 1.580

# Bike and trafic with cycling lane
def bike_30km_withlane(traffic):
    return 0.011*exp(0.00015*traffic) + 0.789

def bike_40km_withlane(traffic):
    return 0.011*exp(0.00020*traffic) + 0.889

def bike_50km_withlane(traffic):
    return 0.011*exp(0.00020*traffic) + 0.989

def bike_60km_withlane(traffic):
    return 0.011*exp(0.00020*traffic) + 1.180

def bike_80km_withlane(traffic):
    return 0.011*exp(0.00020*traffic) + 1.380

# Cost function for the condition of traffic, speed and infrastructure
def IC_cost(traffic,maxspeed,Am_cycl, speed_zone):

    global infra_cost
    # Cycle track 
    if Am_cycl == 'Piste cyclable':
        infra_cost = 0.75
    # Bus lane
    elif Am_cycl == 'Voie de bus':
        infra_cost = 0.85
    # Trottoir autorise aux velos
    elif Am_cycl == 'Trottoir':
        infra_cost = 0.9
    elif Am_cycl == 'ZP autorisee velos':
        infra_cost = 0.95
    # Zone de rencontre
    elif (speed_zone == 'Zone de rencontre') | (Am_cycl == 'Zone de rencontre'):
        infra_cost = 0.9
    # Bike lane 
    elif Am_cycl == 'Bande cyclable':
        if maxspeed ==  30:
            infra_cost = bike_30km_withlane(traffic)
        elif maxspeed == 40:
            infra_cost = bike_40km_withlane(traffic)
        elif maxspeed == 50:
            infra_cost = bike_50km_withlane(traffic)
        elif maxspeed == 60:
            infra_cost = bike_60km_withlane(traffic)
        elif maxspeed == 80:
            infra_cost = bike_80km_withlane(traffic)
    # no infrastructure  
    elif Am_cycl == 'Aucun':
        if maxspeed ==  30:  
            infra_cost = bike_30km(traffic)
        elif maxspeed == 40:
            infra_cost = bike_40km(traffic)
        elif maxspeed == 50:
            infra_cost = bike_50km(traffic)
        elif maxspeed == 60:
            infra_cost = bike_60km(traffic)
        elif maxspeed == 80:
            infra_cost = bike_80km(traffic)

    return infra_cost

# Defining function for the roundabout edges
def roundabout_cost(trafic, maxspeed, lanes):
    global round_cost
    if lanes == 1:
        if maxspeed == 30:
            if trafic < 5000:
                round_cost = 1
            elif (trafic > 5000) and (trafic < 15000):
                round_cost = 1.05
            elif trafic >= 15000:
                round_cost = 1.2
        if maxspeed == 50:
            if trafic < 5000:
                round_cost = 1
            elif (trafic > 5000) and (trafic < 15000):
                round_cost = 1.1
            elif trafic >= 15000:
                round_cost = 1.3
    elif lanes > 1:
        if maxspeed == 30:
            if trafic < 5000:
                round_cost = 1.05
            elif (trafic > 5000) and (trafic < 15000):
                round_cost = 1.1
            elif trafic >= 15000:
                round_cost = 1.3
        if maxspeed == 50:
            if trafic < 5000:
                round_cost = 1.1
            elif (trafic > 5000) and (trafic < 15000):
                round_cost = 1.3
            elif trafic >= 15000:
                round_cost = 1.5

    return round_cost

def avg_speed_cycling(gradient):
    """This function returns the assumed average speed for cycling according to the slope"""

    if (gradient > -0.5) & (gradient < 1):
        avg_speed = 15
    elif (gradient >= 1) & (gradient < 4):
        avg_speed = 10
    elif (gradient >= 4) :
        avg_speed = 7
    elif (gradient <= -0.5) & (gradient > -2):
        avg_speed = 18
    elif (gradient <= -2) & (gradient > -6):
        avg_speed = 25
    elif (gradient <= -6):
        avg_speed = 30

    return avg_speed


# read shp file
network = gpd.read_file(fp_edges, encoding='utf-8')
nodes = gpd.read_file(fp_nodes, encoding='utf-8')


# print(network.columns.values.tolist())
# ['u', 'v', 'osmid', 'oneway', 'lanes', 'name', 'highway', 'maxspeed', 'length', 'grade', 'service', 'junction', 'bridge', 'tunnel', 'speed_zone', 'Am_cycl', 'Am_Direct', 'Am_cycl_2', 'Am_Dir_2', 'DWV_ALLE', 'DWV_PW', 'DWV_LI', 'DWV_LW', 'DWV_LZ', 'MSP_ALLE', 'MSP_PW', 'MSP_LI', 'MSP_LW', 'MSP_LZ', 'ASP_ALLE', 'ASP_PW', 'ASP_LI', 'ASP_LW', 'ASP_LZ', 'pour100_GW', 'key_edge', 'geometry']

# drop unecessary columns
network.drop(columns=['key_edge'], inplace=True)

# Transform utf-8 in ascii : remove accents to avoid errors
cols = network.select_dtypes(include=[object]).columns
network[cols] = network[cols].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))

# Some column types are not good, so change them. And also complete values for some columns
# OSMID column : object because some osmid are together from merging of edges

# u, v columns : saved as float, need to change into integers
# First round the value ups and downs if saved with decimals
network['u'] = network['u'].round()
network['v'] = network['v'].round()
# Then change the data types of the columns into int
cols = ['u', 'v']
network[cols] = network[cols].applymap(np.int64)
network[cols] = network[cols].applymap(np.int64)

# Grade column : make sure the slope values are numeric and recalculate them to be sure of their sign 
network['grade'] = pd.to_numeric(network['grade'])

# Prepare nodes data
nodes.drop(columns=['field_1', 'Unnamed_ 0'])
# Round omsid value ups and downs if saved with decimals
nodes['osmid'] = nodes['osmid'].round()
# Then change the data types of the columns into int
cols = ['osmid']
nodes[cols] = nodes[cols].applymap(np.int64)

print("Calculating the slope for every edge to avoid errors of way")
# Apparently some slope are inversed, so calculate them again. 
for i in network.index: # Iterates over every edge of the network
    elevation_col = -3
    # Select u from edge
    edge = network.loc[network.index == i]
    u = edge['u'].item()
    v = edge['v'].item()
    length = edge['length'].item()
    # Select corresponding nodes
    node_u = nodes[nodes['osmid'] == u]
    node_v = nodes[nodes['osmid']== v]
    # select the elevation
    elevation_u = node_u['elevation'].item()
    elevation_v = node_v['elevation'].item()
    # Calculate slope from u to v
    slope_uv = (elevation_v - elevation_u) / length
    # The other way
    slope_vu = (elevation_u - elevation_v) / length
    # update the values in the edges dataframe
    # u to v way
    network.loc[(network['u'] == u) & (network['v']==v), 'GR_uv'] = slope_uv
    network.loc[(network['u'] == u) & (network['v']==v), 'GR_vu'] = slope_vu

network['GR_uv'] = network['GR_uv'].round(4)
network['GR_vu'] = network['GR_vu'].round(4)
network.drop(columns=['grade'], inplace=True)

# Maxspeed column : some maxspeed as lists 
# Take the highest maxspeed because it is the one that has the most negative influence 
network.loc[network['maxspeed'].isin(["['60', '80']", "['60', '50']"]), 'maxspeed'] = 60 # 60 because ic_cost for 70 km/h does not exist
network.loc[network['maxspeed'] == "['60', '80']", 'maxspeed'] = 80
network.loc[network['maxspeed'] == '70', 'maxspeed'] = 80

# Make sure values are numeric
network['maxspeed'] = pd.to_numeric(network['maxspeed'], errors='coerce')

# Lanes column : fill missing value and deal with lists
network['lanes'].fillna(1, inplace=True) #assume missing values are 1 
# For lists, keep highest lanes value, cause it has the most negative effect
network.loc[network['lanes'].isin(["['2', '3']", "['2', '1', '3']"]), 'lanes'] = 3
network.loc[network['lanes'].isin(["['4', '3']", "['4', '2']"]), 'lanes'] = 4
network.loc[network['lanes'].isin(["['4', '5', '6']","['5', '2']","['5', '3']"]), 'lanes'] = 5
network.loc[network['lanes'].isin(["['2', '1']"]), 'lanes'] = 2
# Change column to numeric
network['lanes'] = pd.to_numeric(network['lanes'])
# change it into integers 
network['lanes']  = network['lanes'].astype(int)


# Am_cycl and Am_direct column
# Put Zone de rencontre in Am_cycl column (if no Am_cycl)
network.loc[ (network['Am_cycl'].isna() ) & (network['speed_zone'] == 'Zone de rencontre'), 'Am_cycl' ] = 'Zone de rencontre'
# Harmonise how Am_cycl values are stored  
network.loc[network['Am_cycl'] == 'Voie bus', 'Am_cycl'] = 'Voie de bus'
network.loc[network['Am_cycl'] == 'Zp autorisee velos', 'Am_cycl'] = 'ZP autorisee velos'
network.loc[network['Am_cycl'] == 'None', 'Am_cycl'] = np.nan
network.loc[network['Am_cycl'].isna(), 'Am_cycl'] = np.nan
network.loc[network['Am_cycl']=='v to u', 'Am_cycl'] = np.nan
# Harmonise  Am_direct
# Change some values of Am_Direct 
network.loc[ (network['Am_Direct'] == 'Bi') | (network['Am_Direct'] == 'Bidirectionnel'), 'Am_Direct' ] = 'Both'

# Trafic columns
# DWV_ALLE column : there still are some missing values, see the repartition
# For residential street and living_street, uniformise trafic values by taking median of predicted trafic values
# Calculate median for the columns, and store it in df
highway_values = ['residential', 'living_street']
selected_highway = network.loc[network['highway'].isin(highway_values)]
roads_names = selected_highway['name'].unique().tolist()

for name in roads_names:
    # Select edges with this name
    df = network.loc[network['name']==name]
    df = df[['DWV_ALLE', 'DWV_PW', 'DWV_LI', 'DWV_LW', 'DWV_LZ','MSP_ALLE', 'MSP_PW', 'MSP_LI', 'MSP_LW', 'MSP_LZ', 'ASP_ALLE', 'ASP_PW', 'ASP_LI', 'ASP_LW', 'ASP_LZ']]
    # Calculate median for existing values
    cols_median = df.median(skipna=True).round(2).tolist()
    # Replace values
    cols_to_replace = ['DWV_ALLE', 'DWV_PW', 'DWV_LI', 'DWV_LW', 'DWV_LZ','MSP_ALLE', 'MSP_PW', 'MSP_LI', 'MSP_LW', 'MSP_LZ', 'ASP_ALLE', 'ASP_PW', 'ASP_LI', 'ASP_LW', 'ASP_LZ']
    for i in range(0,len(cols_median)):
        network.loc[network['name'] == name, cols_to_replace[i]] = cols_median[i]

print("Update of median values for trafic is finished")

# Set trafic values to zero 
cols_zero = ['DWV_ALLE', 'DWV_PW','DWV_LI','DWV_LW','DWV_LZ','MSP_ALLE','MSP_PW','MSP_LI','MSP_LW','MSP_LZ','ASP_ALLE','ASP_PW','ASP_LI','ASP_LW','ASP_LZ']
notrafic_values = ['ZP autorisee velos', 'Piste cyclable', 'Zone de rencontre', 'Voie de bus', 'Trottoir'] 
mask = network['Am_cycl'].isin(notrafic_values)
network.loc[mask, cols_zero] = 0

# Missing rate of heavy vehicles
# Calculating % of heavy vehicles (LI, LW and LZ) for DWV, MHP and ASP 
network["HV_DWV"] = ((network["DWV_LI"] + network["DWV_LW"] + network["DWV_LZ"]) / network["DWV_ALLE"] * 100)
network["HV_MSP"] = ((network["MSP_LI"] + network["MSP_LW"] + network["MSP_LZ"]) / network["MSP_ALLE"] * 100)
network["HV_ASP"] = ((network["ASP_LI"] + network["ASP_LW"] + network["ASP_LZ"]) / network["ASP_ALLE"] * 100)
# Keep only two decimals for precision
network["HV_DWV"] = network["HV_DWV"].round(2)
network["HV_MSP"] = network["HV_MSP"].round(2)
network["HV_ASP"] = network["HV_ASP"].round(2)

# 1. Links cost

# define number of decimals to keep
precision = 3

# 1.1 Gradient cost

# Set a max value for the slope of 10%
network.loc[network['GR_uv'] > 0.1, 'GR_uv'] = 0.1
network.loc[network['GR_vu'] < -0.1, 'GR_vu'] = -0.1

# Apply the gradient cost function to the two columns containing slope and store result in two new columns
network[['C_GR_uv', 'C_GR_vu']] = network[['GR_uv', 'GR_vu']].apply(gradient_cost).round(precision)

print("\n The cost gradient evaluation has been done")

# 1.2 Benefit from cover of green and aquatic areas
# Make sure the values are numeric 
network['pour100_GW'] = pd.to_numeric(network['pour100_GW'])
# Not different for u to v or v to u, so easier 
network['B_GW'] = network['pour100_GW'].apply(green_water_benefit).round(precision)

print("\n The benefit of green water areas has been calculated")

# 1.3  The cost for the heavy vehicle rate for 3 different trafic time
network['C_HV_DWV'] = network['HV_DWV'].apply(HV_cost).round(precision)
network['C_HV_ASP'] = network['HV_ASP'].apply(HV_cost).round(precision)
network['C_HV_MSP'] = network['HV_MSP'].apply(HV_cost).round(precision)

print("\n The cost for heavy vehicle has been calculated")

# 1.4 Cost for the cycling infrastructure

# have to define a value for infra_cost and rounabout_cost otherwise raise an error in the functions
infra_cost = 1
round_cost = 1

# Change missing values in Am_cycl column with Aucun 
network['Am_cycl'].fillna('Aucun', inplace=True)

# Change some values of maxspeed that are list to single values. Take the highest maxspeed because it is the one that has the most negative influence 
network.loc[network['maxspeed'] == "['60', '80']", 'maxspeed'] = '80'
network.loc[network['maxspeed'] == "['50', '70']", 'maxspeed'] = '60'
network.loc[network['maxspeed'] == "['60', '50']", 'maxspeed'] = '60'

# Change columns for numeric values
network['maxspeed'] = pd.to_numeric(network['maxspeed'])
network['DWV_ALLE'] = pd.to_numeric(network['DWV_ALLE'])
network['DWV_ALLE'] = network['DWV_ALLE'].round(precision)

# 1.4.1 For trafic DWV (monday to friday)
# First apply IC_cost function for every row without taking into account possible infrastructure (Am_cycl defined as 'Aucun')
# U TO V way
network['C_IC_uv_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], 'Aucun', x["speed_zone"]), axis = 1).round(precision)
# V TO U way
network['C_IC_vu_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], 'Aucun', x["speed_zone"]), axis = 1).round(precision)

# Then we apply again this IC_cost function but we take into account cycling infrastructure. It will update values for edges with infrastructure
# cycling infrastructure in U TO V way and in both sides
network.loc[(network['Am_Direct'] == 'u to v') | (network['Am_Direct'] == 'Both'), 'C_IC_uv_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], x["Am_cycl"], x["speed_zone"]), axis = 1).round(precision)

# cycling infrastructure in V TO U way and in both sides
network.loc[(network['Am_Direct'] == 'v to u') | (network['Am_Direct'] == 'Both'), 'C_IC_vu_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], x["Am_cycl"], x["speed_zone"]), axis = 1).round(precision)

# Now do the same with the 2nd column of cycling infrastructure 
# cycling infrastructure in U TO V way
network.loc[(network['Am_Dir_2'] == 'u to v') , 'C_IC_uv_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], x["Am_cycl_2"], x["speed_zone"]), axis = 1).round(precision)

# cycling infrastructure in V TO U way and in both sides
network.loc[(network['Am_Dir_2'] == 'v to u') , 'C_IC_vu_DWV'] = network.apply(lambda x: IC_cost(x["DWV_ALLE"], x["maxspeed"], x["Am_cycl_2"], x["speed_zone"]), axis = 1).round(precision)

# Checking if there are some missing cost for the infrastructure (as it is the "basis" for the PD)
missing_IC_cost = network.loc[(network['C_IC_uv_DWV'].isna()) | (network['C_IC_vu_DWV'].isna()) ]

# 1.5 Calculate the cost for the edges in roundabout. Can only go from u to v in roundabout
# 1.5.1 DWV trafic 
network.loc[network['junction']=='roundabout', 'C_RA_DWV'] = network.apply(lambda x: roundabout_cost(trafic=x['DWV_ALLE'],maxspeed = x['maxspeed'], lanes=x['lanes']), axis = 1)

# 2. Determine total cost and the perceived distance
# 2.1 DWV trafic
# u to v way
# Total cost
network['TC_uv_DWV'] = network['C_HV_DWV'] + network ['B_GW'] + network['C_GR_uv'] + network['C_IC_uv_DWV']
# update value for roundabout edges
network.loc[network['junction']=='roundabout', 'TC_uv_DWV'] = network['C_RA_DWV'] # edges are oneway in roundabout, so do not need to do 
# Perceived distance
network['PD_uv_DWV'] = network['length']*network['TC_uv_DWV']
network['PD_uv_DWV'] = network['PD_uv_DWV'].round(precision)

# v to u way
network.loc[network['oneway']=='False', 'TC_vu_DWV'] = network['C_HV_DWV'] + network ['B_GW'] + network['C_GR_vu'] + network['C_IC_vu_DWV'] 
# Perceived distance
network.loc[network['oneway']=='False', 'PD_vu_DWV'] = network['length']*network['TC_vu_DWV']
network['PD_vu_DWV'] = network['PD_vu_DWV'].round(precision)

# Define avg speed of biking according to slope 
network['avg_speed_uv'] = network['GR_uv'].apply(avg_speed_cycling)
network['avg_speed_vu'] = network['GR_vu'].apply(avg_speed_cycling)

# Then we can use the speed to determine time to go through a link (need to use true length and not perceived distance) 
network['tt_s_uv'] = network['length'] / (network['avg_speed_uv']/3.6)
network['tt_s_vu'] = network['length'] / (network['avg_speed_vu']/3.6)

print("The total cost and pereceived distance have been evaluated for the 3 trafic situations")

print("\n The cycling quality of the bike network has been evaluated and saved in csv. It took %s seconds" % (time.time() - start_time))

# 3. Create pandas edgelist

edges = network

print(edges.dtypes)

# Checking if no more missing nodes values 
u_values = edges['u'].unique().tolist()
v_values = edges['v'].unique().tolist()
# Put two lists together
u_values.extend(v_values)
# Remove duplicate values
uv_values = [*set(u_values)] # nodes appearing in the edges 

# Keep the nodes with attributes that appear in the list of nodes values
nodes = nodes.loc[nodes['osmid'].isin(uv_values)]
nodes_values = nodes['osmid'].unique().tolist()
missing_nodes = list(set(uv_values).symmetric_difference(set(nodes_values)))

print(missing_nodes)

assert len(nodes) == len(uv_values)

# Need to build the directed graph from scratch 
# Separate oneways and twoways
oneway = edges.loc[edges['oneway'].isin(['True', '1'])].copy().reset_index()
twoway = edges.loc[edges['oneway'] == 'False'].copy().reset_index()

# make sure there are no edges left
assert (len(oneway) + len(twoway)) == len(edges)

# make a copy from twoway edges
opposite_direction = twoway.copy()
# make sure it s the same frame
pd.testing.assert_frame_equal(twoway, opposite_direction)

# the first two way df is from u to v and the 2nd two way df is for v to u
# For the U TO V, can drop columns related to v to u information
cols_drop_vu = ['GR_vu', 'C_GR_vu', 'C_IC_vu_DWV', 'TC_vu_DWV','PD_vu_DWV', 'tt_s_vu', 'avg_speed_vu']
twoway.drop(columns=cols_drop_vu, inplace=True)
# Rename columns too (get rid of u to v specification)
cols_rename_uv = {'GR_uv': 'grade', 'C_GR_uv':'C_GR', 'C_IC_uv_DWV': 'C_IC_DWV', 'TC_uv_DWV':'TC_DWV', 'PD_uv_DWV':'PD_DWV','tt_s_uv':'tt_s', 'avg_speed_uv':'avg_speed'}
twoway = twoway.rename(columns=cols_rename_uv)

# For the v to u way
# drop columns for u to v originally 
cols_drop_uv = ['GR_uv', 'C_GR_uv', 'C_IC_uv_DWV', 'TC_uv_DWV','PD_uv_DWV', 'tt_s_uv', 'avg_speed_uv']
opposite_direction.drop(columns=cols_drop_uv, inplace=True)
# Rename columns : exchange u and v column and remove v to u specification !! need to take v_to_u columns (that becomes u to v now)
cols_rename_vu = {'u':'v','v':'u','GR_vu': 'grade', 'C_GR_vu':'C_GR', 'C_IC_vu_DWV': 'C_IC_DWV', 'TC_vu_DWV':'TC_DWV', 'PD_vu_DWV':'PD_DWV', 'tt_s_vu':'tt_s', 'avg_speed_vu':'avg_speed'}
opposite_direction = opposite_direction.rename(columns=cols_rename_vu)

# ONEWAY : retake what was done for u v for twoways 
# Drop unecessary columns (v to u as it is not possible in oneways)
oneway.drop(columns=cols_drop_vu, inplace=True)
# Rename columns too (get rid of u to v specification)
oneway = oneway.rename(columns=cols_rename_uv)

# merge together 
directed_edges = pd.concat([oneway, twoway, opposite_direction], ignore_index=True)

# reset index
directed_edges.reset_index(inplace=True)
directed_edges = directed_edges.rename(columns = {'index':'key_edge'})
# remove unecessary columns
directed_edges.drop(columns=['key_edge'], inplace=True)
directed_edges = directed_edges.rename(columns = {'level_0':'key'})

print(directed_edges.columns.values.tolist())

print("The complete directedgraph has %s edges and %s nodes" % (len(directed_edges), len(nodes)))
