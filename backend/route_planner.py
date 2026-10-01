"""Graph-based fastest-route planner with traffic-aware edge weights."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from ai_models.config import PROJECT_ROOT


@dataclass
class RouteResult:
    origin: str
    destination: str
    path: list[str]
    path_names: list[str]
    total_distance_km: float
    eta_minutes: float
    upcoming_signals: int
    congestion_level: str


class RoutePlanner:
    """Finds least-congested routes through city intersections."""

    def __init__(self, map_path: Path | None = None) -> None:
        map_path = map_path or PROJECT_ROOT / "config" / "city_map.json"
        with open(map_path) as f:
            data = json.load(f)

        self.intersections = data["intersections"]
        self.roads = data["roads"]
        self.destinations = data.get("default_destinations", data.get("destinations", {}))
        self.avg_speed = data["avg_speed_kmh"]
        self.graph = self._build_graph()

    def _build_graph(self) -> dict[str, list[dict]]:
        graph: dict[str, list[dict]] = {node: [] for node in self.intersections}
        for road in self.roads:
            graph[road["from"]].append(road)
            graph[road["to"]].append(
                {
                    "from": road["to"],
                    "to": road["from"],
                    "distance_km": road["distance_km"],
                    "signals": road["signals"],
                }
            )
        return graph

    def _edge_weight(self, road: dict, congestion: str) -> float:
        speed = self.avg_speed.get(congestion, 30)
        travel_hours = road["distance_km"] / speed
        signal_penalty = road["signals"] * 0.5 / 60
        return travel_hours + signal_penalty

    def find_fastest_route(
        self,
        origin: str,
        destination: str,
        congestion: str = "Moderate",
    ) -> RouteResult | None:
        if origin not in self.intersections or destination not in self.intersections:
            return None

        dist: dict[str, float] = {node: math.inf for node in self.intersections}
        prev: dict[str, str | None] = {node: None for node in self.intersections}
        signals: dict[str, int] = {node: 0 for node in self.intersections}
        dist[origin] = 0.0

        visited: set[str] = set()
        while len(visited) < len(self.intersections):
            current = min(
                (n for n in self.intersections if n not in visited),
                key=lambda n: dist[n],
            )
            if dist[current] == math.inf:
                break
            visited.add(current)

            if current == destination:
                break

            for road in self.graph[current]:
                neighbor = road["to"]
                weight = self._edge_weight(road, congestion)
                alt = dist[current] + weight
                if alt < dist[neighbor]:
                    dist[neighbor] = alt
                    prev[neighbor] = current
                    signals[neighbor] = signals[current] + road["signals"]

        if prev[destination] is None and origin != destination:
            return None

        path: list[str] = []
        node: str | None = destination
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        total_distance = sum(
            r["distance_km"]
            for r in self.roads
            if any(path[i] == r["from"] and path[i + 1] == r["to"] for i in range(len(path) - 1))
        )

        speed = self.avg_speed.get(congestion, 30)
        eta = (total_distance / speed) * 60 + signals[destination] * 0.5

        return RouteResult(
            origin=origin,
            destination=destination,
            path=path,
            path_names=[self.intersections[p]["name"] for p in path],
            total_distance_km=round(total_distance, 2),
            eta_minutes=round(eta, 1),
            upcoming_signals=signals[destination],
            congestion_level=congestion,
        )

    def resolve_destination(self, vehicle_type: str, override: str | None = None) -> str:
        if override and override in self.intersections:
            return override
        return self.destinations.get(vehicle_type, "Hospital")

    def nearest_intersection(self, lat: float, lng: float) -> str:
        best, best_dist = "A", math.inf
        for key, node in self.intersections.items():
            d = (node["lat"] - lat) ** 2 + (node["lng"] - lng) ** 2
            if d < best_dist:
                best_dist = d
                best = key
        return best

    def route_to_string(self, route: RouteResult) -> str:
        return " → ".join(route.path_names)
