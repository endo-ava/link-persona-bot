#!/bin/bash
set -e

echo "Starting Link Persona Bot..."

# APIサーバーを起動（バックグラウンド）
echo "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# APIサーバーが起動するまで待機
echo "Waiting for API server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "API server is ready!"
        break
    fi
    sleep 1
done

# Discord Botを起動（フォアグラウンド、エラーでも継続）
echo "Starting Discord Bot..."
python -m bot.main || {
    echo "Discord Bot failed to start or crashed, but keeping API server running..."
    # APIサーバーのプロセスを待機（フォアグラウンドに）
    wait $API_PID
}
