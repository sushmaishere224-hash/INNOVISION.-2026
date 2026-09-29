function render() {
    globePole.style.display = config.isPoleVisible
        ? "block"
        : "none";

    globeHalo.style.display = config.isHaloVisible
        ? "block"
        : "none";

    var ratio = Math.pow(config.zoom, 1.5);

    pixelExpandOffset = 1.5 * ratio - 1.25;

    ratio = 1 / ratio * 3;

    globe.style[transformStyleName] =
        "scale3d(" + ratio + "," + ratio + ",1)";

    transformGlobe();
}
