# Project-04: LiteChat — ローカルLLMチャットサービス

## 概要
月額¥300/¥600のAIチャットサービス。ローカルLLM(Qwen 2.5 7B)でAPI費用ゼロ運用。
ChatGPT Plus ¥3,000は高いという層をターゲットに、プライバシー重視・低価格で提供。

## プロジェクト状態（2026-04-09時点）
- **本番URL**: https://pik-tal.com
- **ステータス**: デプロイ済み・稼働中
- **決済**: 未有効化（Stripe/PayPal準備中のため「準備中」表示）
- **SiteScan**: 停止中（LiteChatに移行済み）

## アーキテクチャ

```
[ユーザー] → [Cloudflare DNS] → [Nginx + Let's Encrypt]
                                    ├── /         → Next.js (pm2, port 3000)
                                    └── /api/*    → FastAPI (Docker, port 8000)
                                                      └── llama.cpp (Docker, port 8080)
                                                            └── Qwen 2.5 7B Q4_K_M
```

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 15.1 (App Router), React 19, TypeScript 5.7 |
| バックエンド | FastAPI 0.115.6, Python 3.12, Uvicorn |
| データベース | SQLite (aiosqliteによる非同期アクセス) |
| AI/LLM | llama.cpp (Qwen 2.5 7B Q4_K_M) + Claude Haiku（フォールバック） |
| 決済 | Stripe（準備中） |
| インフラ | Docker Compose, Nginx, Let's Encrypt, Vultr VPS |
| DNS | Cloudflare (DNS only) |

## VPS情報
- **LiteChat本番**: Vultr Tokyo 4vCPU/8GB RAM, IP: `45.77.24.224`
  - Instance ID: `368cd92b-0e52-4cc2-aa6d-5df2fa2b4695`
  - OS: Ubuntu, Docker Compose + pm2
- **SiteScan（停止中）**: IP: `45.77.17.143` — halt状態、削除可能
- **旧VM（不要）**: `45.32.41.195`, `149.28.28.108` — 削除可能

## ディレクトリ構成

```
Project-04/
├── CLAUDE.md                          ← このファイル
├── claude-agents-company-design.md    ← Agents会社構想（v3.1）
├── local-llm-chat-design.md           ← LiteChat設計書（v2.0）
├── litechat-app/                      ← メインプロジェクト
│   ├── docker-compose.yml             ← backend + llama.cpp
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt           ← fastapi, uvicorn, aiosqlite, httpx, anthropic, stripe
│   │   ├── .env.example               ← 環境変数テンプレート
│   │   ├── .env                       ← 本番用（gitignore済み）
│   │   └── app/
│   │       ├── main.py                ← FastAPIエントリ（lifespan, CORS, routers）
│   │       ├── config.py              ← Pydantic Settings（.env読込）
│   │       ├── database.py            ← SQLiteスキーマ（users, chats, messages, user_memory, usage_stats）
│   │       ├── routers/
│   │       │   ├── chat.py            ← POST /api/chat/send (SSE), GET /modes, /history, /list, /memory
│   │       │   ├── users.py           ← POST /register, /login, GET /{user_id}, POST /settings
│   │       │   ├── admin.py           ← GET /api/admin/dashboard (Basic Auth)
│   │       │   └── health.py          ← GET /api/health
│   │       └── services/
│   │           ├── llm.py             ← llama.cpp OpenAI互換API通信、SSEストリーミング
│   │           ├── modes.py           ← 8チャットモード（free, brainstorm, english, interview, writing, story, task, schedule）
│   │           ├── memory.py          ← ユーザー記憶（正規表現キーワード抽出、max30/user）
│   │           ├── fallback.py        ← Claude Haiku安全フォールバック（キーワード抽出のみ外部送信）
│   │           └── haiku_limit.py     ← プランベースHaiku使用制限
│   ├── frontend/
│   │   ├── package.json               ← Next.js 15
│   │   ├── next.config.ts             ← output: "standalone"
│   │   └── src/app/
│   │       ├── page.tsx               ← LP（8モード、3プラン、プライバシー説明）
│   │       ├── chat/page.tsx          ← チャットUI（ログイン/登録、モード選択、SSE表示）
│   │       ├── admin/page.tsx         ← 管理者ダッシュボード（KPI、日次統計、ユーザー一覧）
│   │       ├── legal/page.tsx         ← 特定商取引法に基づく表記
│   │       └── privacy/page.tsx       ← プライバシーポリシー
│   └── models/                        ← LLMモデルファイル（gitignore済み）
│       └── qwen2.5-7b-instruct-q4_k_m.gguf (4.4GB)
└── sitescan-app/                      ← SiteScan（停止中、参考用に残存）
```

