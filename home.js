document.body.classList.add("site-loaded");

const sections = document.querySelectorAll(".section-fade");
const sectionObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
        if (entry.isIntersecting) entry.target.classList.add("in-view");
    }
}, { threshold: 0.15 });
sections.forEach((section) => sectionObserver.observe(section));

const canvas = document.querySelector("#sandCursorCanvas");
const context = canvas.getContext("2d");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const grains = [];
let width = 0;
let height = 0;
let pointerX = 0;
let pointerY = 0;

function resizeCanvas() {
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * pixelRatio;
    canvas.height = height * pixelRatio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

if (!reducedMotion) {
    window.addEventListener("pointermove", (event) => {
        pointerX = event.clientX;
        pointerY = event.clientY;
        for (let index = 0; index < 3; index += 1) {
            grains.push({
                x: pointerX + (Math.random() * 10 - 5),
                y: pointerY + (Math.random() * 10 - 5),
                vx: (Math.random() - 0.5) * 1.2,
                vy: Math.random() + 0.4,
                size: Math.random() * 2 + 1,
                alpha: 0.7,
            });
        }
    });

    function animateGrains() {
        context.clearRect(0, 0, width, height);
        for (let index = grains.length - 1; index >= 0; index -= 1) {
            const grain = grains[index];
            grain.x += grain.vx;
            grain.y += grain.vy;
            grain.alpha -= 0.025;
            if (grain.alpha <= 0) {
                grains.splice(index, 1);
                continue;
            }
            context.fillStyle = `rgba(210, 180, 140, ${grain.alpha})`;
            context.fillRect(grain.x, grain.y, grain.size, grain.size);
        }
        requestAnimationFrame(animateGrains);
    }
    animateGrains();
}
