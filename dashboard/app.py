from flask import (
    Flask,
    render_template,
    jsonify,
    request
)

import os


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "..",
    "frontend"
)

app = Flask(
    __name__,
    template_folder=FRONTEND_DIR,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)


# ==========================================
# DEFAULT STATUS
# ==========================================

status = {

    "ambulance_detected": False,

    "confidence": 0,

    "emergency_mode": False,

    "vehicle_counts": {

        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0
    },

    "total_vehicles": 0,

    "traffic_level": "LOW",

    "traffic_score": 0,

    "route": "Waiting for real route...",

    "distance": 0,

    "eta": "--",

    "signal_priority": False,

    "green_junction": "--",

    "destination": "Waiting...",

    "start_location": {},

    "destination_location": {},

    "route_geometry": {

        "type": "LineString",

        "coordinates": []
    }
}


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# STATUS
# ==========================================

@app.route("/api/status")
def get_status():

    return jsonify(status)


# ==========================================
# UPDATE
# ==========================================

@app.route(
    "/api/update",
    methods=["POST"]
)
def update_status():

    global status

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Invalid JSON"
        }), 400

    status.update(data)

    return jsonify(status)


# ==========================================
# EMERGENCY
# ==========================================

@app.route("/api/emergency")
def emergency():

    return jsonify({

        "emergency":
            status["emergency_mode"],

        "ambulance_detected":
            status["ambulance_detected"]
    })


# ==========================================
# RESET
# ==========================================

@app.route("/api/reset")
def reset():

    global status

    status = {

        "ambulance_detected": False,

        "confidence": 0,

        "emergency_mode": False,

        "vehicle_counts": {

            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        },

        "total_vehicles": 0,

        "traffic_level": "LOW",

        "traffic_score": 0,

        "route":
            "Waiting for real route...",

        "distance": 0,

        "eta": "--",

        "signal_priority": False,

        "green_junction": "--",

        "destination": "Waiting...",

        "start_location": {},

        "destination_location": {},

        "route_geometry": {

            "type": "LineString",

            "coordinates": []
        }
    }

    return jsonify(status)


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    print()
    print(
        "=================================="
    )
    print(
        " RescueRoute AI Dashboard"
    )
    print(
        " Real World Routing"
    )
    print(
        " http://127.0.0.1:5050"
    )
    print(
        "=================================="
    )
    print()

    app.run(
        host="127.0.0.1",
        port=5050,
        debug=False
    )