## 料金プラン

| プラン | 月額 | ローカルLLM | Haiku | 履歴保持 |
|--------|------|-------------|-------|----------|
| Free   | ¥0   | 10msg/日    | 5回/日（opt-in） | 7日 |
| Lite   | ¥300 | 無制限      | 30回/週（opt-in） | 14日 |
| Pro    | ¥600 | 無制限      | 無制限 | 30日 |

## 8つのチャットモード
1. **フリートーク** — 日常会話
2. **ブレスト** — アイデア発散（精度不要）
3. **英語練習** — 英会話レッスン
4. **面接対策** — 模擬面接
5. **文章添削** — 文章改善
6. **ストーリー** — 創作支援
7. **タスク管理** — ToDoリスト整理
8. **スケジュール** — 予定管理

## 管理者アカウント
- メール: `gamma.narberal@gmail.com`
- 管理者パスワード: `LiteChat@Admin2026!`
- 管理画面: https://pik-tal.com/admin （Basic Auth）
- 管理者はチャット無制限、レート制限バイパス

## Haiku フォールバック仕組み
1. ローカルLLMが「わかりません」パターンを返したら発動
2. ユーザーが外部AI使用をopt-inしている場合のみ
3. ユーザーのメッセージからキーワードのみ抽出（個人情報は除外）
4. キーワードだけをClaude Haikuに送信
5. Haikuの回答をローカルLLMに再構成させて返す

## VPSデプロイ手順

### 方法1: デプロイスクリプト（推奨）
```bash
ssh root@45.77.24.224 "/root/deploy.sh"
```

### 方法2: 手動
```bash
ssh root@45.77.24.224
cd /root/project-04
git pull origin main
rsync -av --delete --exclude='models' --exclude='.env' --exclude='node_modules' --exclude='.next' /root/project-04/litechat-app/ /root/litechat-app/
cd /root/litechat-app
docker compose up -d --build backend
cd frontend && npm install && NEXT_PUBLIC_API_URL=https://pik-tal.com npm run build
pm2 restart litechat-frontend
curl http://localhost:8000/api/health
```

### VPS上のディレクトリ構成
```
/root/
├── project-04/          ← Gitリポジトリ（git pullはここ）
├── litechat-app/        ← 実行用ディレクトリ（rsyncで同期）
│   ├── backend/         ← FastAPI + .env
│   ├── frontend/        ← Next.js
│   ├── models/          ← Qwen 2.5 7B (4.4GB)
│   └── docker-compose.yml
└── deploy.sh            ← ワンクリックデプロイ
```

### サービス管理コマンド
```bash
docker ps                          # バックエンド + llama.cpp状態確認
pm2 list                           # フロントエンド状態確認
curl http://localhost:8000/api/health  # ヘルスチェック
docker compose logs -f backend     # バックエンドログ
docker compose logs -f llama       # LLMログ
pm2 logs litechat-frontend         # フロントエンドログ
```

## 別端末でのセットアップ

```bash
# 1. リポジトリクローン
git clone https://github.com/narberal13/project-04-litechat.git project-04
cd project-04

# 2. バックエンド .env作成（本番の値はVPSの /root/litechat-app/backend/.env を参照）
cp litechat-app/backend/.env.example litechat-app/backend/.env
# .envを編集: ANTHROPIC_API_KEY, STRIPE_SECRET_KEY等を設定

# 3. ローカル開発（バックエンド）
cd litechat-app/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. ローカル開発（フロントエンド）
cd litechat-app/frontend
npm install
npm run dev

# 5. 本番デプロイ
git add . && git commit -m "変更内容" && git push origin main
ssh root@45.77.24.224 "/root/deploy.sh"
```

