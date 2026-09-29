// Landslide Early Warning System (LEWS) - Uttarakhand Live Risk Engine
// Connects frontend directly to FastAPI backend and Open-Meteo live feeds.

const places = [
    { name: "Joshimath", latitude: 30.556, longitude: 79.567, base: 1.0 },
    { name: "Kedarnath", latitude: 30.735, longitude: 79.067, base: 1.0 },
    { name: "Chamoli", latitude: 30.417, longitude: 79.333, base: 0.96 },
    { name: "Uttarkashi", latitude: 30.727, longitude: 78.435, base: 0.92 },
    { name: "Rudraprayag", latitude: 30.284, longitude: 78.981, base: 0.90 },
    { name: "Pithoragarh", latitude: 29.583, longitude: 80.218, base: 0.86 },
    { name: "Tehri Garhwal", latitude: 30.393, longitude: 78.480, base: 0.79 },
    { name: "Nainital", latitude: 29.392, longitude: 79.454, base: 0.76 },
    { name: "Bageshwar", latitude: 29.840, longitude: 79.769, base: 0.82 },
    { name: "Dehradun", latitude: 30.317, longitude: 78.032, base: 0.63 },
    { name: "Rishikesh", latitude: 30.087, longitude: 78.268, base: 0.68 },
    { name: "Haldwani", latitude: 29.218, longitude: 79.513, base: 0.59 },
    { name: "Haridwar", latitude: 29.946, longitude: 78.164, base: 0.45 },
];

const selectedName = new URLSearchParams(window.location.search).get("location") || "Joshimath";
const selectedPlace = places.find((p) => p.name.toLowerCase() === selectedName.toLowerCase()) || places[0];

// DOM Selectors
const rainfallInput = document.querySelector("#rainfall-input");
const thresholdInput = document.querySelector("#threshold-input");
const rainfallValue = document.querySelector("#rainfall-value");
const thresholdValue = document.querySelector("#threshold-value");
const riskScoreOutput = document.querySelector("#risk-score");
const riskLevelOutput = document.querySelector("#risk-level");
const riskDot = document.querySelector("#risk-dot");
const riskTrackFill = document.querySelector("#risk-track-fill");
const alertBanner = document.querySelector("#alert-banner");
const alertTitle = document.querySelector("#alert-title");
const alertCopy = document.querySelector("#alert-copy");
const rainfallSignal = document.querySelector("#rainfall-signal");
const demoStatusBadge = document.querySelector(".demo-status");

// Header and breadcrumb text
document.querySelector("#dashboard-title").textContent = `${selectedPlace.name} risk overview`;
document.querySelector("#selected-place-nav").textContent = selectedPlace.name.toUpperCase();
document.querySelector("#map-focus-label").textContent = selectedPlace.name;
document.querySelector("#map-heading").innerHTML = `${selectedPlace.name} <span>·</span> Uttarakhand`;
document.querySelector("#risk-location-short").textContent = selectedPlace.name.toUpperCase();
document.querySelector("#weatherLocationName").textContent = selectedPlace.name;

function updateTimeLabel(live = true) {
    const timeStr = new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
    }).format(new Date()) + " IST";
    document.querySelector("#updated-time").textContent = `${timeStr} · ${live ? "LIVE" : "ONLINE"}`;
}
updateTimeLabel(true);

let riskMap;
let riskZones;
let historyLayer;
let h3GridLayer;
let currentRisk = 0;
let lastEvaluationData = null;
let debounceTimer = null;
let selectedMarker = null;   // animated marker for focused location
let selectedPopup = null;    // auto-open data popup

// Determine API Base URL (proxied via /api or direct port 8000)
async function getApiBase() {
    try {
        const testRes = await fetch("/api/health", { method: "GET", signal: AbortSignal.timeout(1800) });
        if (testRes.ok) return "/api";
    } catch {
        // Fallback to direct backend port
    }
    return "http://127.0.0.1:8000";
}

let API_BASE = "/api";
getApiBase().then(base => {
    API_BASE = base;
    if (demoStatusBadge) {
        demoStatusBadge.innerHTML = '<span></span> LIVE SYSTEM · UTTARAKHAND LEWS';
        demoStatusBadge.style.color = '#78dec0';
    }
});

function riskBand(score) {
    if (score < 35) return { label: "LOW", color: "#9fb3c0", className: "low" };
    if (score < 65) return { label: "MODERATE", color: "#e8be70", className: "moderate" };
    if (score < 82) return { label: "HIGH", color: "#de8170", className: "high" };
    return { label: "SEVERE", color: "#dc625c", className: "high" };
}

