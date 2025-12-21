import pandas as pd
import networkx as nx
import heapq
import math
import requests
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

# --------------------------------------------------------------
def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def nearby_stops(coord, stops_df, max_dist):
    res = []
    for sid, row in stops_df.iterrows():
        d = haversine(coord, (row["lat"], row["lng"]))
        if d <= max_dist:
            res.append((sid, d))
    return res

def make_heuristic(stops_df, dest_coord, speed):
    def h(sid):
        sc = (stops_df.loc[sid, "lat"], stops_df.loc[sid, "lng"])
        return haversine(sc, dest_coord) / speed
    return h


def a_star(G, route_info, stops, start_stops, dest_stop_set, heuristic,
                speed, walk_speed, c, p):
    """
    p = transfer penalty multiplier (3.0 = strong preference for no transfer)
    """
    open_set = []
    came_from = {}
    g_score = defaultdict(lambda: float('inf'))
    cum_fare = {}
    cum_wait = {}
    special_stops = {} #used to store first stop _ transfered stop _ last stop
    counter = 0

    for sid, walk_m in start_stops:
        state = (sid, None)
        g = walk_m / walk_speed
        g_score[state] = g
        f = g + heuristic(sid)
        heapq.heappush(open_set, (f, counter, state))
        came_from[state] = None
        cum_fare[state] = 0
        cum_wait[state] = 0
        special_stops[state] = []
        counter += 1

    while open_set:
        _, _, current = heapq.heappop(open_set)
        stop, cur_route = current

        # === EARLY EXIT: if we reach a dest stop AND continuing is worse ===
        if stop in dest_stop_set:
            # Heuristic: straight-line to dest
            h_to_dest = heuristic(stop)
            current_to_dest = g_score[current] + h_to_dest

            # If any node in open_set has f >= current_to_dest → no better path
            if open_set and open_set[0][0] >= current_to_dest:
                # Reconstruct and return
                path = []
                routes_used = []
                current_state = current
                current_stop, current_route = current_state
                best_stop = current_stop
                best_h = heuristic(current_stop)

                # Only extend if we're actually on a bus (not walking)
                if current_route not in (None, "0"):
                    temp_state = current_state
                    while True:
                        extended = False
                        for _, nei, key, data in G.out_edges(best_stop, data=True, keys=True):
                            if data["route"] != current_route:
                                continue
                            nei_h = heuristic(nei)
                            if nei_h < best_h:
                                # Found better (closer) stop on same route
                                dist = data["distance"]
                                new_g = g_score[temp_state] + dist / speed
                                new_state = (nei, current_route)
                                # Update best
                                best_stop = nei
                                best_h = nei_h
                                g_score[new_state] = new_g
                                came_from[new_state] = temp_state
                                temp_state = new_state
                                extended = True
                                break # only one outgoing edge per route usually
                        if not extended: break
                    
                # Now use the best (closest) stop on this route
                final_state = temp_state
                final_stop = best_stop
                final_h = best_h

                # === PHASE 2: Reconstruct full path from final_state ===
                path = []
                routes_used = []
                state = final_state
                while state is not None:
                    s, r = state
                    path.append(s)
                    if r is not None:
                        routes_used.append(r)
                    state = came_from.get(state)

                path.reverse()
                routes_used.reverse()

                # special stops: use the ones from original arrival + final stop
                final_special = special_stops[current] + [final_stop]


                # list name of used route
                uniqueName_Route_used = []
                uniqueBus_Number_used = []
                
                last = None

                for route_id in routes_used:
                    if route_id == last:
                        continue   # skip duplicate consecutive values

                    last = route_id

                    if route_id is None:
                        continue

                    if route_id == "0":
                        uniqueName_Route_used.append("walk")
                        uniqueBus_Number_used.append("walk")
                        continue
                    
                    row = route_info[route_id]
                    uniqueName_Route_used.append(row["trip_name"])
                    uniqueBus_Number_used.append(row["bus_number"])

                # total_fare = cum_fare[current]
                # total_wait_sec = cum_wait[current]

                # worst_sec = g_score[final_state] - c * total_fare - (p - 1)* total_wait_sec + final_h / walk_speed
                # best_sec = worst_sec - total_wait_sec


                total_fare     = cum_fare[current]
                total_wait_sec = cum_wait[current]
                g_at_arrival   = g_score[current]                  # includes penalties
                g_at_final     = g_score[final_state]              # higher due to riding

                print(f"g_at_arrival: {g_at_arrival}")
                print(f"total_wait_sec: {total_wait_sec}, p: {p}, Penalty Wait: {p * total_wait_sec}")
                print(f"total_fare: {total_fare}, c: {c}, Penalty Fare: {c * total_fare}")

                # Extract real travel time up to first dest stop
                real_time_at_arrival = g_at_arrival - p  * total_wait_sec - c * total_fare

                # Add the free extra riding time
                extra_riding_time = g_at_final - g_at_arrival
                real_time_at_final = real_time_at_arrival + extra_riding_time

                remaining_walk = final_h / walk_speed

                best_sec  = real_time_at_final + remaining_walk
                worst_sec = best_sec + total_wait_sec

                print(f"Best: {best_sec/60:.1f} min, Worst: {worst_sec/60:.1f} min")


                return {
                        "coords": path,
                        "best_min": best_sec / 60,
                        "worst_min": worst_sec / 60,
                        "total_fare": total_fare,
                        "unique_Routes" : uniqueName_Route_used,
                        "unique_BusNumbers": uniqueBus_Number_used,
                        "special_stops": final_special
                    }

        if stop not in G:
            continue

        for u, nei, key, data in G.out_edges(stop, data=True, keys=True):
            dist = data["distance"]
            new_route = data["route"]

            wait = 0.0
            fare_add = 0
            if new_route == "0":   # walking edge
                if cur_route == "0": continue # prevent consecutive walking 
                tentative_g = g_score[current] + dist/walk_speed
            else:
                # transfer or new bus route
                if cur_route is None or cur_route != new_route:
                    fare_add = route_info[new_route]["fare"]
                    wait = route_info[new_route]["headway_sec"]
                tentative_g = g_score[current] + dist/speed + wait * p + c * fare_add

            new_state = (nei, new_route)
            if tentative_g < g_score[new_state]:
                came_from[new_state] = current
                g_score[new_state] = tentative_g
                cum_fare[new_state] = cum_fare[current] + fare_add
                cum_wait[new_state] = cum_wait[current] + wait
                f = tentative_g + heuristic(nei)

                if new_route == "0" or (cur_route is None or cur_route != new_route): special_stops[new_state] = special_stops[current] + [stop]
                else : special_stops[new_state] = list(special_stops[current])

                heapq.heappush(open_set, (f, counter, new_state))
                counter += 1

    return {}

