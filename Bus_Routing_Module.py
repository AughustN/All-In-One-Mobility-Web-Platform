import pandas as pd
import networkx as nx
import heapq
import math
from collections import defaultdict
from draw_bus_path import find_shortest_path
from API import calculate_route


# --------------------------------------------------------------
# 1. Load data
# --------------------------------------------------------------
def load_data():
    routes = pd.read_csv("routes.csv")
    trips  = pd.read_csv("trips.csv")
    stops  = pd.read_csv("stops.csv").set_index("stopId")
    return routes, trips, stops


# --------------------------------------------------------------
# 2. Build graph
# --------------------------------------------------------------
def build_graph(trips, stops_df, max_walking_between_stops = 250):
    G = nx.MultiDiGraph()
    # Add all bus route edges
    for route_id in trips["routeId"].unique():
        sub = trips[trips["routeId"] == route_id].sort_values("stopSequence")
        stops_list = sub["stopId"].tolist()
        distances  = sub["distanceToNextStop"].tolist()
        for i in range(len(stops_list)-1):
            u = stops_list[i]
            v = stops_list[i+1]
            G.add_edge(u, v, distance=distances[i], route=route_id)
        for sid in stops_list:
            if sid not in G:
                G.add_node(sid)

    # Ensure all stops exist as nodes with coordinates
    for _, row in stops_df.iterrows():
        sid = row.name
        G.add_node(sid)

    # Add walking edges between nearby stops (within max_walking_between_stops)
    stop_ids = list(stops_df.index)

    for i in range(len(stop_ids)):
        u = stop_ids[i]
        u_coord = (stops_df.loc[u, "lat"], stops_df.loc[u, "lng"])

        for j in range(i + 1, len(stop_ids)):
            v = stop_ids[j]
            v_coord = (stops_df.loc[v, "lat"], stops_df.loc[v, "lng"])

            dist = haversine(u_coord, v_coord)

            if dist <= max_walking_between_stops:
                G.add_edge(u, v, distance=dist, route="0", mode="walk")
                G.add_edge(v, u, distance=dist, route="0", mode="walk")

    print(f"Added walking edges for {max_walking_between_stops}m radius")
    return G


# --------------------------------------------------------------
# 3. Route info (fare + headway)
# --------------------------------------------------------------
def build_route_info(routes, trips, stops_df):
    info = {}
    for _, row in routes.iterrows():
        rid = row["routeId"]
        headway_min = row["busStopSpacing(time of trip)"]
        # Find first and last stop name for this route
        sub = trips[trips["routeId"] == rid].sort_values("stopSequence")
        if not sub.empty:
            first_stop = stops_df.loc[sub.iloc[0]["stopId"], "stopName"]
            last_stop  = stops_df.loc[sub.iloc[-1]["stopId"], "stopName"]
            trip_name = f"{first_stop} → {last_stop}"
        else:
            trip_name = "Unknown"
        info[rid] = {
            "bus_number" : row["busNumber"],
            "fare": row["fee"],
            "headway_sec": headway_min * 60,
            "trip_name": trip_name
        }
    return info


# --------------------------------------------------------------
# 4. Helpers
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
                state = current
                lastStop = stop
                while state is not None:
                    for u, nei, key, data in G.out_edges(stop, data=True, keys=True):
                        dist = data["distance"]
                        new_route = data["route"]
                        if cur_route is None or cur_route != new_route: continue
                        new_h_to_dest = heuristic(nei)
                        if(heuristic(stop) > new_h_to_dest):
                            h_to_dest= new_h_to_dest
                            new_state = (nei, new_route)
                            g_score[new_state] = g_score[state] + dist/speed
                            came_from[new_state] = state
                            state = new_state
                            lastStop = nei
                        break
                    if(state == current): break
                                
                while state is not None:
                    s, r = state
                    if s is not None:
                        path.append(s)
                        if r is not None:
                            routes_used.append(r)
                    state = came_from[state]
                path.reverse()
                routes_used.reverse()

                # special stops
                final_special = special_stops[current] + [lastStop]

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

                total_fare = cum_fare[current]
                total_wait_sec = cum_wait[current]
                worst_sec = g_score[current] - c * total_fare - (p - 1)* total_wait_sec + h_to_dest * walk_speed
                best_sec = worst_sec - total_wait_sec

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
                fare_add = 0
                wait = 0
                if cur_route == "0": continue # prevent consecutive walking 
            else:
                # transfer or new bus route
                if cur_route is None or cur_route != new_route:
                    fare_add = route_info[new_route]["fare"]
                    wait = route_info[new_route]["headway_sec"]
                else:
                    fare_add = 0
                    wait = 0
            # STRONG PENALTY ON WAITING → FEWER TRANSFERS
            if(cur_route is not None and new_route != "0"):
                tentative_g = g_score[current] + dist/speed + wait * p + c * fare_add
            else: tentative_g = g_score[current] + dist/walk_speed

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
             path, Walk_nodes, Walk_graph):
    
    print("Drawing map...")
    if not path:
        return

    # === 1. Walk to first stop ===
    first_stop_coord = (stops_df.loc[path[0], "lat"], stops_df.loc[path[0], "lng"])
    walk_to_bus = find_shortest_path(
        start_coord[0], start_coord[1],
        first_stop_coord[0], first_stop_coord[1],
        Walk_nodes, Walk_graph
    )


    # === 3. Final walk ===
    last_stop_coord = (stops_df.loc[path[-1], "lat"], stops_df.loc[path[-1], "lng"])
    walk_to_dest = find_shortest_path(
        last_stop_coord[0], last_stop_coord[1],
        dest_coord[0], dest_coord[1],
        Walk_nodes, Walk_graph
    )
   

        
    return walk_to_bus, walk_to_dest 

def calculate_transfer_walkingCoords(special_stops, stop_df, unique_BusNumbers, Walk_nodes, Walk_graph, walk_to_bus, walk_to_des):
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

            coords = find_shortest_path(start_coord["lat"],
                                         start_coord["lon"], 
                                         end_coord["lat"], 
                                         end_coord["lon"], 
                                         Walk_nodes,
                                         Walk_graph)
            walk_coords.append(coords)

            continue

        # Compute car path between previous stop → current stop
        coords = calculate_route(start_coord, end_coord)["coords"]

        special_stops_coords.append(coords)
    
    walk_coords.append(walk_to_des)
    walk_coords.insert(0, walk_to_bus)

    return special_stops_name, special_stops_coords, walk_coords