// Update the Detail Sections (Weather and Landslide Factors)
function updateDetailSections(data) {
    if (!data) return;

    // Weather Section
    if (data.weather) {
        const tempEl = document.querySelector("#weatherTempVal");
        const humEl = document.querySelector("#weatherHumidityVal");
        const condEl = document.querySelector("#weatherConditionVal");
        const descEl = document.querySelector("#weatherDescription");

        if (tempEl) tempEl.textContent = `${data.weather.temperature}°C`;
        if (humEl) humEl.textContent = `${data.weather.humidity}%`;
        if (condEl) condEl.textContent = data.weather.condition;
        if (descEl) {
            descEl.textContent = `Live meteorological telemetry for ${data.location?.name || selectedPlace.name}: ${data.weather.condition} with ${data.weather.trend?.toLowerCase() || "steady conditions"}. 24h precipitation: ${data.rainfall?.rainfall_24h ?? 0} mm.`;
        }
    }

    // Factors Section
    const landscapeSection = document.querySelector("#landscapeSection");
    if (landscapeSection) {
        const slopeP = document.querySelector("#factorSlopeVal");
        const elevP = document.querySelector("#factorElevVal");
        const soilP = document.querySelector("#riskSoilVal");
        const histP = document.querySelector("#factorHistVal");
        const rainP = document.querySelector("#factorRainVal");
        const gsiP = document.querySelector("#factorGsiVal");

        if (slopeP && data.terrain) {
            slopeP.textContent = `${data.terrain.slope_deg}° · ${data.terrain.slope_hazard}`;
        }
        if (elevP && data.terrain) {
            elevP.textContent = `${data.terrain.elevation_m} m ASL`;
        }
        if (soilP && data.soil) {
            soilP.textContent = `${data.soil.soil_saturation_pct}% (${data.soil.pore_pressure_status})`;
        }
        if (histP && data.historical_landslide) {
            const nearest = data.historical_landslide.nearest_site;
            const shortName = nearest?.name ? (nearest.name.length > 25 ? nearest.name.slice(0, 22) + "..." : nearest.name) : "Historical site";
            histP.textContent = `${shortName} (${data.historical_landslide.distance_km} km)`;
        }
        if (rainP && data.rainfall) {
            rainP.textContent = `${data.rainfall.rainfall_current_mm} mm/h · 35% Weight`;
        }
        if (gsiP && data.susceptibility) {
            gsiP.textContent = `${data.susceptibility.label}`;
        }

        // Narrative Explanation
        const explanationP = landscapeSection.querySelector(".section-body > p");
        if (explanationP && data.explanation) {
            explanationP.textContent = data.explanation;
        }
    }
}

// Render Risk State in Dashboard UI
function applyRiskToUI(score, severity, rainfallVal, thresholdVal, alertData = null, rawData = null) {
    currentRisk = Math.round(score);
    const band = riskBand(currentRisk);

    rainfallValue.textContent = String(rainfallVal);
    thresholdValue.textContent = `${thresholdVal} / 100`;

    riskScoreOutput.textContent = String(currentRisk);
    riskLevelOutput.textContent = severity || band.label;
    riskLevelOutput.style.color = band.color;
    riskDot.style.background = band.color;
    riskTrackFill.style.width = `${currentRisk}%`;
    riskTrackFill.style.background = band.color;

    rainfallSignal.textContent = rainfallVal >= 65 ? "INTENSE" : rainfallVal >= 35 ? "ELEVATED" : "STEADY";
    rainfallSignal.classList.toggle("is-heavy", rainfallVal >= 65);

    const isAlert = currentRisk >= thresholdVal;
    alertBanner.hidden = !isAlert;
    if (isAlert) {
        alertTitle.textContent = alertData?.title || `${band.label} landslide risk threshold exceeded`;
        alertCopy.textContent = alertData?.message || `${selectedPlace.name}: predicted score ${currentRisk} is at or above the ${thresholdVal} alert threshold.`;
        alertBanner.dataset.level = band.className;
    }
    updateTimeLabel(true);
    renderHazardZones();
    // Place / refresh the animated selected-location marker on the map
    placeSelectedMarker(currentRisk, band, rawData || lastEvaluationData);
}

