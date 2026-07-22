# Linear Regression Model — Stunting Prediction

Predicts a toddler's WHO Height-for-Age Z-Score from gender, height,
weight-for-age z-score, and weight-for-height z-score.

## Structure

```
linear_regression_model/
├── summative/
│   ├── linear_regression/
│   │   └── multivariate.ipynb      # EDA, feature engineering, model training/comparison
│   ├── API/
│   │   └── prediction.py            # FastAPI service (Pydantic schema, CORS, /predict, /retrain)
│   └── FlutterApp/                  # Single-page Flutter app calling the API
├── pyproject.toml
└── uv.lock
```

## Package & environment management (uv)

This project uses [uv](https://docs.astral.sh/uv/) for all dependency and
virtual environment management — no `pip`/`venv`/`requirements.txt`.

**Install uv** (one-time, if you don't have it):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # macOS/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows
```

**Install project dependencies** (creates `.venv` automatically, reads the
locked versions from `uv.lock`):
```bash
uv sync
```

To also install notebook-only dependencies (matplotlib, seaborn, jupyter):
```bash
uv sync --group notebook
```

## 1. Add your trained model artifacts

Copy these three files (produced by running `multivariate.ipynb`) into
`summative/API/`:
```
summative/API/best_model_random_forest.pkl
summative/API/scaler.pkl
summative/API/feature_names.pkl
```

## 2. Run the API locally

```bash
uv run uvicorn summative.API.prediction:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## 3. Run the notebook

```bash
uv run --group notebook jupyter lab summative/linear_regression/multivariate.ipynb
```
(Or open it in Google Colab / VS Code — see the notebook itself for
Google Drive setup so you don't need to re-upload the dataset each time.)

## 4. Deploy to Render

1. Push this whole `linear_regression_model/` folder to GitHub (include the
   `.pkl` files in `summative/API/` — don't gitignore them).
2. Render → **New** → **Web Service** → connect the repo.
3. Configure:
   - **Build Command**: `pip install uv && uv sync --frozen`
   - **Start Command**: `uv run uvicorn summative.API.prediction:app --host 0.0.0.0 --port $PORT`
4. Once live, Swagger UI is at `https://<your-service-name>.onrender.com/docs`.
5. Update `ALLOWED_ORIGINS` in `prediction.py` with your deployed Flutter
   web origin if/when you deploy the Flutter web build (native mobile
   builds aren't affected by CORS at all).

## 5. Flutter app

See `summative/FlutterApp/README.md` for setup and run instructions.
