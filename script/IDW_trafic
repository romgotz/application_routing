"""
This code is to predict trafic values for missing data using Inverse Distance Weighting (IDW) based on distance. It will take a fixed number of neighbors to predict trafic value. The input data contains edges with existing values for trafic. The preparation of this data has been done with QGIS using a spatial join. 

Written by Romain Götz in september 2022
"""
import time
start_time = time.time()

# import necessary modules
from ast import Is
from cmath import nan
from errno import EDEADLK
from operator import ne
from turtle import distance
import pandas as pd
from pandas import DataFrame
import numpy as np
import scipy 
import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
from shapely import wkt
import math

# Definition of functions
# Function for distance calculation
def distance_calculation(road_novalue, road_withvalue):
    """
    This function calculates the distance between two objects (here edges) using shapely distance function
    """
    distance = road_novalue.distance(road_withvalue)
    return(distance)

# Prediction  
def idw(known_values, unknown_values):
    """
    Function performing an Inverse Distance Weighting for roads with missing values. The IDW is based on the 20 edges that are the closest to the predicted value
        - known_values : the objects with values that will be used to predict unknown values
        - unknwon values : the objects without values that we want to predict
    """
    lst_xyzi = []
    # Iterates on every unknown value, and predict a value
    for p in range(len(unknown_values)):
        w_list = [] 
        lst_distance = []
        if ( (p == 500) | (p == 1000) | (p == 2000) ):
            print("The prediction has been done for", p, "values")
        for s in range(len(known_values)):
            # takes the p-th/s-th row and the last column that contains geometry
            geometry_unknown = unknown_values.iloc[p, -1]
            geometry_known = known_values.iloc[s, -1]
            d = distance_calculation(geometry_unknown, geometry_known)
            d = round(d,3)
            values = [unknown_values.iloc[p,0],known_values.iloc[s,0],d]
            lst_distance.append(values)
        # Create np array from the list of distance 
        distance_array = np.array(lst_distance, dtype=object)
        # We will sort this array by distance
        # Define on which "column" the sort is based on (here distance with index = 2)
        colIndex = 2
        distance_sorted = distance_array[distance_array[:,colIndex].argsort()]
        # take the 20 first edges 
        distance_sorted = distance_sorted[0:21]
        
        for l in range(len(distance_sorted)):

            if distance_sorted[l,2]>0:
                d_2 = d**2
                if d_2>0: # double check distance is > 0 cause error is raised of float division by zero 
                    w=1.0/(d_2)
                    weight = [distance_sorted[l,1], w]
                    w_list.append(weight)
                else:
                    w=1.0
                    weight = [distance_sorted[l,1], w]
                    w_list.append(weight)
                # np.append(weight_array, values, axis=0)
            else: # weight = 1 if no distance
                weight = [distance_sorted[l,1], 1]
                w_list.append(weight)
                # values=(distance_sorted[l,1], w)
                # np.append(weight_array, values, axis=0)

        weight_array = np.array(w_list, dtype=object)
        suminf=np.sum(weight_array, axis=0)
        suminf = suminf[1]
        # print("The suminf is", suminf, "for the uknown values number", p)
        # As the weights are the same for all 20 columns, duplicate it 
        suminf = np.stack((suminf,) * 20, axis=-1)
        w_list = np.array(weight_array[:,1], dtype=object)
        # Make w_list with 20 columns, so each column of trafic value is multiplied by the weight, otherwise gets an error of shape btw w_list and known_values
        w_list = np.stack((w_list,) * 20, axis=-1)

        # Select the edges used to predict the trafic value
        # Getting the id of the selected edges with values 
        indices = distance_sorted[:,1]
        selected_edges = known_values.loc[indices, ["DWV_ALLE","DWV_PW","DWV_LI","DWV_LW","DWV_LZ","DTV_ALLE","DTV_PW","DTV_LI","DTV_LW","DTV_LZ","MSP_ALLE","MSP_PW","MSP_LI","MSP_LW","MSP_LZ","ASP_ALLE","ASP_PW","ASP_LI", "ASP_LW","ASP_LZ"]]

        sumsup_int = w_list * np.array(selected_edges)
        # We sum every column together (that contains all values for the specific trafic value, e.g DWV_ALLE, then DWV_PI ,etc)
        sumsup = np.sum(sumsup_int, axis=0) # axis = 0 to sum by column
        prediction = sumsup / suminf
        xyzi= [unknown_values.iloc[p,0], prediction]
        lst_xyzi.append(xyzi)
        # print("The prediction has been done for the", p,"-th value. It corresponds to the edges with index", unknown_values.iloc[p,0])
    return(lst_xyzi)

# 1. Download and preparation of the data 

# Network already pre-processsed for cleaning edges and maxpeed limitation. Some trafic values were also added using a spatial join in QGIS.
# fp_network = r'data/input/osm_complete_edges_nodp_with_trafic_epsg32632.shp'
# Need a gdf with roads and trafic values
# Reading file
network = gpd.read_file(fp_network)

# Making sure that the field_1 value corresponds to the index position 
network.drop(columns=['field_1', 'key_edge'], inplace=True)
network.reset_index(inplace=True)
network = network.rename(columns = {'index':'key_edge'})

# Some edges have two highway classifications because of the simplification of the osm network from osmnx, so rename them (renaming was done after exploring data in QGIS)
for index in network.index:
    # Residential 
    if network.loc[index, 'highway'] == ['living_street', 'residential']:
        network.loc[index, 'highway'] = 'living_street'
    # Residential
    elif network.loc[index, 'highway'] == ['residential', 'service']:
        network.loc[index, 'highway'] = 'residential'
    # Residential
    elif network.loc[index, 'highway'] == ['residential', 'unclassified']:
        network.loc[index, 'highway'] = 'residential'
    # Pedestrian 
    elif network.loc[index, 'highway'] == ['pedestrian', 'living_street']:
        network.iloc[index, 'highway'] = 'pedestrian'
    # Pedestrian
    elif network.loc[index, 'highway'] == ['pedestrian', 'residential']:
        network.iloc[index, 'highway'] = 'pedestrian'
    # Pedestrian
    elif network.loc[index, 'highway'] == ['pedestrian', 'service']:
        network.iloc[index, 'highway'] = 'pedestrian'

