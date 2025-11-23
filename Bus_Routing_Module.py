import json
import pandas as pd
import networkx as nx
import heapq
import folium
import math
from collections import defaultdict
from draw_bus_path import find_shortest_path , build_graph_from_json


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
def build_graph(trips):
    G = nx.MultiDiGraph()
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

                final_special = special_stops[current] + [lastStop]
                for i in range(len(final_special)):
                    final_special[i] = stops.loc[final_special[i], "stopName"]

                total_fare = cum_fare[current]
                total_wait_sec = cum_wait[current]
                worst_sec = g_score[current] - c * total_fare - (p - 1)* total_wait_sec + h_to_dest * walk_speed
                best_sec = worst_sec - total_wait_sec

                return {
                        "coords": path,
                        "best_min": best_sec / 60,
                        "worst_min": worst_sec / 60,
                        "total_fare": total_fare,
                        "route_seq" : routes_used,
                        "special_stops": final_special
                    }


        if stop not in G:
            continue

        for u, nei, key, data in G.out_edges(stop, data=True, keys=True):
            dist = data["distance"]
            new_route = data["route"]

            wait = 0.0
            fare_add = 0
            if cur_route is None or cur_route != new_route:
                fare_add = route_info[new_route]["fare"]
                wait = route_info[new_route]["headway_sec"]

            # STRONG PENALTY ON WAITING → FEWER TRANSFERS
            tentative_g = g_score[current] + dist/speed + wait * p + c * fare_add

            new_state = (nei, new_route)
            if tentative_g < g_score[new_state]:
                came_from[new_state] = current
                g_score[new_state] = tentative_g
                cum_fare[new_state] = cum_fare[current] + fare_add
                cum_wait[new_state] = cum_wait[current] + wait
                f = tentative_g + heuristic(nei)

                if cur_route is None or cur_route != new_route: special_stops[new_state] = special_stops[current] + [stop]
                else : special_stops[new_state] = list(special_stops[current])

                heapq.heappush(open_set, (f, counter, new_state))
                counter += 1

    return {}

def draw_map(route_info, start_coord, dest_coord, stops_df,
             path, route_seq, total_fare, worst_min, best_min, Car_nodes, Car_graph, Walk_nodes, Walk_graph):
    
    print("Drawing map...")
    m = folium.Map(location=start_coord, zoom_start=14, tiles="OpenStreetMap")
    folium.Marker(start_coord, popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(dest_coord,  popup="End",   icon=folium.Icon(color="red")).add_to(m)

    if not path:
        m.save("bus_route_pro.html")
        return

    # === 1. Walk to first stop ===
    first_stop_coord = (stops_df.loc[path[0], "lat"], stops_df.loc[path[0], "lng"])
    walk_to_bus = find_shortest_path(
        start_coord[0], start_coord[1],
        first_stop_coord[0], first_stop_coord[1],
        Walk_nodes, Walk_graph
    )
    if walk_to_bus:
        folium.PolyLine(walk_to_bus, color="gray", weight=5, opacity=0.8, tooltip="Walk").add_to(m)
        prev_end_coord = walk_to_bus[-1]
    else:
        folium.PolyLine([start_coord, first_stop_coord], color="gray", weight=5, opacity=0.8).add_to(m)
        prev_end_coord = first_stop_coord

    # === 2. Bus segments (CHAINED) ===
    colors = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f"]
    color_map = {}
    col_idx = 0

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        v_coord = (stops_df.loc[v, "lat"], stops_df.loc[v, "lng"])
        edge_route = route_seq[i] 

        if edge_route not in color_map:
            color_map[edge_route] = colors[col_idx % len(colors)]
            col_idx += 1
        color = color_map[edge_route]

        road_path = find_shortest_path(
            prev_end_coord[0], prev_end_coord[1],
            v_coord[0], v_coord[1],
            Car_nodes, Car_graph
        )

        if road_path:
            folium.PolyLine(road_path, color=color, weight=7, opacity=0.9,
                            tooltip=f"Bus {route_info[edge_route]['bus_number']}").add_to(m)
            prev_end_coord = road_path[-1]
        else:
            folium.PolyLine([prev_end_coord, v_coord], color=color, weight=7, opacity=0.6,
                            tooltip=f"Bus {route_info[edge_route]['bus_number']} (approx)").add_to(m)
            prev_end_coord = v_coord

    # === 3. Final walk ===
    walk_to_dest = find_shortest_path(
        prev_end_coord[0], prev_end_coord[1],
        dest_coord[0], dest_coord[1],
        Walk_nodes, Walk_graph
    )
    if walk_to_dest:
        folium.PolyLine(walk_to_dest, color="gray", weight=5, opacity=0.8, tooltip="Walk").add_to(m)
    else:
        folium.PolyLine([prev_end_coord, dest_coord], color="gray", weight=5, opacity=0.8).add_to(m)

    # === Legend ===
    legend_items = []
    for route_id in set(route_seq):
        if route_id is None: 
            continue
        color = color_map.get(route_id, "#000000")
        bus_num = route_info[route_id]["bus_number"]
        trip = route_info[route_id]["trip_name"]
        legend_items.append(
            f'<i style="background:{color};width:20px;height:4px;display:inline-block;"></i> '
            f'<b>Bus {bus_num}</b>: {trip}'
        )
    
    legend_html = f"""
    <style>
    /* Force the folium map container to be relative */
    #map {{
        position: relative;
    }}

    #maplegend {{
        position: absolute;
        top: 20px;
        left: 50px;
        z-index: 999999;
        background: white;
        padding: 15px;
        border: 2px solid gray;
        font-size: 14px;
        width: 260px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    </style>

    <div id='maplegend'>
        <b>Bus number:</b><br>
        {"<br>".join(legend_items)}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    m.save("bus_route_pro.html")
    print("Map saved → bus_route_pro.html (MultiDiGraph + Real Roads!)")
