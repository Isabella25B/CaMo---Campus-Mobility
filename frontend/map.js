// Beispielkoordinaten – hier kannst du euren Campus einsetzen
const CAMPUS_LAT = 48.78262808316957;
const CAMPUS_LNG = 9.16717991367041;

// Karte initialisieren
const map = L.map("map").setView([CAMPUS_LAT, CAMPUS_LNG], 17);

// Kacheln von OpenStreetMap laden
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap-Mitwirkende",
}).addTo(map);

// Beispielmarker setzen
L.marker([CAMPUS_LAT, CAMPUS_LNG])
  .addTo(map)
  .bindPopup("DHBW Fakultät Technik")
  .openPopup();

// Platzhalter für ÖPNV: später hier API-Aufruf einbauen
const departuresDiv = document.getElementById("departures");
departuresDiv.innerHTML =
  "<p>Hier werden später die Live-ÖPNV-Daten angezeigt.</p>";