# Replace all missing values by 0 to simplify  
network['DWV_ALLE'].fillna(0, inplace=True)

# Keep only columns related to trafic 
subset = network.loc[:,
    ["key_edge", "DWV_ALLE","DWV_PW","DWV_LI","DWV_LW","DWV_LZ","DTV_ALLE","DTV_PW","DTV_LI","DTV_LW","DTV_LZ","MSP_ALLE","MSP_PW","MSP_LI","MSP_LW","MSP_LZ","ASP_ALLE","ASP_PW","ASP_LI", "ASP_LW","ASP_LZ", "geometry"]]

# Separate roads with and without values
known_points = subset.loc[network['DWV_ALLE'] > 0]
unknown_points = subset.loc[network['DWV_ALLE'] == 0]

print("\nThere are ", len(unknown_points)," points to predict\n.")

# Prediction of values using Inverse Distance Weighting. The prediction takes some time, ca 1sec/value to predict so around 45-60 minutes.
predicted_values = idw(known_points, unknown_points)
# Transform the result in an array
predicted_values = np.array(predicted_values, dtype=object)

# Create a dataframe for the prediction values
columns_names = ["key_edge","DWV_ALLE","DWV_PW","DWV_LI","DWV_LW","DWV_LZ","DTV_ALLE","DTV_PW","DTV_LI","DTV_LW","DTV_LZ","MSP_ALLE","MSP_PW","MSP_LI","MSP_LW","MSP_LZ","ASP_ALLE","ASP_PW","ASP_LI", "ASP_LW","ASP_LZ"]
df_prediction = pd.DataFrame(index=range(len(unknown_points)),columns=columns_names)
    
# Update dataframe with predicted trafic values
for i in range(len(predicted_values)):
    array = np.array(predicted_values[i,1])
    for s in range(len(array)):
        df_prediction.iat[i,s+1] = array[s]

# Update the field_1 column
df_prediction['key_edge'].fillna(0,inplace=True)
# Values stored as numpy.int64, so has to convert them in python native int to add them to the dataframe (otherwise it puts Nan)
field_values = unknown_points['key_edge'].tolist()
df_prediction['key_edge'] = field_values

# Update the original network dataframe
col = 'key_edge'
# The column to update
cols_to_replace = ["DWV_ALLE","DWV_PW","DWV_LI","DWV_LW","DWV_LZ","DTV_ALLE","DTV_PW","DTV_LI","DTV_LW","DTV_LZ","MSP_ALLE","MSP_PW","MSP_LI","MSP_LW","MSP_LZ","ASP_ALLE","ASP_PW","ASP_LI", "ASP_LW","ASP_LZ"]
# "merging" using the field_1 column (that is the index)
network.loc[network[col].isin(df_prediction[col]), cols_to_replace] = df_prediction.loc[df_prediction[col].isin(network[col]),cols_to_replace].values

print("\n The IDW has been done and the predicted values have been added to the osm edges\n")

# Keep only necessary columns for the network
network=network.loc[:,
['key_edge', 'u', 'v', 'osmid', 'oneway', 'lanes', 'name', 'highway','maxspeed', 'length', 'grade', 'grade_abs', 'service', 'junction', 'access','bridge', 'tunnel', 'speed_zone', 'Am_cycl', 'Am_Direct', 'Sens_Am','Am_cycl_2', 'Am_Dir_2', 'DWV_ALLE', 'DWV_PW', 'DWV_LI', 'DWV_LW', 'DWV_LZ', 'DTV_ALLE', 'DTV_PW', 'DTV_LI', 'DTV_LW', 'DTV_LZ', 'MSP_ALLE', 'MSP_PW','MSP_LI', 'MSP_LW', 'MSP_LZ', 'ASP_ALLE', 'ASP_PW', 'ASP_LI', 'ASP_LW', 'ASP_LZ','geometry']]

# Removing trafic values for pedestrian and cycleway if exist a value by error
for index in network.index: 
    if network.loc[index, 'highway'] == 'pedestrian':
        network.loc[index, 'DWV_ALLE'] = 0
    elif network.loc[index, 'highway'] == 'cycleway':
        network.loc[index, 'DWV_ALLE'] = 0

# Calculating % of heavy vehicles (LI, LW and LZ) only if DWV_ALLE > 0
network["Rate_heavy_vehicles"] = ((network["DWV_LI"] + network["DWV_LW"] + network["DWV_LZ"]) / network["DWV_ALLE"] * 100)
# Keep only two decimals for precision
network["Rate_heavy_vehicles"] = network["Rate_heavy_vehicles"].round(2)


# Set value of zero for rate vehicles and all trafic values if DWV_ALLE is 0
cols_zero = ['Rate_heavy_vehicles','DWV_PW','DWV_LI','DWV_LW','DWV_LZ','DTV_ALLE','DTV_PW','DTV_LI','DTV_LW','DTV_LZ','MSP_ALLE','MSP_PW','MSP_LI','MSP_LW','MSP_LZ','ASP_ALLE','ASP_PW','ASP_LI','ASP_LW','ASP_LZ']
# to test if it works 
network.loc[network['DWV_ALLE'] == 0, cols_zero] = 0

print("\n--- The program took %s seconds ---" % (time.time() - start_time))