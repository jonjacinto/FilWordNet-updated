import os
import json
import pickle
import unicodedata
import regex as re
from itertools import combinations

import pandas as pd
from tqdm import tqdm

tqdm.pandas()



is_local = False

drive_dir = "/content/drive/Shareddrives/"
local_dir = "G:/Shared drives/"

stopwords_tl = None
stopwords_en = None

export_folder_name = "edgelists_nopos"

#retain_pos_list = ["NN", "VB", "JJ", "RB", "FW", "TS"]

def download_stopwords():
    global stopwords_tl
    global stopwords_en
    
    stopwords_dir = f"{local_dir if is_local else drive_dir}DOST FilWordNet x WordSense/Thesis/NetSci Team/stopwords"
    
    if stopwords_tl != None or stopwords_en != None:
        print("Redownloading stopwords.")
        
    with open(f"{stopwords_dir}/tagalog-stopwords.txt", 'r') as text:
        stopwords_tl = text.readlines()
    stopwords_tl = list(map(lambda a : a.strip(), stopwords_tl))
    print("Finished downloading stopwords_tl.")

    with open(f"{stopwords_dir}/english-stopwords.txt", 'r') as text:
        stopwords_en = text.readlines()
    stopwords_en = list(map(lambda a : a.strip(), stopwords_en))
    print("Finished downloading stopwords_en.")
    
    

def set_is_local(truth_val):
    global is_local
    is_local = truth_val
    if is_local:
        print(f"Running locally using directory {local_dir}.")
    else:
        print(f"Running in cloud using directory {drive_dir}.")
        
def set_export_folder(folder_name):
    global export_folder_name
    export_folder_name = folder_name
    print(f"Export directory set to {local_dir if is_local else drive_dir}DOST FilWordNet x WordSense/Thesis/NetSci Team/{export_folder_name}.")

    
    
def normalize(word):
    word = unicodedata.normalize('NFC', word)
    
    # if word is not alphanumeric and does not have accents
    if not word.isalnum() and not bool(re.match("^.*ÃƒÂ±.*$", word)):
        word = word.encode('ascii', 'ignore').decode('UTF-8')
        
    word = re.sub("\s", " ", word)
    word = re.sub(r"(.{1,}?)\1{3,}", r"\1\1", word)
    word = re.sub("('[a-z]{,2})+$", r"", word)
    word = re.sub("^[[:punct:]]+|[[:punct:]]+$", r"", word)
    
    return word

def is_valid(word):
    return (
        #pos[:2] in retain_pos_list
        len(word) > 1
        and word not in stopwords_en 
        and word not in stopwords_tl
        and not bool(re.match(r"xx_[a-z]+", word)) 
        
        and bool(re.match("^.*\w.*$", word))
            
        and type(word) == str
        and not bool(re.match("^(\p{Sc}|p)*[0-9.,]*$", word)) 
        and not bool(re.match(r"^[0-9]",word)) 
        and bool(re.match("(?!([h]*[aeui]*)+$).*", word))
    )

def word_tokenize_with_filter(sentence):
    words = []
    sent = sentence["pos_tags"]

    sent = [(normalize(word.lower().strip()).strip(), pos) for word, pos in sent]

    for index in range(len(sent)):
        word = sent[index][0]
        if is_valid(word):
            words.append(word)

    sentence["word_list"] = words

    return sentence

def create_edgelist(df):
    print("Processing...")
    if stopwords_tl == None or stopwords_en == None:
        print("Please download stopwords_tl and stopwords_en first by calling download_stopwords.")
        return df
    else:
        if 'lang_prob' in df.columns:
            df = df[df['lang_prob'] > 0.5]
        else:
            "Skipped filtering by lang_prob, column does not exist."
            
        df = df.progress_apply(word_tokenize_with_filter, axis=1)
            
        if df.empty:
            return df

        df = df[df['word_list'].apply(lambda tokens: len(tokens) > 1)]

        return df.reset_index(drop=True)[['text', 'word_list']]
    


def load_comms_dict(file_name):
    communities_directory = f"{local_dir if is_local else '/content/drive/Shareddrives/'}DOST FilWordNet x WordSense/Thesis/NetSci Team/communities"
    return json.load(open(f"{communities_directory}/{file_name}.json"))

def filter_sentences(edgelist_df, file_name):
    sense_json = load_comms_dict(file_name)
    return edgelist_df[edgelist_df['index_list'].apply(lambda word_pos_list: len(set(sense_json['ego']).intersection(set(word_pos_list))) > 0)]



def jaccard_similarity(comm1, comm2):
    intersection = len(set(comm1).intersection(set(comm2)))
    union = len(set(comm1)) + len(set(comm2)) - intersection

    return len(comm1) * intersection / union if union > 0 else 0

def get_similar_comm(context_words, file_name):
    comms = pd.DataFrame(list(load_comms_dict(file_name)['community'].items()), columns = ['index', 'communities'])
    comms['similarity'] = comms['communities'].apply(lambda community: jaccard_similarity(community, context_words))
    
    max_id = comms['similarity'].idxmax()
    
    return (comms.loc[max_id]['index'], comms.loc[max_id]['similarity'])

def get_word_intersections(context_words, file_name, inverted_nodelist):
    intersection_list = []
    for community_index, community_list in list(load_comms_dict(file_name)['community'].items()):
        intersection_list.append((community_index, [inverted_nodelist[index] for index in set(context_words).intersection(set(community_list))]))
    return intersection_list

def word_sense_disambiguation(sentences_df, file_name, inverted_nodelist=None):
    if not sentences_df.empty:
        sentences_df['cluster'] = sentences_df['index_list'].apply(lambda context_words: get_similar_comm(context_words, file_name))
        if inverted_nodelist:
            sentences_df['intersection'] = sentences_df['index_list'].apply(lambda context_words: get_word_intersections(context_words, file_name, inverted_nodelist))
    else:
        print("No sentences found.")
        
    return sentences_df