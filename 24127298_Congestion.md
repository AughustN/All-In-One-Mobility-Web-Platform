# 🔹 Congestion & Alert Module Report

*Full name:* Lương Hưng Phát  
*Student ID:* 24127298
*Role:* ⚙️ Safety & Monitoring
*Key Responsibilities:* Real-time congestion & Alert system

---

# 💡 2. Problem Definition

*Core problem:*  
How to detect and count vehicles at city junctions in near-real time, convert those counts into a road-graph traffic flow, and predict congestion on each road segment using a Graph Neural Network (GNN), then surface alerts with red/yellow/green states.

- **Why vision?**
  - Fixed cameras are non-intrusive and can extract rich traffic parameters beyond simple counts (class, lane, speed proxies).
- **Why GNN?**
  - Congestion is spatiotemporal: neighboring links/junctions influence each other; graph models capture these dependencies.

### Stakeholders
- *Traffic Operations Center:* Needs timely R/Y/G alerts on interpretable segments.
- *Data/ML Team:* Maintains detector, tracker, and GNN; monitors drift.

### Objectives
- Deploy YOLOv8 vehicle detection (car, motorbike, bicycle, bus/truck).
- Track and count vehicles per lane/movement; estimate per-interval flow.
- Build a directed road graph (nodes=junctions, edges=movements/links).
- Train a spatiotemporal GNN to predict short-term congestion per edge.
- Baseline and report accuracy (mAP, counting MAE, alert precision/recall).

### Input Data

*External/Static*
- Junction/road geometry (GIS/OSM), lane polygons & virtual count lines.
- Camera calibration (homography) for lane/movement mapping.

*Live Streams*
- RTSP video from fixed cameras (≥1080p preferred; stable mount & AoI).

*Derived/Model Inputs*
- Per-interval counts by class (car, motorbike, bicycle, bus/truck).
- Edge features for GNN: recent flows, occupancy proxies, historical averages.
- (Optional) Exogenous: rain/temp, hour/day seasonality.

### Expected Output
- Time-stamped per-movement/edge flow table (by class).
- Segment/junction congestion score ∈ [0,1] → {Green, Yellow, Red}.
- API + live map with color states; exportable CSV/Parquet.
- Model metrics report (mAP@50, counting MAE/MAPE, alert P/R/F1).

### Constraints
- Occlusion, shadows, night/glare, and camera shake degrade vision.
- Domain shift across junctions/cameras; few-shot tuning may be needed.
- GNN depends on reliable flows; upstream count errors propagate.
- Privacy & policy: no face/plate storage; only aggregates persist.
- Edge compute & bandwidth constraints at some sites.

---

## 🔸 3. Guiding Questions

### 3.1 What do we know?
- Vision can deliver counts + classes; feasible at scale with good placement.
- YOLOv8 handles multi-scale vehicles; light pre/post-processing helps.
- Congestion prediction benefits from ML/DL with exogenous signals.
- Simple tree/MLP baselines are strong for discrete congestion labels.

### 3.2 What do we want?
- `detect_vehicles_yolov8()` → per-frame boxes+classes+conf.
- `track_and_count()` → lane/movement-aware tracks; interval counts.
- `build_flow_graph()` → assemble edge features from counts.
- `gnn_predict_congestion()` → short-term edge congestion score.
- `alert_router()` → thresholds + hysteresis → R/Y/G; push to API/DB.

### 3.3 What are the rules or constraints?
- One camera per junction should cover all movements (minimal blind spots).
- Counting via *crossing* virtual lines; de-dup with track IDs + cooldown.
- GNN trained on rolling windows (e.g., past 15–30 min → next 5–10 min).
- No raw video retention beyond transient buffers; store only aggregates.

### 3.4 What’s missing?
- Night/rain robustness; may need IR/low-light cameras or extra fine-tuning.
- Ground-truth flow for evaluation (short audit campaigns).
- Reliable GIS homographies for every camera.

---

## ⚙️ 4. Resource Requirements

### 4.1 Hardware
- Fixed camera(s), stable mount, PoE, low-compression RTSP.
- Central server (GNN training/inference + storage) or cloud VM with GPU.

### 4.2 Software
- **Detection/Tracking:** Ultralytics YOLOv8, OpenCV, ByteTrack/DeepSORT.
- **Graph & ML:** PyTorch + PyTorch Geometric (GNN), scikit-learn.
- **Pipelines:** Kafka/Redis (stream), FastAPI, TimescaleDB/InfluxDB (time series).
- **Labeling:** Label Studio/Roboflow for junction-specific fine-tuning.

---

## 📊 5. Third-Party Resources and Services

