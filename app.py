from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import json
from io import TextIOWrapper

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/upload")
def upload():
    """
    Accept CSV, auto-detect delimiter, coerce numeric-looking columns,
    and return NaN-free JSON (NaN -> null) so the browser can parse it.
    """
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400

    # Auto-detect delimiter (handles commas/semicolons)
    df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"), sep=None, engine="python")

    # Try to coerce object columns that look numeric (heuristic ≥50% parsable)
    for col in df.columns:
        if df[col].dtype == "object":
            coerced = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
                errors="coerce",
            )
            if coerced.notna().mean() >= 0.5:
                df[col] = coerced

    # ---- Build preview with NaN -> null (valid JSON) ----
    preview_json = df.head(20).to_json(orient="records", allow_nan=False)
    preview = json.loads(preview_json)  # list[dict] that jsonify can re-encode

    # ---- Summary (first numeric column only if it has values) ----
    summary = {"rows": int(len(df)), "columns": list(df.columns), "numericSummary": None}
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        col = num_cols[0]
        series = df[col]
        count = int(series.count())
        if count > 0:
            summary["numericSummary"] = {
                "column": col,
                "mean": float(series.mean()),
                "min": float(series.min()),
                "max": float(series.max()),
                "count": count,
            }

    return jsonify({"summary": summary, "preview": preview})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
