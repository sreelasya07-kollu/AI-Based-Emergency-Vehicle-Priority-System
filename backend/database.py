"""SQLite persistence for emergency alerts and signal events."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "rescue_route.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS emergency_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE,
            vehicle_type TEXT,
            location TEXT,
            destination TEXT,
            recommended_route TEXT,
            eta_minutes REAL,
            upcoming_signals INTEGER,
            traffic_density TEXT,
            direction TEXT,
            message TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS signal_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT,
            intersection TEXT,
            action TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS active_emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE,
            vehicle_type TEXT,
            current_location TEXT,
            destination TEXT,
            route TEXT,
            status TEXT DEFAULT 'active',
            updated_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def save_alert(alert_dict: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO emergency_alerts
        (alert_id, vehicle_type, location, destination, recommended_route,
         eta_minutes, upcoming_signals, traffic_density, direction, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert_dict["alert_id"],
            alert_dict["vehicle_type"],
            alert_dict["location"],
            alert_dict["destination"],
            alert_dict["recommended_route"],
            alert_dict["eta_minutes"],
            alert_dict["upcoming_signals"],
            alert_dict["traffic_density"],
            alert_dict.get("direction"),
            alert_dict["message"],
            alert_dict["timestamp"],
        ),
    )
    conn.commit()
    conn.close()


def save_active_emergency(alert_dict: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO active_emergencies
        (alert_id, vehicle_type, current_location, destination, route, status, updated_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
        """,
        (
            alert_dict["alert_id"],
            alert_dict["vehicle_type"],
            alert_dict["location"],
            alert_dict["destination"],
            alert_dict["recommended_route"],
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_recent_alerts(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM emergency_alerts ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_emergencies() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM active_emergencies WHERE status = 'active' ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
