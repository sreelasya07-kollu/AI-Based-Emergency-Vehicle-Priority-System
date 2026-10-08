import os
import time

import cv2
import requests
from ultralytics import YOLO


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = os.getenv(
    "AMBULANCE_MODEL_PATH",
    "runs/detect/runs/ambulance_yolo11/weights/best.pt"
)

API_URL = os.getenv(
    "RESCUEROUTE_API",
    "http://127.0.0.1:5050/api/camera-detection"
)

AMBULANCE_ID = os.getenv(
    "AMBULANCE_ID",
    "AMB-102"
)

CONFIDENCE = 0.70

REQUIRED_FRAMES = 3


# ============================================================
# CAMERA LOCATION
# ============================================================

CAMERA_LAT = float(
    os.getenv(
        "CAMERA_LAT",
        "17.3850"
    )
)

CAMERA_LON = float(
    os.getenv(
        "CAMERA_LON",
        "78.4867"
    )
)


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "\nLoading ambulance YOLO model..."
)

model = YOLO(
    MODEL_PATH
)

print(
    "Model loaded:",
    MODEL_PATH
)

print(
    "Classes:",
    model.names
)


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(0)


if not cap.isOpened():

    raise SystemExit(
        "Camera could not be opened."
    )


# ============================================================
# VARIABLES
# ============================================================

hits = 0

last_post = 0

last_confirmed = False


print(
    "\n========================================"
)

print(
    "RESCUEROUTE AI LIVE DETECTION"
)

print(
    "========================================"
)

print(
    "Ambulance:",
    AMBULANCE_ID
)

print(
    "Confidence:",
    CONFIDENCE
)

print(
    "Required frames:",
    REQUIRED_FRAMES
)

print(
    "Backend:",
    API_URL
)

print(
    "Camera:",
    CAMERA_LAT,
    CAMERA_LON
)

print(
    "Press Q to quit."
)

print(
    "========================================\n"
)


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ok, frame = cap.read()


    if not ok:

        print(
            "Could not read camera frame."
        )

        break


    # --------------------------------------------------------
    # YOLO
    # --------------------------------------------------------

    results = model(
        frame,
        conf=CONFIDENCE,
        verbose=False
    )


    found = False

    best_confidence = 0.0


    # --------------------------------------------------------
    # DETECTION
    # --------------------------------------------------------

    for result in results:

        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            class_name = str(
                model.names.get(
                    class_id,
                    ""
                )
            ).lower()


            if class_name != "ambulance":

                continue


            found = True


            best_confidence = max(
                best_confidence,
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

                (
                    x1,
                    max(
                        30,
                        y1 - 10
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 0, 255),

                2
            )


    # --------------------------------------------------------
    # FRAME CONFIRMATION
    # --------------------------------------------------------

    if found:

        hits = min(

            REQUIRED_FRAMES,

            hits + 1
        )

    else:

        hits = 0


    confirmed = (
        hits >= REQUIRED_FRAMES
    )


    # --------------------------------------------------------
    # BACKEND UPDATE
    # --------------------------------------------------------

    now = time.time()


    if now - last_post >= 1:

        payload = {

            "ambulance_id":
                AMBULANCE_ID,

            "detected":
                confirmed,

            "confidence":
                best_confidence,

            "camera_lat":
                CAMERA_LAT,

            "camera_lng":
                CAMERA_LON
        }


        try:

            response = requests.post(

                API_URL,

                json=payload,

                timeout=2
            )


            if response.ok:

                if confirmed:

                    print(
                        f"🚨 EMERGENCY "
                        f"| {AMBULANCE_ID} "
                        f"| confidence="
                        f"{best_confidence:.2f}"
                    )

                else:

                    print(
                        "Camera:"
                        " no confirmed ambulance"
                    )

            else:

                print(
                    "Backend HTTP error:",
                    response.status_code
                )


        except requests.RequestException as error:

            print(
                "Backend connection error:",
                error
            )


        last_post = now


    # --------------------------------------------------------
    # DISPLAY STATUS
    # --------------------------------------------------------

    if confirmed:

        label = (
            "🚨 EMERGENCY CONFIRMED"
        )

        label_color = (
            0,
            0,
            255
        )

    elif hits:

        label = (
            f"VERIFYING "
            f"{hits}/{REQUIRED_FRAMES}"
        )

        label_color = (
            0,
            255,
            255
        )

    else:

        label = (
            "NO AMBULANCE"
        )

        label_color = (
            255,
            255,
            255
        )


    cv2.putText(

        frame,

        label,

        (20, 40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.9,

        label_color,

        2
    )


    cv2.putText(

        frame,

        f"ID: {AMBULANCE_ID}",

        (20, 75),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2
    )


    # --------------------------------------------------------
    # SHOW
    # --------------------------------------------------------

    cv2.imshow(

        "RescueRoute AI - YOLO Camera",

        frame
    )


    if (
        cv2.waitKey(1)
        &
        0xFF
        ==
        ord("q")
    ):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

print(
    "\nRescueRoute camera stopped."
)