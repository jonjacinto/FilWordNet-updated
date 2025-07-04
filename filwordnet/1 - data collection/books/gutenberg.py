import os
import pandas as pd
import glob
import json
import re
import nltk
import string
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup 

########################################
#  Author: Shravan Kuchkula
########################################
def remove_gutenburg_headers(book_text):
    book_text = book_text.replace('\r', '')
    book_text = book_text.replace('\n', ' ')
    start_match = re.search(r'\*{3}\s?START.+?\*{3}', book_text)
    end_match = re.search(r'\*{3}\s?END.+?\*{3}', book_text)
    try:
        book_text = book_text[start_match.span()[1]:end_match.span()[0]]
    except AttributeError:
        print('No match found')    
    return book_text

def remove_gutenberg_footer(book_text):
    if book_text.find('End of the Project Gutenberg') != -1:
        book_text = book_text[:book_text.find('End of the Project Gutenberg')]
    elif book_text.find('End of Project Gutenberg') != -1:
        book_text = book_text[:book_text.find('End of Project Gutenberg')]
    return book_text

def getTextFromURLByRemovingHeaders(book_urls):
    book_texts = []

    for url in tqdm(book_urls):
        book_text = requests.get(url).text
        book_title = get_title(book_text)
        book_text = remove_gutenburg_headers(book_text)
        book_text = remove_gutenberg_footer(book_text)
        book_texts.append([book_title, book_text])

    return book_texts

def get_page(URL):
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36"
    }

    page = requests.get(URL, headers=headers)
    return [BeautifulSoup(page.content.decode(), 'html.parser'), page.status_code]

def get_urls_to_plaintext(books_page):
    lst = books_page[0].find("div", class_="pgdbbylanguage").find_all("li", class_="pgdbetext")
    links = [li.find("a")["href"] for li in lst]
    book_id = [link.split('/')[2] for link in links]
    links_to_plaintext = [f"https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt" for id in book_id]
    return links_to_plaintext

def get_title(text):
    start = text.find('Title:')
    end = text.find('Author:', start)
    output = text[start:end].replace('\n', '').replace('Title: ', '').replace('\r', '').replace('$', '')

    return output

def save_txtfile(path, filename, content):
    f = open(path + filename, "w", encoding="utf-8")
    f.write(content)
    f.close()
    print(f"Saved {filename}")

if __name__ == "__main__":
    # Set path
    PARENT_DIR_NAME = "FilWordNet"
    PATH_BEFORE_PARENT_DIR_NAME = os.path.abspath(os.curdir).split(PARENT_DIR_NAME)[0]
    ROOT_DIR = PATH_BEFORE_PARENT_DIR_NAME + PARENT_DIR_NAME
    SAVE_DIR = ROOT_DIR + "/RAW_DATA/books/gutenberg/"

    # Collect
    print("Collecting data...")
    tagalog_books_page = get_page("https://www.gutenberg.org/browse/languages/tl")
    book_urls = get_urls_to_plaintext(tagalog_books_page)
    book_texts = getTextFromURLByRemovingHeaders(book_urls)

    # Save
    print("Saving data...")
    if not os.path.exists(SAVE_DIR): # if SAVE_DIR doesn't exist
        print(f"{SAVE_DIR} doesn't exist. Creating directory...")
        os.makedirs(SAVE_DIR)
    else:
        print(f"{SAVE_DIR} exists.")

    for item in book_texts:
        title = item[0]
        filename = (title + '.txt').replace('"', "")
        content = item[1]
        save_txtfile(SAVE_DIR, filename, content)

    

    