import { useState } from "react";
import { predictGame } from "./api/predict";

// Teaching goals in this file:
// - Controlled inputs (React basics)
// - Making a typed-ish payload (string -> number conversions)
// - Handling loading, error, and success states cleanly
// App.jsx (inside onSubmit, after e.preventDefault())
// 1) Build + validate fields BEFORE calling predictGame
// 2) Return early with setErr(...) if something is off
// 3) Keep conversions explicit so types are predictable

// Example pattern (not final code):
// const w = Number(week)     // week must be 1..22
// const s = Number(season)   // season must be 2003..2025
// if (!home.trim() || !away.trim()) { setErr("Team codes required"); return; }
// if (w < 1 || w > 22)       { setErr("Week out of range"); return; }
// if (s < 2003 || s > 2025)  { setErr("Season out of range"); return; }
// if (Number.isNaN(Number(homeOff)) || Number.isNaN(Number(awayOff))) {
//   setErr("Features must be numeric"); return;
// }


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

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true); setErr(""); setResult(null);
    try {
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
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>NFL Prediction — Step 1</h1>

      <form onSubmit={onSubmit}>
        <label>Home Team <input value={home} onChange={e => setHome(e.target.value)} /></label>
        <label>Away Team <input value={away} onChange={e => setAway(e.target.value)} /></label>
        <label>Week <input type="number" value={week} onChange={e => setWeek(e.target.value)} /></label>
        <label>Season <input type="number" value={season} onChange={e => setSeason(e.target.value)} /></label>
        <label>Home Offense <input type="number" step="0.1" value={homeOff} onChange={e => setHomeOff(e.target.value)} /></label>
        <label>Away Offense <input type="number" step="0.1" value={awayOff} onChange={e => setAwayOff(e.target.value)} /></label>
        <button disabled={loading}>{loading ? "Predicting…" : "Predict"}</button>
      </form>

      {err && <p role="alert">Error: {err}</p>}
      {result && <pre aria-live="polite">{JSON.stringify(result, null, 2)}</pre>}
    </main>
  );
}