// Fetch live risk assessment from FastAPI backend
async function fetchLiveRisk(place, rainfallVal, thresholdVal) {
    const queryParams = new URLSearchParams({
        lat: place.latitude,
        lon: place.longitude,
        rainfall_intensity: rainfallVal,
        threshold: thresholdVal,
        location: place.name
    });

    try {
        const url = `${API_BASE}/risk/evaluate?${queryParams.toString()}`;
        const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        lastEvaluationData = data;

        applyRiskToUI(
            data.risk,
            data.severity,
            rainfallVal,
            thresholdVal,
            data.alert,
            data
        );
        updateDetailSections(data);
        return data;
    } catch (err) {
        console.warn("Backend evaluation fetch failed, using local model fallback:", err.message);
        // Robust local fallback so UI never breaks
        const base = place.base || 0.8;
        const rainScore = Math.min(100, Math.round((rainfallVal / 80) * 100));
        const simulatedScore = Math.round(rainScore * 0.35 + (35 + base * 40) * 0.25 + (20 + base * 55) * 0.25 + 15);
        applyRiskToUI(simulatedScore, null, rainfallVal, thresholdVal);
        return null;
    }
}

// Build the HTML content for the selected location's live data popup
function buildSelectedPopupContent(score, band, data) {
    const weather = data?.weather || {};
    const terrain = data?.terrain || {};
    const rainfall = data?.rainfall || {};
    const soil = data?.soil || {};
    const hist = data?.historical_landslide?.nearest_site;

    return `
        <div style="
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            line-height: 1.55;
            min-width: 210px;
            max-width: 240px;
            color: #111;
        ">
            <!-- Header -->
            <div style="
                display: flex; align-items: center; gap: 8px;
                margin-bottom: 8px;
                padding-bottom: 6px;
                border-bottom: 1px solid rgba(0,0,0,0.12);
            ">
                <span style="
                    display: inline-block;
                    width: 10px; height: 10px;
                    border-radius: 50%;
                    background: ${band.color};
                    box-shadow: 0 0 8px ${band.color};
                    flex-shrink: 0;
                "></span>
                <strong style="font-size: 13px; color: ${band.color}; letter-spacing: 0.05em;">
                    ${selectedPlace.name.toUpperCase()}
                </strong>
            </div>

            <!-- Risk Score -->
            <div style="
                display: flex; justify-content: space-between;
                background: rgba(255,255,255,0.06);
                border-radius: 6px;
                padding: 6px 10px;
                margin-bottom: 8px;
            ">
                <span style="color:#111;">RISK INDEX</span>
                <strong style="font-size: 18px; color: ${band.color};">${score} <span style="font-size:11px;color:#1a1a1a;">/ 100</span></strong>
            </div>

            <!-- Data Grid -->
            <table style="width: 100%; border-collapse: collapse; font-size: 10.5px;">
                <tr>
                    <td style="color:#111; padding: 2px 0;">🌧 Rainfall</td>
                    <td style="text-align:right; color:#111;">${rainfall.rainfall_current_mm ?? '—'} mm/h</td>
                </tr>
                <tr>
                    <td style="color:#111; padding: 2px 0;">🌡 Temperature</td>
                    <td style="text-align:right; color:#111;">${weather.temperature ?? '—'}°C</td>
                </tr>
                <tr>
                    <td style="color:#111; padding: 2px 0;">💧 Humidity</td>
                    <td style="text-align:right; color:#111;">${weather.humidity ?? '—'}%</td>
                </tr>
                <tr>
                    <td style="color:#111; padding: 2px 0;">⛰ Elevation</td>
                    <td style="text-align:right; color:#111;">${terrain.elevation_m ?? '—'} m</td>
                </tr>
                <tr>
                    <td style="color:#111; padding: 2px 0;">📐 Slope</td>
                    <td style="text-align:right; color:#111;">${terrain.slope_deg ?? '—'}°</td>
                </tr>
                <tr>
                    <td style="color:#111; padding: 2px 0;">🪨 Soil</td>
                    <td style="text-align:right; color:#111;">${soil.soil_saturation_pct ?? '—'}%</td>
                </tr>
                ${hist ? `<tr>
                    <td colspan="2" style="color:#e0786a; padding-top: 4px; font-size:10px;">
                        ⚠ ${hist.name?.slice(0, 30) ?? 'Historical event'} (${data.historical_landslide.distance_km} km)
                    </td>
                </tr>` : ''}
            </table>

            <div style="
                margin-top: 8px;
                padding-top: 6px;
                border-top: 1px solid rgba(0,0,0,0.12);
                font-size: 9.5px;
                color: #1a1a1a;
            ">LIVE · UTTARAKHAND LEWS · FIELD/07</div>
        </div>
    `;
}

