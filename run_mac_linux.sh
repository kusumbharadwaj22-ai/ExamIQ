#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if command -v g++ >/dev/null 2>&1; then
  g++ cpp/analytics.cpp -o analytics -std=c++17
fi
python3 -m pip install -r requirements.txt
python3 app.py
