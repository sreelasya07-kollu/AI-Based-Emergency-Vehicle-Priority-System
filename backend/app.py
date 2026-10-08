import os
import asyncio
from typing import Dict, Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


load_dotenv()


app = FastAPI(
    title="RescueRoute AI",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GOOGLE_MAPS_API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY",
    ""
)


# ============================================================
# DEMO USERS
# ============================================================

USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },

    "traffic": {
        "password": "traffic123",
        "role": "traffic"
    },

    "hospital1": {
        "password": "hospital123",
        "role": "hospital",
        "hospital_id": "HOSP-001",
        "hospital_name": "City Care Hospital"
    },

    "hospital2": {
        "password": "hospital123",
        "role": "hospital",
        "hospital_id": "HOSP-002",
        "hospital_name": "Metro Emergency Hospital"
    },

    "AMB-101": {
        "password": "driver123",
        "role": "driver",
        "ambulance_id": "AMB-101"
    },

    "AMB-102": {
        "password": "driver123",
        "role": "driver",
        "ambulance_id": "AMB-102"
    },

    "AMB-103": {
        "password": "driver123",
        "role": "driver",
        "ambulance_id": "AMB-103"
    },

    "AMB-104": {
        "password": "driver123",
        "role": "driver",
        "ambulance_id": "AMB-104"
    }
}


# ============================================================
# LIVE AMBULANCE DATA
# ============================================================

ambulances: Dict[str, Dict[str, Any]] = {

    "AMB-101": {
        "ambulance_id": "AMB-101",
        "hospital_id": "HOSP-001",
        "hospital_name": "City Care Hospital",
        "driver": "Driver 101",

        "status": "AVAILABLE",
        "emergency": False,

        "lat": 17.3850,
        "lng": 78.4867,

        "destination": "City Care Hospital",

        "eta": "--",
        "distance_km": 0,

        "speed": 0,
        "confidence": 0,

        "signal_priority": False,

        "route": [],
        "route_polyline": "",

        "last_camera_lat": None,
        "last_camera_lng": None
    },

    "AMB-102": {
        "ambulance_id": "AMB-102",
        "hospital_id": "HOSP-001",
        "hospital_name": "City Care Hospital",
        "driver": "Driver 102",

        "status": "AVAILABLE",
        "emergency": False,

        "lat": 17.3984,
        "lng": 78.4800,

        "destination": "City Care Hospital",

        "eta": "--",
        "distance_km": 0,

        "speed": 0,
        "confidence": 0,

        "signal_priority": False,

        "route": [],
        "route_polyline": "",

        "last_camera_lat": None,
        "last_camera_lng": None
    },

    "AMB-103": {
        "ambulance_id": "AMB-103",
        "hospital_id": "HOSP-002",
        "hospital_name": "Metro Emergency Hospital",
        "driver": "Driver 103",

        "status": "AVAILABLE",
        "emergency": False,

        "lat": 17.4100,
        "lng": 78.4900,

        "destination": "Metro Emergency Hospital",

        "eta": "--",
        "distance_km": 0,

        "speed": 0,
        "confidence": 0,

        "signal_priority": False,

        "route": [],
        "route_polyline": "",

        "last_camera_lat": None,
        "last_camera_lng": None
    },

    "AMB-104": {
        "ambulance_id": "AMB-104",
        "hospital_id": "HOSP-002",
        "hospital_name": "Metro Emergency Hospital",
        "driver": "Driver 104",

        "status": "AVAILABLE",
        "emergency": False,

        "lat": 17.3600,
        "lng": 78.5000,

        "destination": "Metro Emergency Hospital",

        "eta": "--",
        "distance_km": 0,

        "speed": 0,
        "confidence": 0,

        "signal_priority": False,

        "route": [],
        "route_polyline": "",

        "last_camera_lat": None,
        "last_camera_lng": None
    }
}


# ============================================================
# TRAFFIC SIGNALS
# ============================================================

signals = {

    "SIGNAL-001": {
        "signal_id": "SIGNAL-001",
        "name": "Main Junction",
        "lat": 17.3900,
        "lng": 78.4850,
        "status": "RED",
        "priority_for": None
    },

    "SIGNAL-002": {
        "signal_id": "SIGNAL-002",
        "name": "Central Junction",
        "lat": 17.4000,
        "lng": 78.4900,
        "status": "RED",
        "priority_for": None
    },

    "SIGNAL-003": {
        "signal_id": "SIGNAL-003",
        "name": "Hospital Junction",
        "lat": 17.3750,
        "lng": 78.4950,
        "status": "RED",
        "priority_for": None
    }
}


