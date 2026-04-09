# SiteScan デプロイ手順書

## 前提
- Vultr VPS（$20/月 — 2vCPU / 4GB RAM / Ubuntu 24.04）
- Cloudflare で pik-tal.com を管理中
- Anthropic APIキー取得済み
- Stripe アカウント（pik-tal.com で承認済み）

---

## Step 1: Vultr VPS を契約・セットアップ

### 1-1. Vultr でサーバーを作成

1. https://my.vultr.com/ にログイン
2. 「Deploy New Server」をクリック
3. 以下を選択:
   - **Type**: Cloud Compute — Shared CPU
   - **Location**: Tokyo（日本ユーザー向け最速）
   - **OS**: Ubuntu 24.04 LTS
   - **Plan**: Regular Cloud Compute — $20/mo（2 vCPU, 4GB RAM, 80GB SSD）
   - **SSH Key**: 既存のSSHキーを追加（またはパスワード認証）
4. 「Deploy Now」をクリック
5. サーバーのIPアドレスをメモ（例: `203.0.113.10`）

### 1-2. SSHでサーバーに接続

```bash
ssh root@<YOUR_VPS_IP>
```

### 1-3. Docker & Docker Compose をインストール

```bash
# Docker公式インストール
curl -fsSL https://get.docker.com | sh

# Docker Composeはdocker pluginとして含まれている（確認）
docker compose version

# 一般ユーザーを作成（rootで動かさない）
adduser deploy
usermod -aG docker deploy
```

### 1-4. ファイアウォール設定

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## Step 2: Cloudflare DNS 設定

Cloudflare ダッシュボード → pik-tal.com → DNS で以下を追加:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `<YOUR_VPS_IP>` | Proxied (オレンジ雲) |
| A | `api` | `<YOUR_VPS_IP>` | Proxied (オレンジ雲) |

※ Cloudflare Proxy を有効にすることで SSL/TLS が自動適用されます。

### Cloudflare SSL設定

1. SSL/TLS → Overview → 「Full (strict)」に設定
2. Edge Certificates → 「Always Use HTTPS」をON
3. Edge Certificates → 「Automatic HTTPS Rewrites」をON

---

## Step 3: VPS にアプリをデプロイ

### 3-1. プロジェクトをVPSに転送

ローカルPCから:

```bash
# sitescan-appフォルダをVPSに転送
scp -r sitescan-app deploy@<YOUR_VPS_IP>:~/
```

### 3-2. VPSで.envファイルを作成

```bash
ssh deploy@<YOUR_VPS_IP>
cd ~/sitescan-app/backend

cp .env.example .env
nano .env
```

以下を記入:

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx  # ← あなたのAPIキー

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxx  # ← Stripeダッシュボードから取得
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # ← Step 5 で設定後に記入
STRIPE_PRICE_SINGLE=price_xxxxx  # ← Step 4 で作成後に記入
STRIPE_PRICE_MONTHLY=price_xxxxx  # ← Step 4 で作成後に記入

# Resend (メール通知)
RESEND_API_KEY=re_xxxxx  # ← https://resend.com で取得
FROM_EMAIL=noreply@pik-tal.com

# Discord (管理者通知)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx  # ← Discordで作成

# App
APP_URL=https://pik-tal.com
API_URL=https://api.pik-tal.com
DATABASE_URL=sqlite:///./sitescan.db

# Rate limits
MAX_FREE_SCANS_PER_MONTH=3
MAX_CONCURRENT_SCANS=2
API_MONTHLY_BUDGET_USD=50
```

### 3-3. Nginx リバースプロキシを設定

```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/sitescan << 'EOF'
server {
    listen 80;
    server_name api.pik-tal.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future use)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings for long-running scans
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/sitescan /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 3-4. Docker でバックエンドを起動

```bash
cd ~/sitescan-app

# ビルド＆起動
docker compose up -d --build

# ログ確認
docker compose logs -f

# ヘルスチェック
curl http://localhost:8000/api/health
```

成功すると `{"status":"ok","timestamp":"..."}` が返ります。

### 3-5. 動作確認

```bash
# VPS内部から
curl http://localhost:8000/api/health

# 外部から（Cloudflare経由）
curl https://api.pik-tal.com/api/health
```

---

## Step 4: Stripe で料金商品を作成

1. https://dashboard.stripe.com にログイン
2. Products → 「Add Product」

