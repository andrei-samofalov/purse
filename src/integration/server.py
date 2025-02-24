from flask import Flask, jsonify

app = Flask(__name__)


@app.get('/index')
def index():
    return jsonify({"retry_after": 1}), 429
