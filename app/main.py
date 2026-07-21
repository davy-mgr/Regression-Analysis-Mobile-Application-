"""
Stunting (Height-for-Age Z-Score) Prediction API
==================================================

Serves a trained RandomForestRegressor that predicts a toddler's WHO
Height-for-Age Z-Score from gender, height, weight-for-age z-score, and
weight-for-height z-score.

Run locally:
    uvicorn app.main:app --reload

Docs (Swagger UI):
    http://127.0.0.1:8000/docs
"""

import io
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictionRequest, PredictionResponse, RetrainResponse
from app.model_utils import model_service

app = FastAPI(
    title="Stunting Prediction API",
    description="Predicts Height-for-Age Z-Score for toddlers (0-60 months) "
    "from gender, height, and WHO weight-based z-scores.",
    version="1.0.0",
)

# --------------------------------------------------------------------------
# CORS configuration
# --------------------------------------------------------------------------
# WHAT IS ALLOWED:
#   - allow_origins: set to the Flutter web app's deployed origin (and
#     localhost for development). We do NOT use "*" (wildcard) because this
#     API accepts POST requests that trigger model retraining -- allowing
#     arbitrary origins to call that endpoint would let any website silently
#     trigger retraining or flood the /predict endpoint from a browser
#     context using a visitor's session, an easy vector for abuse.
#   - allow_methods: restricted to GET and POST, since those are the only
#     verbs this API actually exposes (no PUT/DELETE/PATCH anywhere).
#   - allow_headers: restricted to Content-Type and Accept, since JSON
#     POST bodies and file uploads are all this API needs.
#
# WHAT IS RESTRICTED:
#   - No wildcard origin ("*") in production. Update ALLOWED_ORIGINS below
#     with your actual deployed Flutter web origin (or leave the mobile
#     app case aside entirely -- native Flutter mobile builds are not
#     subject to browser CORS at all; CORS only matters for a Flutter *web*
#     build calling this API from a browser).
#   - Credentials (cookies/auth headers) are not allowed cross-origin since
#     this API is stateless and does not use cookie-based auth.
# --------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",       # local web dev
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
    Z-Score, plus a simple stunting-risk interpretation.

    Pydantic enforces types and range constraints automatically -- any
    request with a missing field, wrong type, or out-of-range value is
    rejected with a 422 error before this function body even runs.
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
    Accepts a CSV or Excel file of new labeled data and retrains the model
    from scratch on it, then hot-swaps the retrained model into the running
    service (and overwrites the saved .pkl files on disk).

    Required columns in the uploaded file (case-sensitive):
        Gender, Height, Z-Score W/A, Z-Score W/H, Z-Score H/A

    This is intended for periodic batch retraining as new survey data
    becomes available (e.g. a new DHS/nutrition survey wave), not for
    per-request online learning.
    """
    filename = file.filename or ""
    contents = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a .csv or .xlsx file.",
            )
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
