import cv2
import requests
import time
from ultralytics import YOLO

# ==============================
# CONFIGURATION
# ==============================

AMBULANCE_MODEL_PATH = "runs/detect/runs/ambulance_yolo11/weights/best.pt"
VEHICLE_MODEL_PATH = "yolo11n.pt"

API_URL = "http://127.0.0.1:5050/api/update"

# -------------------------------------------------
# REAL LOCATION
# Change these coordinates for your actual demo.
# Hyderabad example:
# -------------------------------------------------

START_LAT = 17.3850
START_LON = 78.4867

# Example destination:
# Rajiv Gandhi International Airport area
DEST_LAT = 17.2403
DEST_LON = 78.4294

DESTINATION_NAME = "Rajiv Gandhi International Airport"

# Ambulance confirmation
AMBULANCE_CONFIDENCE = 0.70
REQUIRED_FRAMES = 3

# General vehicle detection
VEHICLE_CONFIDENCE = 0.45

# COCO classes used by YOLO11n
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

# ==============================
# LOAD MODELS
# ==============================

print("Loading ambulance model...")
ambulance_model = YOLO(AMBULANCE_MODEL_PATH)

print("Loading vehicle model...")
vehicle_model = YOLO(VEHICLE_MODEL_PATH)

print("Ambulance model:", ambulance_model.names)
print("Vehicle model:", vehicle_model.names)

# ==============================
# REAL-WORLD ROUTING
# ==============================

def get_real_route(start_lat, start_lon, dest_lat, dest_lon):

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{dest_lon},{dest_lat}"
    )

    url = f"{OSRM_URL}/{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "alternatives": "true"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            print("OSRM error:", data.get("code"))
            return None

        route = data["routes"][0]

        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        geometry = route["geometry"]

        # Extract road names
        road_names = []

        if "legs" in route:

            for leg in route["legs"]:

                for step in leg.get("steps", []):

                    name = step.get("name")

                    if name and name not in road_names:
                        road_names.append(name)

        return {
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min, 1),
            "geometry": geometry,
            "road_names": road_names
        }

    except Exception as e:

        print("Routing error:", e)

        return None


# ==============================
# DASHBOARD UPDATE
# ==============================

def update_dashboard(
    ambulance_detected,
    confidence,
    emergency_mode,
    vehicle_counts,
    traffic_level,
    traffic_score,
    route_data
):

    if route_data:

        distance = route_data["distance_km"]
        duration = route_data["duration_min"]

        road_names = route_data["road_names"]

        if road_names:

            route_text = " → ".join(
                road_names[:6]
            )

        else:

            route_text = (
                "Current Location → "
                + DESTINATION_NAME
            )

        geometry = route_data["geometry"]

    else:

        distance = 0
        duration = 0

        route_text = (
            "Route unavailable"
        )

        geometry = {
            "type": "LineString",
            "coordinates": []
        }

    signal_priority = emergency_mode

    if emergency_mode:

        green_junction = "NEXT SIGNAL"

    else:

        green_junction = "--"

    payload = {

        "ambulance_detected": ambulance_detected,

        "confidence": round(
            float(confidence),
            2
        ),

        "emergency_mode": emergency_mode,

        "vehicle_counts": vehicle_counts,

        "total_vehicles": sum(
            vehicle_counts.values()
        ),

        "traffic_level": traffic_level,

        "traffic_score": traffic_score,

        "route": route_text,

        "distance": distance,

        "eta": (
            f"{duration:.1f} min"
            if emergency_mode
            else "--"
        ),

        "signal_priority": signal_priority,

        "green_junction": green_junction,

        "destination": DESTINATION_NAME,

        "start_location": {
            "latitude": START_LAT,
            "longitude": START_LON
        },

        "destination_location": {
            "latitude": DEST_LAT,
            "longitude": DEST_LON
        },

        "route_geometry": geometry
    }

    try:

        requests.post(
            API_URL,
            json=payload,
            timeout=2
        )

    except Exception as e:

        print(
            "Dashboard connection error:",
            e
        )


# ==============================
# TRAFFIC CALCULATION
# ==============================

def calculate_traffic(vehicle_counts):

    total = sum(
        vehicle_counts.values()
    )

    if total <= 5:

        level = "LOW"

    elif total <= 12:

        level = "MEDIUM"

    else:

        level = "HIGH"

    # Normalize score to 0–100
    score = min(
        100,
        int(total / 20 * 100)
    )

    return level, score


