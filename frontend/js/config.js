/**
 * Frontend: config.js
 * Purpose: Definiert die Basis-API-URL (`API_BASE`) abhängig von der Hostumgebung.
 * - lokal (localhost/127.0.0.1) -> Entwicklungs-Backend
 * - sonst -> Produktions-Backend
 */
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:9601'
    : 'http://vsv-research.volkmann-webservices.de:9601';