# Geo Answer Key Webapp

## Introduction

This project is a small Python web app that acts like a GeoGuessr answer key.

Drop in a photo, and the app returns:

- a best-guess location
- a confidence level
- visual clues that support the guess
- alternate guesses to compare against

The UI is intentionally lightweight and runs from a single Python server process.
By default, it runs in demo mode and does not require any API key.

## How It Works

1. Open the web app in a browser.
2. Drag and drop a photo onto the upload zone.
3. The frontend sends the image to the Python backend as a base64 data URL.
4. In demo mode, the backend returns a deterministic answer-key scenario based on the uploaded file name.
5. In optional live mode, the backend calls the OpenAI Responses API for multimodal image analysis.
6. The app renders an answer-key style card with the guess and clues.

## Requirements

- Python 3.10+

Optional environment variables:

- `GEO_ANSWER_KEY_MODE` defaults to `demo`
- `OPENAI_MODEL` defaults to `gpt-4.1-mini`
- `GEO_ANSWER_KEY_PORT` defaults to `8008`
- `OPENAI_API_KEY` is only needed when `GEO_ANSWER_KEY_MODE=live`

## Run

```bash
python3 "non-gtm side projects/geo_answer_key_webapp/app.py"
```

Then open:

```text
http://127.0.0.1:8008
```

To use live AI mode instead:

```bash
export GEO_ANSWER_KEY_MODE=live
export OPENAI_API_KEY="your_api_key_here"
python3 "non-gtm side projects/geo_answer_key_webapp/app.py"
```

## Notes

- This is a best-effort visual inference tool, not a precise geolocation system.
- Demo mode is intended for portfolio/UI demos and does not inspect the actual image contents.
- Live mode results depend on the image quality and how distinctive the visual clues are.
