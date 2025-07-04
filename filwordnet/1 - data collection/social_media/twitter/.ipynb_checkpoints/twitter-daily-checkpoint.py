# Collects tweets within a single day and saves to json file
# Args:
#   - offset: int 0-7
#   - user: one of the following [set_1, set_2, set_3, set_4]
#   - num_tweets: int (hardcoded in __main__)
#   - print_head : int 0 (false) or 1 (true)
# Usage: python twitter-daily.py 1 dan (collects tweets from yesterday using config "dan")

import tweepy
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pathlib

# Twitter Keys
CONSUMER_KEY = '<REPLACE WITH YOUR KEY>'
CONSUMER_SECRET = '<REPLACE WITH YOUR KEY>'
ACCESS_TOKEN = '<REPLACE WITH YOUR KEY>'
ACCESS_SECRET = '<REPLACE WITH YOUR KEY>'

# Users
set_1 = {'name': 'set_1', 'stop_words' : "nila OR nilang OR nito OR niya OR niyang OR noon OR o OR pa OR paano OR pababa OR paggawa OR pagitan OR pagkakaroon OR pagkatapos OR palabas OR pamamagitan OR panahon OR pangalawa OR para OR paraan OR pareho OR pataas OR pero OR pumunta OR pumupunta OR sa OR saan OR sabi OR sabihin OR sarili OR sila OR sino OR siya OR tatlo OR tayo OR tulad OR tungkol OR una OR walang"}
set_2 = {'name': 'set_2', 'stop_words' : "akin OR aking OR ako OR alin OR amin OR aming OR ang OR ano OR anumang OR apat OR at OR atin OR ating OR ay OR bababa OR bago OR bakit OR bawat OR bilang OR dahil OR dalawa OR dapat OR din OR dito OR doon OR gagawin OR gayunman OR ginagawa OR ginawa OR ginawang OR gumawa OR gusto OR habang OR hanggang OR hindi"}
set_3 = {'name': 'set_3', 'stop_words' : "kulang OR kumuha OR kung OR laban OR lahat OR lamang OR likod OR lima OR maaari OR maaaring OR maging OR mahusay OR makita OR marami OR marapat OR masyado OR may OR mayroon OR mga OR minsan OR mismo OR mula OR muli OR na OR nabanggit OR naging OR nagkaroon OR nais OR nakita OR namin OR napaka OR narito OR nasaan OR ng OR ngayon OR ni"}
set_4 = {'name': 'set_4', 'stop_words' : "huwag OR iba OR ibaba OR ibabaw OR ibig OR ikaw OR ilagay OR ilalim OR ilan OR inyong OR isa OR isang OR itaas OR ito OR iyo OR iyon OR iyong OR ka OR kahit OR kailangan OR kailanman OR kami OR kanila OR kanilang OR kanino OR kanya OR kanyang OR kapag OR kapwa OR karamihan OR katiyakan OR katulad OR kaya OR kaysa OR ko OR kong"}

# Set active user
def set_active_user(user):
    if user == 'axel':
        active_user = axel
    elif user == 'bryce':
        active_user = bryce
    elif user == 'dan':
        active_user = dan
    elif user == 'trisha':
        active_user = trisha
    else:
        print("user argument must be one of the following: [axel, bryce, dan, trisha]")
        exit()
    
    return active_user

# Setup access to API
def connect_to_twitter_OAuth():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return api

# fuction to extract data from tweet object
def extract_tweet_attributes_to_json(tweet_objects, filename, print_head=False):
    # create empty list
    tweet_list = []
    # loop through tweet objects
    for tweet in tweet_objects:
        tweet_id = tweet.id # unique integer identifier for tweet
        user_username = tweet.user.screen_name # unique integer identifier for tweet
        text = tweet.full_text # utf-8 text of tweet
        favorite_count = tweet.favorite_count
        retweet_count = tweet.retweet_count
        created_at = tweet.created_at # utc time tweet created
        location = tweet.user.location
        # append attributes to list
        tweet_list.append({'tweet_id':tweet_id, 
                           'user_username':user_username, 
                           'text':text, 
                           'favorite_count':favorite_count,
                           'retweet_count':retweet_count,
                           'created_at':created_at,
                           'location': location})
    
    # create dataframe   
    df = pd.DataFrame(tweet_list, columns=['tweet_id',
                                           'user_username', 
                                           'text',
                                           'favorite_count',
                                           'retweet_count',
                                           'created_at',
                                           'location'])

    # Preview collected data
    if print_head:
        print(df[{'text', 'created_at'}].head())

    # Save to JSON
    print(f'Saving {filename}...')
    with open(filename, 'w') as f:
        f.write(df.to_json(orient='records', lines=True))
    print(f'{filename} saved.')


