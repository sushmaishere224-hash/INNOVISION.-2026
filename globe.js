import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js";

const stage = document.querySelector("#globeStage");
const canvas = document.querySelector("#globeCanvas");
const loader = document.querySelector("#globeLoadLabel");
const pin = document.querySelector("#globePin");
const enterButton = document.querySelector("#globeEnterButton");
const locationForm = document.querySelector("#globeLocationForm");
const locationInput = document.querySelector("#globeLocationInput");
const locationError = document.querySelector("#globeLocationError");
const hint = document.querySelector("#globeHint");

const places = {
    joshimath: { name: "Joshimath", latitude: 30.57, longitude: 79.57 },
    kedarnath: { name: "Kedarnath", latitude: 30.735, longitude: 79.067 },
    chamoli: { name: "Chamoli", latitude: 30.40, longitude: 79.32 },
    uttarkashi: { name: "Uttarkashi", latitude: 30.73, longitude: 78.44 },
    rudraprayag: { name: "Rudraprayag", latitude: 30.28, longitude: 78.98 },
    pithoragarh: { name: "Pithoragarh", latitude: 29.58, longitude: 80.22 },
    "tehri garhwal": { name: "Tehri Garhwal", latitude: 30.39, longitude: 78.48 },
    nainital: { name: "Nainital", latitude: 29.39, longitude: 79.45 },
    bageshwar: { name: "Bageshwar", latitude: 29.84, longitude: 79.77 },
    dehradun: { name: "Dehradun", latitude: 30.32, longitude: 78.03 },
    rishikesh: { name: "Rishikesh", latitude: 30.09, longitude: 78.27 },
    haldwani: { name: "Haldwani", latitude: 29.22, longitude: 79.52 },
    haridwar: { name: "Haridwar", latitude: 29.946, longitude: 78.164 },
};

function normalizePlaceName(value) {
    return value.trim().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

const placeAliases = new Map([
    ["nannital", "nainital"],
    ["nanital", "nainital"],
]);

let renderer;
try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "high-performance" });
} catch {
    loader.textContent = "3D GLOBE REQUIRES WEBGL";
    throw new Error("WebGL is unavailable in this browser.");
}

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(37, 1, 0.1, 100);
camera.position.z = 7.8;
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.3;

const earthGroup = new THREE.Group();
scene.add(earthGroup);
const earthMaterial = new THREE.MeshStandardMaterial({ roughness: 0.88, metalness: 0.015 });
const earth = new THREE.Mesh(new THREE.SphereGeometry(1.75, 96, 96), earthMaterial);
earthGroup.add(earth);

const atmosphere = new THREE.Mesh(new THREE.SphereGeometry(1.86, 72, 72), new THREE.ShaderMaterial({
    uniforms: { glowColor: { value: new THREE.Color("#d7eaff") } },
    vertexShader: `varying vec3 n; varying vec3 v; void main() { vec4 p = modelViewMatrix * vec4(position, 1.0); n = normalize(normalMatrix * normal); v = normalize(-p.xyz); gl_Position = projectionMatrix * p; }`,
    fragmentShader: `uniform vec3 glowColor; varying vec3 n; varying vec3 v; void main() { float rim = pow(1.0 - max(dot(normalize(n), normalize(v)), 0.0), 3.0); gl_FragColor = vec4(glowColor, rim * .78); }`,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    transparent: true,
    depthWrite: false,
}));
earthGroup.add(atmosphere);

const marker = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 16), new THREE.MeshBasicMaterial({ color: 0xffd58c }));
marker.visible = false;
earthGroup.add(marker);
scene.add(new THREE.AmbientLight(0xa4b9a2, 1.35));
const keyLight = new THREE.DirectionalLight(0xffefd7, 3.1);
keyLight.position.set(-4, 3, 5);
scene.add(keyLight);

