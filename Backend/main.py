from flask import Flask, jsonify
import requests
import pandas as pd
import json

app = Flask(__name__)

#Config File Storage

CONFIG = "config.json"

def loadConfig():
    global CONFIG
    try:
        with open(CONFIG, "r") as f:
                        CONFIG = json.load(f)
    except FileNotFoundError:
        return "Config file not found."


def saveConfig():
    with  open(CONFIG, "w") as f:
        json.dump(CONFIG, f, indent=2)
        return "Config saved successfully."

loadConfig()

def fetch_orbits(CONFIG):
    
    # Fetch live competitor data from Orbits API and return as a pandas DataFrame.
    
    event_id = CONFIG.get('orbits', {}).get('event_id')
    api_key = CONFIG.get('orbits', {}).get('api_key')

    if not event_id or not api_key:
        print("Orbits fetch skipped: missing event_id or api_key")
        return pd.DataFrame()

    url = f"https://api.mylaps.com/v5/events/{event_id}/results"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        competitors = response.json().get("competitors", [])
        return pd.json_normalize(competitors)

    except requests.RequestException as e:
        print(f"Orbits fetch error: {e}")
        return pd.DataFrame()


#  Flask Route
@app.route("/live-data")
def live_data():
    df = fetch_orbits(CONFIG)
    # Convert DataFrame to JSON records
    return df.to_json(orient="records")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)