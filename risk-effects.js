const weatherSection = document.querySelector("#weatherSection");
const weatherCanvas = document.querySelector("#weatherAnimCanvas");
const weatherContext = weatherCanvas.getContext("2d");
let canvasWidth = 0;
let canvasHeight = 0;
let weatherParticles = [];
let raining = false;

function updateRainState() {
    const condition = document.querySelector("#weatherConditionVal").textContent.toLowerCase();
    const nextRaining = /rain|shower|storm|drizzle/.test(condition);
    if (nextRaining && !raining) resizeWeatherCanvas();
    raining = nextRaining;
    if (!raining) weatherContext.clearRect(0, 0, canvasWidth, canvasHeight);
}

function resizeWeatherCanvas() {
    const bounds = weatherSection.getBoundingClientRect();
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    canvasWidth = bounds.width;
    canvasHeight = bounds.height;
    weatherCanvas.width = Math.round(canvasWidth * pixelRatio);
    weatherCanvas.height = Math.round(canvasHeight * pixelRatio);
    weatherCanvas.style.width = `${canvasWidth}px`;
    weatherCanvas.style.height = `${canvasHeight}px`;
    weatherContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    weatherParticles = Array.from({ length: 100 }, () => ({
        x: Math.random() * canvasWidth,
        y: Math.random() * canvasHeight,
        length: Math.random() * 20 + 10,
        speed: Math.random() * 8 + 6,
        opacity: Math.random() * 0.6 + 0.2,
    }));
}

new ResizeObserver(resizeWeatherCanvas).observe(weatherSection);
resizeWeatherCanvas();

function animateWeather() {
    if (!raining) {
        weatherContext.clearRect(0, 0, canvasWidth, canvasHeight);
        requestAnimationFrame(animateWeather);
        return;
    }
    weatherContext.clearRect(0, 0, canvasWidth, canvasHeight);
    for (const particle of weatherParticles) {
        weatherContext.beginPath();
        weatherContext.strokeStyle = `rgba(135, 206, 250, ${particle.opacity})`;
        weatherContext.lineWidth = 1.5;
        weatherContext.moveTo(particle.x, particle.y);
        weatherContext.lineTo(particle.x - 1, particle.y + particle.length);
        weatherContext.stroke();
        particle.y += particle.speed;
        particle.x -= 0.5;
        if (particle.y > canvasHeight) {
            particle.y = 0;
            particle.x = Math.random() * canvasWidth;
        }
        if (particle.x < 0) particle.x = canvasWidth;
    }
    requestAnimationFrame(animateWeather);
}

updateRainState();
new MutationObserver(updateRainState).observe(document.querySelector("#weatherConditionVal"), { childList: true, characterData: true, subtree: true });
if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) animateWeather();
