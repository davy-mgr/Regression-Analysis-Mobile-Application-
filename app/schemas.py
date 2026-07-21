"""
Pydantic schemas for the Stunting (Height-for-Age Z-Score) Prediction API.

Range constraints below are derived directly from the cleaned training
dataset (39,521 toddler records, ages 0-60 months, Indonesia 2021-2024):
  - height:      observed range 44.0 - 120.0 cm
  - zscore_wa:   filtered to |z| <= 6 during training (biologically plausible
                 range per WHO growth standards; beyond this is almost always
                 a measurement/data-entry error, not a real child)
  - zscore_wh:   same filtering logic, |z| <= 6
  - gender:      binary encoding used in source data (0 / 1); the dataset
                 does not document which value maps to male/female, so this
                 is passed through as-is, matching how the model was trained
"""

from pydantic import BaseModel, Field, ConfigDict


class PredictionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gender": 1,
                "height": 87.3,
                "zscore_wa": -1.35,
                "zscore_wh": -0.62,
            }
        }
    )

    gender: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary gender code as used in the source dataset (0 or 1).",
    )
    height: float = Field(
        ...,
        ge=44.0,
        le=120.0,
        description="Child height in centimeters. Valid range 44.0-120.0 cm, "
        "matching the observed range in the training data (ages 0-60 months).",
    )
    zscore_wa: float = Field(
        ...,
        ge=-6.0,
        le=6.0,
        description="WHO Weight-for-Age Z-Score. Valid range -6.0 to 6.0.",
    )
    zscore_wh: float = Field(
        ...,
        ge=-6.0,
        le=6.0,
        description="WHO Weight-for-Height Z-Score. Valid range -6.0 to 6.0.",
    )


class PredictionResponse(BaseModel):
    predicted_zscore_ha: float = Field(
        ..., description="Predicted Height-for-Age Z-Score."
    )
    stunting_risk: str = Field(
        ..., description="Interpretation: 'stunted' if predicted z-score < -2, else 'normal'."
    )
    model_used: str = Field(..., description="Name of the model that produced this prediction.")


class RetrainResponse(BaseModel):
    status: str
    rows_used: int
    new_test_r2: float
    new_test_rmse: float
    message: str
