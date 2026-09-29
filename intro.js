/**
 * INNOVISION - 3D Cinematic Intro (Himalayan Theme)
 * White Glowing Boulder Cascade + Team INNOVISION Showcase
 */

(function () {
    "use strict";

    function initIntroDOM() {
        if (document.getElementById("innovisionIntro")) return;
        const el = document.createElement("div");
        el.id = "innovisionIntro";
        el.innerHTML = `
            <canvas id="innovisionCanvas"></canvas>
            <div class="innovision-center-content">
                <div class="innovision-title-wrap">
                    <h1 class="innovision-title" id="innovisionTitle">INNOVISION</h1>
                </div>
                <div class="innovision-subtitle" id="innovisionSub">LANDSLIDE PREDICTOR &amp; TERRAIN INTELLIGENCE</div>
                <div class="innovision-team-tag" id="innovisionTeam">DEVELOPED BY TEAM INNOVISION</div>
            </div>
            <button class="innovision-skip-btn" id="innovisionSkip">SKIP INTRO <i class="fa-solid fa-forward" style="margin-left:6px;"></i></button>
        `;
        document.body.prepend(el);
    }

    initIntroDOM();

    const introOverlay = document.getElementById("innovisionIntro");
    const canvas       = document.getElementById("innovisionCanvas");
    const titleEl      = document.getElementById("innovisionTitle");
    const subEl        = document.getElementById("innovisionSub");
    const teamEl       = document.getElementById("innovisionTeam");
    const skipBtn      = document.getElementById("innovisionSkip");

    if (!canvas || !introOverlay) return;

    const ctx = canvas.getContext("2d");
    let width = 0, height = 0, dpr = 1;
    let animationFrameId = null, startTime = null, isFinished = false;
    const fov = 400;

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width  = width  * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);
    }
    resize();
    window.addEventListener("resize", resize);

    const palette = [
        { r:255,g:255,b:255 },
        { r:230,g:245,b:255 },
        { r:0,  g:245,b:212 },
        { r:212,g:175,b:55  },
        { r:226,g:232,b:197 }
    ];

    // 3D Particles
    const PARTICLE_COUNT = 1400;
    const particles = [];

    function create3DParticles() {
        particles.length = 0;
        const baseR = Math.min(width, height) * 0.32;
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            const isLeft = Math.random() < 0.5;
            const sX = isLeft ? (-width*0.6 - Math.random()*400) : (width*0.6 + Math.random()*400);
            const sY = (Math.random()-0.5)*height*1.5;
            const sZ = (Math.random()-0.5)*600;
            const angle = Math.random()*Math.PI*2;
            const ro = (Math.random()-0.5)*(baseR*0.35);
            const r  = baseR + ro;
            const c  = palette[Math.floor(Math.random()*palette.length)];
            particles.push({
                x:sX,y:sY,z:sZ,startX:sX,startY:sY,startZ:sZ,
                targetX:Math.cos(angle)*r, targetY:Math.sin(angle)*r*0.45, targetZ:Math.sin(angle)*r*0.8,
                angle, radius:r,
                size: Math.random()*2.4+0.6,
                baseAlpha: Math.random()*0.8+0.2,
                color:c, delay:Math.random()*1.6,
                orbitSpeed:(Math.random()*0.008+0.003)*(Math.random()<0.5?1:-1),
                pulsePhase:Math.random()*Math.PI*2
            });
        }
    }
    create3DParticles();

    // White Boulders (intro only)
    const boulders = [];
    function genPoly(size) {
        const n = Math.floor(Math.random()*3)+5;
        const pts = [];
        for (let i=0;i<n;i++){
            const a=(i/n)*Math.PI*2;
            const r=size*(0.65+Math.random()*0.35);
            pts.push({x:Math.cos(a)*r,y:Math.sin(a)*r});
        }
        return pts;
    }
    function createBoulders() {
        boulders.length = 0;
        for (let i=0;i<38;i++){
            const isLeft = Math.random()<0.5;
            const size   = Math.random()*22+8;
            const sX     = isLeft ? Math.random()*(width*0.3) : width*0.7+Math.random()*(width*0.3);
            const sY     = -Math.random()*(height*0.4)-40;
            boulders.push({
                x:sX, y:sY,
                vx:(isLeft?1.2:-1.2)*(Math.random()*2.5+1),
                vy:Math.random()*4.5+2.8,
                size, polygon:genPoly(size),
                rotation:Math.random()*Math.PI*2,
                vRot:(Math.random()-0.5)*0.08,
                delay:Math.random()*3+0.6,
                opacity:Math.random()*0.75+0.25
            });
        }
    }
    createBoulders();

    function project3D(x,y,z,rX,rY){
        const cY=Math.cos(rY),sY=Math.sin(rY);
        const x1=x*cY+z*sY, z1=-x*sY+z*cY;
        const cX=Math.cos(rX),sXv=Math.sin(rX);
        const y2=y*cX-z1*sXv, z2=y*sXv+z1*cX;
        const sc=fov/(fov+z2+400);
        return {px:width/2+x1*sc, py:height/2+y2*sc, scale:sc, z:z2};
    }

    function render(ts) {
        if (!startTime) startTime = ts;
        const elapsed = (ts - startTime) / 1000;

        if (elapsed < 2.5) {
            ctx.fillStyle = "rgba(4,10,8,0.32)";
            ctx.fillRect(0,0,width,height);
        } else {
            ctx.clearRect(0,0,width,height);
        }

        const rX = Math.sin(elapsed*0.3)*0.12+0.1;
        const rY = elapsed*0.25;

        if (elapsed >= 1.0 && !titleEl.classList.contains("reveal")) titleEl.classList.add("reveal");
        if (elapsed >= 2.8 && !subEl.classList.contains("reveal"))   subEl.classList.add("reveal");
        if (elapsed >= 3.8 && teamEl && !teamEl.classList.contains("reveal")) teamEl.classList.add("reveal");
        if (elapsed >= 6.4 && !isFinished) finishIntro();

        // Particles
        for (let i=0;i<particles.length;i++){
            const p=particles[i];
            if (elapsed < p.delay) continue;
            const tp = Math.min(1,(elapsed-p.delay)/2.2);
            const ep = 1-Math.pow(1-tp,3);
            p.angle += p.orbitSpeed;
            const cR = p.radius+Math.sin(elapsed*2.5+i)*6;
            const tX=Math.cos(p.angle)*cR, tY=Math.sin(p.angle)*cR*0.45, tZ=Math.sin(p.angle)*cR*0.8;
            const curX=p.startX+(tX-p.startX)*ep;
            const curY=p.startY+(tY-p.startY)*ep;
            const curZ=p.startZ+(tZ-p.startZ)*ep;
            const proj=project3D(curX,curY,curZ,rX,rY);
            p.pulsePhase+=0.04;
            const alpha=p.baseAlpha*(0.8+0.2*Math.sin(p.pulsePhase))*Math.min(1,tp*1.5);
            const ds=Math.max(0.4,p.size*proj.scale);
            ctx.save(); ctx.beginPath();
            ctx.arc(proj.px,proj.py,ds,0,Math.PI*2);
            ctx.fillStyle="rgba("+p.color.r+","+p.color.g+","+p.color.b+","+alpha+")";
            if(ds>1.8){ctx.shadowColor="rgba("+p.color.r+","+p.color.g+","+p.color.b+",0.8)";ctx.shadowBlur=10;}
            ctx.fill(); ctx.restore();
        }

        // Boulders
        for (const b of boulders){
            if (elapsed < b.delay) continue;
            b.x+=b.vx; b.y+=b.vy; b.rotation+=b.vRot;
            if (b.y > height-80) b.opacity-=0.02;
            if (b.opacity<=0||b.y>height+60) continue;
            ctx.save(); ctx.translate(b.x,b.y); ctx.rotate(b.rotation);
            ctx.beginPath();
            ctx.moveTo(b.polygon[0].x,b.polygon[0].y);
            for(let k=1;k<b.polygon.length;k++) ctx.lineTo(b.polygon[k].x,b.polygon[k].y);
            ctx.closePath();
            ctx.fillStyle  ="rgba(255,255,255,"+(b.opacity*0.85)+")";
            ctx.strokeStyle="rgba(255,255,255,"+b.opacity+")";
            ctx.lineWidth=1.8; ctx.shadowColor="rgba(255,255,255,0.9)"; ctx.shadowBlur=12;
            ctx.fill(); ctx.stroke(); ctx.restore();
        }

        if (!isFinished) animationFrameId = requestAnimationFrame(render);
    }

    function finishIntro() {
        if (isFinished) return;
        isFinished = true;
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        introOverlay.classList.add("fade-out");
        setTimeout(() => {
            introOverlay.style.display = "none";
            document.body.classList.add("intro-complete");
        }, 1200);
    }

    animationFrameId = requestAnimationFrame(render);
    if (skipBtn) skipBtn.addEventListener("click", finishIntro);
})();
