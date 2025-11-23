# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uuid, os
from fastapi.responses import HTMLResponse
import numpy as np
from typing import Any

# Import your cached data
import graph_cache

from Bus_Routing_Module import a_star, draw_map, nearby_stops, make_heuristic
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ADD THIS BLOCK -------------------------------------------------
origins = [
    "http://localhost:3000"   # React dev server
    # Add your production URL later, e.g.:
    # "https://yourdomain.com",
]

def to_python(obj: Any) -> Any:
    """Recursively convert numpy types → native python types"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_python(v) for v in obj]
    elif hasattr(obj, "__dict__"):          # Pydantic models, dataclasses, etc.
        return to_python(obj.__dict__)
    else:
        return obj

# Constants
SPEED_MPS = 7.0
WALK_SPEED = 1.5
C_FARE = 10.0
P_TRANSFER_PEN = 100.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    graph_cache.load_all_data()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],             # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],             # Allows all headers
)

# Serve the generated map
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/route")
async def get_bus_route(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    max_walk: float = 400
):
    start_coord = (start_lat, start_lng)
    end_coord = (end_lat, end_lng)

    print("Bus routing...")
    start_stops = nearby_stops(start_coord, graph_cache.STOPS_DF, max_walk)
    if not start_stops:
        return {"error": "No bus stop near start"}

    dest_stops = nearby_stops(end_coord, graph_cache.STOPS_DF, max_walk)
    if not dest_stops:
        return {"error": "No bus stop near destination"}

    dest_set = {sid for sid, _ in dest_stops}
    heuristic = make_heuristic(graph_cache.STOPS_DF, end_coord, SPEED_MPS)

    result = a_star(
        G=graph_cache.G_BUS,
        route_info=graph_cache.ROUTE_INFO,
        stops = graph_cache.STOPS_DF,
        start_stops=start_stops,
        dest_stop_set=dest_set,
        heuristic=heuristic,
        speed=SPEED_MPS,
        walk_speed=WALK_SPEED,
        c=C_FARE,
        p=P_TRANSFER_PEN
    )

    if not result:
        return {"error": "No route found"}

    # Generate unique filename
    map_filename = f"route_{uuid.uuid4().hex[:10]}.html"
    map_path = f"./{map_filename}"

    draw_map(
        route_info=graph_cache.ROUTE_INFO,
        start_coord=start_coord,
        dest_coord=end_coord,
        stops_df=graph_cache.STOPS_DF,
        path=result["coords"],
        route_seq=result["route_seq"],
        total_fare=result["total_fare"],
        worst_min=result["worst_min"],
        best_min=result["best_min"],
        Car_nodes= graph_cache.CAR_NODES,
        Car_graph= graph_cache.CAR_GRAPH,
        Walk_nodes= graph_cache.WALK_NODES,
        Walk_graph= graph_cache.WALK_GRAPH
    )
    os.rename("bus_route_pro.html", map_path)  # rename to unique name

    # Read the HTML file and send it
    with open(map_path, "r", encoding="utf-8") as f:
        map_html = f.read()

    transfers = len(set(r for r in result["route_seq"] if r is not None))

    result =  {
        "fare_vnd": int(result["total_fare"]),
        "best_case_min": round(result["best_min"], 1),
        "worst_case_min": round(result["worst_min"], 1),
        "transfers": transfers,
        "map_url": "/static/bus_route_pro.html",
        "specialStops": result["special_stops"],
        "map_html": map_html,
        "stops": result["coords"]
    }

    return to_python(result)