def get_tweets_oneday(offset=1, user=None, num_tweets=16666, print_head=False):
    # Input must be integer and within 0-7
    # Default to 1 means yesterday's date
    if isinstance(offset, int) and offset in range(0,8):
        target_day_datetime = (datetime.now() - timedelta(offset))
        next_day_datetime = target_day_datetime + timedelta(1)
        target_day_str = target_day_datetime.strftime('%Y-%m-%d')
        next_day_str = next_day_datetime.strftime('%Y-%m-%d')
    else:
        return "Please input integer between 0-7 in offset parameter."
    
    # Set active user
    active_user = set_active_user(user)

    # PARAMETERS
    start_time = time.time() # Log start time
    max_sleeps = 12
    n_sleep = 0
    tweet_ctr = 0
    tweets = [] # initialize empty list
    prev_count = 0
    sleep_time_seconds = 300
    sleep_time_minutes = sleep_time_seconds / 60

    # Create API object
    api = connect_to_twitter_OAuth()

    # Connect to GDrive OAuth
    gauth = connect_to_gdrive_OAuth()

    #search_terms = '*' # use if no filter
    search_terms = active_user['stop_words'] # filtered by stop words
    query = tweepy.Cursor(api.search,q=search_terms + ' -filter:retweets',
                                    lang='fil', tweet_mode='extended', 
                                    since=target_day_str, 
                                    until=next_day_str,
                                    result_type='mixed').items(num_tweets)

    # Collect tweets by target_date
    print(f"Config: {active_user['name']}")
    print(f"Collecting {num_tweets} tweets for {target_day_str}...")
    print(f"Exception sleep time: {sleep_time_minutes} minutes")
    print(f"Max # of continuous sleeps: {max_sleeps} sleeps")

    while True:
        try:
            #tweets = [tweet for tweet in tweepy.Cursor(api.search,q=search_terms + ' -filter:retweets',
            #tweets = [tweet for tweet in query]
            for tweet in query:
                tweets.append(tweet)
                tweet_ctr += 1
                if tweet_ctr % 1000 == 0:
                    print(f"Tweets collected: {tweet_ctr}")

            break
        except (tweepy.TweepError) as e:
            print(e.reason)
            if n_sleep == max_sleeps: # if reached max num of sleeps without progress
                break

            if n_sleep == 0: # first time sleeping
                prev_count = tweet_ctr # remember tweet count

            if prev_count == tweet_ctr: # if no progress, increment sleep
                n_sleep += 1
            else:                       # reset if there's progress
                prev_count = tweet_ctr  # update prev_size
                n_sleep = 1

            # Print message
            print(f"Sleeping for {sleep_time_minutes} minutes ({n_sleep} out of {max_sleeps})...")
            # Get current time
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            # Print start time
            print(f"Sleep start: {current_time}")
            # Sleep
            time.sleep(sleep_time_seconds)
            continue

    end_time = time.time() # Log end time
    run_time = end_time-start_time # Running time
    print(f"Total execution time: {run_time:.2f} seconds") # Print running time of tweet collection

    # Save tweets to json file
    if len(tweets) > 0: # if tweets list is not empty
        filename = target_day_str + '_' + active_user['name'] + '.json' # set filename
        extract_tweet_attributes_to_json(tweets, filename, print_head=print_head) # save to json
    
if __name__ == "__main__":
    # Get args
    offset = int(sys.argv[1])
    user = sys.argv[2]

    # default
    num_tweets = 33333

    # Run script
    get_tweets_oneday(offset, user, num_tweets, print_head=True)