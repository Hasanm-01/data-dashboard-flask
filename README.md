# Data Dashboard (Flask + Docker)
Upload a CSV → quick summary + preview + a simple chart.

## Run
pip install -r requirements.txt
python app.py  # http://localhost:8000

## Docker
docker build -t data-dashboard .
docker run -p 8000:8000 data-dashboard
