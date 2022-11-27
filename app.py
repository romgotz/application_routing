# Import necessary modules for flask 
from flask import Flask, render_template, url_for, abort, request, jsonify
from markupsafe import escape
# importe python modules specific for own code
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

app = Flask(__name__)
app.debug = True

# Edges file
dir_edges_list = gpd.read_file(r'static/data/edgelist_network.shp')
# Nodes file

# Intersection cost file


# Python functions necessary for routing
# Construct directed graph 
def construct_digraph(dir_edges_list, nodes_df):
    """ Take a pandas edgelist and construct a directed graph using networkx
    The pandas edgelist must have at least a source and target column and an attribute to use as weight: here source is u and target is v
    The nodes should have a unique id, here it is osmid
    """
    G = nx.from_pandas_edgelist(dir_edges_list, source='u', target='v', edge_attr=True, create_using=nx.DiGraph(), edge_key='key')

    # Add attributes for nodes
    nodes_attr = nodes_df.set_index('osmid').to_dict(orient = 'index')
    # then add nodes attributes in the Graph 
    nx.set_node_attributes(G, nodes_attr)

    # Specify a crs projection for osmnx
    G = nx.DiGraph(G, crs='epsg:32632')

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
                edge_cost = nx.get_edge_attributes(G, "PD")[v,w]
                if v in intersection_cost['id_in'].unique():
                    pred = paths[v] # get predecessor from current node
                    # Get the turn cost in the df
                    row_mov = intersection_cost.loc[(intersection_cost['id_anf']==pred) & (intersection_cost['id_in']== v) & (intersection_cost['id_ant'] == w)]
                    print(row_mov)
                    # get the cost value
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
def get_shortest_path(dwg, source, target, verbose=False):
    
    # Validation
    if not source in dwg.nodes() or not target in dwg.nodes():
        print('Both the source and the target must exist in the graph.')
        return {}
    
    start_time = timeit.default_timer()
    
    # Get the distance from 'source' to the other nodes
    sol = get_dijkstra_dist(dwg, source, verbose)
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


def fahrenheit_from(celsius):
    """Convert Celsius to Fahrenheit degrees."""
    try:
        fahrenheit = float(celsius) * 9 / 5 + 32
        fahrenheit = round(fahrenheit, 3)  # Round to three decimal places
        return str(fahrenheit)
    except ValueError:
        return "invalid input"

# Different app routes
@app.route('/')
def index():
    celsius = request.args.get("celsius", "")
    if celsius:
        fahrenheit  = fahrenheit_from(celsius)
    else: fahrenheit = ""
    return render_template(
        'index.html', 
        fahrenheit=fahrenheit,
        utc_dt=datetime.datetime.utcnow()
    )

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/comments/')
def comments():
    comments = ['This is the first comment.',
                'This is the second comment.',
                'This is the third comment.',
                'This is the fourth comment.'
                ]

    return render_template('comments.html', comments=comments)

if __name__ == '__main__':
    app.run()