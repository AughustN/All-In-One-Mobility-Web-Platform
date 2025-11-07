# 🏙️ All-In-One Urban Mobility Platform - Group02

### 🚀 Integrated Smart Transit Planning for Urban Commuters

---

## 📋 Group Information

| Name          | MSSV |
|--------------------|----------------|
| Lương Hưng Phát    | 24127298       |
| Hoàng Trung Hiếu   | 24127041       |
| Nguyễn Thành Đạt   | 24127021       |
| Nguyễn Anh Khôi    | 24127430       |
| Nguyễn Tấn Hiệu    | 24127373       |
| Nguyễn Minh Khoa   | 24127188       |


## 🧩 Problem Definition

Urban commuters currently face fragmented mobility experiences.  
Key challenges include scattered data sources, and inefficient route planning via multiple platforms.

**Core Problems**
- Fragmented data across multiple services (public-transportation, personal vehicles).
- Inability to respond to congestion dynamically.
- Lack of centralized safety and congestion insights.

**Impact**
- ⏱️ Inefficient planning and delays.  
- 💸 Increased travel cost.  
- 😣 Poor commuter satisfaction.

**Project Objective**  
To create a **unified mobility platform** integrating all transport modes into a single interface — combining **planning, recommendation, and safety monitoring** for smarter, faster, and safer urban travel.

---

## Proposed Solution

* **A web platform** separating pre-trip routing from in-trip recommendations, with a safety/alerting layer. 

  * Routing (pre-trip): generates 1–2 itineraries (e.g., *Fastest* and *Normal*) under user constraints.
  * Recommender (in-trip): live ETA/cost options with confidence scores in a kanban-style UI.
  * Safety & alerts: context-aware warnings on congested segments. 
* **In-scope transport modes:** bus, taxi /motorbike, walking. Trains/flights are out-of-scope for MVP. 

---

## Success criteria (PoC)

* **Planning feasibility:** ≥80% of generated itineraries satisfy all hard constraints. 
* **User acceptance of plans:** ≥60% select one of the top-3 plans. 
* **In-trip performance:** on-time ≥80%, missed-connection ≤5%, cost error ≤12%. 
* **Safety value:** alert precision ≥80%, exposure to busy segments ≤15 min/day, CSAT ≥4.2/5. 

---

## 👥 Team Roles Overview                                                                      

| Role | Member | Key Responsibility |
|------|---------|--------------------|
| 🧭 Routing Lead | Nguyễn Thành Đạt - 24127021 | Algorithm design, API integration |
| 🚌 Recommendation System | Hoàng Trung Hiếu - 24127041 | Suggestion logic, feedback tuning |
| ⚙️ Safety & Monitoring | Lương Hưng Phát - 24127298| Real-time congestion & alert system |
| Data Collection | Nguyễn Minh Khoa - 24127188 | Scrape real-time data |
| Database | Nguyễn Anh Khôi - 24127430 | Design & Manage Database |
| 🎨 UI/UX & Integration | Nguyễn Tấn Hiệu - 24127373 | Frontend & cross-module integration |

---

## 🕒 Timeline
### 📅 Development Phases (11 Weeks Total)

| Phase | Duration | Key Activities |
|:------|:----------|:---------------|
| **A. Design & Concept** | Week 1–3 | Define architecture, roadmap, and methodology. |
| **B. Development** | Week 4–8 | Implement routing, APIs, and UI integration. |
| **C. Testing** | Week 9–10 | Unit & integration testing, UX validation. |
| **D. Deployment & Launch** | Week 10–11 | Public deployment, demo & presentation. |

---

## Decomposition

```mermaid
graph LR
    Web["Web"]

    %% --- ROUTING ---
    Web --> Routing["Routing"]
    Routing --> RA["Routing Algorithm"]
    RA --> RAP1["Multi-modal pathfinding: Extend A* to handle walk → bus → metro → walk transitions"]
    RA --> RAP2["Cost function: Combine time, distance, fare, comfort, and congestion"]

    Routing --> OSM["OSM Integration"]
    OSM --> OSM1["Overpass API for road networks, transit stops, pedestrian paths"]
    OSM --> OSM2["Caching layer: Store frequently accessed map tiles and routes"]
    OSM --> OSM3["Fallback handling: Deal with API rate limits and offline scenarios"]

    Routing --> PT["Performance Testing"]
    PT --> PT1["Unit tests: Individual algorithm components (heuristic accuracy, path reconstruction)"]
    PT --> PT2["Integration tests: End-to-end routing with mock OSM data"]

    %% --- SUGGESTION ENGINE ---
    Web --> SE["Suggestion Engine"]
    SE --> DC["Data Collecting / Cleaning"]
    DC --> DC1["Scrape Web"]
    DC --> DC2["Organize to datasets"]

    SE --> OA["Optimization Algorithm"]
    OA --> OA1["User preferences: Weight personalization (number of bus station)"]

    SE --> RL["Ranking Logic for Optimal Choices"]
    RL --> RL1["Sorting Algorithm"]
    RL --> RL2["Scoring system: Weighted sum of normalized metrics"]
    

    %% --- CONGESTION PREDICTION ---
    Web --> CP["Object Detection To Simulate Traffic Flow"]
    CP --> CP1["Training"]
    CP --> CP2["Alert System"]
    CP --> CP3["Scrape Data"]
    CP --> CP4["Architecture: Graph Neural Network"]
    

    %% --- UI LAYER ---
    Web --> UI["Interface / UI Layer"]
    UI --> UI1["Framework"]
    UI --> UI2["Kanban-Style UI (Top-3 Modes)"]
    UI --> UI3["Localization + Accessibility Support"]
    UI --> UI4["Backend API Integration"]

    %% --- BACKEND ---
    Web --> BE["Backend & Infrastructure"]
    BE --> GW["API Gateway"]
    GW --> GW1["Endpoint"]
    BE --> DB["Database"]
    DB --> DB1["Transit"]
    DB --> DB2["Fare"]
    DB --> DB3["User Data"]