# ============================================================
# WEBSOCKET MANAGER
# ============================================================

class ConnectionManager:

    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):

        await websocket.accept()

        self.connections.append(websocket)

        await self.send_state(websocket)

    def disconnect(self, websocket: WebSocket):

        if websocket in self.connections:
            self.connections.remove(websocket)

    async def send_state(self, websocket: WebSocket):

        await websocket.send_json({
            "type": "state",
            "ambulances": list(ambulances.values()),
            "signals": list(signals.values())
        })

    async def broadcast(self):

        message = {
            "type": "state",
            "ambulances": list(ambulances.values()),
            "signals": list(signals.values())
        }

        dead = []

        for websocket in self.connections:

            try:

                await websocket.send_json(message)

            except Exception:

                dead.append(websocket)

        for websocket in dead:

            self.disconnect(websocket)


manager = ConnectionManager()


# ============================================================
# REQUEST MODELS
# ============================================================

class LoginRequest(BaseModel):

    username: str
    password: str


class LocationRequest(BaseModel):

    ambulance_id: str

    lat: float
    lng: float

    speed: float = 0


class EmergencyRequest(BaseModel):

    ambulance_id: str

    emergency: bool


class CameraDetectionRequest(BaseModel):

    ambulance_id: str

    detected: bool

    confidence: float

    camera_lat: float

    camera_lng: float


class SignalRequest(BaseModel):

    signal_id: str

    status: str

    ambulance_id: str | None = None


class RouteRequest(BaseModel):

    ambulance_id: str

    origin_lat: float
    origin_lng: float

    destination_lat: float
    destination_lng: float


# ============================================================
# BASIC API
# ============================================================

@app.get("/")
async def root():

    return {
        "name": "RescueRoute AI",
        "status": "running",
        "version": "2.0"
    }


