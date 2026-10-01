from ultralytics import YOLO
import cv2

MODEL_PATH = "yolo11n.pt"

print("Loading YOLO11n...")
model = YOLO(MODEL_PATH)

print("Opening camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera could not be opened.")
    exit()

print("Camera opened successfully!")
print("Human detection started.")
print("Press Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not read camera frame.")
        break

    results = model(frame, conf=0.35, classes=[0])

    annotated = results[0].plot()

    cv2.imshow("RescueRoute AI - Human Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print("Human detection completed.")
