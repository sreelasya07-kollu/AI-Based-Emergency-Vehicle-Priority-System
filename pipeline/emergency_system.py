import heapq
from datetime import datetime


# ============================================================
# 1. SIMULATED ROAD NETWORK
# ============================================================

ROAD_NETWORK = {
    "Junction E": {
        "Junction D": 4,
        "Junction C": 7
    },

    "Junction D": {
        "Junction E": 4,
        "Junction A": 3,
        "Junction B": 5
    },

    "Junction C": {
        "Junction E": 7,
        "Junction A": 6
    },

    "Junction B": {
        "Junction D": 5,
        "Junction A": 2
    },

    "Junction A": {
        "Junction D": 3,
        "Junction C": 6,
        "Junction B": 2,
        "Hospital": 4
    },

    "Hospital": {
        "Junction A": 4
    }
}


# ============================================================
# 2. DIJKSTRA SHORTEST PATH
# ============================================================

def find_fastest_route(graph, start, destination):

    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        if current_node == destination:
            break

        for neighbour, weight in graph[current_node].items():

            distance = current_distance + weight

            if distance < distances[neighbour]:

                distances[neighbour] = distance
                previous[neighbour] = current_node

                heapq.heappush(
                    priority_queue,
                    (distance, neighbour)
                )

    # Reconstruct route
    route = []

    current = destination

    while current is not None:
        route.append(current)
        current = previous[current]

    route.reverse()

    return route, distances[destination]


# ============================================================
# 3. TRAFFIC SIGNAL PRIORITY
# ============================================================

def activate_signal_priority(route):

    print("\n🚦 SIGNAL PRIORITY")

    # Ignore Hospital because it is not a junction
    junctions = [
        node for node in route
        if "Junction" in node
    ]

    if junctions:

        recommended = junctions[0]

        print(f"🟢 Recommended GREEN: {recommended}")
        print("🚑 Emergency vehicle priority: ON")

    else:

        recommended = None
        print("No junction priority required.")

    return recommended


# ============================================================
# 4. EMERGENCY DECISION
# ============================================================

def emergency_response(ambulance_detected, confidence):

    print("\n" + "=" * 55)
    print("        🚑 RESCUEROUTE AI EMERGENCY SYSTEM")
    print("=" * 55)

    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"Time: {timestamp}")

    print(f"\nAmbulance detected: {ambulance_detected}")
    print(f"Confidence: {confidence:.2f}")

    if not ambulance_detected:

        print("\n🟢 STATUS: NORMAL TRAFFIC")
        print("Emergency mode: OFF")

        return

    # --------------------------------------------------------
    # Emergency detected
    # --------------------------------------------------------

    print("\n🔴 STATUS: EMERGENCY VEHICLE DETECTED")
    print("🚨 Emergency Mode: ON")
    print("🚑 Ambulance priority activated")

    # Route calculation
    start = "Junction E"
    destination = "Hospital"

    route, distance = find_fastest_route(
        ROAD_NETWORK,
        start,
        destination
    )

    print("\n🗺️ FASTEST ROUTE")

    print(" → ".join(route))

    print(f"\nEstimated route cost: {distance}")

    # Signal priority
    recommended_junction = activate_signal_priority(route)

    # ETA simulation
    eta = max(1, int(distance * 1.5))

    print("\n⏱️ ESTIMATED ETA")

    print(f"{eta} minutes")

    print("\n📊 DASHBOARD STATUS")

    print("----------------------------------------")
    print("Vehicle        : Ambulance")
    print("Detection      : CONFIRMED")
    print(f"Confidence     : {confidence:.2f}")
    print("Emergency Mode : ON")
    print("Route          : " + " → ".join(route))
    print(f"ETA            : {eta} minutes")
    print("Signal Priority: ON")
    print(
        "Green Junction: "
        + str(recommended_junction)
    )
    print("----------------------------------------")


# ============================================================
# 5. DEMO
# ============================================================

if __name__ == "__main__":

    # Simulated YOLO result for now
    ambulance_detected = True
    confidence = 0.91

    emergency_response(
        ambulance_detected,
        confidence
    )
