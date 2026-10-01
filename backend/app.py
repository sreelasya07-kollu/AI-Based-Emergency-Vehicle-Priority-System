"""RescueRoute AI — Flask backend API."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.database import (
    get_active_emergencies,
    get_recent_alerts,
    init_db,
    save_active_emergency,
    save_alert,
)
from backend.notification_service import NotificationService
from backend.route_planner import RoutePlanner
from pipeline.rescue_pipeline import RescueRoutePipeline

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR))
CORS(app)

planner = RoutePlanner()
notifier = NotificationService()
pipeline = RescueRoutePipeline()


@app.before_request
def setup():
    init_db()


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "RescueRoute AI"})


@app.route("/api/alerts")
def alerts():
    return jsonify(get_recent_alerts())


@app.route("/api/active")
def active():
    return jsonify(get_active_emergencies())


@app.route("/api/route", methods=["POST"])
def calculate_route():
    data = request.json or {}
    origin = data.get("origin", "A")
    destination = data.get("destination", "Hospital")
    congestion = data.get("congestion", "Moderate")

    route = planner.find_fastest_route(origin, destination, congestion)
    if not route:
        return jsonify({"error": "No route found"}), 404

    return jsonify(
        {
            "origin": route.origin,
            "destination": route.destination,
            "path": route.path,
            "path_names": route.path_names,
            "route_string": planner.route_to_string(route),
            "eta_minutes": route.eta_minutes,
            "distance_km": route.total_distance_km,
            "upcoming_signals": route.upcoming_signals,
            "congestion": route.congestion_level,
            "signal_priority": notifier.get_signal_priority_list(route),
        }
    )


@app.route("/api/notify", methods=["POST"])
def send_notification():
    data = request.json or {}
    vehicle_type = data.get("vehicle_type", "Ambulance")
    location = data.get("location", "Intersection A")
    origin = data.get("origin", "A")
    destination = data.get("destination")
    congestion = data.get("congestion", "Moderate")

    dest = planner.resolve_destination(vehicle_type, destination)
    route = planner.find_fastest_route(origin, dest, congestion)
    if not route:
        return jsonify({"error": "No route found"}), 404

    alert = notifier.create_alert(
        vehicle_type=vehicle_type,
        location=location,
        route=route,
        traffic_density=congestion,
        direction=data.get("direction"),
    )
    save_alert(alert.to_dict())
    save_active_emergency(alert.to_dict())

    return jsonify(
        {
            "alert": alert.to_dict(),
            "signal_priority": notifier.get_signal_priority_list(route),
        }
    )


@app.route("/api/detect", methods=["POST"])
def detect_emergency():
    data = request.json or {}
    result = pipeline.handle_detection_event(
        vehicle_type=data.get("vehicle_type", "Ambulance"),
        location=data.get("location", "Intersection A"),
        origin=data.get("origin", "A"),
        destination=data.get("destination"),
        congestion=data.get("congestion", "Moderate"),
        direction=data.get("direction"),
    )
    return jsonify(result)


@app.route("/api/map")
def city_map():
    return jsonify(planner.intersections)


if __name__ == "__main__":
    init_db()
    print("RescueRoute AI backend running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
