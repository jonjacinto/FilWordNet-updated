from copy import deepcopy

import networkx as nx
import igraph as ig



# Accepts an igraph object 'g', outputs a networkx object
def convert_to_networkx(g):
    return g.to_networkx()

def reverse_edge(graph, node1, node2, key):
    graph.add_edge(node2, node1, **(deepcopy(graph.get_edge_data(node1, node2, key))))
    graph.remove_edges_from([(node1, node2, key)])

def convert_to_undirected_networkx(directed):
    undirected = directed.copy()
    for edge in directed.edges(data=True, keys=True):
        if edge[0] > edge[1]:
            reverse_edge(undirected, edge[0], edge[1], edge[2])
    return undirected.to_undirected()



# Accepts a networkx object 'g', outputs an igraph object
def convert_to_igraph(g):
    return ig.Graph.from_networkx(g)

def convert_to_undirected_igraph(directed):
    return directed.to_undirected(mode='mutual', combine_edges='sum')