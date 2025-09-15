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

def fetchFTP():

    # Fetch driver CSV files and team logos from FTP, parses through them, and return combined CSV data as a pandas DataFrame.

    combined_df = pd.DataFrame

    host = CONFIG['ftp'].get('host')
    username = CONFIG['ftp'].get('username')
    password = CONFIG['ftp'].get('password')
    directory = CONFIG['ftp'].get('directory', '/')
    file_pattern = CONFIG['ftp'].get('file_pattern', '*.csv')

    if not host or not username or not password:
        print("FTP fetch skipped: missing host, username, or password")
        return combined_df

    try:
        with FTP(host) as ftp:
            ftp.login(user=username, passwd=password)
            ftp.cwd(directory)
            files = ftp.nlst()

            # ---------- Parse CSV files in memory ----------
            csv_files = [f for f in files if f.endswith(".csv") and glob.fnmatch.fnmatch(f, file_pattern)]
            for csv_file in csv_files:
                r = io.BytesIO()
                ftp.retrbinary(f"RETR {csv_file}", r.write)
                r.seek(0)  # move to start of the file
                df = pd.read_csv(r)
                combined_df = pd.concat([combined_df, df], ignore_index=True)

            # ---------- List logos (no download) ----------
            logo_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if logo_files:
                print(f"Found logos: {logo_files}")

        return combined_df

    except Exception as e:
        print(f"FTP error: {e}")
        return combined_df


def mergeData():

    # Fetch Orbits data and FTP CSVs in memory, normalize driver names, merge, and update global merged_data.

    global merged_data

    orbits_df = fetchOrbits()
    if orbits_df.empty:
        mergeData = pd.DataFrame()
        return

    ftp_df = fetchFTP()
    if ftp_df.empty:
        mergeData = pd.DataFrame()
        return

    # Get merge keys from config
    orbits_key = CONFIG['merge_keys'].get('orbits_key', 'driver_name')
    ftp_key = CONFIG['merge_keys'].get('ftp_key', 'Driver')

    # Normalize driver names
    orbits_df['driver_clean'] = orbits_df[orbits_key].astype(str).str.lower().str.replace(" ", "")
    ftp_df['driver_clean'] = ftp_df[ftp_key].astype(str).str.lower().str.replace(" ", "")

    # Merge
    merged_data = pd.merge(orbits_df, ftp_df, on='driver_clean', how='left')

# ---------- LIVE POLLING ----------
def startPolling():
    # Start background thread that updates merged_data every poll_interval seconds.

    def pollingLoop():
        while True:
            mergeData()
            time.sleep(CONFIG.get('poll_interval', 5))

    thread = threading.Thread(target=pollingLoop, daemon=True)
    thread.start()

# Start polling when backend runs
startPolling()


# ---------- API ENDPOINTS ----------
@app.get("/live-data")


def getLiveData():
    # Return latest merged data as JSON.
    return merged_data.to_dict(orient="records")

class ConfigUpdate(BaseModel):
    orbits: dict
    ftp: dict
    merge_keys: dict
    poll_interval: int = 5

@app.get("/config")
def get_config():
    return CONFIG

@app.post("/config")
def update_config(config_update: ConfigUpdate):
    global CONFIG
    CONFIG = config_update.dict()
    saveConfig()
    return {"status": "success", "message": "Configuration updated"}