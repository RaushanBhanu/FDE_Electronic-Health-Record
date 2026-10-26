#!/bin/sh
echo "Starting FastAPI..."
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

echo "Waiting for FastAPI to become ready..."
until python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json')" 2>/dev/null; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "FastAPI failed to start."
    exit 1
  fi
  sleep 2
done

echo "FastAPI is ready. Starting Streamlit..."
exec streamlit run src/ui/app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
