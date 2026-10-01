"""Main RescueRoute AI pipeline orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_models.config import EMERGENCY_ICONS
from ai_models.traffic_analyzer import TrafficAnalyzer
from backend.database import init_db, save_active_emergency, save_alert
from backend.notification_service import NotificationService
from backend.route_planner import RoutePlanner, RouteResult

if TYPE_CHECKING:
    from ai_models.emergency_detection import EmergencyDetector


class RescueRoutePipeline:
    """
    End-to-end flow:
    Detect → Identify → Locate → Analyze Traffic → Route → Notify → Monitor
    """

    def __init__(self) -> None:
        self.traffic = TrafficAnalyzer()
        self.planner = RoutePlanner()
        self.notifier = NotificationService()
        self.active_routes: dict[str, RouteResult] = {}
        self._detector: EmergencyDetector | None = None

    @property
    def detector(self) -> "EmergencyDetector":
        if self._detector is None:
            from ai_models.emergency_detection import EmergencyDetector

            self._detector = EmergencyDetector()
        return self._detector

    def handle_detection_event(
        self,
        vehicle_type: str,
        location: str,
        origin: str = "A",
        destination: str | None = None,
        congestion: str = "Moderate",
        direction: str | None = None,
    ) -> dict:
        dest = self.planner.resolve_destination(vehicle_type, destination)
        route = self.planner.find_fastest_route(origin, dest, congestion)
        if not route:
            return {"error": "Could not compute route"}

        alert = self.notifier.create_alert(
            vehicle_type=vehicle_type,
            location=location,
            route=route,
            traffic_density=congestion,
            direction=direction,
        )
        save_alert(alert.to_dict())
        save_active_emergency(alert.to_dict())
        self.active_routes[alert.alert_id] = route

        signal_priority = self.notifier.get_signal_priority_list(route)
        self.notifier.print_alert(alert)

        return {
            "alert": alert.to_dict(),
            "route": {
                "path": route.path,
                "path_names": route.path_names,
                "eta_minutes": route.eta_minutes,
                "upcoming_signals": route.upcoming_signals,
            },
            "signal_priority": signal_priority,
        }

    def process_frame(
        self,
        frame_analysis,
        origin: str = "A",
        destination_override: str | None = None,
    ) -> dict | None:
        if not frame_analysis.emergency_vehicles:
            return None

        emergency = frame_analysis.emergency_vehicles[0]
        traffic_report = self.traffic.analyze(frame_analysis)

        return self.handle_detection_event(
            vehicle_type=emergency.class_name,
            location=f"Camera Zone ({emergency.center[0]}, {emergency.center[1]})",
            origin=origin,
            destination=destination_override,
            congestion=traffic_report.density,
            direction=frame_analysis.direction,
        )

    def monitor_and_reroute(
        self,
        alert_id: str,
        new_congestion: str,
        current_location: str,
    ) -> dict | None:
        old_route = self.active_routes.get(alert_id)
        if not old_route:
            return None

        new_route = self.planner.find_fastest_route(
            current_location, old_route.destination, new_congestion
        )
        if not new_route or new_route.path == old_route.path:
            return None

        alert = self.notifier.alert_history[-1] if self.notifier.alert_history else None
        if not alert:
            return None

        reroute = self.notifier.create_reroute_alert(
            vehicle_type=alert.vehicle_type,
            location=current_location,
            old_route=old_route,
            new_route=new_route,
            reason=f"Traffic changed to {new_congestion}",
        )
        save_alert(reroute.to_dict())
        self.active_routes[alert_id] = new_route
        self.notifier.print_alert(reroute)

        return {"alert": reroute.to_dict(), "new_route": new_route.path_names}

    def run_live(self, camera_source: str | int = 0, origin: str = "A") -> None:
        import cv2

        cap = cv2.VideoCapture(camera_source)
        prev_center = None
        active_alert_id: str | None = None

        print("🚑 RescueRoute AI — Live monitoring started (press Q to quit)")

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            analysis = self.detector.analyze_frame(frame, prev_center)
            if analysis.emergency_vehicles:
                prev_center = analysis.emergency_vehicles[0].center
                result = self.process_frame(analysis, origin=origin)
                if result:
                    active_alert_id = result["alert"]["alert_id"]
            elif active_alert_id and analysis.traffic_density == "Heavy":
                self.monitor_and_reroute(active_alert_id, "Heavy", origin)

            annotated = self.detector.draw_detections(frame, analysis.detections)
            cv2.imshow("RescueRoute AI", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


def demo():
    """Run a demo detection → route → notify cycle."""
    init_db()
    pipeline = RescueRoutePipeline()

    scenarios = [
        {"vehicle_type": "Ambulance", "location": "Intersection A", "origin": "A", "congestion": "Moderate"},
        {"vehicle_type": "Fire Engine", "location": "Intersection B", "origin": "B", "congestion": "Heavy"},
        {"vehicle_type": "Police Vehicle", "location": "Intersection C", "origin": "C", "congestion": "Low"},
    ]

    print("\n🚑 RescueRoute AI — Demo Mode\n")
    for scenario in scenarios:
        icon = EMERGENCY_ICONS.get(scenario["vehicle_type"], "🚨")
        print(f"\n--- Simulating {icon} {scenario['vehicle_type']} ---")
        pipeline.handle_detection_event(**scenario)


if __name__ == "__main__":
    demo()
