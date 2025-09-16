from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from ftplib import FTP
import pandas as pd
import io
import glob
import threading
import time
import json

app = FastAPI()

# ---------- CORS (allow React dev server) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Config File Storage

CONFIG_FILE = "config.json"

def loadConfig():
    global CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
                        CONFIG = json.load(f)
    except FileNotFoundError:
        return "Config file not found."


def saveConfig():
    with  open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f, indent=2)
        return "Config saved successfully."

loadConfig()

# merged data cache
merged_data = pd.DataFrame()

# Orbits Fetch Data

def fetchOrbits():
    # Fetch live competitor data from Orbits API and return as a pandas DataFrame.
    event_id = CONFIG['orbits'].get('event_id')
    api_key = CONFIG['orbits'].get('api_key')

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
        # Handles connection errors, timeouts, and HTTP errors
        print(f"Orbits fetch error: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print("Fetching Orbits data...")
    df = fetch_orbits()

    if df.empty:
        print("No data found.")
    else:
        print(df.head())   # print first few rows so you can see the structure