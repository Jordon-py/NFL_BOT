/**
 * src/api/predict.js
 * Teaching goals:
 * - Encapsulate fetch logic (App.jsx stays readable)
 * - Show how to do optimistic UI and basic error handling
 */
export async function predictGame(payload) {
  const requestPayload = buildPredictRequest(payload);  // Validate and build the request payload

  const r = await fetch("/api/predict", {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(requestPayload)
  });


  const data = await r.json().catch(() => ({}));    // If the server returns a 4xx/5xx, it will throw an error
  if (!r.ok) {
    const msg = data?.detail || data?.error || `HTTP ${r.status}`;
    throw new Error(`Predict failed:check predict.js in front end folder ${msg}`);  // Useful surface for juniors: bubble the message up
  }
  return data;
}

// We call the proxy path; Vite forwards to http://localhost:8000