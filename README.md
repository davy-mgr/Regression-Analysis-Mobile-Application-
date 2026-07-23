# Linear Regression Model — Stunting Prediction

## Mission & Problem

Childhood stunting (low height-for-age) affects millions of children under
five worldwide and is a key indicator of chronic undernutrition, with
lasting effects on cognitive development and long-term health. This project
predicts a toddler's WHO Height-for-Age Z-Score from easily-collected
measurements (gender, height, weight-for-age and weight-for-height
z-scores), giving health workers a fast, data-driven way to flag at-risk
children for follow-up without waiting on full growth-chart calculations.

**Dataset:** *Stunting and Nutritional Status of Toddlers — Jeneponto,
Indonesia* (2021–2024), sourced from Mendeley Data
(https://data.mendeley.com/datasets/wzwpc9j5bx/4). 40,071 individual
toddler records (age 0–60 months) with gender, height, weight, and
WHO-computed weight-for-age, height-for-age, and weight-for-height
z-scores; 39,521 rows remain after cleaning (see notebook Section 2).

## Live API (Swagger UI)

**https://regression-analysis-mobile-application-1ab3.onrender.com/docs**

> Note: the free Render tier spins down after inactivity — the first
> request may take 30-60 seconds to respond while the service wakes up.

## Video Demo

**[Add your YouTube link here once recorded]**


## Package & environment management (uv)

This project uses [uv](https://docs.astral.sh/uv/) for dependency and
virtual environment management.

**Install uv** (one-time):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # macOS/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows
```

**Install dependencies:**
```bash
uv sync
```
Add `--group notebook` as well if you want to run the Jupyter notebook
locally (installs matplotlib, seaborn, jupyter, etc.).

## Run the API locally

Model artifact files (`best_model_random_forest.pkl`, `scaler.pkl`,
`feature_names.pkl`, produced by running the notebook) must be present in
`summative/API/` first.

```bash
uv run uvicorn summative.API.prediction:app --reload
```
Swagger UI: http://127.0.0.1:8000/docs

## Run the mobile app

1. Install the Flutter SDK: https://docs.flutter.dev/get-started/install
2. From `summative/FlutterApp/`:
   ```bash
   flutter pub get
   flutter run
   ```
   Select a connected device or emulator when prompted. The app is
   pre-configured to call the live Render API above, so no local backend is
   required to use the mobile app.
3. Enter the four values (Gender, Height, Weight-for-Age Z-Score,
   Weight-for-Height Z-Score) and tap **Predict**.

Full setup/run details: `summative/FlutterApp/README.md`.

## Deploy to Render

- **Build Command**: `pip install uv && uv sync --frozen`
- **Start Command**: `uv run uvicorn summative.API.prediction:app --host 0.0.0.0 --port $PORT`
