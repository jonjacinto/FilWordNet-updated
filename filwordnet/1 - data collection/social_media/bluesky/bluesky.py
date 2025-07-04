from atproto import FirehoseSubscribeReposClient, parse_subscribe_repos_message, CAR, IdResolver, DidInMemoryCache, Client
from atproto_client import models
import json
import time
import argparse
from datetime import datetime, timedelta
import sys
import signal
import pandas as pd
import os

# modified version of search_all_tweets.py
STOP_WORDS = list(set(
"""
akin
aking
ako
alin
amin
aming
ang
ano
atin
ating
bababa
bago
bakit
bawat
dahil
dapat
din
dito
doon
gagawin
gusto
habang
hanggang
hindi
huwag
iba
ibaba
ibabaw
ibig
ikaw
ilagay
ilalim
ilan
inyong
isa
isang
itaas
ito
iyo
iyon
iyong
kahit
kami
kanila
kanilang
kanino
kanya
kanyang
kapag
kapwa
katulad
kaya
kaysa
kong
kulang
kumuha
kung
laban
lahat
lamang
likod
maging
mahusay
makita
marami
masyado
mga
minsan
mismo
mula
muli
naging
nais
nakita
namin
napaka
narito
nasaan
ngayon
nila
nilang
nito
niya
niyang
noon
paano
pababa
panahon
para
paraan
pareho
pataas
pero
saan
sabi
sabihin
sarili
sila
sino
siya
tayo
tungkol
walang
""".split()
))

STOP_WORDS = " || ".join(STOP_WORDS)

def connect_client():
    at_client = Client()
    at_client.login('my-handle', 'password')
    return at_client
    

def get_posts_oneday(offset=1):
    if isinstance(offset, int) and offset in range(0,8):
        target_day_datetime = (datetime.now() - timedelta(offset))
        next_day_datetime = target_day_datetime + timedelta(1)
        target_day_str = target_day_datetime.strftime('%Y-%m-%d')
        next_day_str = next_day_datetime.strftime('%Y-%m-%d')
    else:
        return "Please input integer between 0-7 in offset parameter."
    
    start_time = time.time() # Log start time
    max_sleeps = 1000000
    n_sleep = 0
    post_ctr = 0
    cursor_ctr = 0
    max_cursor = 5
    posts = [] # initialize empty list
    prev_count = 0
    sleep_time_seconds = 300
    sleep_time_minutes = sleep_time_seconds / 60

    client = connect_client()

    query = client.app.bsky.feed.search_posts(
        params = models.AppBskyFeedSearchPosts.Params(
            q=STOP_WORDS))
    cursor_ctr += 1
    for post in query.posts:
        posts.append(post)
        post_ctr += 1
    while cursor_ctr <= max_cursor:
        cursor = query.cursor
        query = client.app.bsky.feed.search_posts(
            params = models.AppBskyFeedSearchPosts.Params(
                q=STOP_WORDS, cursor = cursor
            )
        )
        for post in query.posts:
            posts.append(post)
            post_ctr += 1
        cursor_ctr += 1
    print(query.cursor)
    print(f"Number of posts: {post_ctr}")

    

if __name__ == "__main__":
    get_posts_oneday()
