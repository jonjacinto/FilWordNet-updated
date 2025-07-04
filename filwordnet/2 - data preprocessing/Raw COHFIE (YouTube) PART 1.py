import json
import pandas as pd
import os
from os.path import exists
import glob
import datetime
from datetime import datetime
import gc
from multiprocessing import Pool
import time

# Define constants
DATA_DIR = r"CHANGE_PATH_HERE"
SAVE_DIR = r"CHANGE_PATH_HERE"

def getYearMonthFromISO8601(d):
    '''
    Return year and month from ISO8601 format.
    '''
    new_date = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S%z").date()
        
    return new_date.year, new_date.month

def stripUnicode(text):
    text_encoded= text.encode("ascii", "ignore")
    text_decoded= text_encoded.decode()
    
    return text_decoded

def saveToCSV(filepath, texts, years, months):
    df = pd.DataFrame({'text': texts, 'year': years, 'month': months})

    if exists(filepath):
        df.to_csv(filepath, mode='a', header=False)
    else: # first time 
        df.to_csv(filepath, mode='w', header=True)
        
    print(f"Saved to {filepath}...")
    
def display_process_info(title):
    print(title)
    print(f'    module name:', __name__)
    print(f'    parent process:', os.getppid())
    print(f'    process id:', os.getpid())

def preprocess(json_files):
    # log time
    start = time.time()

    # display process info
    display_process_info("preprocess()")
    # define variables
    texts = []
    years = []
    months = []
    checkpoint_count = 1000000
    datetime_now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S.%f')
    #datetime_now = datetime.today().strftime('%Y-%m-%d')
    filepath = f'{SAVE_DIR}/PID_{datetime_now}.csv'
    
    # iterate through json files
    for file in json_files:
        # open single json file
        with open(file,'r') as f:
            comments = json.load(f)
    
        # process json file
        for comment in comments:
            cleaned_text = stripUnicode(comment['snippet']['textDisplay']).strip()

            if len(cleaned_text) == 0: # skip empty strings after stripping unicode
                continue
            
            if len(cleaned_text.split(" ")) < 4: # if less than 4 tokens, skip
                continue

            year, month = getYearMonthFromISO8601(comment['snippet']['publishedAt'])

            texts.append(cleaned_text)
            years.append(year)
            months.append(month)
            
            # if reached checkpoint, save to CSV (this is to prevent memory issues)
            if len(texts) == checkpoint_count:
                print(f"Reached checkpoint ({checkpoint_count} comments)... saving to {filepath}")
                saveToCSV(filepath, texts, years, months)

                # Free memory
                del texts
                del years
                del months
                gc.collect()
                
                # Reinitialize variables
                texts = []
                years = []
                months = []
    
    # if tapos na lahat, save to CSV
    saveToCSV(filepath, texts, years, months)

    print(f"end of preprocess() for PID {os.getpid()} ---{time.time() - start} seconds---")


if __name__ == "__main__":
    # Define variables
    json_files = glob.glob(os.path.join(DATA_DIR, '*.json'))
    n_files = len(json_files) # total number of files
    n_processes = 8 # cpu cores
    bs = (n_files // n_processes) # batch size
    print(f"batch size: {bs}")

    # Slice data to batches
    batches = []
    for p in range(n_processes):
        if not p == n_processes - 1: # if not last process
            X_batch = json_files[p * bs : bs * (p+1)]
        else: # if last slice, take all remaining data 
            X_batch = json_files[p * bs :]

        batches.append(X_batch)
        del X_batch

    with Pool(n_processes) as p:
        result = p.map(preprocess, batches)