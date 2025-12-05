// config.js
// Change API_URL depending on environment
const CONFIG = {
    API_URL: window.location.hostname === "localhost"
             ? "http://localhost:5001"
             : "http://132.247.46.104:5001"
  };
  