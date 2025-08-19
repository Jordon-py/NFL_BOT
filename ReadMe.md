# NFL Bot

```mermaid
Frontend form -> payload built in App.jsx (onSubmit)
HTTP POST -> predict.js calls /api/predict (Vite proxy)
Backend route -> main.py predict(req: PredictRequest) uses req.features.* -> returns PredictResponse (Pydantic validated)
Files / lines to inspect now
pydantic_models.py — model definitions (Features, PredictRequest, Prediction, PredictResponse). Check the Features fields (home_offense, away_offense). (file top → lines ~1–40)
main.py — predict handler; currently accesses home_defense/away_defense. (search for def predict and the lines referencing .home_defense / .away_defense)
App.jsx — onSubmit builds payload: home_team, away_team, week, season, features (home_offense, away_offense). (search for const payload inside onSubmit)
predict.js — network call and error handling. (function predictGame)
vite.config.js — proxy config to forward /api to backend:8000 (ensures fetch('/api/predict') works during dev)
````
