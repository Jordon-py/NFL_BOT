/**
 * src/dto/predictDTO.js
 * Goal: Build a *validated-ish* request object that matches the FastAPI PredictRequest DTO.
 * Why: Keep UI clean, reduce bugs, and make the client/server contract explicit.
 *
 * Server contract (see main.py PredictRequest):
 *   {
 *     home_team: str(>=2),
 *     away_team: str(>=2),
 *     week: int (1..22),
 *     season: int (2003..2025),
 *     features: { [k:string]: number }
 *   }
 */

const clamp = (num, lo, hi) => Math.min(Math.max(num, lo), hi);

/**
 * buildPredictRequest(form) -> PredictRequest-like object
 * @param {Object} form  // Raw values from your React state (may be strings)
 * @returns {Object}     // Safe, normalized payload for /api/predict
 */
export function buildPredictRequest(form) {
    // Trim strings and coerce numerics safely. Defaults keep learners un-stuck.
    const home = String(form.home ?? '').trim();
    const away = String(form.away ?? '').trim();

    // Coerce to numbers, then clamp into the server’s documented ranges.
    const week = clamp(Number(form.week ?? 1), 1, 22);
    const season = clamp(Number(form.season ?? 2024), 2003, 2025);

    // Feature bag: keep names stable so the server heuristic sees what it expects.
    const homeOff = Number(form.homeOff ?? 0);
    const awayOff = Number(form.awayOff ?? 0);

    // Lightweight client-side guardrails
    if (home.length < 2) throw new Error("home_team must be 2+ chars (e.g., 'KC').");
    if (away.length < 2) throw new Error("away_team must be 2+ chars (e.g., 'BUF').");

    return {
        home_team: home,
        away_team: away,
        week,
        season,
        features: {
            home_offense: homeOff,
            away_offense: awayOff
        }
    };
}

/* ── Tiny usage demo ──────────────────────────────────────────────────────────
import { buildPredictRequest } from './dto/predictDTO';
const payload = buildPredictRequest({
  home: ' KC ', away: 'BUF',
  week: '3', season: '2024',
  homeOff: '7.2', awayOff: 6.8
});
console.log(payload);
// {
//   home_team: 'KC', away_team: 'BUF',
//   week: 3, season: 2024,
//   features: { home_offense: 7.2, away_offense: 6.8 }
// }
--------------------------------------------------------------------------- */