### 商品1: 単発診断

- Product name: `SiteScan 単発診断`
- Price: ¥1,000（JPY）— One time
- 作成後、Price ID（`price_xxxxx`）をメモ → `.env` の `STRIPE_PRICE_SINGLE` に記入

### 商品2: 月額プラン

- Product name: `SiteScan 月額プラン`
- Price: ¥2,980（JPY）— Recurring / Monthly
- 作成後、Price ID（`price_xxxxx`）をメモ → `.env` の `STRIPE_PRICE_MONTHLY` に記入

---

## Step 5: Stripe Webhook を設定

1. Stripe ダッシュボード → Developers → Webhooks
2. 「Add endpoint」をクリック
3. Endpoint URL: `https://api.pik-tal.com/api/webhooks/stripe`
4. Events to listen:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`
5. 作成後、Signing Secret（`whsec_xxxxx`）をメモ → `.env` に記入

### .env 更新後にコンテナを再起動

```bash
cd ~/sitescan-app
docker compose restart
```

---

## Step 6: フロントエンドを Cloudflare Pages にデプロイ

### 6-1. GitHubリポジトリを作成（推奨）

```bash
# ローカルPCで
cd sitescan-app/frontend
git init
git add .
git commit -m "Initial commit: SiteScan frontend"
git remote add origin https://github.com/<YOUR_USERNAME>/sitescan-frontend.git
git push -u origin main
```

### 6-2. Cloudflare Pages でプロジェクトを作成

1. https://dash.cloudflare.com → Pages → 「Create a project」
2. 「Connect to Git」→ GitHubリポジトリを選択
3. Build settings:
   - **Framework preset**: Next.js (Static HTML Export)
   - **Build command**: `npm run build`
   - **Build output directory**: `out`
   - **Environment variables**: `NEXT_PUBLIC_API_URL` = `https://api.pik-tal.com`
4. 「Save and Deploy」

### 6-3. カスタムドメインを設定

1. Cloudflare Pages → プロジェクト → Custom Domains
2. `pik-tal.com` を追加
3. `www.pik-tal.com` も追加（リダイレクト用）
4. Cloudflare が自動的にDNSレコードを設定

---

## Step 7: Resend でメール送信を設定

1. https://resend.com でアカウント作成
2. Domains → `pik-tal.com` を追加
3. Cloudflare DNS に表示されるレコード（TXT, CNAME）を追加して認証
4. API Keys → 新しいキーを発行 → `.env` の `RESEND_API_KEY` に記入

---

## Step 8: Discord Webhook を作成

1. Discord でサーバーを作成（または既存サーバーを使用）
2. チャンネル設定 → Integrations → Webhooks → 「New Webhook」
3. Webhook URL をコピー → `.env` の `DISCORD_WEBHOOK_URL` に記入

---

## Step 9: 最終確認

```bash
# VPSでコンテナ再起動（全設定反映）
cd ~/sitescan-app
docker compose down
docker compose up -d --build

# 確認項目
# 1. API ヘルスチェック
curl https://api.pik-tal.com/api/health

# 2. フロントエンド
# ブラウザで https://pik-tal.com を開く

# 3. テスト診断（無料）
# フォームにURLとメールを入力して「無料で診断する」をクリック

# 4. Discord通知
# 日次レポートが届くか確認（翌日19:00）

# 5. Stripe テスト決済
# Stripeテストモードで有料診断をテスト
```

---

## 運用コマンド集

```bash
# ログ確認
docker compose logs -f

# 再起動
docker compose restart

# 停止
docker compose down

# DBバックアップ
cp ~/sitescan-app/backend/sitescan.db ~/backups/sitescan-$(date +%Y%m%d).db

# 統計確認
curl https://api.pik-tal.com/api/stats
```

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `502 Bad Gateway` | `docker compose logs` でエラー確認。コンテナが起動しているか `docker ps` で確認 |
| Playwrightエラー | Dockerコンテナ内でChromiumが正常インストールされているか確認。メモリ不足の可能性 |
| Stripe Webhook失敗 | Stripe ダッシュボードのWebhookログを確認。Signing Secretが正しいか確認 |
| メールが届かない | Resend ダッシュボードのログを確認。ドメイン認証が完了しているか確認 |
| APIコスト超過 | `curl https://api.pik-tal.com/api/stats` でAPI費用を確認。月$50超過でアラート |
