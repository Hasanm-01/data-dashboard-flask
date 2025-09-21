from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
import pandas as pd
import numpy as np
from io import StringIO
import traceback

app = Flask(__name__)

# Always return JSON on errors (no HTML 500 pages)
@app.errorhandler(Exception)
def handle_all_errors(e):
    status = e.code if isinstance(e, HTTPException) else 500
    print("SERVER ERROR:", repr(e))
    print(traceback.format_exc(), flush=True)
    return jsonify({"error": str(e), "type": e.__class__.__name__}), status

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/upload")
def upload():
    # 1) Get file safely
    f = request.files.get("file")
    if not f or f.filename == "":
        return jsonify({"error": "no file"}), 400
    raw = f.stream.read()
    if not raw:
        return jsonify({"error": "empty file"}), 400
    text = raw.decode("utf-8", errors="ignore")

    # 2) Parse CSV (auto-detect delimiter; fall back to comma)
    try:
        df = pd.read_csv(StringIO(text), sep=None, engine="python")
    except Exception:
        df = pd.read_csv(StringIO(text))

    # 3) Coerce numeric-looking object columns (≥50% parsable)
    for col in df.columns:
        if df[col].dtype == "object":
            cleaned = df[col].astype(str).str.replace(r"[^\d.\-]", "", regex=True)
            coerced = pd.to_numeric(cleaned, errors="coerce")
            if coerced.notna().mean() >= 0.5:
                df[col] = coerced

    # 4) Build preview with NaN -> None (valid JSON)
    preview = (
        df.head(20)
          .replace({np.nan: None})
          .to_dict(orient="records")
    )

    # 5) Summary for first numeric column with values
    summary = {"rows": int(len(df)), "columns": list(df.columns), "numericSummary": None}
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        col = num_cols[0]
        series = df[col].dropna()
        if len(series) > 0:
            summary["numericSummary"] = {
                "column": col,
                "mean": float(series.mean()),
                "min": float(series.min()),
                "max": float(series.max()),
                "count": int(series.count()),
            }

    return jsonify({"summary": summary, "preview": preview})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
