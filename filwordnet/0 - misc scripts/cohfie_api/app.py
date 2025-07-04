from flask import Flask, request
from pymongo import MongoClient
from mongo_utils import get_database, get_sentences


app = Flask(__name__)


@app.route('/search', methods=['GET'])
def index():
    #query = request.form['query']
    query = request.args.get("query")
    start_year = int(request.args.get("start_year", 0))
    end_year = int(request.args.get("end_year", 999999))
    start_month = int(request.args.get("start_month", 0))
    end_month = int(request.args.get("end_month", 999999))
    source_type = request.args.get("source_type", None)
    limit = int(request.args.get("limit", 0))

    return get_sentences(query, start_year, end_year, start_month, end_month, source_type, limit)