@app.get("/api/health")
async def health():

    return {
        "status": "healthy",
        "ambulances": len(ambulances),
        "signals": len(signals),
        "websocket_clients": len(manager.connections)
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
async def login(data: LoginRequest):

    user = USERS.get(data.username)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if user["password"] != data.password:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    return {
        "success": True,
        "username": data.username,
        "role": user["role"],

        "hospital_id": user.get(
            "hospital_id"
        ),

        "hospital_name": user.get(
            "hospital_name"
        ),

        "ambulance_id": user.get(
            "ambulance_id"
        )
    }


# ============================================================
# GET AMBULANCES
# ============================================================

@app.get("/api/ambulances")
async def get_ambulances():

    return {
        "ambulances": list(
            ambulances.values()
        )
    }


@app.get("/api/ambulances/{ambulance_id}")
async def get_ambulance(
    ambulance_id: str
):

    ambulance = ambulances.get(
        ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    return ambulance


# ============================================================
# DRIVER GPS LOCATION
# ============================================================

@app.post("/api/location")
async def update_location(
    data: LocationRequest
):

    ambulance = ambulances.get(
        data.ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    ambulance["lat"] = data.lat
    ambulance["lng"] = data.lng
    ambulance["speed"] = data.speed

    await manager.broadcast()

    return {
        "success": True,
        "ambulance": ambulance
    }


# ============================================================
# MANUAL EMERGENCY
# ============================================================

@app.post("/api/emergency")
async def update_emergency(
    data: EmergencyRequest
):

    ambulance = ambulances.get(
        data.ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    ambulance["emergency"] = data.emergency

    if data.emergency:

        ambulance["status"] = "EMERGENCY"
        ambulance["signal_priority"] = True

    else:

        ambulance["status"] = "AVAILABLE"
        ambulance["signal_priority"] = False

    await manager.broadcast()

    return {
        "success": True,
        "ambulance": ambulance
    }


# ============================================================
# CAMERA AI DETECTION
# ============================================================

@app.post("/api/camera-detection")
async def camera_detection(
    data: CameraDetectionRequest
):

    ambulance = ambulances.get(
        data.ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    # Store camera location

    ambulance["last_camera_lat"] = (
        data.camera_lat
    )

    ambulance["last_camera_lng"] = (
        data.camera_lng
    )

    # Camera detection location

    ambulance["lat"] = data.camera_lat
    ambulance["lng"] = data.camera_lng

    ambulance["confidence"] = (
        data.confidence
    )

    # --------------------------------------------------------
    # EMERGENCY CONFIRMED
    # --------------------------------------------------------

    if (
        data.detected
        and data.confidence >= 0.70
    ):

        ambulance["emergency"] = True

        ambulance["status"] = "EMERGENCY"

        ambulance["signal_priority"] = True

        # Automatically prioritize nearby signals

        for signal in signals.values():

            distance = (
                abs(
                    signal["lat"]
                    - ambulance["lat"]
                )
                +
                abs(
                    signal["lng"]
                    - ambulance["lng"]
                )
            )

            if distance < 0.015:

                signal["status"] = "GREEN"

                signal["priority_for"] = (
                    data.ambulance_id
                )

    # --------------------------------------------------------
    # NO CONFIRMED AMBULANCE
    # --------------------------------------------------------

    else:

        # Don't immediately clear an active emergency
        # if the camera temporarily loses the ambulance.

        pass

    await manager.broadcast()

    return {
        "success": True,
        "detected": data.detected,
        "confidence": data.confidence,
        "ambulance": ambulance
    }


# ============================================================
# GOOGLE ROUTES API
# ============================================================

async def calculate_google_route(
    origin_lat,
    origin_lng,
    destination_lat,
    destination_lng
):

    if not GOOGLE_MAPS_API_KEY:

        return {
            "success": False,
            "message": "GOOGLE_MAPS_API_KEY not configured"
        }

    url = (
        "https://routes.googleapis.com/"
        "directions/v2:computeRoutes"
    )

    headers = {

        "Content-Type":
            "application/json",

        "X-Goog-Api-Key":
            GOOGLE_MAPS_API_KEY,

        "X-Goog-FieldMask":
            "routes.duration,"
            "routes.distanceMeters,"
            "routes.polyline.encodedPolyline"
    }

    body = {

        "origin": {

            "location": {

                "latLng": {

                    "latitude":
                        origin_lat,

                    "longitude":
                        origin_lng
                }
            }
        },

        "destination": {

            "location": {

                "latLng": {

                    "latitude":
                        destination_lat,

                    "longitude":
                        destination_lng
                }
            }
        },

        "travelMode":
            "DRIVE",

        "routingPreference":
            "TRAFFIC_AWARE",

        "computeAlternativeRoutes":
            False
    }

    async with httpx.AsyncClient(
        timeout=10
    ) as client:

        response = await client.post(
            url,
            headers=headers,
            json=body
        )

    if response.status_code != 200:

        return {
            "success": False,
            "message": response.text
        }

    data = response.json()

    routes = data.get(
        "routes",
        []
    )

    if not routes:

        return {
            "success": False,
            "message": "No route found"
        }

    route = routes[0]

    duration = route.get(
        "duration",
        "0s"
    )

    distance_meters = route.get(
        "distanceMeters",
        0
    )

    polyline = (
        route
        .get("polyline", {})
        .get("encodedPolyline", "")
    )

    return {

        "success": True,

        "duration": duration,

        "distance_km":
            round(
                distance_meters / 1000,
                2
            ),

        "polyline":
            polyline
    }


@app.post("/api/route")
async def calculate_route(
    data: RouteRequest
):

    ambulance = ambulances.get(
        data.ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    route = await calculate_google_route(
        data.origin_lat,
        data.origin_lng,
        data.destination_lat,
        data.destination_lng
    )

    if not route["success"]:

        return route

    ambulance["eta"] = (
        route["duration"]
    )

    ambulance["distance_km"] = (
        route["distance_km"]
    )

    ambulance["route_polyline"] = (
        route["polyline"]
    )

    ambulance["lat"] = data.origin_lat
    ambulance["lng"] = data.origin_lng

    await manager.broadcast()

    return {
        "success": True,
        "ambulance": ambulance,
        "route": route
    }


# ============================================================
# TRAFFIC SIGNAL CONTROL
# ============================================================

@app.post("/api/signal")
async def update_signal(
    data: SignalRequest
):

    signal = signals.get(
        data.signal_id
    )

    if not signal:

        raise HTTPException(
            status_code=404,
            detail="Signal not found"
        )

    status = data.status.upper()

    if status not in [
        "GREEN",
        "RED",
        "YELLOW"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid signal status"
        )

    signal["status"] = status

    signal["priority_for"] = (
        data.ambulance_id
    )

    await manager.broadcast()

    return {
        "success": True,
        "signal": signal
    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await manager.connect(
        websocket
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(
            websocket
        )

    except Exception:

        manager.disconnect(
            websocket
        )


# ============================================================
# PERIODIC LIVE BROADCAST
# ============================================================

async def broadcaster():

    while True:

        await asyncio.sleep(2)

        if manager.connections:

            await manager.broadcast()


@app.on_event("startup")
async def startup_event():

    asyncio.create_task(
        broadcaster()
    )