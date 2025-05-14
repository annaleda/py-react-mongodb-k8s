from flask import Flask
from pymongo import MongoClient
import os

app = Flask(__name__)
client = MongoClient(f"mongodb://{os.environ.get('MONGO_USER')}:{os.environ.get('MONGO_PASS')}@mongodb-service:27017/")
db = client.testdb

@app.route("/api/hello")
def hello():
    return {"message": "Hello from Flask + Mongo"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
