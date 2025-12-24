/**
 * Frontend: map.js
 * Purpose: Einfaches Zoom-Handling für eingebettete Kartenkomponente `<gmp-map>`.
 * Bietet Buttons zum Vergrößern / Verkleinern und setzt das `zoom`-Attribut am
 * Karten-Element.
 */
// Zoom-Steuerung für <gmp-map>
document.addEventListener("DOMContentLoaded", () => {
  const mapEl = document.getElementById("map");
  const zoomInBtn = document.getElementById("zoom-in");
  const zoomOutBtn = document.getElementById("zoom-out");

  if (!mapEl || !zoomInBtn || !zoomOutBtn) return;

  // Startwert aus dem HTML-Attribut
  let zoom = parseInt(mapEl.getAttribute("zoom") || "16", 10);

  /**
   * Setzt das aktuelle Zoom-Level als Attribut auf das Map-Element.
   * Diese Funktion ändert ausschließlich das DOM-Attribut `zoom`.
   */
  const applyZoom = () => {
    // <gmp-map> nimmt zoom als Attribut
    mapEl.setAttribute("zoom", String(zoom));
  };

  // Zoom-In Knopf: erhöht das Zoom-Level bis max 20
  zoomInBtn.addEventListener("click", () => {
    zoom = Math.min(20, zoom + 1);
    applyZoom();
  });

  // Zoom-Out Knopf: verringert das Zoom-Level bis min 3
  zoomOutBtn.addEventListener("click", () => {
    zoom = Math.max(3, zoom - 1);
    applyZoom();
  });
});
