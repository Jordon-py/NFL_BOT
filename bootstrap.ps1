# bootstrap.ps1

# Purpose: Automate a minimal, teach-first NFL app: FastAPI backend + Vite/React front-end.
# Notes:
# - No Docker, no gateway. Keep it simple: /api/* on FastAPI, Vite proxy to backend.
# - You can rerun pieces safely; files will be overwritten (idempotent-ish).

$ErrorActionPreference = "Stop"

# --- 0) Helpers ---
function Write-Section($msg){ Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# --- 1) Create folders ---
Write-Section "Create project structure"
$root = Join-Path (Get-Location) "nfl-webapp"
New-Item -ItemType Directory -Force -Path $root | Out-Null
New-Item -ItemType Directory -Force -Path "$root\backend" | Out-Null

# --- 2) Backend files ---
Write-Section "Write backend files"
@'
# requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.4
'@ | Set-Content "$root\backend\requirements.txt"

@'
# .gitignore
__pycache__/
.env
.venv/
'@ | Set-Content "$root\backend\.gitignore"

@'
# backend/main.py
"""
FastAPI backend (no Docker). Teaching goals:
- Show a clean /api/health and /api/predict.
- Use Pydantic models to define the contract (auto OpenAPI).
- Keep inference as a stub for now; we’ll swap in a real model later.
Run:  uvicorn main:app --reload --port 8000
"""
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint, confloat

# --- Pydantic DTOs (data transfer objects) ---
class PredictRequest(BaseModel):
    """Contract: What the frontend sends. Keep it small and explicit for teaching."""
    home_team: str = Field(min_length=2, description="Home team code, e.g., 'KC'")
    away_team: str = Field(min_length=2, description="Away team code, e.g., 'BUF'")
    week: conint(ge=1, le=22) = Field(description="NFL week number")
    season: conint(ge=2003, le=2025) = Field(description="Season year")
    # For Step 1 we accept just two numeric features for clarity.
    features: Dict[str, float] = Field(
        description="Feature bag, e.g., {'home_offense':7.2,'away_offense':6.8}"
    )

class Prediction(BaseModel):
    point_diff: float = Field(description="Predicted home_points - away_points")
    win_prob_home: confloat(ge=0, le=1) = Field(description="Home win probability [0,1]")

class PredictResponse(BaseModel):
    prediction: Prediction
    model_version: str
    latency_ms: float

# --- App init ---
app = FastAPI(title="NFL Backend", version="0.1.0")

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

    # Safely get features with defaults so learners see predictable behavior.
    home_off = float(req.features.get("home_offense", 0.0))
    away_off = float(req.features.get("away_offense", 0.0))

    point_diff = 0.7 * (home_off - away_off)
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
'@ | Set-Content "$root\backend\main.py"

# --- 3) Python venv + install ---
Write-Section "Create Python venv and install backend deps"
Push-Location "$root\backend"
py -3.12 -m venv .venv
# Activate venv for this session
$venvPath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
. $venvPath
pip install --no-input -r requirements.txt
Pop-Location

# --- 4) Frontend scaffold via Vite ---
Write-Section "Scaffold Vite React frontend"
Push-Location $root
# `npm create vite@latest` can prompt; we force params for non-interactive run.
# If it still prompts, accept defaults in the terminal.
npm create vite@latest frontend -- --template react | Out-Null

Push-Location "$root\frontend"
npm i

# --- 5) Frontend files (proxy, API util, App.jsx with form) ---
Write-Section "Write frontend files"

@'
/* vite.config.js
 * Teaching goal:
 * - Proxy /api/* to the FastAPI backend on :8000 so fetch('/api/predict') "just works".
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000"
    }
  }
});
'@ | Set-Content "$root\frontend\vite.config.js"

# Simple LCH-based CSS tokens
@'
:root{
  --bg: lch(98% 0 0);
  --fg: lch(20% 10 260);
  --accent: lch(60% 60 40);
}
@media (prefers-color-scheme: dark){
  :root{ --bg: lch(10% 8 260); --fg: lch(92% 5 260); --accent: lch(70% 45 40); }
}
html,body,#root{ height:100% }
body{ margin:0; font-family: system-ui, sans-serif; background:var(--bg); color:var(--fg); }
main{ max-width:720px; margin:3rem auto; padding:1rem }
label{ display:block; margin:.5rem 0 }
input{ padding:.5rem; margin-left:.5rem }
button{ padding:.6rem 1rem; border:1px solid var(--fg); background:transparent; border-radius:.5rem }
pre{ background:rgba(0,0,0,.05); padding:1rem; border-radius:.5rem; overflow:auto }
'@ | Set-Content "$root\frontend\src\index.css"

# API helper (keeps App.jsx clean, commented for teaching)
@'
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
'@ | New-Item -ItemType File -Force -Path "$root\frontend\src\api\predict.js" | Out-Null

# Replace App.jsx with a small form
@'
import { useState } from "react";
import { predictGame } from "./api/predict";

// Teaching goals in this file:
// - Controlled inputs (React basics)
// - Making a typed-ish payload (string -> number conversions)
// - Handling loading, error, and success states cleanly

export default function App() {
  const [home, setHome] = useState("KC");
  const [away, setAway] = useState("BUF");
  const [week, setWeek] = useState(3);
  const [season, setSeason] = useState(2024);
  const [homeOff, setHomeOff] = useState(7.2);
  const [awayOff, setAwayOff] = useState(6.8);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  async function onSubmit(e){
    e.preventDefault();
    setLoading(true); setErr(""); setResult(null);
    try{
      const payload = {
        home_team: home.trim(),
        away_team: away.trim(),
        week: Number(week),
        season: Number(season),
        features: {
          home_offense: Number(homeOff),
          away_offense: Number(awayOff)
        }
      };
      const data = await predictGame(payload);
      setResult(data);
    }catch(ex){
      setErr(ex.message);
    }finally{
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>NFL Prediction — Step 1</h1>

      <form onSubmit={onSubmit}>
        <label>Home Team <input value={home} onChange={e=>setHome(e.target.value)} /></label>
        <label>Away Team <input value={away} onChange={e=>setAway(e.target.value)} /></label>
        <label>Week <input type="number" value={week} onChange={e=>setWeek(e.target.value)} /></label>
        <label>Season <input type="number" value={season} onChange={e=>setSeason(e.target.value)} /></label>
        <label>Home Offense <input type="number" step="0.1" value={homeOff} onChange={e=>setHomeOff(e.target.value)} /></label>
        <label>Away Offense <input type="number" step="0.1" value={awayOff} onChange={e=>setAwayOff(e.target.value)} /></label>
        <button disabled={loading}>{loading ? "Predicting…" : "Predict"}</button>
      </form>

      {err && <p role="alert">Error: {err}</p>}
      {result && <pre aria-live="polite">{JSON.stringify(result, null, 2)}</pre>}
    </main>
  );
}
'@ | Set-Content "$root\frontend\src\App.jsx"

Pop-Location  # frontend
Pop-Location  # root

Write-Section "Done!"
Write-Host "Next:"
Write-Host "  1) Start backend:  cd $root\backend; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
Write-Host "  2) Start frontend: cd $root\frontend; npm run dev"
Write-Host "Open http://localhost:5173 and click Predict."
