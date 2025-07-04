import os
import json

import networkx as nx
import igraph as ig

import leidenalg as la
import pandas as pd
from cdlib import NodeClustering, viz

temp_path = os.getcwd().split('\\')
project_dir = '\\'.join(temp_path[:temp_path.index('SOURCE') + 1])

 # Set initial partition
def leiden_modularity_algorithm(G, max_comm_size = None, weighted=True):
    if weighted:
        partition = la.ModularityVertexPartition(G, weights="weight")
        refined_partition = la.ModularityVertexPartition(G, weights="weight")
    else:
        partition = la.ModularityVertexPartition(G)
        refined_partition = la.ModularityVertexPartition(G)
    partition_agg = refined_partition.aggregate_partition()
    optimiser = la.Optimiser()
    if max_comm_size:
        optimiser.max_comm_size = max_comm_size
    # Consider all nodes
    # optimiser.consider_comms = la.ALL_COMMS  
    optimiser.set_rng_seed(42)
    while optimiser.move_nodes(partition_agg):
        # Get individual membership for partition
        partition.from_coarse_partition(partition_agg, refined_partition.membership)

        # Refine partition
        if weighted:
            refined_partition = la.ModularityVertexPartition(G, weights="weight")
        else:
            refined_partition = la.ModularityVertexPartition(G)

        optimiser.merge_nodes_constrained(refined_partition, partition)

        # Define aggregate partition on refined partition
        partition_agg = refined_partition.aggregate_partition()
        # But use membership of actual partition
        aggregate_membership = [None] * len(refined_partition)
    
        for i in range(G.vcount()):
            aggregate_membership[refined_partition.membership[i]] = partition.membership[i]
        partition_agg.set_membership(aggregate_membership)

    return NodeClustering(list(partition), graph=None, method_name="leiden_modularity")



 # Set initial partition
def leiden_cpm_algorithm(G, rp, weighted=True):
    if weighted:
        partition = la.CPMVertexPartition(G, resolution_parameter = rp, weights="weight")
        refined_partition = la.CPMVertexPartition(G, resolution_parameter = rp, weights="weight")
    else:
        partition = la.CPMVertexPartition(G, resolution_parameter = rp)
        refined_partition = la.CPMVertexPartition(G, resolution_parameter = rp)
    partition_agg = refined_partition.aggregate_partition()
    optimiser = la.Optimiser()
    # optimiser.consider_comms = la.ALL_COMMS
    optimiser.set_rng_seed(42)
    while optimiser.move_nodes(partition_agg):
        # Get individual membership for partition
        partition.from_coarse_partition(partition_agg, refined_partition.membership)

        # Refine partition
        if weighted:
            refined_partition = la.CPMVertexPartition(G, resolution_parameter = rp, weights="weight")
        else:
            refined_partition = la.CPMVertexPartition(G, resolution_parameter = rp)

        optimiser.merge_nodes_constrained(refined_partition, partition)

        # Define aggregate partition on refined partition
        partition_agg = refined_partition.aggregate_partition()
        # But use membership of actual partition
        aggregate_membership = [None] * len(refined_partition)
    
        for i in range(G.vcount()):
            aggregate_membership[refined_partition.membership[i]] = partition.membership[i]
        partition_agg.set_membership(aggregate_membership)

    return NodeClustering(list(partition), graph=None, method_name="leiden_cpm")



# https://cdlib.readthedocs.io/en/latest/reference/cd_algorithms/algs/cdlib.algorithms.chinesewhispers.html#cdlib.algorithms.chinesewhispers
def cw_algorithm(ego_network, iterations):
    return algorithms.chinesewhispers(ego_network, iterations=iterations, seed=42)



def louvain_algorithm(ego_network, weighted=True):
    # Set initial partition
    if weighted:
        partition = la.ModularityVertexPartition(ego_network, weights="weight")
    else:
        partition = la.ModularityVertexPartition(ego_network)
    #partition = la.find_partition(G, la.ModularityVertexPartition, seed=12)
    # Group the nodes in a partition into one aggregated node
    partition_agg = partition.aggregate_partition()
    
    optimiser = la.Optimiser()
#     optimiser.max_comm_size = 10
    optimiser.set_rng_seed(42)
    
    # Keep on iterating until there are no improvements in the partitions
    while optimiser.move_nodes(partition_agg) > 0:
        # Updates membership based on aggregate partition
        partition.from_coarse_partition(partition_agg)
        # Group the nodes in a partition again
        partition_agg = partition_agg.aggregate_partition()
        
    return NodeClustering(partition, graph=None, method_name="louvain")



def print_communities(graph, partitions):
    if type(partitions) == list:
        for community in partitions:
            print("[", end='')
            for node_index in community:
                print(graph.vs[node_index]['word'], end = ', ')
            print("]\n")
    else:
        for community in partitions.values():
            print("[", end='')
            for node_index in community:
                print(graph.vs[node_index]['word'], end = ', ')
            print("]\n")

# Accepts a NodeClustering object and returns a dictionary of the communities and a list of its nodes
def get_node_comm(ego_communities):
    
    comm_tuple = list(ego_communities.to_node_community_map().items())
    comm_dict = {}
    
    for tup in comm_tuple:
        for community in tup[1]:
            if community not in comm_dict:
                comm_dict[community] = []
            
            comm_dict[community].append(tup[0])

    return comm_dict

def save_communities(ego_network, global_network, word, algorithm_name, communities):
    communities_directory = f"{project_dir}/data/4 - Word Sense Induction/communities/{algorithm_name}"
    if not os.path.exists(communities_directory):
        os.makedirs(communities_directory)
        
    data = {}
    file_name = f'{communities_directory}/{word}.json'
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)
    
    final_communities = {}
    current_index = 0
    
    temp_communities = communities.values() if type(communities) == dict else communities
    
    for community in temp_communities:
        if len(community) > 2:
            final_communities.update({current_index: [int(ego_network.vs[ego_node_index]['index']) for ego_node_index in community]})
            current_index += 1
            
    data.update({
        "ego": [int(vertex['index']) for vertex in global_network.vs.select(word_eq=word)][0],
        "community": final_communities
    })
        
    with open(file_name, 'w') as f:
        json.dump(data, f)