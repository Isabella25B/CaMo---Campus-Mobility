// config.js
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:9601'
    : 'http://vsv-research.volkmann-webservices.de:9601';