def calculate_First_Last_walkingCoords(start_coord, dest_coord, stops_df,
             path):
    
    print("Drawing map...")
    if not path:
        return

    # === 1. Walk to first stop ===
    # first_stop_coord = (float(stops_df.loc[path[0], "lat"]), float(stops_df.loc[path[0], "lng"]))

    start_coord = {
                "lat": start_coord[0],
                "lon": start_coord[1]}
    dest_coord = {
                "lat": dest_coord[0],
                "lon": dest_coord[1]}

    first_stop_coord = {
                "lat": stops_df.loc[path[0], "lat"],
                "lon": stops_df.loc[path[0], "lng"]
                }
    
    # walk_to_bus = find_shortest_path(
    #     start_coord[0], start_coord[1],
    #     first_stop_coord[0], first_stop_coord[1],
    #     Walk_nodes, Walk_graph
    # )
    walk_to_bus = calculate_route(start_coord, first_stop_coord, travel_mode="pedestrian")["coords"]


    # === 3. Final walk ===
    # last_stop_coord = (float(stops_df.loc[path[-1], "lat"]), float(stops_df.loc[path[-1], "lng"]))
    last_stop_coord = {
                "lat": stops_df.loc[path[-1], "lat"],
                "lon": stops_df.loc[path[-1], "lng"]
                }
    # walk_to_dest = find_shortest_path(
    #     last_stop_coord[0], last_stop_coord[1],
    #     dest_coord[0], dest_coord[1],
    #     Walk_nodes, Walk_graph
    # )
    walk_to_dest = calculate_route(last_stop_coord, dest_coord, travel_mode="pedestrian")["coords"]
   

        
    return walk_to_bus, walk_to_dest 

def calculate_transfer_walkingCoords(special_stops, stop_df, unique_BusNumbers, walk_to_bus, walk_to_des):
    special_stops_name = []
    special_stops_coords = []
    walk_coords = []

    for i in range(len(special_stops)):
        stop_id = special_stops[i]

        # Add the name normally
        special_stops_name.append(stop_df.loc[stop_id, "stopName"])

        # Skip first and last → no car segment
        if i == 0:
            continue

        start_coord = {
                "lat": stop_df.loc[special_stops[i - 1], "lat"],
                "lon": stop_df.loc[special_stops[i - 1], "lng"]
                }

        end_coord = {
                "lat": stop_df.loc[special_stops[i], "lat"],
                "lon": stop_df.loc[special_stops[i], "lng"]
                }
        
        if(unique_BusNumbers[i - 1] == "walk"):

            # coords = find_shortest_path(start_coord["lat"],
            #                              start_coord["lon"], 
            #                              end_coord["lat"], 
            #                              end_coord["lon"], 
            #                              Walk_nodes,
            #                              Walk_graph)
            coords = calculate_route(start_coord, end_coord, travel_mode="pedestrian")["coords"]
            walk_coords.append(coords)

            continue

        # Compute car path between previous stop → current stop
        coords = calculate_route(start_coord, end_coord)["coords"]

        special_stops_coords.append(coords)
    
    walk_coords.append(walk_to_des)
    walk_coords.insert(0, walk_to_bus)

    return special_stops_name, special_stops_coords, walk_coords


def calculate_route(start, end, travel_mode="car", route_type="fastest"):
    if not start or not end:
        return {"error": "start and end locations required"}, 400

    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/"
        f"{start['lat']},{start['lon']}:{end['lat']},{end['lon']}/json"
    )

    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "routeType": route_type,
        "travelMode": travel_mode,
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except:
        return {"error": "Failed to call TomTom Routing API"}, 500

    data = res.json()

    if "routes" not in data or len(data["routes"]) == 0:
        return {"error": "Không tìm thấy đường đi"}, 404

    route = data["routes"][0]
    points = route["legs"][0]["points"]
    coords = [{"lat": p["latitude"], "lon": p["longitude"]} for p in points]
    summary = route["summary"]

    return {
        "coords": coords,
        "distance_km": summary["lengthInMeters"] / 1000,
        "duration_min": summary["travelTimeInSeconds"] / 60
    }