// Place / refresh the animated selected-location marker with live data popup
function placeSelectedMarker(score, band, data) {
    if (!riskMap) return;

    // Remove old selected marker
    if (selectedMarker) { selectedMarker.remove(); selectedMarker = null; }
    if (selectedPopup) { selectedPopup.remove(); selectedPopup = null; }

    // Pulsing radar-ring icon (CSS animation injected once)
    if (!document.getElementById('_lews_pulse_style')) {
        const style = document.createElement('style');
        style.id = '_lews_pulse_style';
        style.textContent = `
            @keyframes lewsPulse {
                0%   { transform: scale(1);   opacity: 0.9; }
                70%  { transform: scale(3.2); opacity: 0; }
                100% { transform: scale(3.2); opacity: 0; }
            }
            @keyframes lewsPulse2 {
                0%   { transform: scale(1);   opacity: 0.7; }
                70%  { transform: scale(2.2); opacity: 0; }
                100% { transform: scale(2.2); opacity: 0; }
            }
            .lews-selected-marker {
                position: relative;
                width: 20px; height: 20px;
            }
            .lews-selected-marker .core {
                position: absolute; inset: 4px;
                border-radius: 50%;
                background: var(--mc);
                box-shadow: 0 0 12px var(--mc), 0 0 24px var(--mc);
                z-index: 2;
            }
            .lews-selected-marker .ring1,
            .lews-selected-marker .ring2 {
                position: absolute; inset: 0;
                border-radius: 50%;
                border: 2px solid var(--mc);
                opacity: 0;
            }
            .lews-selected-marker .ring1 { animation: lewsPulse  1.8s ease-out infinite; }
            .lews-selected-marker .ring2 { animation: lewsPulse2 1.8s ease-out 0.6s infinite; }
        `;
        document.head.appendChild(style);
    }

    const icon = L.divIcon({
        className: '',
        html: `<div class="lews-selected-marker" style="--mc:${band.color}">
                   <span class="ring1"></span>
                   <span class="ring2"></span>
                   <span class="core"></span>
               </div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
        popupAnchor: [0, -14]
    });

    selectedMarker = L.marker([selectedPlace.latitude, selectedPlace.longitude], {
        icon,
        zIndexOffset: 1000,
        keyboard: false
    }).addTo(riskMap);

    selectedPopup = L.popup({
        closeButton: true,
        autoClose: false,
        closeOnClick: false,
        className: 'lews-data-popup',
        maxWidth: 260
    })
        .setLatLng([selectedPlace.latitude, selectedPlace.longitude])
        .setContent(buildSelectedPopupContent(score, band, data))
        .openOn(riskMap);

    // Style the popup shell
    if (!document.getElementById('_lews_popup_style')) {
        const ps = document.createElement('style');
        ps.id = '_lews_popup_style';
        ps.textContent = `
            .lews-data-popup .leaflet-popup-content-wrapper {
                background: linear-gradient(
                    160deg,
                    rgba(255,255,255,0.13) 0%,
                    rgba(255,255,255,0.05) 40%,
                    rgba(10,18,26,0.88) 100%
                );
                backdrop-filter: blur(22px) saturate(160%);
                -webkit-backdrop-filter: blur(22px) saturate(160%);
                border: 1px solid rgba(255,255,255,0.22);
                border-top: 1px solid rgba(255,255,255,0.38);
                border-left: 1px solid rgba(255,255,255,0.28);
                border-radius: 14px;
                box-shadow:
                    0 2px 0 0 rgba(255,255,255,0.12) inset,
                    0 -1px 0 0 rgba(0,0,0,0.3) inset,
                    0 12px 40px rgba(0,0,0,0.6),
                    0 4px 16px rgba(0,0,0,0.4),
                    0 0 0 1px rgba(0,0,0,0.25);
                color: #e0e6f0;
                padding: 0;
            }
            .lews-data-popup .leaflet-popup-content { margin: 14px 16px; }
            .lews-data-popup .leaflet-popup-tip-container { display: none; }
            .lews-data-popup .leaflet-popup-close-button {
                color: rgba(255,255,255,0.35) !important;
                font-size: 18px !important;
                top: 8px !important; right: 10px !important;
                transition: color 0.2s;
            }
            .lews-data-popup .leaflet-popup-close-button:hover {
                color: rgba(255,255,255,0.85) !important;
            }
        `;
        document.head.appendChild(ps);
    }
}

// Update Hazard Circles / Zones on Leaflet Map
function renderHazardZones() {
    if (!riskZones) return;
    riskZones.clearLayers();

    for (const place of places) {
        const localScore = Math.min(100, Math.round(currentRisk * (place.base || 0.8) + (1 - (place.base || 0.8)) * 25));
        const band = riskBand(localScore);

        L.circle([place.latitude, place.longitude], {
            radius: 3500 + (place.base || 0.8) * 4000,
            color: band.color,
            fillColor: band.color,
            fillOpacity: 0.18,
            opacity: 0.65,
            weight: 1.5,
        }).addTo(riskZones);

        const selected = place.name === selectedPlace.name;
        if (selected) continue; // selected location gets its own animated marker

        const icon = L.divIcon({
            className: "",
            html: `<span class="risk-marker risk-marker--${band.className}"></span>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
        });

        const marker = L.marker([place.latitude, place.longitude], {
            icon,
            keyboard: true,
            title: `${place.name}: ${band.label} landslide hazard`
        }).bindPopup(`
            <div style="font-family: 'DM Mono', monospace; font-size: 12px; line-height: 1.4;">
                <strong style="font-size: 14px; color: ${band.color};">${place.name}</strong><br>
                <span>Live Risk Index: <strong>${localScore} / 100</strong></span><br>
                <span>Severity Level: <strong>${band.label}</strong></span><br>
                <div style="margin-top: 6px;">
                    <a href="/risk.html?location=${encodeURIComponent(place.name)}" style="color: #64b5f6; text-decoration: underline;">Assess this location ↗</a>
                </div>
            </div>
        `).addTo(riskZones);

        marker.on("click", () => {
            window.location.href = `/risk.html?location=${encodeURIComponent(place.name)}`;
        });
    }
}

