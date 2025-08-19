# backend/main.py
"""
FastAPI backend (no Docker). Teaching goals:
    - Show a clean /api/health and /api/predict.
    - Use Pydantic models to define the contract (auto OpenAPI).
    - Keep inference as a stub for now; we’ll swap in a real model later.

Run:  uvicorn main:app --reload --port 8000
"""

from models.pydantic_models import PredictRequest, PredictResponse, Prediction
from fastapi import FastAPI, HTTPException

# ==============================
# --- App init ---
# ==============================
app = FastAPI(
    title="NFL Backend",
    version="0.1.0"
)

# --- Routes ---
@app.get("/api/health")
def health():
    """Lightweight health endpoint to test the wire."""
    return {"status": "ok", "version": "0.1.0"}

@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """
    Step-1 heuristic (teaching stub):
    - Use a tiny linear intuition instead of a model.
    - Negative diff means away-favored; positive favors home.
    - We'll replace this with a real model soon.
    """
    import time, math
    t0 = time.perf_counter()

    # Access features from the nested Pydantic model. No need for .get() with defaults,
    # as Pydantic has already validated that these fields exist and are floats.
    home_off = req.features.home_offense
    away_off = req.features.away_offense
    home_def = req.features.home_defense
    away_def = req.features.away_defense

    # Simple heuristic: offense vs defense for each team, plus home field advantage.
    point_diff = (home_off - away_def) - (away_off - home_def) + 2.5  # 2.5 for home field
    # Logistic squish → probability
    win_prob_home = 1.0 / (1.0 + math.exp(-0.25 * point_diff))

    latency = (time.perf_counter() - t0) * 1000.0
    return PredictResponse(
        prediction=Prediction(point_diff=point_diff, win_prob_home=win_prob_home),
        model_version="0.1.0-stub",
        latency_ms=latency,
    )

# Teaching note:
# We put '/api' in the path so the Vite proxy can forward '/api/*' to http://localhost:8000
# without you touching CORS for now. That keeps the mental model tidy.
