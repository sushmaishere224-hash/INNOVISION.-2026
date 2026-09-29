# Hackathon-2o6
Veni vedi veci
<br>
author katyayani kaira
======================
# Hackathon-2o6
Veni vedi veci
<br>
author Katyayani Kaira

A LANDSLIDE RISK PREDICATOR and early warning system focused on the Uttrakhand region of ndia.

LRP combines rainfall, soil moisture, terrain, elevation, slope and landslide susceptibility data to estimate the risk level of a location and display it through a GIS-based interface.

SJC AI GENESIS 2026 — Problem Statement D4P1- LANDSLIDE RISK PREDICATOR:UTTARAKHAND 
PROBLEM : Build a real-time landslide risk assessment platform specifically designed for Uttarakhand using factors such as rainfall intensity, slope angle, elevation, soil characteristics and historical landslide locations. The system should generate location-based risk levels, explain the factors contributing to each prediction and display vulnerable areas on an interactive map. Teams may integrate suitable geographic and weather datasets and should design the system so that changing environmental conditions can automatically alter the predicted risk. Alerts should be generated when predefined danger thresholds are crossed.
What is LPR?

The main idea is simple:

collect environmental data → calculate risk → show it on a map → eventually send warnings when the risk becomes critical.

Landslides in the Uttrakhand are strongly affected by factors such as heavy rainfall, saturated soil and steep terrain. Instead of looking at these factors separately, LPR combines them into a location-based risk score.

The current version is a prototype. The risk calculation is based on weighted environmental factors, while a trained ML model can be integrated later when enough reliable historical landslide data is available.

How it works
<br>
flowchart LR
    A[Weather Data] --> D[Data Processing]
    B[Terrain / DEM] --> D
    C[Soil Moisture] --> D
    E[Landslide Susceptibility] --> D

    D --> F[Risk Calculation]
    F --> G[Risk Score]
    G --> H{Risk Level}

    H -->|Low| I[LOW]
    H -->|Medium| J[MEDIUM]
    H -->|High| K[HIGH]

    I --> L[GIS Map]
    J --> L
    K --> L
The system currently considers:

Rainfall
<nb>
Recent accumulated rainfall
<nb>
Soil moisture
<nb>
Elevation
<nb>
Slope
<nb>
Regional landslide susceptibility
<nb>
These values are processed and converted into a risk score.

SYSTEM ARCHITECTURE
flowchart TB
    subgraph Data["Data Sources"]
        W[Weather API]
        G[GIS / DEM Data]
        S[Soil Moisture]
        H[Historical / Susceptibility Data]
    end

    subgraph Backend["Backend"]
        API[FastAPI]
        PROC[Data Processing]
        RISK[Risk Engine]
        DB[(PostgreSQL)]
    end

    subgraph Client["Client"]
        MAP[Interactive GIS Map]
        INFO[Risk Information]
        ALERT[Future Alerts]
    end

    W --> PROC
    G --> PROC
    S --> PROC
    H --> PROC

    PROC --> RISK
    RISK --> DB
    RISK --> API

    API --> MAP
    API --> INFO
    API --> ALERT

Risk Calculation 
 The prototype uses a weighted risk score rather than claiming to predict an actual landslide with an ML model.

A simplified view of the process is:
flowchart LR
    R[Rainfall] --> N[Normalize Factors]
    SM[Soil Moisture] --> N
    SL[Slope] --> N
    EL[Elevation] --> N
    SU[Susceptibility] --> N

    N --> W[Apply Weights]
    W --> SCORE[Risk Score]
    SCORE --> CLASS[Risk Classification]
The score is then classified into different risk levels.

The weights and thresholds are configurable and are intended to be improved as better datasets become available.


<nb>
GIS 
The application focuses on the North Eastern Region of India rather than showing a generic world map.

The GIS layer is used to visualize the relationship between terrain and environmental conditions.

The idea is to eventually have a continuously updating regional risk map where the visible areas are queried for their latest risk information.

<nb>
BACKEND

The backend is built using FastAPI and exposes the risk calculation through a REST API.

Example:

GET /risk?lat=27.03333&lon=88.26667
A response can contain information such as:

{
  "elevation": 2127,
  "slope": 28.2,
  "soil_moisture": 79.2,
  "risk_score": 44,
  "risk_level": "MEDIUM"
}
<nb>
The frontend uses this response to display the risk for the selected location.


TECH STACK

BACKEND 
<nb>
 Python
 <nb>
 FastAPI
 <nb>
 Uvicorn
 <nb>
 PostgreSQL

<nb>
FRONTEND
    <nb>

 HTML
<nb>
NodeJS
<nb>
CSS
    
<nb>
DATA 
 Weather data
    <nb>
        
    
Digital Elevation Model
<nb>
Slope / terrain data
<nb>
Soil moisture
<nb>
Landslide susceptibility data
<nb>
Current Status
This is currently a working prototype focused on the core pipeline:

Weather / GIS Data
        ↓
Data Processing
        ↓
Risk Calculation
        ↓
FastAPI
        ↓
GIS Frontend
<nb>
TEAM
Innovision





======================