## コーディング規約

### Python（バックエンド）

- **全て非同期**: データベース操作・HTTP通信は全て `async`/`await` を使用
- **型ヒント**: Python 3.10+ のユニオン構文 (`str | None`、`Optional[str]` は使わない)
- **命名規則**: 関数・変数は `snake_case`、定数は `UPPERCASE`
- **import順序**: 標準ライブラリ → サードパーティ → ローカル (`from app.database import get_db`)
- **Pydanticモデル**: 全リクエスト・レスポンススキーマに使用
- **エラーハンドリング**: `HTTPException(status_code=..., detail="...")` でAPIエラーを返す
- **SQL**: パラメータ化クエリ (`?` プレースホルダー)。文字列結合によるSQL構築は禁止
- **タイムスタンプ**: UTC ISO文字列 `datetime.now(timezone.utc).isoformat()`

### TypeScript/React（フロントエンド）

- **`"use client"`**: React Hooksを使うコンポーネントに必須
- **状態管理**: React Hooksのみ (useState, useEffect, useRef)。外部ライブラリ不使用
- **データ取得**: ネイティブ `fetch` API。axios・SWR不使用
- **ストリーミング**: SSEレスポンスには `ReadableStream` リーダーを使用
- **環境変数**: `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"` パターン
- **ユーザーセッション**: `localStorage` に保存

### API設計

- **ルーターパターン**: `APIRouter(prefix="/api/...", tags=["..."])` を `main.py` でインクルード
- **SSEストリーミング**: `StreamingResponse(generate(), media_type="text/event-stream")`
- **CORS**: 開放設定 (`allow_origins=["*"]`)
- **認証**: グローバルミドルウェアなし。エンドポイントごとにユーザーIDを検証

### データベース

- **SQLite** + `aiosqlite`（非同期ドライバ）
- **スキーマ初期化**: `init_db()` 内の `CREATE TABLE IF NOT EXISTS` をlifespanで起動時に実行
- **行アクセス**: `db.row_factory = aiosqlite.Row` で辞書ライクにアクセス

## .env必須変数（本番）
```
LLAMA_SERVER_URL=http://llama:8080
ANTHROPIC_API_KEY=sk-ant-api03-...（Anthropicダッシュボードから取得）
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
APP_URL=https://pik-tal.com
DATABASE_URL=sqlite:///./litechat.db
FREE_MESSAGES_PER_DAY=10
MAX_CONTEXT_MESSAGES=10
MAX_TOKENS_PER_RESPONSE=1024
```

## 既知の注意事項
- Qwen 2.5 7Bは中国語を混ぜる傾向あり → 全モードのsystem promptに「中国語使用禁止」を明記済み
- 日付を聞くと2023年と答える → system promptに現在のJST日時を動的注入済み
- モデルファイル(4.4GB)はgitignore済み、VPSでは `/root/litechat-app/models/` に配置
- `.env` ファイルは絶対にコミットしない — APIキー・Stripeキーを含む
- SQLite DBファイル (`*.db`) はgitignore済み
- llama.cppコンテナは6GB RAM必要
- テストスイート未作成（pytest・Jest）
- CI/CDパイプラインなし（SSH + Docker Composeによる手動デプロイ）
- 日本語ファースト: UI、システムプロンプト、ユーザー向けメッセージは主に日本語

## 残タスク（優先度順）
1. Stripe決済有効化（オンボーディング完了後、「準備中」ボタンを有効化）
2. PayPalビジネスアカウント作成（Stripe代替）
3. Resendメール通知（アカウント作成+ドメイン認証）
4. Discord Webhook（管理者通知）
5. APIキーローテーション
6. 不要VM削除（45.77.17.143, 45.32.41.195, 149.28.28.108）
7. Agents自律管理機能（CEO/DevOps/Finance Agent）
