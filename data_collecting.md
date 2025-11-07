# Data Collection — Scrape Real-Time Traffic Camera Data

## 1. Problem Definition
Collecting and maintaining continuous, high-quality, legally compliant real-time traffic camera image streams. These data streams support downstream modules such as object detection, flow estimation, congestion scoring, and safety alerting.

Challenges:
- Different resolutions and frame rates across camera sources
- Stream instability and network latency
- Privacy and legal constraints on public camera usage
- Lighting, weather, and occlusion affecting frame clarity
- Requirement for low-latency, real-time data access

Goal: Ensure reliable and compliant real-time frame ingestion.

---

## 2. Decomposition

| Component             | Description                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------------|
| Camera Registry      | Maintain camera metadata (URL, GPS location, orientation, refresh rate, permission status).      |
| Scraper / Fetcher    | Pull live streams with retry logic, rate limiting, and health checks.                             |
| Frame Extraction     | Sample frames at a configurable rate (e.g., 1 fps) using FFmpeg.                                 |
| Preprocessing        | Normalize frames (resize, contrast correction) and apply region-of-interest (ROI) masking.        |
| Calibration          | Generate per-camera homography mapping to enable speed and movement estimation downstream.        |
| Storage              | Store recent frames/clips (24–72 hours) for debugging and model reference.                        |
| Metrics Monitoring   | Track frame freshness, uptime, fetch success rate, latency and display via dashboard.             |
| Compliance & Privacy | Verify terms-of-use and blur/remove identifiable features when required.                          |

---

## 3. Solution
Implement a real-time data ingestion pipeline that:
1. Registers traffic camera feeds and verifies legal usage.
2. Continuously retrieves and samples frames via FFmpeg.
3. Normalizes frames and applies camera-specific ROI masks.
4. Stores frames and logs metadata for use by downstream modules.
5. Provides API endpoints to access frames and camera health information.
6. Ensures privacy protections and retention compliance.

Deliverables:
- Camera registry
- Working scraper and frame sampling pipeline
- ROI masks and calibration maps
- Time-series ingestion logs
- Monitoring dashboard
- Compliance documentation

---

## 4. Tools / Framework

| Category         | Tools / Frameworks                     |
|------------------|----------------------------------------|
| Data Fetching     | FFmpeg, aiohttp, requests, gstreamer  |
| Storage           | S3 / MinIO, Local Staging             |
| Metadata Database | Postgres                               |
| Metrics Database  | TimescaleDB / InfluxDB                 |
| Preprocessing     | OpenCV                                 |
| Monitoring        | Grafana, Prometheus, Sentry            |
| API Layer         | FastAPI                                |
| Deployment        | Docker, GitHub Actions, Terraform      |
| Annotation        | CVAT, LabelStudio                      |

---

## 5. Timeline

| Week     | Focus             | Output / Deliverables                                                |
|----------|-------------------|----------------------------------------------------------------------|
| Week 0   | Setup & Legal     | Camera inventory, permissions review, sampling plan                  |
| Week 1–2 | Pipeline Build    | Scraper, FFmpeg extractor, camera registry, health monitoring        |
| Week 3–4 | Preprocessing     | Frame normalization and ROI masking                                 |
| Week 5   | Calibration       | Homography / perspective calibration for selected cameras            |
| Week 6   | Metrics Logging   | Frame freshness and uptime metrics stored in time-series DB          |
| Week 7   | API Integration   | Endpoints for latest frame & camera health                           |
| Week 8   | Privacy Controls  | Blurring/masking + retention policy application                      |
| Week 9   | Dashboards        | Grafana monitoring dashboard and alert thresholds                    |
| Week 10  | E2E Testing       | Validate pipeline stability and latency performance                  |
| Week 11  | Documentation     | Runbooks, onboarding guide, compliance confirmation                  |
