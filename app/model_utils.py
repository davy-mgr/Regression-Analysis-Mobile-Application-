"""
Utilities for loading the trained model artifacts and running
predictions / retraining.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model_random_forest.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_names.pkl")

FEATURE_ORDER = ["Gender", "Height", "Z-Score W/A", "Z-Score W/H"]


class ModelService:
    """
    Wraps the trained model + scaler so they're loaded once at startup
    (not re-read from disk on every request) and can be hot-swapped
    in place after a retrain.
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = FEATURE_ORDER
        self.load()

    def load(self):
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        if os.path.exists(FEATURES_PATH):
            self.feature_names = joblib.load(FEATURES_PATH)

    def predict(self, gender: int, height: float, zscore_wa: float, zscore_wh: float) -> float:
        X = pd.DataFrame(
            [[gender, height, zscore_wa, zscore_wh]],
            columns=self.feature_names,
        )
        X_scaled = self.scaler.transform(X)
        pred = self.model.predict(X_scaled)[0]
        return float(pred)

    def retrain(self, df: pd.DataFrame) -> dict:
        """
        Retrains a fresh RandomForestRegressor on the provided dataframe
        and hot-swaps it in place of the current model + scaler.

        Expected columns in df (case-sensitive, matches training pipeline):
          Gender, Height, Z-Score W/A, Z-Score W/H, Z-Score H/A (target)
        """
        required_cols = self.feature_names + ["Z-Score H/A"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Uploaded data is missing required columns: {missing}")

        df = df.dropna(subset=required_cols)
        df = df[(df["Z-Score W/A"].abs() <= 6) & (df["Z-Score H/A"].abs() <= 6) & (df["Z-Score W/H"].abs() <= 6)]

        X = df[self.feature_names]
        y = df["Z-Score H/A"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        new_scaler = StandardScaler()
        X_train_scaled = new_scaler.fit_transform(X_train)
        X_test_scaled = new_scaler.transform(X_test)

        new_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
        new_model.fit(X_train_scaled, y_train)

        preds = new_model.predict(X_test_scaled)
        r2 = r2_score(y_test, preds)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))

        # Persist to disk (overwrite existing artifacts)
        joblib.dump(new_model, MODEL_PATH)
        joblib.dump(new_scaler, SCALER_PATH)

        # Hot-swap in memory
        self.model = new_model
        self.scaler = new_scaler

        return {
            "rows_used": int(len(df)),
            "new_test_r2": float(r2),
            "new_test_rmse": rmse,
        }


# Singleton instance, loaded once when the module is imported
model_service = ModelService()
