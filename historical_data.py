"""
Historical Landslide Database for Uttarakhand, India.
Compiled from Geological Survey of India (GSI), NDMA, and State Disaster Management Authority records.
"""

import math

HISTORICAL_LANDSLIDES = [
    {
        "id": "ls-01",
        "name": "Joshimath Urban Subsidence & Creep Fractures",
        "district": "Chamoli",
        "latitude": 30.556,
        "longitude": 79.567,
        "elevation_m": 1890,
        "year": 2023,
        "type": "Slope Subsidence & Creep",
        "trigger": "Internal toe erosion, heavy monsoon saturation, ancient slide debris reactivation",
        "impact": ">860 commercial and residential buildings cracked; emergency evacuation ordered",
        "gsi_hazard": "Critical",
        "corridor": "Rishikesh-Badrinath NH-07",
    },
    {
        "id": "ls-02",
        "name": "Kedarnath Valley Catastrophic Debris Surge",
        "district": "Rudraprayag",
        "latitude": 30.735,
        "longitude": 79.067,
        "elevation_m": 3584,
        "year": 2013,
        "type": "Debris Flow & Glacial Breach",
        "trigger": "Multi-day torrential cloudburst (>325 mm) and Chorabari glacial lake breach",
        "impact": "Over 4,000 casualties; catastrophic destruction of Mandakini river corridor",
        "gsi_hazard": "Extreme",
        "corridor": "Char Dham Pilgrimage Route (Kedarnath)",
    },
    {
        "id": "ls-03",
        "name": "Chamoli / Raini Rock-Ice Avalanche & Flash Surge",
        "district": "Chamoli",
        "latitude": 30.485,
        "longitude": 79.738,
        "elevation_m": 2050,
        "year": 2021,
        "type": "Rock-Ice Avalanche & Debris Surge",
        "trigger": "Hanging glacier detachment on Ronti peak into Rishiganga canyon",
        "impact": "204 fatalities; Tapovan-Vishnugad hydel project obliterated",
        "gsi_hazard": "Extreme",
        "corridor": "Dhauliganga Valley",
    },
    {
        "id": "ls-04",
        "name": "Malpa Rockfall & Debris Avalanche",
        "district": "Pithoragarh",
        "latitude": 29.920,
        "longitude": 80.750,
        "elevation_m": 2200,
        "year": 1998,
        "type": "Rockfall & Debris Avalanche",
        "trigger": "Prolonged high-intensity monsoon cloudburst on steep dolomitic gorge",
        "impact": "221 fatalities including Kailash Mansarovar pilgrims; entire Malpa village wiped out",
        "gsi_hazard": "Extreme",
        "corridor": "Dharchula-Lipulekh Border Route",
    },
    {
        "id": "ls-05",
        "name": "Varunavat Parvat Landslide",
        "district": "Uttarkashi",
        "latitude": 30.738,
        "longitude": 78.442,
        "elevation_m": 1250,
        "year": 2003,
        "type": "Massive Rock & Debris Slide",
        "trigger": "Severe monsoon pore-pressure buildup along fractured schist foliation",
        "impact": ">3,000 residents evacuated; extensive urban infrastructure damaged along Bhagirathi",
        "gsi_hazard": "Very High",
        "corridor": "Gangotri National Highway",
    },
    {
        "id": "ls-06",
        "name": "Balia Ravine Chronic Slope Subsidence",
        "district": "Nainital",
        "latitude": 29.382,
        "longitude": 79.462,
        "elevation_m": 1950,
        "year": 2022,
        "type": "Rotational Slump & Ravine Creep",
        "trigger": "Progressive lake-rim drainage saturation and toe cutting in fractured Krol limestone",
        "impact": "Ongoing structural threat to Nainital town core and lower lake basin settlements",
        "gsi_hazard": "High",
        "corridor": "Nainital-Kathgodam Highway",
    },
    {
        "id": "ls-07",
        "name": "Sirobagarh Chronic Landslide Zone",
        "district": "Rudraprayag",
        "latitude": 30.237,
        "longitude": 78.892,
        "elevation_m": 720,
        "year": 2023,
        "type": "Chronic Colluvial Debris Flow",
        "trigger": "Alaknanda toe-scour and fractured quartzites sliding during every monsoon",
        "impact": "Frequent arterial blockage of NH-58; critical supply chain disruptions",
        "gsi_hazard": "High",
        "corridor": "NH-58 Srinagar-Rudraprayag",
    },
    {
        "id": "ls-08",
        "name": "Kaliasaur Fault Slide",
        "district": "Rudraprayag",
        "latitude": 30.258,
        "longitude": 78.932,
        "elevation_m": 680,
        "year": 2021,
        "type": "Shear Zone Rockfall",
        "trigger": "Proximity to Alaknanda fault zone, wedge failure on dip slopes",
        "impact": "Chronic recurring highway closures, vehicular damage",
        "gsi_hazard": "High",
        "corridor": "NH-58 Central Garhwal",
    },
    {
        "id": "ls-09",
        "name": "Lambagar Chronic Slide Zone",
        "district": "Chamoli",
        "latitude": 30.650,
        "longitude": 79.517,
        "elevation_m": 2150,
        "year": 2022,
        "type": "Debris Avalanche & Scree Flow",
        "trigger": "Monsoon torrents destabilizing loose glacial till on 45° slopes",
        "impact": "Major disruption of Badrinath Dham pilgrimage convoys",
        "gsi_hazard": "Very High",
        "corridor": "Joshimath-Badrinath Highway",
    },
    {
        "id": "ls-10",
        "name": "Pagal Nala Torrential Debris Corridor",
        "district": "Chamoli",
        "latitude": 30.538,
        "longitude": 79.528,
        "elevation_m": 1780,
        "year": 2023,
        "type": "High-Velocity Mud & Boulder Flow",
        "trigger": "Localized cloudburst channelization through narrow catchment gulley",
        "impact": "Repeated stranding of border defense and pilgrim vehicles",
        "gsi_hazard": "High",
        "corridor": "NH-07 Helang-Joshimath",
    },
    {
        "id": "ls-11",
        "name": "Madhyamaheshwar Valley Slopes",
        "district": "Rudraprayag",
        "latitude": 30.640,
        "longitude": 79.215,
        "elevation_m": 2400,
        "year": 1998,
        "type": "Co-seismic & Cloudburst Debris Flow",
        "trigger": "Intense rainstorm over steep weathered metamorphic ridges",
        "impact": "109 fatalities across Benta, Mansuna, and surrounding hamlets",
        "gsi_hazard": "Extreme",
        "corridor": "Ukhimath-Madhyamaheshwar Valley",
    },
    {
        "id": "ls-12",
        "name": "Tawaghat - Dharchula Slide",
        "district": "Pithoragarh",
        "latitude": 29.960,
        "longitude": 80.600,
        "elevation_m": 1150,
        "year": 2009,
        "type": "Massive Rockfall & Scree Run",
        "trigger": "Kali river canyon undercutting and monsoon saturation",
        "impact": "43 fatalities, strategic border road severed for 3 weeks",
        "gsi_hazard": "Very High",
        "corridor": "Pithoragarh-Dharchula-Tawaghat Road",
    },
    {
        "id": "ls-13",
        "name": "Kapkot Cloudburst & Slope Failure",
        "district": "Bageshwar",
        "latitude": 29.940,
        "longitude": 79.910,
        "elevation_m": 1100,
        "year": 2010,
        "type": "Rotational Debris Slide",
        "trigger": "Severe monsoon cloudburst over saturated colluvial slopes",
        "impact": "18 school children killed when primary school building collapsed",
        "gsi_hazard": "High",
        "corridor": "Bageshwar-Kapkot-Pindar Valley",
    },
    {
        "id": "ls-14",
        "name": "Kempty Falls Road Slip",
        "district": "Dehradun",
        "latitude": 30.480,
        "longitude": 78.050,
        "elevation_m": 1360,
        "year": 2021,
        "type": "Colluvial Slope Washout",
        "trigger": "High-intensity precipitation on cut slopes along hill road",
        "impact": "Tourist highway blocked, multiple vehicle strandings",
        "gsi_hazard": "Moderate",
        "corridor": "Mussoorie-Chakrata Route",
    },
    {
        "id": "ls-15",
        "name": "Narendra Nagar Bypass Failure",
        "district": "Tehri Garhwal",
        "latitude": 30.170,
        "longitude": 78.300,
        "elevation_m": 1120,
        "year": 2023,
        "type": "Planar Rock Slide",
        "trigger": "Monsoon downpours lubricating bedding planes in weathered quartzite",
        "impact": "Chamba-Rishikesh highway blocked during peak pilgrimage rush",
        "gsi_hazard": "Moderate",
        "corridor": "Rishikesh-Chamba-Tehri Road",
    },
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * R * math.asin(math.sqrt(a))


def find_nearest_landslide(lat: float, lon: float) -> dict:
    nearest = None
    min_dist = float("inf")
    for item in HISTORICAL_LANDSLIDES:
        d = haversine_km(lat, lon, item["latitude"], item["longitude"])
        if d < min_dist:
            min_dist = d
            nearest = item

    return {
        "nearest_site": nearest,
        "distance_km": round(min_dist, 2),
        "proximity_hazard": "Critical (<5km)" if min_dist < 5 else (
            "Elevated (5-15km)" if min_dist < 15 else (
                "Moderate (15-30km)" if min_dist < 30 else "Low (>30km)"
            )
        ),
    }


def get_historical_landslides_geojson() -> dict:
    features = []
    for site in HISTORICAL_LANDSLIDES:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [site["longitude"], site["latitude"]],
            },
            "properties": site,
        })
    return {
        "type": "FeatureCollection",
        "region": "Uttarakhand, India",
        "count": len(features),
        "features": features,
    }
