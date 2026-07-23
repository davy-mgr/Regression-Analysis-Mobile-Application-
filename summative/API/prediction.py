"""
prediction.py — Stunting (Height-for-Age Z-Score) Prediction API

Run locally:
    uv run uvicorn prediction:app --reload

Docs (Swagger UI):
    http://127.0.0.1:8000/docs
"""

import io
import os
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model_random_forest.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "feature_names.pkl")
FEATURE_ORDER = ["Gender", "Height", "Z-Score W/A", "Z-Score W/H"]


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
        ..., ge=0, le=1,
        description="Binary gender code as used in the source dataset (0 or 1).",
    )
    height: float = Field(
        ..., ge=44.0, le=120.0,
        description="Child height in centimeters. Valid range 44.0-120.0 cm.",
    )
    zscore_wa: float = Field(
        ..., ge=-6.0, le=6.0,
        description="WHO Weight-for-Age Z-Score. Valid range -6.0 to 6.0.",
    )
    zscore_wh: float = Field(
        ..., ge=-6.0, le=6.0,
        description="WHO Weight-for-Height Z-Score. Valid range -6.0 to 6.0.",
    )


class PredictionResponse(BaseModel):
    predicted_zscore_ha: float = Field(..., description="Predicted Height-for-Age Z-Score.")
    stunting_risk: str = Field(..., description="'stunted' if predicted z-score < -2, else 'normal'.")
    model_used: str = Field(..., description="Name of the model that produced this prediction.")


class RetrainResponse(BaseModel):
    status: str
    rows_used: int
    new_test_r2: float
    new_test_rmse: float
    message: str

class ModelService:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.feature_names = (
            joblib.load(FEATURES_PATH) if os.path.exists(FEATURES_PATH) else FEATURE_ORDER
        )

    def predict(self, gender: int, height: float, zscore_wa: float, zscore_wh: float) -> float:
        X = pd.DataFrame([[gender, height, zscore_wa, zscore_wh]], columns=self.feature_names)
        X_scaled = self.scaler.transform(X)
        return float(self.model.predict(X_scaled)[0])

    def retrain(self, df: pd.DataFrame) -> dict:
        required_cols = self.feature_names + ["Z-Score H/A"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Uploaded data is missing required columns: {missing}")

        df = df.dropna(subset=required_cols)
        df = df[
            (df["Z-Score W/A"].abs() <= 6)
            & (df["Z-Score H/A"].abs() <= 6)
            & (df["Z-Score W/H"].abs() <= 6)
        ]

        X = df[self.feature_names]
        y = df["Z-Score H/A"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        new_scaler = StandardScaler()
        X_train_scaled = new_scaler.fit_transform(X_train)
        X_test_scaled = new_scaler.transform(X_test)

        new_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
        new_model.fit(X_train_scaled, y_train)

        preds = new_model.predict(X_test_scaled)
        r2 = r2_score(y_test, preds)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))

        joblib.dump(new_model, MODEL_PATH)
        joblib.dump(new_scaler, SCALER_PATH)
        self.model = new_model
        self.scaler = new_scaler

        return {"rows_used": int(len(df)), "new_test_r2": float(r2), "new_test_rmse": rmse}


model_service = ModelService()

app = FastAPI(
    title="Stunting Prediction API",
    description="Predicts Height-for-Age Z-Score for toddlers (0-60 months) "
    "from gender, height, and WHO weight-based z-scores.",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5000",
    # Add your deployed Flutter web origin here, e.g.:
    # "https://your-flutter-app.web.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/")
def root():
    return {"message": "Stunting Prediction API is running. Visit /docs for Swagger UI."}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Accepts child measurements and returns the predicted Height-for-Age
    Z-Score. Pydantic enforces types and range constraints automatically —
    invalid requests are rejected with a 422 before this function even runs.
    """
    try:
        pred = model_service.predict(
            gender=request.gender,
            height=request.height,
            zscore_wa=request.zscore_wa,
            zscore_wh=request.zscore_wh,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    risk = "stunted" if pred < -2 else "normal"
    return PredictionResponse(
        predicted_zscore_ha=round(pred, 4),
        stunting_risk=risk,
        model_used="RandomForestRegressor",
    )


@app.post("/retrain", response_model=RetrainResponse)
async def retrain(file: UploadFile = File(...)):
    """
    Accepts a CSV or Excel file of new labeled data, retrains a fresh
    Random Forest on it, and hot-swaps the retrained model into the running
    service (overwriting the saved .pkl files on disk).

    Required columns (case-sensitive):
        Gender, Height, Z-Score W/A, Z-Score W/H, Z-Score H/A
    """
    filename = file.filename or ""
    contents = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload .csv or .xlsx.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    try:
        metrics = model_service.retrain(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {e}")

    return RetrainResponse(
        status="success",
        rows_used=metrics["rows_used"],
        new_test_r2=round(metrics["new_test_r2"], 4),
        new_test_rmse=round(metrics["new_test_rmse"], 4),
        message="Model retrained and hot-swapped successfully.",
    )
