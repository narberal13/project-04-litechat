#!/bin/bash
# ============================================================
# きくよ VPS 初期セットアップスクリプト
# Vultr $6プラン (1vCPU / 1GB RAM / Ubuntu 22.04+) 用
#
# 使い方:
#   1. Vultrで新しい$6 VPSを作成 (Ubuntu 22.04)
#   2. SSHでログイン: ssh root@<新しいIP>
#   3. このスクリプトを実行:
#      curl -sL https://raw.githubusercontent.com/narberal13/project-04-litechat/main/setup-vps.sh | bash
#      もしくは:
#      scp setup-vps.sh root@<IP>:/root/ && ssh root@<IP> "bash /root/setup-vps.sh"
# ============================================================

set -e
echo "🚀 きくよ VPS セットアップ開始..."

# --- 1. システム更新 ---
echo "📦 システム更新中..."
apt-get update -qq && apt-get upgrade -y -qq

# --- 2. Docker インストール ---
echo "🐳 Docker インストール中..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Docker Compose プラグイン確認
if ! docker compose version &> /dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi

# --- 3. Node.js (20.x LTS) インストール ---
echo "📗 Node.js インストール中..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

# --- 4. pm2 インストール ---
echo "📗 pm2 インストール中..."
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
    pm2 startup systemd -u root --hp /root
fi

# --- 5. Nginx + Certbot インストール ---
echo "🌐 Nginx + Certbot インストール中..."
apt-get install -y -qq nginx certbot python3-certbot-nginx

# --- 6. リポジトリクローン ---
echo "📥 リポジトリクローン中..."
cd /root
if [ ! -d "project-04" ]; then
    git clone https://github.com/narberal13/project-04-litechat.git project-04
fi

# --- 7. 実行ディレクトリ作成 ---
echo "📁 実行ディレクトリ作成..."
mkdir -p /root/kikuyo-app
rsync -av --delete \
    --exclude='models' \
    --exclude='.env' \
    --exclude='node_modules' \
    --exclude='.next' \
    /root/project-04/litechat-app/ /root/kikuyo-app/

# --- 8. .env テンプレート配置 ---
if [ ! -f /root/kikuyo-app/backend/.env ]; then
    echo "⚠️  .envファイルを作成します。APIキーを設定してください。"
    cp /root/kikuyo-app/backend/.env.example /root/kikuyo-app/backend/.env
    echo ""
    echo "============================================"
    echo "  重要: .envファイルを編集してください"
    echo "  nano /root/kikuyo-app/backend/.env"
    echo ""
    echo "  必須項目:"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - STRIPE_SECRET_KEY"
    echo "  - STRIPE_WEBHOOK_SECRET"
    echo "  - STRIPE_PRICE_MAINICHI"
    echo "  - DISCORD_WEBHOOK_URL (任意)"
    echo "============================================"
    echo ""
fi

# --- 9. Nginx設定 ---
echo "🌐 Nginx設定中..."
cat > /etc/nginx/sites-available/kikuyo <<'NGINX'
server {
    listen 80;
    server_name pik-tal.com www.pik-tal.com;

    # API (FastAPI)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX

# シンボリックリンク有効化
ln -sf /etc/nginx/sites-available/kikuyo /etc/nginx/sites-enabled/kikuyo
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# --- 10. デプロイスクリプト作成 ---
cat > /root/deploy.sh <<'DEPLOY'
#!/bin/bash
set -e
echo "🚀 きくよ デプロイ開始..."

cd /root/project-04
git pull origin main

echo "📂 ファイル同期中..."
rsync -av --delete \
    --exclude='models' \
    --exclude='.env' \
    --exclude='node_modules' \
    --exclude='.next' \
    /root/project-04/litechat-app/ /root/kikuyo-app/

echo "🐳 バックエンド更新中..."
cd /root/kikuyo-app
docker compose up -d --build backend

echo "📗 フロントエンド更新中..."
cd /root/kikuyo-app/frontend
npm install --production
NEXT_PUBLIC_API_URL=https://pik-tal.com npm run build
pm2 delete kikuyo-frontend 2>/dev/null || true
pm2 start npm --name "kikuyo-frontend" -- start
pm2 save

echo "✅ ヘルスチェック..."
sleep 3
curl -s http://localhost:8000/api/health | python3 -m json.tool
echo ""
echo "✅ デプロイ完了!"
DEPLOY
chmod +x /root/deploy.sh

echo ""
echo "============================================"
echo "  ✅ きくよ VPS セットアップ完了!"
echo ""
echo "  次のステップ:"
echo "  1. .envを編集:  nano /root/kikuyo-app/backend/.env"
echo "  2. デプロイ実行: /root/deploy.sh"
echo "  3. SSL証明書:   certbot --nginx -d pik-tal.com -d www.pik-tal.com"
echo "  4. Cloudflare DNS: pik-tal.com → $(curl -s ifconfig.me)"
echo ""
echo "  管理コマンド:"
echo "  docker ps                          # バックエンド確認"
echo "  pm2 list                           # フロントエンド確認"
echo "  curl http://localhost:8000/api/health  # ヘルスチェック"
echo "  docker compose logs -f backend     # バックエンドログ"
echo "  pm2 logs kikuyo-frontend           # フロントエンドログ"
echo "============================================"
