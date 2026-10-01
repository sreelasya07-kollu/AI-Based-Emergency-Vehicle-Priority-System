"""Traffic control center notification service."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime

from ai_models.config import EMERGENCY_ICONS
from backend.route_planner import RouteResult


@dataclass
class EmergencyAlert:
    alert_id: str
    vehicle_type: str
    location: str
    destination: str
    recommended_route: str
    eta_minutes: float
    upcoming_signals: int
    traffic_density: str
    direction: str | None
    timestamp: str
    action_required: bool = True
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class NotificationService:
    """Formats and dispatches alerts to the traffic control center."""

    def __init__(self) -> None:
        self._alert_counter = 0
        self.alert_history: list[EmergencyAlert] = []

    def _next_id(self) -> str:
        self._alert_counter += 1
        return f"EV-{self._alert_counter:04d}"

    def create_alert(
        self,
        vehicle_type: str,
        location: str,
        route: RouteResult,
        traffic_density: str,
        direction: str | None = None,
    ) -> EmergencyAlert:
        icon = EMERGENCY_ICONS.get(vehicle_type, "🚨")
        route_str = " → ".join(route.path_names)

        message = (
            f"{icon} EMERGENCY VEHICLE DETECTED\n"
            f"Type: {vehicle_type}\n"
            f"Location: {location}\n"
            f"Destination: {route.path_names[-1]}\n"
            f"Recommended Route: {route_str}\n"
            f"ETA: {route.eta_minutes} minutes\n"
            f"Upcoming Signals: {route.upcoming_signals}\n"
            f"Traffic: {traffic_density}\n"
            f"⚠️ Traffic Control Action Required"
        )

        alert = EmergencyAlert(
            alert_id=self._next_id(),
            vehicle_type=vehicle_type,
            location=location,
            destination=route.path_names[-1],
            recommended_route=route_str,
            eta_minutes=route.eta_minutes,
            upcoming_signals=route.upcoming_signals,
            traffic_density=traffic_density,
            direction=direction,
            timestamp=datetime.now().isoformat(),
            message=message,
        )
        self.alert_history.append(alert)
        return alert

    def create_reroute_alert(
        self,
        vehicle_type: str,
        location: str,
        old_route: RouteResult,
        new_route: RouteResult,
        reason: str,
    ) -> EmergencyAlert:
        alert = self.create_alert(vehicle_type, location, new_route, new_route.congestion_level)
        alert.message = (
            f"🔄 ROUTE UPDATE — {vehicle_type}\n"
            f"Reason: {reason}\n"
            f"Previous: {' → '.join(old_route.path_names)}\n"
            f"New Route: {' → '.join(new_route.path_names)}\n"
            f"New ETA: {new_route.eta_minutes} min\n"
            f"⚠️ Update signal priority for new corridor"
        )
        return alert

    def get_signal_priority_list(self, route: RouteResult) -> list[dict]:
        """Returns intersections where signals should turn green."""
        return [
            {
                "intersection": node,
                "name": route.path_names[i],
                "priority": "GREEN",
                "order": i + 1,
            }
            for i, node in enumerate(route.path)
        ]

    def print_alert(self, alert: EmergencyAlert) -> None:
        print("\n" + "=" * 50)
        print(alert.message)
        print("=" * 50)
