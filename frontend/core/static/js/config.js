
const CONFIG = {
    // If running locally (localhost), use Flask dev port
    API_URL: window.location.hostname === "localhost"
             ? "http://localhost:5001/predict"
             : "/api/predict"   // On deployment, Nginx will forward /predict to Flask
  };
  