import overpy
import pandas as pd
import json
import requests
import math
import heapq
import folium
from geopy.geocoders import Nominatim


# ---------------- Haversine ----------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ---------------- Build Graph ----------------
def build_graph_from_json(json_data):
    nodes = {}
    graph = {}

    for el in json_data['elements']:
        if el['type'] == 'node':
            nodes[el['id']] = (el['lat'], el['lon'])

    for el in json_data['elements']:
        if el['type'] == 'way' and 'nodes' in el:
            way_nodes = el['nodes']
            
            tags = el.get('tags', {})
            oneway = tags.get('oneway', 'no')
            
            for i in range(len(way_nodes) - 1):
                n1, n2 = way_nodes[i], way_nodes[i + 1]
                if n1 in nodes and n2 in nodes:
                    dist = haversine(*nodes[n1], *nodes[n2])
                    graph.setdefault(n1, []).append((n2, dist)) # create adjency list
                    if oneway not in ['yes']:
                        graph.setdefault(n2, []).append((n1, dist))  # hai chiều
    return nodes, graph

# ---------------- Find nearest node ----------------
def find_nearest_node(lat, lon, nodes):
    nearest = None
    min_dist = float("inf")
    for nid, (nlat, nlon) in nodes.items():
        d = haversine(lat, lon, nlat, nlon)
        if d < min_dist:
            min_dist, nearest = d, nid
    return nearest

# ---------------- A* (A-star) ----------------
def astar(graph, nodes, start, end):
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: haversine(*nodes[start], *nodes[end])}
    visited = set()

    while open_set:
        # Lấy node có f_score nhỏ nhất
        _, current = heapq.heappop(open_set)
        if current in visited:
            continue
        visited.add(current)

        # Nếu đến đích -> truy vết đường đi
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return g_score[end], path

        # Duyệt các node kề
        for neighbor, weight in graph.get(current, []):
            tentative_g = g_score[current] + weight
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + haversine(*nodes[neighbor], *nodes[end])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return float("inf"), []

# ---------------- Shortest path ----------------
def find_shortest_path(start_lat, start_lon, end_lat, end_lon, nodes, graph):

    start_node = find_nearest_node(start_lat, start_lon, nodes)
    end_node = find_nearest_node(end_lat, end_lon, nodes)

    distance, path = astar(graph, nodes, start_node, end_node)

    if not path:
        print("❌ Not found path.")
        print(f"Start: {start_lat}, {start_lon}")
        print(f"Des: {end_lat}, {end_lon}")

        return []

    coords = [(nodes[nid][0], nodes[nid][1]) for nid in path]

    return coords
