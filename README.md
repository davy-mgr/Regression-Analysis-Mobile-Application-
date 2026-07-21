# Stunting Prediction API

FastAPI service that predicts a toddler's Height-for-Age Z-Score from
gender, height, weight-for-age z-score, and weight-for-height z-score.

## 1. Add your model files

Copy the three files you downloaded from the Colab notebook into `app/models/`:

```
app/models/best_model_random_forest.pkl
app/models/scaler.pkl
app/models/feature_names.pkl
```

## 2. Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to see the Swagger UI and test `/predict`
and `/retrain` directly in the browser.

Example request body for `/predict`:
```json
{
  "gender": 1,
  "height": 87.3,
  "zscore_wa": -1.35,
  "zscore_wh": -0.62
}
```

## 3. Deploy to Render (free tier)

1. Push this folder to a GitHub repo (must include `app/models/*.pkl` --
   don't gitignore them, the API needs them at startup).
2. Go to https://render.com -> **New** -> **Web Service**.
3. Connect your GitHub repo.
4. Configure:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**. Render will build and deploy automatically.
6. Once live, your Swagger UI is at:
   `https://<your-service-name>.onrender.com/docs`

## 4. Update CORS before going live

Open `app/main.py` and add your deployed Flutter web app's origin to
`ALLOWED_ORIGINS` (see the comment block above the CORS middleware for the
full reasoning on what's allowed/restricted and why). If your Flutter app
is a native mobile build (not web), CORS does not apply to it at all --
only a Flutter *web* build calling this API from a browser needs to be
listed here.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/docs` | Swagger UI |
| POST | `/predict` | Predict Height-for-Age Z-Score from 4 inputs |
| POST | `/retrain` | Upload a CSV/XLSX of new labeled data to retrain the model |
