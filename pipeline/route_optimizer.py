import heapq

# Road network
# Each connection has a travel-time cost in minutes
GRAPH = {
    "Hospital": {
        "Junction_A": 4,
        "Junction_B": 7
    },
    "Junction_A": {
        "Hospital": 4,
        "Junction_C": 3,
        "Junction_D": 6
    },
    "Junction_B": {
        "Hospital": 7,
        "Junction_D": 2,
        "Junction_E": 4
    },
    "Junction_C": {
        "Junction_A": 3,
        "Junction_D": 2
    },
    "Junction_D": {
        "Junction_A": 6,
        "Junction_B": 2,
        "Junction_C": 2,
        "Junction_E": 3
    },
    "Junction_E": {
        "Junction_B": 4,
        "Junction_D": 3
    }
}


def dijkstra(graph, start, destination):
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

        for neighbor, travel_time in graph[current_node].items():
            new_distance = current_distance + travel_time

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node
                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor)
                )

    # Reconstruct route
    route = []
    current = destination

    while current is not None:
        route.append(current)
        current = previous[current]

    route.reverse()

    return route, distances[destination]


if __name__ == "__main__":
    start = "Junction_E"
    destination = "Hospital"

    route, time = dijkstra(GRAPH, start, destination)

    print("\n===== RESCUEROUTE AI =====")
    print("Emergency Vehicle: Ambulance")
    print("Starting Location:", start)
    print("Destination:", destination)
    print("Fastest Route:", " -> ".join(route))
    print("Estimated Travel Time:", time, "minutes")
