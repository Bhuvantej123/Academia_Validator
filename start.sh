#!/bin/bash

# start.sh — Entrypoint for multi-process deployment

# 1. Start FastAPI Backend in background
echo "[SYSTEM] Starting FastAPI Backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 2. Start Streamlit Frontend
echo "[SYSTEM] Starting Streamlit Dashboard..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