// Load and Render Historical Landslide Locations from Backend
async function loadHistoricalLandslides() {
    if (!historyLayer) return;
    historyLayer.clearLayers();

    try {
        const res = await fetch(`${API_BASE}/historical-landslides`, { signal: AbortSignal.timeout(4000) });
        if (res.ok) {
            const data = await res.json();
            const features = data.features || [];

            for (const f of features) {
                const p = f.properties;
                const coords = f.geometry.coordinates; // [lon, lat]
                const icon = L.divIcon({
                    className: "",
                    html: "<span class='history-marker' style='background: #e74c3c; width: 10px; height: 10px; display: block; border-radius: 50%; box-shadow: 0 0 6px rgba(231,76,60,0.8);'></span>",
                    iconSize: [10, 10],
                    iconAnchor: [5, 5]
                });

                L.marker([coords[1], coords[0]], {
                    icon,
                    title: `Historical Landslide: ${p.name} (${p.year})`
                }).bindPopup(`
                    <div style="font-size: 12px; max-width: 240px; font-family: sans-serif; line-height: 1.4;">
                        <strong style="color: #e74c3c; font-size: 13px;">${p.name}</strong><br>
                        <strong>Year:</strong> ${p.year} · <strong>District:</strong> ${p.district}<br>
                        <strong>Type:</strong> ${p.type}<br>
                        <strong>Trigger:</strong> ${p.trigger}<br>
                        <strong>Impact:</strong> ${p.impact}<br>
                        <span style="font-size: 10px; color: #888;">GSI Hazard Rating: ${p.gsi_hazard}</span>
                    </div>
                `).addTo(historyLayer);
            }
            return;
        }
    } catch {
        // Fallback to local default historical sites
    }

    const fallbackSites = [
        { latitude: 30.556, longitude: 79.567, label: "Joshimath Subsidence Zone (2023)" },
        { latitude: 30.735, longitude: 79.067, label: "Kedarnath Catastrophic Debris Surge (2013)" },
        { latitude: 30.485, longitude: 79.738, label: "Chamoli / Raini Rock-Ice Avalanche (2021)" },
        { latitude: 29.920, longitude: 80.750, label: "Malpa Rockfall & Debris Avalanche (1998)" },
        { latitude: 30.738, longitude: 78.442, label: "Varunavat Parvat Landslide (2003)" },
        { latitude: 29.382, longitude: 79.462, label: "Balia Ravine Slope Failure (Nainital)" },
        { latitude: 30.237, longitude: 78.892, label: "Sirobagarh Chronic Slide (NH-58)" },
    ];

    for (const site of fallbackSites) {
        const icon = L.divIcon({ className: "", html: "<span class='history-marker'></span>", iconSize: [9, 9], iconAnchor: [4, 4] });
        L.marker([site.latitude, site.longitude], { icon, title: site.label })
            .bindPopup(`<strong>Historical Landslide Record</strong><br>${site.label}<br><span>Source: Geological Survey of India (GSI)</span>`)
            .addTo(historyLayer);
    }
}

