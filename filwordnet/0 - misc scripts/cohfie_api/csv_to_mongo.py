from mongo_utils import get_database

if __name__ == "__main__":    
    import pandas as pd
    # Get the database
    db = get_database("WordNet")
    # Get the collection under the database
    collection = db["COHFIE"]
    # Read CSV
    df = pd.read_csv(r"D:\thesis\corpus\COHFIE_V1\COHFIE_LITE.csv")
    # Convert DataFrame to dictionary then upload to MongoDB
    collection.insert_many(df.to_dict('records'))