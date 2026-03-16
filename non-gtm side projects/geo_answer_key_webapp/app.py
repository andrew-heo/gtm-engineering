#!/usr/bin/env python3
"""GeoGuessr-style answer key web app."""

from __future__ import annotations

import json
import os
import hashlib
import textwrap
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORT = int(os.environ.get("GEO_ANSWER_KEY_PORT", "8008"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
DEMO_MODE = os.environ.get("GEO_ANSWER_KEY_MODE", "demo").lower()


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Geo Answer Key</title>
  <style>
    :root {
      --bg: #f3eee3;
      --panel: rgba(255, 252, 246, 0.92);
      --ink: #16211c;
      --muted: #5d6b63;
      --accent: #c65a28;
      --accent-dark: #8f3510;
      --line: rgba(22, 33, 28, 0.12);
      --success: #2f6b45;
      --shadow: 0 24px 70px rgba(58, 39, 20, 0.12);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(198, 90, 40, 0.22), transparent 32%),
        radial-gradient(circle at bottom right, rgba(47, 107, 69, 0.16), transparent 30%),
        linear-gradient(180deg, #efe6d7 0%, var(--bg) 100%);
    }

    .shell {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0 56px;
    }

    .hero {
      display: grid;
      gap: 10px;
      margin-bottom: 28px;
    }

    .eyebrow {
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--accent-dark);
    }

    h1 {
      margin: 0;
      font-size: clamp(40px, 6vw, 78px);
      line-height: 0.92;
      max-width: 780px;
    }

    .lede {
      max-width: 700px;
      margin: 0;
      font-size: 18px;
      line-height: 1.6;
      color: var(--muted);
    }

    .grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 20px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
      border-radius: 28px;
      overflow: hidden;
    }

    .upload-panel {
      padding: 24px;
    }

    .dropzone {
      position: relative;
      display: grid;
      place-items: center;
      min-height: 440px;
      border-radius: 22px;
      border: 2px dashed rgba(198, 90, 40, 0.45);
      background:
        linear-gradient(135deg, rgba(198, 90, 40, 0.08), rgba(47, 107, 69, 0.08)),
        #fcf8f1;
      overflow: hidden;
      transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
      cursor: pointer;
    }

    .dropzone.dragover {
      transform: scale(0.99);
      border-color: var(--accent-dark);
      background:
        linear-gradient(135deg, rgba(198, 90, 40, 0.16), rgba(47, 107, 69, 0.12)),
        #fbf2e5;
    }

    .dropzone.has-image .drop-copy {
      display: none;
    }

    .drop-copy {
      text-align: center;
      padding: 20px;
    }

    .drop-copy h2 {
      margin: 0 0 12px;
      font-size: 32px;
    }

    .drop-copy p {
      margin: 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
    }

    .preview {
      display: none;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .dropzone.has-image .preview {
      display: block;
    }

    input[type="file"] {
      display: none;
    }

    .controls {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-top: 18px;
      flex-wrap: wrap;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 14px 20px;
      font-size: 15px;
      font-family: inherit;
      cursor: pointer;
    }

    .primary {
      background: var(--accent);
      color: #fff8f0;
    }

    .secondary {
      background: rgba(22, 33, 28, 0.08);
      color: var(--ink);
    }

    .hint {
      font-size: 14px;
      color: var(--muted);
    }

    .result-panel {
      padding: 0;
    }

    .result-header {
      padding: 24px 24px 18px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(198, 90, 40, 0.1), rgba(198, 90, 40, 0.02));
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(47, 107, 69, 0.1);
      color: var(--success);
      font-size: 13px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .result-body {
      padding: 24px;
      display: grid;
      gap: 20px;
    }

    .empty {
      color: var(--muted);
      line-height: 1.7;
      font-size: 16px;
    }

    .answer-title {
      margin: 10px 0 4px;
      font-size: clamp(30px, 4vw, 46px);
      line-height: 1;
    }

    .answer-subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }

    .summary {
      margin: 0;
      font-size: 18px;
      line-height: 1.7;
    }

    .meta {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .meta-card, .list-card {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.48);
    }

    .meta-label {
      margin: 0 0 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
    }

    .meta-value {
      margin: 0;
      font-size: 18px;
    }

    .section-title {
      margin: 0 0 12px;
      font-size: 13px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }

    ul {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
      line-height: 1.6;
    }

    .alt-guess {
      padding: 12px 0;
      border-top: 1px solid var(--line);
    }

    .alt-guess:first-of-type {
      border-top: 0;
      padding-top: 0;
    }

    .alt-place {
      margin: 0 0 4px;
      font-size: 18px;
    }

    .alt-why {
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
    }

    .error {
      color: #9c2d1c;
      background: rgba(201, 68, 44, 0.08);
      border: 1px solid rgba(201, 68, 44, 0.18);
      border-radius: 16px;
      padding: 14px 16px;
      line-height: 1.6;
    }

    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .dropzone { min-height: 340px; }
      .meta { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Python Webapp / Visual Inference</div>
      <h1>Geo answer key for a dropped-in photo.</h1>
      <p class="lede">
        Upload a street scene, landmark shot, or travel photo and get a GeoGuessr-style answer key:
        best-guess location, confidence, and the clues that likely gave it away.
      </p>
    </section>

    <section class="grid">
      <div class="panel upload-panel">
        <label class="dropzone" id="dropzone" for="fileInput">
          <div class="drop-copy">
            <h2>Drag, drop, or click</h2>
            <p>JPG, PNG, or WEBP. The backend sends the image to a multimodal model and turns the response into an answer-key card.</p>
          </div>
          <img class="preview" id="preview" alt="Image preview">
        </label>
        <input id="fileInput" type="file" accept="image/*">
        <div class="controls">
          <button class="primary" id="analyzeBtn" disabled>Analyze Location</button>
          <button class="secondary" id="resetBtn" type="button">Reset</button>
          <span class="hint" id="fileHint">No file selected. Demo mode is available without an API key.</span>
        </div>
      </div>

      <div class="panel result-panel">
        <div class="result-header">
          <div class="status" id="statusPill">Waiting for photo</div>
        </div>
        <div class="result-body" id="resultBody">
          <p class="empty">
            Drop in a photo to generate an answer key. The result card will show the likely location,
            why the model thinks that, and a few alternate guesses for comparison.
          </p>
        </div>
      </div>
    </section>
  </main>

  <script>
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const preview = document.getElementById("preview");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const resetBtn = document.getElementById("resetBtn");
    const fileHint = document.getElementById("fileHint");
    const resultBody = document.getElementById("resultBody");
    const statusPill = document.getElementById("statusPill");

    let selectedFile = null;
    let selectedDataUrl = null;

    const setStatus = (label) => {
      statusPill.textContent = label;
    };

    const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[char]));

    const renderError = (message) => {
      resultBody.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
    };

    const renderResult = (payload) => {
      const clues = (payload.clues || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
      const evidence = (payload.supporting_evidence || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
      const alternates = (payload.alternate_guesses || []).map((item) => `
        <div class="alt-guess">
          <p class="alt-place">${escapeHtml(item.place || "Alternate guess")}</p>
          <p class="alt-why">${escapeHtml(item.why || "")}</p>
        </div>
      `).join("");
      const coordinates = payload.latitude != null && payload.longitude != null
        ? `${escapeHtml(payload.latitude)}, ${escapeHtml(payload.longitude)}`
        : "Not provided";

      resultBody.innerHTML = `
        <div>
          <h2 class="answer-title">${escapeHtml(payload.location_name || "Unknown")}</h2>
          <p class="answer-subtitle">${escapeHtml(payload.region || "Region unavailable")}${payload.country ? `, ${escapeHtml(payload.country)}` : ""}</p>
        </div>
        <p class="summary">${escapeHtml(payload.summary || "")}</p>
        <div class="meta">
          <div class="meta-card">
            <p class="meta-label">Confidence</p>
            <p class="meta-value">${escapeHtml(payload.confidence || "Unknown")}</p>
          </div>
          <div class="meta-card">
            <p class="meta-label">Coordinates</p>
            <p class="meta-value">${coordinates}</p>
          </div>
          <div class="meta-card">
            <p class="meta-label">Mode</p>
            <p class="meta-value">${escapeHtml(payload.mode || "demo")}</p>
          </div>
        </div>
        <div class="list-card">
          <p class="section-title">Clues</p>
          <ul>${clues || "<li>No clues returned.</li>"}</ul>
        </div>
        <div class="list-card">
          <p class="section-title">Supporting Evidence</p>
          <ul>${evidence || "<li>No evidence returned.</li>"}</ul>
        </div>
        <div class="list-card">
          <p class="section-title">Alternate Guesses</p>
          ${alternates || '<p class="alt-why">No alternate guesses returned.</p>'}
        </div>
        <div class="list-card">
          <p class="section-title">Disclaimer</p>
          <p class="alt-why">${escapeHtml(payload.disclaimer || "Best-effort visual inference only.")}</p>
        </div>
      `;
    };

    const clearSelection = () => {
      selectedFile = null;
      selectedDataUrl = null;
      fileInput.value = "";
      preview.removeAttribute("src");
      dropzone.classList.remove("has-image");
      analyzeBtn.disabled = true;
      fileHint.textContent = "No file selected. Demo mode is available without an API key.";
      setStatus("Waiting for photo");
      resultBody.innerHTML = `
        <p class="empty">
          Drop in a photo to generate an answer key. The result card will show the likely location,
          why the model thinks that, and a few alternate guesses for comparison.
        </p>
      `;
    };

    const useFile = (file) => {
      if (!file || !file.type.startsWith("image/")) {
        renderError("Please choose an image file.");
        return;
      }

      selectedFile = file;
      const reader = new FileReader();
      reader.onload = () => {
        selectedDataUrl = reader.result;
        preview.src = selectedDataUrl;
        dropzone.classList.add("has-image");
        analyzeBtn.disabled = false;
        fileHint.textContent = `${file.name} • ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        setStatus("Photo ready");
      };
      reader.readAsDataURL(file);
    };

    dropzone.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
      const [file] = event.dataTransfer.files;
      useFile(file);
    });

    fileInput.addEventListener("change", () => {
      const [file] = fileInput.files;
      useFile(file);
    });

    resetBtn.addEventListener("click", clearSelection);

    analyzeBtn.addEventListener("click", async () => {
      if (!selectedDataUrl || !selectedFile) {
        return;
      }

      analyzeBtn.disabled = true;
      setStatus("Analyzing photo");
      resultBody.innerHTML = `<p class="empty">Looking for visual clues, signage, road markings, architecture, terrain, and other location signals.</p>`;

      try {
        const response = await fetch("/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: selectedFile.name,
            image_data_url: selectedDataUrl
          })
        });

        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Analysis failed.");
        }

        renderResult(payload);
        setStatus("Answer key ready");
      } catch (error) {
        renderError(error.message || "Analysis failed.");
        setStatus("Request failed");
      } finally {
        analyzeBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


PROMPT = textwrap.dedent(
    """
    You are generating a GeoGuessr-style answer key from a single uploaded photo.

    Infer the most likely location shown in the image. Use visible geography, road markings,
    language, architecture, vegetation, terrain, climate cues, utilities, vehicles, and signage.

    Return valid JSON only. Do not wrap the JSON in markdown.

    Required schema:
    {
      "location_name": "most likely city, area, or landmark",
      "country": "country",
      "region": "state, province, region, or sub-area",
      "latitude": 0.0,
      "longitude": 0.0,
      "confidence": "low|medium|high",
      "summary": "2-3 sentence answer-key style explanation",
      "clues": ["short clue", "short clue", "short clue"],
      "supporting_evidence": ["short evidence point", "short evidence point", "short evidence point"],
      "alternate_guesses": [
        {"place": "alternate place", "why": "why it is plausible"},
        {"place": "alternate place", "why": "why it is plausible"}
      ],
      "disclaimer": "brief best-effort disclaimer"
    }

    Rules:
    - Be specific when the evidence is strong, and explicit about uncertainty when it is not.
    - If exact coordinates are unknown, provide approximate coordinates for the best guess.
    - Keep clues short and concrete.
    - Keep the tone like an answer key, not a travel article.
    """
).strip()


DEMO_ANSWER_KEYS = [
    {
        "location_name": "Lisbon",
        "country": "Portugal",
        "region": "Lisbon District",
        "latitude": 38.7223,
        "longitude": -9.1393,
        "confidence": "medium",
        "summary": "Best guess is central Lisbon. The answer key points to a coastal southern European city with pastel building stock, steep streets, and visual cues consistent with Portuguese urban neighborhoods.",
        "clues": [
            "Warm-toned stucco and tiled facades",
            "Dense hillside street layout",
            "Southern European road and utility styling",
        ],
        "supporting_evidence": [
            "Architecture fits older Lisbon residential blocks",
            "Street geometry suggests an elevated historic core",
            "Overall climate cues match Atlantic Iberia",
        ],
        "alternate_guesses": [
            {"place": "Porto, Portugal", "why": "Similar Iberian facades and street texture, but the terrain and light feel slightly more Lisbon."},
            {"place": "Valparaiso, Chile", "why": "Also has hills and layered streets, though the built environment looks more European here."},
        ],
        "disclaimer": "Demo-mode answer key generated from a fixed scenario, not from real image recognition.",
    },
    {
        "location_name": "Kyoto",
        "country": "Japan",
        "region": "Kansai",
        "latitude": 35.0116,
        "longitude": 135.7681,
        "confidence": "medium",
        "summary": "Best guess is Kyoto. The answer key leans on a mix of low-rise urban density, restrained signage, and streetscape details that fit a Japanese city with historic-tourism overlap.",
        "clues": [
            "Compact streets with orderly utility lines",
            "Japanese urban design language",
            "Low-rise buildings with mixed old and new textures",
        ],
        "supporting_evidence": [
            "Visual composition fits neighborhood-scale Japanese streets",
            "Kyoto is a plausible match for traditional-modern overlap",
            "The scene suggests a dense but not hyper-high-rise city core",
        ],
        "alternate_guesses": [
            {"place": "Osaka, Japan", "why": "Many street-level cues overlap, though the feel here is calmer and more residential."},
            {"place": "Nara, Japan", "why": "Also plausible for a lower-scale Kansai streetscape with historic character."},
        ],
        "disclaimer": "Demo-mode answer key generated from a fixed scenario, not from real image recognition.",
    },
    {
        "location_name": "Reykjavik",
        "country": "Iceland",
        "region": "Capital Region",
        "latitude": 64.1466,
        "longitude": -21.9426,
        "confidence": "high",
        "summary": "Best guess is Reykjavik. The answer key reads the scene as a cool-climate North Atlantic environment with sparse tree cover, crisp light, and built forms that fit Icelandic urban areas.",
        "clues": [
            "Subarctic light and weather feel",
            "Minimal tree cover",
            "Simple, practical building shapes",
        ],
        "supporting_evidence": [
            "The scene fits Iceland's coastal urban texture",
            "Color palette and environmental cues point north Atlantic",
            "Reykjavik is the most likely dense settlement match",
        ],
        "alternate_guesses": [
            {"place": "Torshavn, Faroe Islands", "why": "Similar weather and North Atlantic cues, but Reykjavik is the stronger urban fit."},
            {"place": "Akureyri, Iceland", "why": "Also plausible in Iceland, though the city scale looks more capital-region than northern town."},
        ],
        "disclaimer": "Demo-mode answer key generated from a fixed scenario, not from real image recognition.",
    },
    {
        "location_name": "Marrakesh",
        "country": "Morocco",
        "region": "Marrakesh-Safi",
        "latitude": 31.6295,
        "longitude": -7.9811,
        "confidence": "medium",
        "summary": "Best guess is Marrakesh. The answer key points toward a dry-climate North African setting with warm earth tones, bright light, and urban textures common in Moroccan cities.",
        "clues": [
            "Dry climate color palette",
            "Earth-toned walls and streetscape",
            "North African architectural feel",
        ],
        "supporting_evidence": [
            "Sunlight and materials suggest a hot inland environment",
            "Built forms align with Moroccan city neighborhoods",
            "Marrakesh is a strong fit for the warm-toned visual profile",
        ],
        "alternate_guesses": [
            {"place": "Fes, Morocco", "why": "Shares many historic Moroccan cues, though the scene feels slightly more open and sun-baked."},
            {"place": "Tunis, Tunisia", "why": "Also plausible for North African urban clues, but the palette leans more Moroccan."},
        ],
        "disclaimer": "Demo-mode answer key generated from a fixed scenario, not from real image recognition.",
    },
]


def extract_text(response_payload: dict) -> str:
    texts: list[str] = []

    if isinstance(response_payload.get("output_text"), str):
        texts.append(response_payload["output_text"])

    for item in response_payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                texts.append(content["text"])

    return "\n".join(part.strip() for part in texts if part and part.strip())


def parse_json_block(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response did not contain valid JSON.") from None
        return json.loads(raw_text[start : end + 1])


def build_demo_answer_key(filename: str) -> dict:
    digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(DEMO_ANSWER_KEYS)
    result = dict(DEMO_ANSWER_KEYS[index])
    result["mode"] = "demo"
    result["summary"] = f"{result['summary']} Demo seed: {filename or 'uploaded image'}."
    return result


def analyze_image(image_data_url: str, filename: str) -> dict:
    if DEMO_MODE != "live" or not OPENAI_API_KEY:
        return build_demo_answer_key(filename)

    request_body = {
        "model": OPENAI_MODEL,
        "instructions": PROMPT,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Analyze this image file named {filename} and produce the answer key JSON.",
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                        "detail": "high",
                    },
                ],
            }
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(error_body)
        except json.JSONDecodeError:
            detail = {"error": {"message": error_body}}
        message = detail.get("error", {}).get("message", "OpenAI API request failed.")
        raise RuntimeError(message) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach the OpenAI API: {error.reason}") from error

    raw_text = extract_text(payload)
    if not raw_text:
        raise RuntimeError("The model returned an empty response.")

    parsed = parse_json_block(raw_text)
    parsed.setdefault("location_name", "Unknown")
    parsed.setdefault("country", "")
    parsed.setdefault("region", "")
    parsed.setdefault("confidence", "low")
    parsed.setdefault("summary", "")
    parsed.setdefault("clues", [])
    parsed.setdefault("supporting_evidence", [])
    parsed.setdefault("alternate_guesses", [])
    parsed.setdefault("disclaimer", "Best-effort visual inference only.")
    parsed.setdefault("latitude", None)
    parsed.setdefault("longitude", None)
    parsed.setdefault("mode", "live")
    return parsed


class GeoAnswerKeyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/index.html"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            image_data_url = payload.get("image_data_url", "")
            filename = payload.get("filename", "upload")

            if not image_data_url.startswith("data:image/"):
                self.respond_json({"error": "Upload an image file before analyzing."}, status=HTTPStatus.BAD_REQUEST)
                return

            result = analyze_image(image_data_url=image_data_url, filename=filename)
            self.respond_json(result, status=HTTPStatus.OK)
        except json.JSONDecodeError:
            self.respond_json({"error": "Request body must be valid JSON."}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.respond_json({"error": str(error)}, status=HTTPStatus.BAD_GATEWAY)
        except Exception as error:  # pragma: no cover - last-resort guard for manual app use
            self.respond_json({"error": f"Unexpected server error: {error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def respond_json(self, payload: dict, status: HTTPStatus) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), GeoAnswerKeyHandler)
    print(f"Geo Answer Key running on http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
