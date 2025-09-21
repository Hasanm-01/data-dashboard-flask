from flask import Flask, render_template, request, jsonify
import pandas as pd
from io import TextIOWrapper

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/upload")
def upload():
    """
    Accept a CSV upload, auto-detect delimiter, coerce numeric columns,
    return a small preview + summary (including the first numeric column).
    """
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400

    # Auto-detect delimiter (handles commas/semicolons); 'python' engine allows sniffing
    df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"), sep=None, engine="python")

    # Coerce object columns to numeric where possible (currency/extra chars will become NaN)
    for col in df.columns:
        if df[col].dtype == "object":
            # Try best-effort numeric coercion; leave non-numeric text as-is
            df[col] = pd.to_numeric(df[col].str.replace(r"[^\d\.\-]", "", regex=True), errors="coerce")

    preview = df.head(20).to_dict(orient="records")

    summary = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "numericSummary": None
    }

    # Pick the first numeric column for the quick chart
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        col = num_cols[0]
        summary["numericSummary"] = {
            "column": col,
            "mean": float(df[col].mean(skipna=True)),
            "min": float(df[col].min(skipna=True)),
            "max": float(df[col].max(skipna=True)),
            "count": int(df[col].count())
        }

    return jsonify({"summary": summary, "preview": preview})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
