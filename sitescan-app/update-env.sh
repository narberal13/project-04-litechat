#!/bin/bash
# ============================================================
# .env 一括更新スクリプト
# ローカルで .env を編集した後、このスクリプトでVPSに反映
#
# 使い方:
#   1. backend/.env を編集
#   2. ./update-env.sh を実行
# ============================================================

VPS_IP="45.77.17.143"
SSH_KEY="~/.ssh/id_ed25519"

echo "=== .env をVPSに転送 ==="
scp -i $SSH_KEY backend/.env root@$VPS_IP:/root/sitescan-app/backend/.env

echo "=== バックエンドを再起動 ==="
ssh -i $SSH_KEY root@$VPS_IP "cd /root/sitescan-app && docker compose restart"

echo "=== ヘルスチェック ==="
sleep 3
curl -s https://api.pik-tal.com/api/health

echo ""
echo "=== 完了 ==="
