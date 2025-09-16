from urllib import response
from flask import Flask, jsonify 
import requests
import json
import os
import pandas as pd
from werkzeug.datastructures import Authorization


app = Flask(__name__)

orbitsAPIKey = ""
orbitsEndpoint = ""

@app.route("/orbits")
def getData():
    headers = {
         "Authorization": f"Bearer {orbitsAPIKey}"
         }

    try:
        response = requests.get(orbitsEndpoint, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        return jsonify(data)
    except requests.exception.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/test")
def test():
    return "This is a test endpoint."


if __name__ == "__main__":
    app.run(debug=True)