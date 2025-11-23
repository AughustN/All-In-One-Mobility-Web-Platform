import json
import pandas as pd
import networkx as nx
from draw_bus_path import build_graph_from_json
from Bus_Routing_Module import build_graph, build_route_info

# --------------------- Global objects (loaded once) ---------------------
G_BUS: nx.MultiDiGraph = None
ROUTE_INFO: dict = None
STOPS_DF: pd.DataFrame = None
CAR_NODES = None
CAR_GRAPH = None
WALK_NODES = None
WALK_GRAPH = None

def load_all_data():
    global G_BUS, ROUTE_INFO, STOPS_DF, CAR_NODES, CAR_GRAPH, WALK_NODES, WALK_GRAPH

    print("Loading bus data...")
    routes_df = pd.read_csv("routes.csv")
    trips_df  = pd.read_csv("trips.csv")
    stops_df  = pd.read_csv("stops.csv").set_index("stopId")

    G_BUS = build_graph(trips_df)                    # your existing function
    ROUTE_INFO = build_route_info(routes_df, trips_df, stops_df)

    print("Loading road networks...")
    with open("car_data.json", "r") as f:
        car_data = json.load(f)
    CAR_NODES, CAR_GRAPH = build_graph_from_json(car_data)

    with open("walk_data.json", "r") as f:
        walk_data = json.load(f)
    WALK_NODES, WALK_GRAPH = build_graph_from_json(walk_data)

    # Keep a copy for fast lookup
    STOPS_DF = stops_df

    print("All data loaded and cached!")