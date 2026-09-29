/**
 * INNOVISION - Interactive Features & Universal Scroll Reveal Engine
 * Covers: main.html + risk.html (map, weather, report sections)
 */

(function () {
    "use strict";

    // 1. DAY & NIGHT MODE TOGGLE
    function initThemeToggle() {
        if (document.getElementById("themeToggleBtn")) return;
        const toggleBtn = document.createElement("button");
        toggleBtn.id = "themeToggleBtn";
        toggleBtn.className = "theme-toggle-btn";
        toggleBtn.ariaLabel = "Toggle Day/Night Mode";
        const savedTheme = localStorage.getItem("innovision_theme") || "night";
        if (savedTheme === "day") {
            document.body.classList.add("day-mode");
            toggleBtn.innerHTML = "<i class=\"fa-solid fa-sun\"></i>";
        } else {
            toggleBtn.innerHTML = "<i class=\"fa-solid fa-moon\"></i>";
        }
        toggleBtn.addEventListener("click", () => {
            const isDay = document.body.classList.toggle("day-mode");
            localStorage.setItem("innovision_theme", isDay ? "day" : "night");
            toggleBtn.innerHTML = isDay ? "<i class=\"fa-solid fa-sun\"></i>" : "<i class=\"fa-solid fa-moon\"></i>";
        });
        document.body.appendChild(toggleBtn);
    }

    // 2. PAGE TRANSITION OVERLAY
    function initPageTransition() {
        let overlay = document.getElementById("pageTransitionOverlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "pageTransitionOverlay";
            overlay.innerHTML = "<div class=\"page-transition-spinner\"></div>";
            document.body.appendChild(overlay);
        }
        window.navigateToPage = function (url) {
            overlay.classList.add("active");
            setTimeout(() => { window.location.href = url; }, 450);
        };
        document.body.addEventListener("click", (e) => {
            const anchor = e.target.closest("a[href]");
            if (!anchor) return;
            const href = anchor.getAttribute("href");
            if (href && !href.startsWith("#") && !href.startsWith("javascript:") && !anchor.target) {
                e.preventDefault();
                window.navigateToPage(href);
            }
        });
    }


    // 4. UNIVERSAL SCROLL REVEAL + PARALLAX
    function initDynamicScrolling() {
        const heroTitleBg  = document.querySelector(".hero-title-bg");
        const glassPanel   = document.querySelector(".glass-panel");
        const globeStage   = document.getElementById("globeStage");
        const dashTitlebar = document.querySelector(".dashboard-titlebar");

        let ticking = false;
        function updateParallax() {
            const sy = window.scrollY || window.pageYOffset;
            if (heroTitleBg)  heroTitleBg.style.transform  = "translateY(" + (sy * 0.38) + "px)";
            if (glassPanel)   glassPanel.style.transform   = "translateY(" + (sy * 0.13) + "px)";
            if (globeStage) {
                const top = globeStage.parentElement ? globeStage.parentElement.offsetTop : 0;
                globeStage.style.transform = "translate(-50%, calc(-50% + " + ((sy - top) * 0.1) + "px))";
            }
            if (dashTitlebar) dashTitlebar.style.transform = "translateY(" + (sy * 0.07) + "px)";
            ticking = false;
        }
        window.addEventListener("scroll", () => { if (!ticking) { requestAnimationFrame(updateParallax); ticking = true; } });

        // All elements that get scroll-reveal — INCLUDING map, weather, report
        const SELECTORS = [
            ".section-fade", ".glass-panel", ".globe-copy", ".globe-interlude",
            ".dashboard-titlebar", ".dashboard-grid", ".analysis-panel",
            ".map-section", ".map-toolbar", ".map-wrap", ".map-footer", ".map-layer-control",
            ".weather-section", ".section-glass-container",
            ".landscape-section", ".risk-detail-section",
            ".info-card", ".dashboard-footer", ".alert-banner"
        ];

        const revealObs = new IntersectionObserver((entries) => {
            entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("in-view"); });
        }, { threshold: 0.08, rootMargin: "0px 0px -30px 0px" });

        function observeAll() {
            SELECTORS.forEach(sel => {
                document.querySelectorAll(sel).forEach((el, i) => {
                    if (el.classList.contains("info-card") && !el.dataset.staggerSet) {
                        el.style.transitionDelay = (i * 0.07) + "s";
                        el.dataset.staggerSet = "1";
                    }
                    if (!el.dataset.revealObserved) {
                        el.dataset.revealObserved = "1";
                        revealObs.observe(el);
                    }
                });
            });
        }

        observeAll();
        const domW = new MutationObserver(() => observeAll());
        domW.observe(document.body, { childList: true, subtree: true });
        document.addEventListener("submit", () => setTimeout(observeAll, 400));
        document.addEventListener("click", (e) => {
            if (e.target.closest("#globeEnterButton, #map-search-button, button[type=\"submit\"]"))
                setTimeout(observeAll, 600);
        });
    }

    function boot() {
        initThemeToggle();
        initPageTransition();
        initDynamicScrolling();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
