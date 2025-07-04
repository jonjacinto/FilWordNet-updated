import math
import igraph as ig
from tqdm import tqdm
from os import path

def get_ego_network_from_word_list(network, word_list, retain_ego=False):
    temp_list = []
    ego_index_list = []
    
    for word in word_list:
        for ego in network.vs.select(word_eq = word):
            ego_index_list.append(ego)
    
    for ego in ego_index_list:
        temp_list.append(network.neighbors(ego))
        
    flattened_list = [item for sublist in temp_list for item in sublist]
            
    if not retain_ego:
        for ego in ego_index_list:
            while ego in temp_list:
                flattened_list.remove(ego)
    else:
        for ego in ego_index_list:
            flattened_list.append(ego)
        
    return network.subgraph(set(flattened_list))