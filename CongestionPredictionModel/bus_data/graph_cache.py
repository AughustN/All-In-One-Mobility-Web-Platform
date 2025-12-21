import json
import pandas as pd
import networkx as nx
import pickle
import os
import math
from pathlib import Path

# --------------------- Global objects (loaded once) ---------------------
G_BUS: nx.MultiDiGraph = None
ROUTE_INFO: dict = None
STOPS_DF: pd.DataFrame = None
# WALK_NODES = None
# WALK_GRAPH = None

# Cache file paths
CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "bus_graph_cache.pkl"


# --------------------------------------------------------------
# 1. Build graph
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
# 2. Route info (fare + headway)
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
def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_data_modification_time():
    """Get the latest modification time of all data files"""
    files = ["routes.csv", "trips.csv", "stops.csv", "walk_data.json"]
    try:
        return max(os.path.getmtime(f) for f in files if os.path.exists(f))
    except:
        return 0

def save_cache():
    """Save all loaded data to cache file"""
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_data = {
            'G_BUS': G_BUS,
            'ROUTE_INFO': ROUTE_INFO,
            'STOPS_DF': STOPS_DF,
            # 'WALK_NODES': WALK_NODES,
            # 'WALK_GRAPH': WALK_GRAPH,
            'data_mtime': get_data_modification_time()
        }
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"💾 Cache saved to {CACHE_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to save cache: {e}")

def load_from_cache():
    """Load data from cache if available and valid"""
    global G_BUS, ROUTE_INFO, STOPS_DF
    # , WALK_NODES, WALK_GRAPH
    
    if not CACHE_FILE.exists():
        return False
    
    try:
        current_mtime = get_data_modification_time()
        
        with open(CACHE_FILE, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Check if cache is still valid
        cached_mtime = cache_data.get('data_mtime', 0)
        if cached_mtime < current_mtime:
            print("⚠️ Cache outdated (data files modified), rebuilding...")
            return False
        
        # Load from cache
        G_BUS = cache_data['G_BUS']
        ROUTE_INFO = cache_data['ROUTE_INFO']
        STOPS_DF = cache_data['STOPS_DF']
        # WALK_NODES = cache_data['WALK_NODES']
        # WALK_GRAPH = cache_data['WALK_GRAPH']
        
        print(f"⚡ Loaded from cache in <1s!")
        print(f"   Graph: {G_BUS.number_of_nodes()} nodes, {G_BUS.number_of_edges()} edges")
        print(f"   Routes: {len(ROUTE_INFO)}")
        print(f"   Stops: {len(STOPS_DF)}")
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to load cache: {e}")
        return False

def load_all_data():
    """Load all bus routing data including OSM road networks"""
    global G_BUS, ROUTE_INFO, STOPS_DF
    # , WALK_NODES, WALK_GRAPH
    
    print(f"📂 Current directory: {os.getcwd()}")

    # Try loading from cache first
    if load_from_cache():
        return

    # Cache miss or invalid - build from scratch
    try:
        print("🔨 Building graph from scratch (this may take a while)...")
        
        print("Loading bus data...")
        routes_df = pd.read_csv("./bus_data/routes.csv")
        print(f"✅ Loaded {len(routes_df)} routes")
        
        trips_df = pd.read_csv("./bus_data/trips.csv")
        print(f"✅ Loaded {len(trips_df)} trips")
        
        stops_df = pd.read_csv("./bus_data/stops.csv").set_index("stopId")
        print(f"✅ Loaded {len(stops_df)} stops")

        print("Building bus graph...")
        G_BUS = build_graph(trips_df, stops_df)
        print(f"✅ Graph built with {G_BUS.number_of_nodes()} nodes and {G_BUS.number_of_edges()} edges")
        
        print("Building route info...")
        ROUTE_INFO = build_route_info(routes_df, trips_df, stops_df)
        print(f"✅ Route info built with {len(ROUTE_INFO)} routes")

        # print("Loading road networks...")
        # with open("walk_data.json", "r") as f:
        #     walk_data = json.load(f)
        # WALK_NODES, WALK_GRAPH = build_graph_from_json(walk_data)
        # print(f"✅ Walk network loaded")

        # Keep a copy for fast lookup
        STOPS_DF = stops_df

        print("✅ All data loaded!")
        
        # Save to cache for next time
        save_cache()
        
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        print("💡 Make sure all CSV and JSON files are in the same directory as API.py")
        raise
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

def clear_cache():
    """Clear the cache file (useful for debugging)"""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            print("🗑️ Cache cleared")
        else:
            print("ℹ️ No cache to clear")
    except Exception as e:
        print(f"⚠️ Failed to clear cache: {e}")