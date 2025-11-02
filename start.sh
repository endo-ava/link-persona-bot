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

# 定期Ping（外部URLを叩くことでスリープ防止）
if [ ! -z "$PING_URL" ]; then
  echo "Starting self-ping to $PING_URL every 10 minutes..."
  while true; do
    curl -fsS "$PING_URL" > /dev/null 2>&1 || echo "Ping failed at $(date)"
    sleep 600  # 10分ごと
  done &
fi

# Discord Botを起動（フォアグラウンド、エラーでも継続）
echo "Starting Discord Bot..."
python -m bot.main || {
    echo "Discord Bot failed to start or crashed, but keeping API server running..."
    # APIサーバーのプロセスを待機（フォアグラウンドに）
    wait $API_PID
}
