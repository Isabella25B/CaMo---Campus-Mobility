// Zoom-Steuerung für <gmp-map>
document.addEventListener("DOMContentLoaded", () => {
  const mapEl = document.getElementById("map");
  const zoomInBtn = document.getElementById("zoom-in");
  const zoomOutBtn = document.getElementById("zoom-out");

  if (!mapEl || !zoomInBtn || !zoomOutBtn) return;

  // Startwert aus dem HTML-Attribut
  let zoom = parseInt(mapEl.getAttribute("zoom") || "16", 10);

  const applyZoom = () => {
    // <gmp-map> nimmt zoom als Attribut
    mapEl.setAttribute("zoom", String(zoom));
  };

  zoomInBtn.addEventListener("click", () => {
    zoom = Math.min(20, zoom + 1);
    applyZoom();
  });

  zoomOutBtn.addEventListener("click", () => {
    zoom = Math.max(3, zoom - 1);
    applyZoom();
  });
});