function createFallbackTexture() {
    const textureCanvas = document.createElement("canvas");
    textureCanvas.width = 2048;
    textureCanvas.height = 1024;
        const context = textureCanvas.getContext("2d");
    const ocean = context.createLinearGradient(0, 0, 1700, 1000);
    ocean.addColorStop(0, "#244b53");
    ocean.addColorStop(0.5, "#173d43");
    ocean.addColorStop(1, "#112e38");
    context.fillStyle = ocean;
    context.fillRect(0, 0, textureCanvas.width, textureCanvas.height);
    const project = ([longitude, latitude]) => [((longitude + 180) / 360) * textureCanvas.width, ((90 - latitude) / 180) * textureCanvas.height];
    const land = [
        [[-168,69],[-145,72],[-127,61],[-118,54],[-125,45],[-117,32],[-108,29],[-101,19],[-91,18],[-84,10],[-78,8],[-81,25],[-96,29],[-103,39],[-111,48],[-123,50],[-130,58],[-149,60]],
        [[-81,12],[-68,10],[-52,5],[-45,-6],[-50,-23],[-57,-35],[-66,-55],[-74,-50],[-77,-28],[-80,-8]],
        [[-11,36],[-3,44],[10,46],[19,55],[32,59],[44,56],[50,48],[38,40],[29,35],[34,29],[43,13],[52,12],[46,-12],[39,-26],[31,-35],[19,-34],[12,-18],[8,-1],[0,6],[-10,15],[-16,25]],
        [[-17,35],[1,37],[25,34],[39,24],[55,20],[73,8],[83,8],[87,20],[104,8],[119,5],[128,18],[142,11],[152,22],[160,57],[143,62],[131,54],[120,50],[108,56],[96,54],[83,65],[66,70],[49,61],[38,48],[28,42],[17,45],[8,54],[-3,58]],
        [[112,-11],[130,-11],[145,-16],[153,-28],[146,-39],[130,-43],[116,-34],[113,-22]],
    ];
    context.fillStyle = "#85977b";
    context.strokeStyle = "rgba(215, 223, 184, .4)";
    context.lineWidth = 2;
    for (const polygon of land) {
        context.beginPath();
        polygon.map(project).forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y));
        context.closePath();
        context.fill();
        context.stroke();
    }
    context.strokeStyle = "rgba(203, 223, 203, .13)";
    context.lineWidth = 1;
    for (let latitude = -60; latitude <= 60; latitude += 30) {
        const y = project([0, latitude])[1];
        context.beginPath(); context.moveTo(0, y); context.lineTo(textureCanvas.width, y); context.stroke();
    }
    return new THREE.CanvasTexture(textureCanvas);
}

function applyEarthTexture(texture) {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    earthMaterial.map = texture;
    earthMaterial.needsUpdate = true;
    loader.classList.add("is-hidden");
}

const earthImage = new Image();
earthImage.crossOrigin = "anonymous";
let textureSettled = false;
earthImage.onerror = () => {
    textureSettled = true;
    applyEarthTexture(createFallbackTexture());
};
const fallbackTimer = window.setTimeout(() => {
    if (textureSettled || earthMaterial.map) return;
    textureSettled = true;
    applyEarthTexture(createFallbackTexture());
}, 5000);
earthImage.onload = () => {
    textureSettled = true;
    window.clearTimeout(fallbackTimer);
    applyEarthTexture(new THREE.Texture(earthImage));
};
earthImage.src = "https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg";

const starGeometry = new THREE.BufferGeometry();
const starPositions = new Float32Array(180 * 3);
for (let index = 0; index < starPositions.length; index += 3) {
    starPositions[index] = (Math.random() - 0.5) * 24;
    starPositions[index + 1] = (Math.random() - 0.5) * 16;
    starPositions[index + 2] = -2 - Math.random() * 12;
}
starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
const stars = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0xd5e5ce, size: 0.02, transparent: true, opacity: 0.55 }));
scene.add(stars);

