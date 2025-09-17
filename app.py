from flask import Flask, render_template, request, jsonify
import pandas as pd
from io import TextIOWrapper

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/upload")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    df = pd.read_csv(TextIOWrapper(f, encoding="utf-8"))
    preview = df.head(20).to_dict(orient="records")
    summary = {"rows": len(df), "columns": list(df.columns)}
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        col = num_cols[0]
        summary["numericSummary"] = {
            "column": col,
            "mean": float(df[col].mean()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "count": int(df[col].count()),
        }
    return jsonify({"summary": summary, "preview": preview})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
