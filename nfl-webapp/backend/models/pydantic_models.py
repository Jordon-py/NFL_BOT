from pydantic import BaseModel, Field
from typing import Annotated
from enum import Enum


# Define constrained types
WeekType = Annotated[int, Field(ge=1, le=22, description="NFL week number")]
SeasonType = Annotated[int, Field(ge=2003, le=2025, description="NFL Season year")]
WinProbType = Annotated[float, Field(ge=0, le=1, description="Home win probability [0,1]")]

# --- Pydantic DTOs (data transfer objects) ---
class Features(BaseModel):
    """Explicitly define the features our model expects for clarity and validation."""
    home_offense: float = Field(description="Home team offensive rating")   # Offense
    away_offense: float = Field(description="Away team offensive rating")   # Offense

    home_defense: float = Field(description="Home team defensive rating")   # Defense
    away_defense: float = Field(description="Away team defensive rating")   # Defense


class PredictRequest(BaseModel):
    """Contract: What the frontend sends. Keep it small and explicit for teaching."""
    home_team: str = Field(min_length=2, description="Home team code, e.g., 'KC'")
    away_team: str = Field(min_length=2, description="Away team code, e.g., 'BUF'")
    week: WeekType
    season: SeasonType
    features: Features  # Use a nested model for features for better validation and clarity.
    
class Prediction(BaseModel):
    """Contract: Model prediction output including point differential and win probability."""
    point_diff: float = Field(description="Predicted home_points - away_points")
    win_prob_home: WinProbType

class PredictResponse(BaseModel):
    prediction: Prediction
    model_version: str
    latency_ms: float