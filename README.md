# RescueRoute AI

AI-based emergency vehicle corridor management system. Detects ambulances, fire engines, and police vehicles using YOLO, calculates the fastest route, and notifies the traffic control center to create a green corridor.

## System Flow

```
Camera Feed → YOLO Detection → Emergency Identified → Traffic Analysis
    → Fastest Route → Map Display → Control Center Notification → Signal Priority
```

## ML Classes

| Class | Role |
|-------|------|
| Ambulance | Emergency |
| Fire Engine | Emergency |
| Police Vehicle | Emergency |
| Car, Bus, Truck, Motorcycle | Traffic context |

## Setup

```bash
cd RescueRouteAI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Train YOLO Models

```bash
python ai_models/train_emergency.py    # Ambulance, Fire Truck, Police
python ai_models/train_vehicles.py     # All vehicle types
```

## Run

```bash
python main.py demo      # Simulate emergency scenarios
python main.py server    # Web dashboard at http://localhost:5000
python main.py live      # Live camera detection
```

## Tech Stack

YOLO11, OpenCV, Flask, SQLite, Leaflet
