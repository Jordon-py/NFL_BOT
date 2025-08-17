/**
 * src/api/predict.js
 * Teaching goals:
 * - Encapsulate fetch logic (App.jsx stays readable)
 * - Show how to do optimistic UI and basic error handling
 */
export async function predictGame(payload) {
  // We call the proxy path; Vite forwards to http://localhost:8000
  const r = await fetch("/api/predict", {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(payload)
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    // Useful surface for juniors: bubble the message up
    const msg = data?.detail || data?.error || `HTTP ${r.status}`;
    throw new Error(`Predict failed: ${msg}`);
  }
  return data;
}