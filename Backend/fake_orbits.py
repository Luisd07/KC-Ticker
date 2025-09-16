# fake_orbits.py
from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

# Example competitors
drivers = [
    {"number": "7", "name": "Alice Johnson"},
    {"number": "12", "name": "Bob Smith"},
    {"number": "22", "name": "Charlie Lee"},
    {"number": "99", "name": "Dana White"},
]

# Store lap data
race_state = {d["number"]: {"laps": 0, "last_time": None, "best_lap": None} for d in drivers}

@app.route("/fake-feed")
def fake_feed():
    # Simulate lap updates
    for d in drivers:
        state = race_state[d["number"]]
        # 30% chance this driver finishes a lap this request
        if random.random() < 0.9:
            lap_time = round(random.uniform(10, 20), 3)  # seconds
            state["laps"] += 1
            state["last_time"] = lap_time
            if state["best_lap"] is None or lap_time < state["best_lap"]:
                state["best_lap"] = lap_time

    # Format JSON response like Orbits might
    competitors = []
    for d in drivers:
        state = race_state[d["number"]]
        competitors.append({
            "number": d["number"],
            "name": d["name"],
            "laps": state["laps"],
            "last_time": state["last_time"],
            "best_lap": state["best_lap"],
        })

    return jsonify({"timestamp": time.time(), "competitors": competitors})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=50000, debug=True)
