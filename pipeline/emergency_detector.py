from ultralytics import YOLO
import cv2

MODEL_PATH = "runs/detect/runs/emergency_test/weights/best.pt"

print("Loading ambulance model...")
model = YOLO(MODEL_PATH)

print("Opening camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera could not be opened.")
    exit()

print("Camera opened successfully!")
print("Ambulance detection started.")
print("Press Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not read camera frame.")
        break

    results = model(frame, conf=0.25)

    annotated = results[0].plot()

    cv2.imshow("RescueRoute AI - Ambulance Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print("Ambulance detection completed.")
