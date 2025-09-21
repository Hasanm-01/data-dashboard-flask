from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import json
from io import StringIO  # << use StringIO for decoded text

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/upload")
def upload():
    """
    Accept CSV upload, read bytes safely, decode to text,
    auto-detect delimiter, coerce numeric-looking columns,
    and return NaN-free JSON (NaN -> null).
    """
    try:
        f = request.files.get("file")
        if not f or f.filename == "":
            return jsonify({"error": "no file"}), 400

        # Read raw bytes, then decode to text (ignore stray bytes)
        raw = f.stream.read()
        if not raw:
            return jsonify({"error": "empty file"}), 400
        text = raw.decode("utf-8", errors="ignore")

        # Parse CSV. Try auto-detect delimiter; fall back to comma if needed.
        try:
            df = pd.read_csv(StringIO(text), sep=None, engine="python")
        except Exception:
            df = pd.read_csv(StringIO(text))

        # Try to coerce object columns that look numeric (>=50% parsable)
        for col in df.columns:
            if df[col].dtype == "object":
                coerced = pd.to_numeric(
                    df[col].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
                    errors="coerce",
                )
                if coerced.notna().mean() >= 0.5:
                    df[col] = coerced

        # Build preview (first 20 rows) with NaN -> null
        preview = json.loads(df.head(20).to_json(orient="records", allow_nan=False))

        # Summary for first numeric column that has values
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

    except Exception as e:
        # Always return JSON so the frontend can show the error cleanly
        return jsonify({"error": f"processing_failed: {e.__class__.__name__}: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
