import json
import pandas as pd
import networkx as nx
from draw_bus_path import build_graph_from_json
from Bus_Routing_Module import build_graph, build_route_info

# --------------------- Global objects (loaded once) ---------------------
G_BUS: nx.MultiDiGraph = None
ROUTE_INFO: dict = None
STOPS_DF: pd.DataFrame = None
WALK_NODES = None
WALK_GRAPH = None

def load_all_data():
    """Load all bus routing data including OSM road networks"""
    global G_BUS, ROUTE_INFO, STOPS_DF, WALK_NODES, WALK_GRAPH
    
    import os
    print(f"📂 Current directory: {os.getcwd()}")

    try:
        print("Loading bus data...")
        routes_df = pd.read_csv("routes.csv")
        print(f"✅ Loaded {len(routes_df)} routes")
        
        trips_df = pd.read_csv("trips.csv")
        print(f"✅ Loaded {len(trips_df)} trips")
        
        stops_df = pd.read_csv("stops.csv").set_index("stopId")
        print(f"✅ Loaded {len(stops_df)} stops")

        print("Building bus graph...")
        G_BUS = build_graph(trips_df, stops_df)
        print(f"✅ Graph built with {G_BUS.number_of_nodes()} nodes and {G_BUS.number_of_edges()} edges")
        
        print("Building route info...")
        ROUTE_INFO = build_route_info(routes_df, trips_df, stops_df)
        print(f"✅ Route info built with {len(ROUTE_INFO)} routes")

        print("Loading road networks...")
        with open("walk_data.json", "r") as f:
            walk_data = json.load(f)
        WALK_NODES, WALK_GRAPH = build_graph_from_json(walk_data)
        print(f"✅ Walk network loaded")

        # Keep a copy for fast lookup
        STOPS_DF = stops_df

        print("✅ All data loaded and cached!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        print("💡 Make sure all CSV and JSON files are in the same directory as API.py")
        raise
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise