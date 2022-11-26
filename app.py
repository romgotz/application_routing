# Import necessary modules for flask 
from flask import Flask, render_template, url_for, abort, request
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

# Python functions necessary for routing
def construct_digraph(dir_edges_list, nodes_df):
    """ Take a pandas edgelist and construct a directed graph using networkx
    The pandas edgelist must have at least a source and target column : source is u and target is v, and at least one attribute to do the routing
    The nodes should have a unique id, here it is osmid
    """
    G = nx.from_pandas_edgelist(dir_edges_list, source='u', target='v', edge_attr=True, create_using=nx.DiGraph(), edge_key='key')

    # Add attributes for nodes
    nodes_attr = nodes_df.set_index('osmid').to_dict(orient = 'index')
    # then add nodes attributes in the Graph 
    nx.set_node_attributes(G, nodes_attr)

    # Specify a crs projection for osmnx
    G = nx.DiGraph(G, crs='epsg:32632')

    # Project the graph ?


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