from flask import Flask, render_template, url_for, abort
from random import choice
from markupsafe import escape
import datetime
import math

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    return render_template(
        'index.html', 
        random=choice(range(1,46)), 
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

graph = {
    'a': {'b': 2, 'c': 6},
    'b': {'a': 4, 'd': 5},
    'c': {
        'a': 8,
        'd': 8,
        },
    'd': {
        'c': 5,
        'e': 15,
        'f': 10,
        },
    'e': {'g': 2, 'd': 8, 'f': 4},
    'f': {'e': 4, 'g': 2},
    'g':{'f':1}
    }

source = 'g'
destination = 'a'

unvisited = graph
shortest_distances = {}
route = []
path_nodes = {}

# set distance at infinity for all, except source 
for nodes in unvisited:
    shortest_distances[nodes] = math.inf
shortest_distances[source] = 0

# run as long as univisted has nodes
while unvisited:
    min_node = None
    for current_node in unvisited:
        if min_node is None:
            min_node = current_node
        elif shortest_distances[min_node] > shortest_distances[current_node]:
            min_node = current_node
    for (node, value) in unvisited[min_node].items():
        if value + shortest_distances[min_node] < shortest_distances[node]:
            shortest_distances[node] = value + shortest_distances[min_node]
            path_nodes[node] = min_node
    unvisited.pop(min_node)
node = destination

while node != source:
    try:
        route.insert(0, node)
        node = path_nodes[node]
    except Exception:
        print('Path not reachable')
        break
route.insert(0, source)

if shortest_distances[destination] != math.inf:
    print('Shortest distance is ' + str(shortest_distances[destination]))
    print('And the path is ' + str(route))
# The above function returns the HTML code to be displayed on the page

if __name__ == '__main__':
    app.run()