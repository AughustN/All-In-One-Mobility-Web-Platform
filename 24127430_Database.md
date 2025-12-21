# BusMap Data Ingestion and Processing Pipeline

**Full Name:** Nguyễn Anh Khôi  
**Student ID:** 24127430  
**Role:** Database  
**Key Responsibilities:** Design & Manage Database  

---

## 1. Context

The *BusMap Data Ingestion and Processing Pipeline* serves as a foundational component for the **All-In-One Urban Mobility Platform**.  
This module is responsible for collecting, decrypting, cleaning, and structuring transit data from BusMap — transforming complex, encrypted web data into usable, analysis-ready CSV datasets.  

Its output provides the **core input data** for two major subsystems:  
- **Suggestion Engine / Data Cleaning:** Supplies the cleaned and standardized bus dataset.  
- **Backend & Infrastructure (Database):** Delivers structured transit schema for database loading and downstream analysis.  

---

## 2. Problem Definition

The project faced a major challenge: BusMap’s data was **not publicly accessible in raw form** and was **transmitted through encrypted API calls**.  
To support route planning and recommendation features, we needed to reverse-engineer, decrypt, and normalize this hidden data pipeline.  

**Main objectives:**  
- Capture encrypted API responses from BusMap.  
- Identify and extract the AES decryption key.  
- Decrypt and reconstruct the entire bus dataset.  
- Normalize and transform the nested, inconsistent data into flat, structured CSV tables.  
- Enrich the dataset (e.g., compute distances between stops).  

**Stakeholders:**  
- **Data Engineering Team:** Builds and maintains the ETL pipeline.  
- **Routing & Suggestion Teams:** Consume the generated CSV data for their modules.  
- **Infrastructure Team:** Loads and maintains the database built from this dataset.  

---

## 3. Objectives

- Successfully capture encrypted BusMap API responses using browser automation.  
- Decrypt the captured data and extract all relevant fields.  
- Parse and clean the data into standardized formats (`routes.csv`, `stops.csv`, `trips.csv`).  
- Ensure the final dataset is accurate, consistent, and ready for integration.  

---

## 4. Work Breakdown Structure

### Phase 1: API Interception (Reverse Engineering)
**Script:** `data-scraper-2.py`  
- Utilized **Playwright** to automate browser interactions with the BusMap website.  
- Captured encrypted API calls and stored responses in `api_responses.json`.  

### Phase 2: Data Decryption
**Script:** `decrypt.py`  
- Analyzed captured API data to locate the AES key used by the web app.  
- Applied the **PyCryptodome** library to decrypt all responses.  
- Generated a decrypted dataset (`busmap_decrypted_data.json`).  

### Phase 3: Raw Data Download and Extraction
**Script:** `hcm_extractor.py`  
- Parsed decrypted data to extract download URLs for BusMap’s static data files.  
- Downloaded multiple raw files (`routes_hcm.raw.json`, `stations_hcm.raw.json`, etc.).  

### Phase 4: Parsing and Normalization
**Scripts:** `hcm_extractor.py`, `routes_export.py`, `stops_export.py`  
- Decompressed and parsed complex nested JSON data.  
- Unified inconsistent field names (e.g., `routeId`, `rid`, `RouteId` → `routeId`; `lat`/`y` → `lat`).  
- Cleaned coordinate data and standardized naming conventions.  

### Phase 5: Data Structuring & Enrichment
**Scripts:** `trips_export.py`, `stops_export.py`, `routes_export.py`  
- Flattened nested JSON structures into well-defined CSV files.  
- Applied the **Haversine formula** to calculate distances between consecutive stops.  
- Produced three final deliverables ready for database ingestion.  

---

## 5. Key Files and Their Functionality

| **File Name** | **Purpose** |
|----------------|-------------|
| `data-scraper-2.py` | Automates browser to intercept encrypted API calls. |
| `decrypt.py` | Extracts AES key and decrypts all captured data. |
| `hcm_extractor.py` | Downloads static BusMap data and performs early normalization. |
| `routes_export.py` | Cleans and exports route data (fares, operation time). |
| `stops_export.py` | Extracts and normalizes bus stop data (coordinates). |
| `trips_export.py` | Builds route-stop sequences and computes inter-stop distances. |

---

## 6. Tools and Technologies

| **Category** | **Tools / Libraries** |
|---------------|------------------------|
| Web Scraping | Playwright |
| Cryptography | PyCryptodome |
| Data Parsing | JSON, gzip, zlib |
| Data Processing | Python (pandas, math) |
| Geospatial | Haversine formula |
| Output Format | CSV files for database integration |

---

## 7. Deliverables

- **`routes.csv`** – Contains all bus routes with ID, code, name, fare, and operation times.  
- **`stops.csv`** – Master list of all bus stops with IDs, names, and cleaned coordinates.  
- **`trips.csv`** – Stop sequences for each route, including calculated distances between stops.  

---

## 8. Challenges and Solutions

| **Challenge** | **Solution** |
|----------------|--------------|
| Encrypted API responses | Reverse-engineered AES key and applied decryption. |
| Inconsistent JSON field names | Standardized naming conventions across all datasets. |
| Missing distance data | Calculated distances using Haversine formula. |
| Complex nested data structures | Designed multi-phase parsing pipeline to flatten and clean data. |

---

## 9. Conclusion

The **BusMap Data Ingestion and Processing Pipeline** successfully completed the full **ETL (Extract–Transform–Load)** process for the BusMap data source.  
This work converts raw, encrypted web data into clean, standardized CSV datasets — enabling further development of the routing and recommendation modules.  

The resulting dataset now serves as the **backbone of the project’s database**, supporting accurate route suggestions and scalable data-driven functionality within the *All-In-One Urban Mobility Platform*.  

🏁 **Outcome:** Data pipeline fully operational and integrated — ready for system-wide use.