# ==============================
# CAMERA
# ==============================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Camera could not be opened.")
    exit()

print()
print("===================================")
print(" RESCUE ROUTE AI")
print(" REAL WORLD ROUTING MODE")
print("===================================")
print()
print("Start:")
print(START_LAT, START_LON)

print()
print("Destination:")
print(
    DESTINATION_NAME,
    DEST_LAT,
    DEST_LON
)

print()
print("Getting real road route...")

route_data = get_real_route(
    START_LAT,
    START_LON,
    DEST_LAT,
    DEST_LON
)

if route_data:

    print(
        f"REAL DISTANCE: "
        f"{route_data['distance_km']} km"
    )

    print(
        f"REAL ROUTE TIME: "
        f"{route_data['duration_min']} min"
    )

else:

    print("Could not obtain real route.")

print()
print("Camera started.")
print("Press Q to quit.")
print()

# ==============================
# STATE
# ==============================

detection_count = 0
last_dashboard_update = 0

# ==============================
# MAIN LOOP
# ==============================

while True:

    ret, frame = cap.read()

    if not ret:

        print("Camera frame error.")
        break

    # ==================================
    # AMBULANCE DETECTION
    # ==================================

    ambulance_results = ambulance_model(
        frame,
        conf=AMBULANCE_CONFIDENCE,
        verbose=False
    )

    ambulance_found = False
    ambulance_confidence = 0

    for result in ambulance_results:

        boxes = result.boxes

        for box in boxes:

            cls_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            class_name = (
                ambulance_model.names[
                    cls_id
                ]
                .lower()
            )

            if class_name == "ambulance":

                ambulance_found = True

                ambulance_confidence = max(
                    ambulance_confidence,
                    confidence
                )

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3
                )

                cv2.putText(
                    frame,
                    f"AMBULANCE {confidence:.2f}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

    # ==================================
    # 3-FRAME CONFIRMATION
    # ==================================

    if ambulance_found:

        detection_count += 1

    else:

        detection_count = 0

    detection_count = min(
        detection_count,
        REQUIRED_FRAMES
    )

    emergency_active = (
        detection_count >= REQUIRED_FRAMES
    )

    # ==================================
    # GENERAL VEHICLE DETECTION
    # ==================================

    vehicle_counts = {

        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0
    }

    vehicle_results = vehicle_model(
        frame,
        conf=VEHICLE_CONFIDENCE,
        verbose=False
    )

    for result in vehicle_results:

        for box in result.boxes:

            cls_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            if cls_id not in VEHICLE_CLASSES:
                continue

            name = VEHICLE_CLASSES[
                cls_id
            ]

            vehicle_counts[name] += 1

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (255, 180, 0),
                2
            )

            cv2.putText(
                frame,
                f"{name} {confidence:.2f}",
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 180, 0),
                1
            )

    # ==================================
    # TRAFFIC
    # ==================================

    traffic_level, traffic_score = (
        calculate_traffic(
            vehicle_counts
        )
    )

    # ==================================
    # SEND TO DASHBOARD
    # ==================================

    current_time = time.time()

    if (
        current_time - last_dashboard_update
        >= 1
    ):

        update_dashboard(

            ambulance_detected=ambulance_found,

            confidence=ambulance_confidence,

            emergency_mode=emergency_active,

            vehicle_counts=vehicle_counts,

            traffic_level=traffic_level,

            traffic_score=traffic_score,

            route_data=route_data
        )

        last_dashboard_update = current_time

    # ==================================
    # CAMERA DISPLAY
    # ==================================

    if emergency_active:

        cv2.putText(
            frame,
            "EMERGENCY MODE ACTIVE",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        cv2.putText(
            frame,
            "SIGNAL PRIORITY: ACTIVE",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    elif detection_count > 0:

        cv2.putText(
            frame,
            f"VERIFYING AMBULANCE "
            f"{detection_count}/{REQUIRED_FRAMES}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

    else:

        cv2.putText(
            frame,
            "NORMAL TRAFFIC",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    # Vehicle counts

    y = 120

    for name, count in vehicle_counts.items():

        cv2.putText(
            frame,
            f"{name}: {count}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        y += 30

    cv2.putText(
        frame,
        f"TRAFFIC: {traffic_level}",
        (20, y + 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    # ==================================
    # SHOW
    # ==================================

    cv2.imshow(
        "RescueRoute AI - Real World",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


cap.release()

cv2.destroyAllWindows()

print("RescueRoute AI stopped.")