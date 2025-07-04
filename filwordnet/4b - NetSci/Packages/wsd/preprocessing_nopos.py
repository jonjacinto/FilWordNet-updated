import os
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



def import_nodelist():
    nodelist_dir = f"{local_dir if is_local else drive_dir}DOST FilWordNet x WordSense/Thesis/NetSci Team/{export_folder_name}"
    
    if not os.path.isfile(f"{nodelist_dir}/nodelist.pkl"):
        nodelist_dict = {}
    else:
        with open(f"{nodelist_dir}/nodelist.pkl", 'rb') as f:
            nodelist_dict = pickle.load(f)
            
    return nodelist_dict

def get_inverted_nodelist():
    nodelist_dict = import_nodelist()
    
#     inverted_nodelist_dict = {}
#     temp = [{index: (word) for (index) in list(pos_list.items())} for word, pos_list in list(nodelist_dict.items())]
#     for sub_dict in temp:
#         inverted_nodelist_dict.update(sub_dict)
        
    return {v: k for k, v in nodelist_dict.items()}

def save_nodelist(nodelist_dict):
    new_nodelist_dir = f"{local_dir if is_local else drive_dir}DOST FilWordNet x WordSense/Thesis/NetSci Team/{export_folder_name}"
    
    if not os.path.exists(f"{new_nodelist_dir}"): 
        os.makedirs(f"{new_nodelist_dir}")
        
    with open(f"{new_nodelist_dir}/nodelist.pkl", 'wb') as f:
        pickle.dump(nodelist_dict, f)

def get_next_id(nodelist_dict):
    if bool(nodelist_dict):
        values = nodelist_dict.values()
        return (max(values) + 1 if values != [] else 0)
    return 0

def add_to_nodelist(nodelist_dict, word_list):
    next_id = get_next_id(nodelist_dict)

    for index, word in enumerate(word_list):
        nodelist_dict[word] = next_id
        next_id += 1
        
    return nodelist_dict



def normalize(word):
    word = unicodedata.normalize('NFC', word)
    
    # if word is not alphanumeric and does not have accents
    if not word.isalnum() and not bool(re.match("^.*ñ.*$", word)):
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
    #pos_tags = []
    sent = sentence["pos_tags"]

    sent = [(normalize(word.lower().strip()).strip(), pos) for word, pos in sent]
    #sent = sorted(list(set(sent)))
    #sent = list(set(sent))

    for index in range(len(sent)):
        word = sent[index][0]
        #pos = sent[index][1][:2]
        #pos = sent[index][1][:2] if sent[index][1] != "NNP" else sent[index][1]
        if is_valid(word):
            words.append(word)
            #pos_tags.append(pos)

    sentence["text"] = words
    #sentence["pos_tags"] = pos_tags

    return sentence



def make_combinations(word_list, window_size):
    final_list = []

    if window_size == "sentence length":
        final_list = list(combinations(word_list, 2))
    else:
        for window in range(1, window_size + 1):
            if len(word_list) > window:
                final_list += list(zip(word_list, word_list[window:]))

    return [sorted(item) for item in final_list]

def create_edgelist(df, window_size):
    print("Processing...")
    if stopwords_tl == None or stopwords_en == None:
        print("Please download stopwords_tl and stopwords_en first by calling download_stopwords.")
        return df
    else:
        df = df[df['lang_prob'] > 0.5].progress_apply(word_tokenize_with_filter, axis=1)

        if df.empty:
            return df

        df = df[df['text'].apply(lambda tokens: len(tokens) > 1)]
        
        edges = df["text"].apply(lambda words: make_combinations(words, window_size)).explode().to_frame()
        #edges["pos_tags"] = df["pos_tags"].apply(lambda tags: make_combinations(tags, window_size)).explode().to_frame()

        edges["word1"] = edges["text"].apply(lambda pair : pair[0])
        #edges["pos1"] = edges["pos_tags"].apply(lambda pair : pair[0])
        edges["word2"] = edges["text"].apply(lambda pair : pair[1])
        #edges["pos2"] = edges["pos_tags"].apply(lambda pair : pair[1])
        edges["window_size"] = 0 if window_size == "sentence length" else window_size

        edges.drop(columns=["text"], inplace=True)

        edges = edges.join(df['year']).join(df['month']).join(df['source']).join(df['source_type'])

        edges['year'], edges['month'] = edges['year'].astype(int), edges['month'].astype(int)

        return edges.reset_index(drop=True)
    
def save_edgelist(df):
    directory = f"{local_dir if is_local else '/content/drive/Shareddrives/'}DOST FilWordNet x WordSense/Thesis/NetSci Team/{export_folder_name}"

    source = df["source"].iloc[0] 
    source_type = df["source_type"].iloc[0]
    month = int(df["month"].iloc[0])
    year = int(df["year"].iloc[0])

    if not os.path.exists(f"{directory}/{source_type}/{source}/{year}/{month}"): 
        os.makedirs(f"{directory}/{source_type}/{source}/{year}/{month}") 
    df.dropna().to_csv(f"{directory}/{source_type}/{source}/{year}/{month}/{source_type}_{source}_{year}_{month}.csv", index=False)
    
    

def update_nodelist(edgelist):
    print("Updating node list...")
    edgelist_nodes = pd.concat([edgelist[['word1']].rename(columns={"word1": "word"}), edgelist[['word2']].rename(columns={"word2": "word"})]).drop_duplicates()

    print("Importing node list...")
    nodelist_dict = import_nodelist()

    print("Adding new words to node list...")
    new_words = edgelist_nodes[edgelist_nodes['word'].apply(lambda word: word not in nodelist_dict)].drop_duplicates()['word'].tolist()
    nodelist_dict.update({new_word: -1 for new_word in new_words})
    
    #new_pos = edgelist_nodes[edgelist_nodes.apply(lambda row: row.pos not in nodelist_dict[row.word], axis=1)].drop_duplicates()
    add_to_nodelist(nodelist_dict, new_words)
    edgelist['word1'] = edgelist.apply(lambda row: nodelist_dict[row.word1], axis=1)
    edgelist['word2'] = edgelist.apply(lambda row: nodelist_dict[row.word2], axis=1)
    #edgelist.drop(columns=['pos1', 'pos2'], inplace=True)

    return edgelist, nodelist_dict