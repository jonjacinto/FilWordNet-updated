import re
from pymongo import MongoClient
from bson import json_util 

def get_database(dbname=None):
    if dbname is None:
        raise Exception("dbname is None.")

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://netsci:1234@cluster0.krbgc.mongodb.net/WordNet?retryWrites=true&w=majority"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[dbname]



def get_sentences(query=None, start_year=None, end_year=None, start_month=None, end_month=None, source_type=None, limit=0):
    # Load db
    db = get_database("WordNet")

    # Load collection
    collection = db["COHFIE"]
    
    # Compile regex
    pat = re.compile(fr' {query} ') # surround query string with whitespaces
    if source_type is None:
        documents_cursor = collection.find({ "text": {'$regex': pat}, "year":{"$gte":start_year,"$lt":end_year}, "month":{"$gte":start_month,"$lt":end_month}}, {"_id": False}).limit(limit)
    else:
        documents_cursor = collection.find({ "text": {'$regex': pat}, "year":{"$gte":start_year,"$lt":end_year}, "month":{"$gte":start_month,"$lt":end_month}, "source_type": source_type}, {"_id": False}).limit(limit)

    documents = [doc for doc in documents_cursor]

    
    return json_util.dumps(documents)