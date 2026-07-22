# Stunting Predictor — Flutter App

Single-page app that calls the Stunting Prediction API
(`https://regression-analysis-mobile-application-1ab3.onrender.com`) to
predict a toddler's Height-for-Age Z-Score.

## Setup

1. Install Flutter SDK if you haven't: https://docs.flutter.dev/get-started/install
2. Open this folder in VS Code (with the Flutter extension) or Android Studio.
3. Get dependencies:
   ```bash
   flutter pub get
   ```

## Run

- **Mobile (emulator or connected device):**
  ```bash
  flutter run
  ```
- **Web (Chrome):**
  ```bash
  flutter run -d chrome
  ```

## What's on the page

- 4 text fields matching the API's required inputs: Gender (0/1), Height (cm),
  Weight-for-Age Z-Score, Weight-for-Height Z-Score
- Client-side validation matches the API's Pydantic range constraints, so
  bad input is caught before a network call is even made
- A "Predict" button that calls `POST /predict`
- A single display area below the button that shows either:
  - the predicted Z-Score + stunting risk category, or
  - a clear error message (out-of-range values, missing fields, or a
    network/server problem)

## Note on Render free tier

The API may take 30-60 seconds to respond on the very first request if the
Render service has been idle (free instances spin down automatically). The
app's HTTP call uses a 60-second timeout to accommodate this — if it still
times out, just tap Predict again once the service has woken up.

## Before submitting / demoing

If you deploy this app itself to the web (e.g. Firebase Hosting, GitHub
Pages), get that URL and add it to `ALLOWED_ORIGINS` in the FastAPI
service's `app/main.py`, otherwise the browser will block the request due
to CORS. Native mobile builds (Android/iOS) are not affected by CORS at all.