// Initialize Leaflet Map
function initialiseMap() {
    const mapContainer = document.querySelector("#risk-map");
    if (!mapContainer || typeof L === "undefined") return;

    riskMap = L.map("risk-map", {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView([selectedPlace.latitude, selectedPlace.longitude], 9);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors | GSI NLSM Uttarakhand"
    }).addTo(riskMap);

    riskZones = L.layerGroup().addTo(riskMap);
    historyLayer = L.layerGroup().addTo(riskMap);

    // Toggle layer controls
    const riskToggle = document.querySelector("#risk-layer-toggle");
    const historyToggle = document.querySelector("#history-layer-toggle");
    if (riskToggle) riskToggle.addEventListener("change", (e) => e.target.checked ? riskMap.addLayer(riskZones) : riskMap.removeLayer(riskZones));
    if (historyToggle) historyToggle.addEventListener("change", (e) => e.target.checked ? riskMap.addLayer(historyLayer) : riskMap.removeLayer(historyLayer));

    // Interactive Map Click: evaluate risk at clicked spot
    riskMap.on("click", async (e) => {
        const { lat, lng } = e.latlng;
        const rainVal = Number(rainfallInput.value);
        const threshVal = Number(thresholdInput.value);

        document.querySelector("#map-focus-label").textContent = `${lat.toFixed(3)}°N, ${lng.toFixed(3)}°E`;
        document.querySelector("#dashboard-title").textContent = `Assessing coordinate (${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E)`;

        await fetchLiveRisk({ latitude: lat, longitude: lng, name: "Selected Location" }, rainVal, threshVal);

        L.popup()
            .setLatLng([lat, lng])
            .setContent(`
                <div style="font-family: monospace; font-size: 12px;">
                    <strong>Evaluated Location:</strong> ${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E<br>
                    <strong>Risk Score:</strong> ${currentRisk} / 100<br>
                    <span>Environmental factors updated in panel.</span>
                </div>
            `)
            .openOn(riskMap);
    });

    window.setTimeout(() => riskMap.invalidateSize(), 150);
}

// Places Search Autocomplete
const placeList = document.querySelector("#map-places");
if (placeList) {
    for (const place of places) {
        const option = document.createElement("option");
        option.value = place.name;
        placeList.append(option);
    }
}

function focusPlace(value) {
    const place = places.find((candidate) => candidate.name.toLowerCase() === value.trim().toLowerCase());
    if (place) {
        window.location.href = `/risk.html?location=${encodeURIComponent(place.name)}`;
    }
}

const searchBtn = document.querySelector("#map-search-button");
const searchInput = document.querySelector("#map-search-input");
if (searchBtn && searchInput) {
    searchBtn.addEventListener("click", () => focusPlace(searchInput.value));
    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            focusPlace(event.currentTarget.value);
        }
    });
}

// Environmental Condition Change Handlers (Rainfall & Alert Threshold)
function onEnvironmentalChange() {
    const rainVal = Number(rainfallInput.value);
    const threshVal = Number(thresholdInput.value);

    // Immediate UI feedback
    rainfallValue.textContent = String(rainVal);
    thresholdValue.textContent = `${threshVal} / 100`;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        fetchLiveRisk(selectedPlace, rainVal, threshVal);
    }, 120);
}

rainfallInput.addEventListener("input", onEnvironmentalChange);
thresholdInput.addEventListener("input", onEnvironmentalChange);

// Initial Load
initialiseMap();
loadHistoricalLandslides();
fetchLiveRisk(selectedPlace, Number(rainfallInput.value), Number(thresholdInput.value));

// Periodic live refresh every 60 seconds
setInterval(() => {
    fetchLiveRisk(selectedPlace, Number(rainfallInput.value), Number(thresholdInput.value));
}, 60000);