| Service | Requirement | Cost |
|---|---|---|
| Ultralytics/YOLOv8 | Detector training/inference | Free (AGPL)/Pro options |
| Label Studio / Roboflow | Annotation & dataset mgmt | Free tiers / Paid |
| OpenStreetMap (OSM) | Base road geometry | Free |
| Weather API (e.g., Open-Meteo) | Exogenous features | Free |

---

## ⚙️ 6. Requirements Definition

### 6.1 Functional Requirements (FR)

| ID | Requirement | Description |
|---|---|---|
| FR1 | Detector Setup | YOLOv8 model with vehicle classes; junction fine-tuning. |
| FR2 | Tracking & Counting | Multi-object tracker + virtual lines per lane/movement; de-dup via track IDs. |
| FR3 | Class-wise Flow | Aggregate counts per 10–15s (configurable) by class & movement. |
| FR4 | Camera Calibration | Homography mapping pixels → lanes/movements. |
| FR5 | Graph Builder | Construct directed graph (junctions/edges) with rolling features. |
| FR6 | GNN Predictor | Short-term congestion per edge using recent flows & exogenous signals. |
| FR7 | Alerting | Map scores to R/Y/G with thresholds + hysteresis; publish via REST/WebSocket. |
| FR8 | Dashboard | Live map with colored segments; history & metrics view. |
| FR9 | Evaluation | mAP (detector), MAE/MAPE (counts), P/R/F1 (alerts); periodic reports. |

### 6.2 Non-Functional Requirements (NFR)

| ID | Requirement | Description |
|---|---|---|
| NFR1 | Latency | Edge detection+count ≤ 300–600 ms/frame; end-to-end alert ≤ 3–5 s. |
| NFR2 | Accuracy | Counting MAE ≤ 10% on audited windows; Alert F1 ≥ 0.85 (initial). |
| NFR3 | Robustness | Operate across day/night & rain; track degradation. |
| NFR4 | Privacy | No faces/plates stored; only aggregates persist. |
| NFR5 | Reliability | 99% pipeline uptime; auto-restart & buffering on network loss. |
| NFR6 | Maintainability | Modular services; config-driven junction onboarding. |

---

## 🔹 7. Work Breakdown Structure

### 7.1 Perception (Detection/Tracking)
*Objective:* Stable counts by movement & class.  
*Modules:* `detect_vehicles_yolov8.py`, `tracker_counter.py`

- Data audit & small fine-tune set per camera (day/night/rain).
- Define lane polygons & virtual lines; homography tool.
- Integrate YOLOv8 + ByteTrack; ID-based de-dup; class remapping.
- Unit tests on clip bank; counting MAE baseline.

### 7.2 Flow Graph & Features
*Objective:* Clean edge features for learning.  
*Modules:* `build_flow_graph.py`, `feature_store.py`

- Map counts → edges; compute rolling stats (Δt=10–15s, 5/10/15-min windows).
- Enrich with hour/day and weather features.
- Data quality monitors (nulls, spikes, drift).

### 7.3 GNN Congestion Model
*Objective:* Predict short-term congestion score per edge.  
*Modules:* `gnn_predictor.py`, `train_gnn.py`

- Define labels (speed/occupancy proxies or percentile thresholds).
- Model: ST-GNN (GraphConv/TemporalConv) with rolling windows.
- Baselines: DT/MLP classifier for discrete R/Y/G (sanity check).
- Backtesting; choose thresholds + hysteresis.

### 7.4 Serving & Observability
*Objective:* Productionize.  
*Modules:* `api_alerts.py`, `dashboard/`, `metrics_exporter.py`

- FastAPI for alerts & metrics; WebSocket for live map.
- Prometheus/Grafana dashboards (latency, FPS, MAE, alert P/R).
- Canary on 1–2 junctions; rollout plan.

---

## 🚀 8. Execution Plan

| No. | Task | Objective | Expected Output | Date | Status |
|---|---|---|---|---|---|
| 1 | Camera & Geometry Audit | Ensure coverage + lanes mapped | Homographies, lane/line configs | 4–6/11/2025 | ✅ Done (pilot sites) |
| 2 | Detector & Tracking POC | Validate counts accuracy | MAE report on annotated clips | 7–8/11/2025 | 🔄 In progress |
| 3 | Flow Graph & Store | Turn counts into features | Feature tables (10–15s bins) | 9/11/2025 | 🔜 Next |
| 4 | GNN Baseline | First congestion predictor | Backtest report (R/Y/G P/R/F1) | 12/11/2025 | ⏳ Planned |
| 5 | Serving & Dash | Live alerts API + map | Live R/Y/G demo | 14/11/2025 | ⏳ Planned |
| 6 | Hardening & QA | Night/rain tests, failsafes | SRE checklist + monitors | 18/11/2025 | ⏳ Planned |

---