function resize() {
    const { width, height } = stage.getBoundingClientRect();
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.fov = width < 450 ? 43 : 37;
    camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(stage);
resize();

let dragging = false;
let pointerX = 0;
let pointerY = 0;
let inertiaX = 0;
let inertiaY = 0;
let movingToTarget = false;
let previousFrameTime = null;
function draw(frameTime) {
    requestAnimationFrame(draw);
    const deltaTime = previousFrameTime === null ? 0 : Math.min(frameTime - previousFrameTime, 50);
    previousFrameTime = frameTime;
    if (!dragging && !movingToTarget) {
        earthGroup.rotation.y += deltaTime * 0.00042 + inertiaX;
        earthGroup.rotation.x += inertiaY;
        inertiaX *= Math.pow(0.96, deltaTime / 16.67);
        inertiaY *= Math.pow(0.96, deltaTime / 16.67);
        earthGroup.rotation.x = THREE.MathUtils.clamp(earthGroup.rotation.x, -0.5, 0.5);
    }
    stars.rotation.y += deltaTime * 0.000018;
    renderer.render(scene, camera);
}
requestAnimationFrame(draw);

stage.addEventListener("pointerdown", (event) => {
    if (movingToTarget) return;
    dragging = true;
    pointerX = event.clientX;
    pointerY = event.clientY;
    inertiaX = 0;
    inertiaY = 0;
    stage.setPointerCapture(event.pointerId);
});
stage.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    inertiaX = (event.clientX - pointerX) * 0.003;
    inertiaY = (event.clientY - pointerY) * 0.002;
    earthGroup.rotation.y += inertiaX;
    earthGroup.rotation.x = THREE.MathUtils.clamp(earthGroup.rotation.x + inertiaY, -0.5, 0.5);
    pointerX = event.clientX;
    pointerY = event.clientY;
});
stage.addEventListener("pointerup", () => { dragging = false; });
stage.addEventListener("pointercancel", () => { dragging = false; });

function positionMarker(latitude, longitude) {
    const latitudeRadians = THREE.MathUtils.degToRad(latitude);
    const longitudeRadians = THREE.MathUtils.degToRad(longitude);
    marker.position.set(
        Math.cos(longitudeRadians) * Math.cos(latitudeRadians) * 1.77,
        Math.sin(latitudeRadians) * 1.77,
        -Math.sin(longitudeRadians) * Math.cos(latitudeRadians) * 1.77,
    );
}

function cameraDistanceForGlobeFill(fillFraction) {
    return earth.geometry.parameters.radius / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * fillFraction);
}

function easeTo(latitude, longitude, finalZoom, complete) {
    movingToTarget = true;
    const fromX = earthGroup.rotation.x;
    const fromY = earthGroup.rotation.y;
    const fromZoom = camera.position.z;
    const targetX = THREE.MathUtils.degToRad(latitude);
    const targetY = -Math.PI / 2 - THREE.MathUtils.degToRad(longitude);
    const deltaY = ((targetY - fromY + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
    const started = performance.now();
    const duration = 1700;
    function frame(now) {
        const progress = Math.min(1, (now - started) / duration);
        const eased = 1 - Math.pow(1 - progress, 4);
        earthGroup.rotation.x = fromX + (targetX - fromX) * eased;
        earthGroup.rotation.y = fromY + deltaY * eased;
        camera.position.z = fromZoom + (finalZoom - fromZoom) * eased;
        if (progress < 1) requestAnimationFrame(frame);
        else { movingToTarget = false; complete(); }
    }
    requestAnimationFrame(frame);
}

enterButton.addEventListener("click", () => {
    enterButton.disabled = true;
    hint.textContent = "ZOOMING TO UTTARAKHAND...";
    stage.classList.add("is-focused");
    positionMarker(30.3, 79);
    marker.visible = true;
    easeTo(30.3, 79.0, cameraDistanceForGlobeFill(0.78), () => {
        enterButton.hidden = true;
        locationForm.hidden = false;
        hint.textContent = "Choose a monitored town or district";
        locationInput.focus();
    }, 1.08);
});

locationForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const normalizedInput = normalizePlaceName(locationInput.value);
    const placeKey = placeAliases.get(normalizedInput) || normalizedInput;
    const place = Object.values(places).find((candidate) => normalizePlaceName(candidate.name) === placeKey);
    if (!place) {
        locationError.textContent = "Choose a listed town or district in Uttarakhand.";
        locationInput.focus();
        return;
    }
    locationError.textContent = "";
    hint.textContent = `ZOOMING TO ${place.name.toUpperCase()}...`;
    positionMarker(place.latitude, place.longitude);
    const finalZoom = cameraDistanceForGlobeFill(0.92);
    easeTo(place.latitude, place.longitude, finalZoom, () => {
        window.location.href = `/risk.html?location=${encodeURIComponent(place.name)}`;
    });
});

window.addEventListener("pagehide", () => renderer.dispose(), { once: true });
