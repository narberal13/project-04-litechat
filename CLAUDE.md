# CLAUDE.md

## リポジトリ概要

**pik-tal.com** プラットフォーム向けの2つのSaaSアプリケーションを含むモノレポ:

1. **LiteChat** (`litechat-app/`) — ローカルQwen 2.5 7Bモデル（llama.cpp）を使った低価格AIチャットサービス（月額¥500）
2. **SiteScan + ToSWatch** (`sitescan-app/`) — Claude APIを使ったWebサイト診断 + 利用規約変更監視サービス

両アプリとも同じ技術スタック: **Next.js 15フロントエンド + FastAPIバックエンド + SQLiteデータベース**

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 15.1 (App Router), React 19, TypeScript 5.7 |
| バックエンド | FastAPI 0.115.6, Python 3.12, Uvicorn |
| データベース | SQLite (aiosqliteによる非同期アクセス) |
| AI/LLM | llama.cpp (Qwen 2.5 7B) — LiteChat用; Anthropic Claude API — SiteScan用 |
| 決済 | Stripe |
| メール | Resend API |
| 通知 | Discord Webhooks |
| インフラ | Docker Compose, Nginx, Cloudflare Pages, Vultr VPS |

## プロジェクト構造

```
project-04-litechat/
├── CLAUDE.md
├── claude-agents-company-design.md   # マルチエージェント事業設計書
├── local-llm-chat-design.md          # LiteChatサービス設計書
├── litechat-app/
│   ├── docker-compose.yml            # backend + llama.cppサーバー
│   ├── frontend/                     # Next.jsアプリ
│   │   └── src/app/                  # App Routerページ
│   │       ├── page.tsx              # ランディングページ
│   │       ├── chat/page.tsx         # チャットインターフェース
│   │       ├── admin/page.tsx        # 管理画面
│   │       ├── legal/page.tsx        # 利用規約
│   │       └── privacy/page.tsx      # プライバシーポリシー
│   └── backend/                      # FastAPIアプリ
│       └── app/
│           ├── main.py               # エントリポイント
│           ├── config.py             # Pydantic Settings
│           ├── database.py           # SQLiteスキーマ & 初期化
│           ├── routers/              # APIエンドポイント
│           │   ├── chat.py           # /api/chat (SSEストリーミング)
│           │   ├── users.py          # ユーザー管理
│           │   ├── admin.py          # 管理操作
│           │   └── health.py         # ヘルスチェック
│           └── services/             # ビジネスロジック
│               ├── llm.py            # LLM連携
│               ├── fallback.py       # Anthropic APIフォールバック
│               ├── memory.py         # チャット履歴管理
│               ├── modes.py          # チャットモード
│               └── haiku_limit.py    # レート制限
└── sitescan-app/
    ├── DEPLOY.md                     # VPSデプロイガイド
    ├── docker-compose.yml            # backendサービス
    ├── generate-pdf.py               # PDFレポート生成
    ├── frontend/                     # Next.jsアプリ
    │   └── src/app/
    │       ├── page.tsx              # ランディングページ
    │       ├── report/[id]/page.tsx  # 動的レポート表示
    │       ├── toswatch/page.tsx     # ToSWatchダッシュボード
    │       ├── legal/page.tsx        # 利用規約
    │       └── privacy/page.tsx      # プライバシーポリシー
    └── backend/                      # FastAPIアプリ
        └── app/
            ├── main.py
            ├── config.py
            ├── database.py
            ├── routers/
            │   ├── scans.py          # /api/scans
            │   ├── toswatch.py       # /api/toswatch
            │   ├── webhooks.py       # Stripe Webhooks
            │   └── health.py
            └── services/
                ├── analyzer.py       # サイト分析 (Claude API)
                ├── crawler.py        # Webスクレイピング
                ├── scanner.py        # スキャン統合管理
                ├── notifier.py       # Discord/メール通知
                └── toswatch/
                    ├── crawler.py    # 利用規約ページ監視
                    ├── analyzer.py   # 利用規約変更分析
                    ├── monitor.py    # スケジューリング
                    └── targets.py    # 監視対象サービス一覧
```

## 開発コマンド

### LiteChat

```bash
# バックエンド
cd litechat-app/backend
pip install -r requirements.txt
cp .env.example .env              # 値を設定する
uvicorn app.main:app --reload --port 8000

# フロントエンド
cd litechat-app/frontend
npm install
npm run dev                       # http://localhost:3000

# Docker Composeでフルスタック起動
cd litechat-app
docker compose up -d --build      # backend + llama.cppを起動
```

### SiteScan

```bash
# バックエンド
cd sitescan-app/backend
pip install -r requirements.txt
playwright install chromium        # Webスクレイピングに必要
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# フロントエンド
cd sitescan-app/frontend
npm install
npm run dev                       # http://localhost:3000

# Docker Composeでフルスタック起動
cd sitescan-app
docker compose up -d --build
```

### 本番デプロイ

```bash
docker compose up -d --build                     # コンテナデプロイ
docker compose logs -f                           # ログ監視
docker compose restart                           # サービス再起動
curl https://api.pik-tal.com/api/health          # ヘルスチェック
```

## コーディング規約

### Python（バックエンド）

- **全て非同期**: データベース操作・HTTP通信は全て `async`/`await` を使用
- **型ヒント**: Python 3.10+ のユニオン構文 (`str | None`、`Optional[str]` は使わない)
- **命名規則**: 関数・変数は `snake_case`、定数は `UPPERCASE`
- **import順序**: 標準ライブラリ → サードパーティ → ローカル (`from app.database import get_db`)
- **モジュールdocstring**: 各ファイル冒頭に簡潔な説明
- **Pydanticモデル**: 全リクエスト・レスポンススキーマに使用
- **エラーハンドリング**: `HTTPException(status_code=..., detail="...")` でAPIエラーを返す
- **リソース解放**: `try/finally` ブロックで `db.close()` を確実に実行
- **SQL**: パラメータ化クエリ (`?` プレースホルダー)。文字列結合によるSQL構築は禁止
- **タイムスタンプ**: UTC ISO文字列 `datetime.now(timezone.utc).isoformat()`

### TypeScript/React（フロントエンド）

- **`"use client"`**: React Hooksを使うコンポーネントに必須
- **Interface定義**: コンポーネント関数の上に定義
- **状態管理**: React Hooksのみ使用 (useState, useEffect, useRef)。Redux等の外部ライブラリは不使用
- **データ取得**: ネイティブ `fetch` API。axios・SWRは不使用
- **ストリーミング**: チャットエンドポイントのSSEレスポンスには `ReadableStream` リーダーを使用
- **CSSモジュール**: `*.module.css` から `styles` としてインポート。BEMライクな命名
- **CSS変数**: `globals.css` でテーマカラー等を定義
- **環境変数**: `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"` パターン
- **ユーザーセッション**: `localStorage` に保存

### API設計

- **ルーターパターン**: `APIRouter(prefix="/api/...", tags=["..."])` を `main.py` でインクルード
- **SSEストリーミング**: `StreamingResponse(generate(), media_type="text/event-stream")` でチャットレスポンス配信
- **CORS**: 開放設定 (`allow_origins=["*"]`)。本番ではCloudflareで制限
- **認証**: グローバルミドルウェアなし。エンドポイントごとにユーザーIDを検証
- **バックグラウンドタスク**: `asyncio.create_task()` でノンブロッキング処理

### データベース

- **SQLite** + `aiosqlite`（非同期ドライバ）
- **スキーマ初期化**: `init_db()` 内の `CREATE TABLE IF NOT EXISTS` をlifespanで起動時に実行
- **行アクセス**: `db.row_factory = aiosqlite.Row` で辞書ライクにアクセス
- **DBファイル**: アプリごとに1ファイル (`litechat.db` / `sitescan.db`)

## アーキテクチャ上の注意点

- **LiteChat LLMフォールバック**: メインはローカルllama.cpp (Qwen 2.5 7B)。利用不可時はAnthropic APIにフォールバック
- **CPU優先推論**: llama.cppはCPU上で動作（4スレッド、2パラレルスロット）。インフラコスト最小化のため
- **SiteScanのPlaywright**: ヘッドレスChromiumでWebサイトクロール・利用規約ページ監視
- **SiteScanのAPScheduler**: 定期的な利用規約チェックをバックグラウンドスケジュールタスクとして実行
- **CI/CDパイプラインなし**: SSH + Docker Composeによる手動デプロイ
- **テストスイートなし**: pytest・Jestテストは現在未作成
- **日本語ファースト**: UI、システムプロンプト、ユーザー向けメッセージは主に日本語

## 環境変数

両アプリとも `backend/` ディレクトリに `.env` ファイルが必要。設定値は `.env.example` を参照:

- **LiteChat**: `litechat-app/backend/.env.example` — llamaサーバーURL、Stripeキー、Discord Webhook、レート制限
- **SiteScan バックエンド**: `sitescan-app/backend/.env.example` — Anthropic APIキー、Stripeキー、Resend API、Discord Webhook、予算制限
- **SiteScan フロントエンド**: `sitescan-app/frontend/.env.example` — `NEXT_PUBLIC_API_URL`

両アプリ共通の環境変数: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `DISCORD_WEBHOOK_URL`, `DATABASE_URL`, `APP_URL`

## 重要な注意事項

- **`.env` ファイルは絶対にコミットしない** — Stripeライブキー、APIキー、Webhookシークレットを含む
- **SQLite DBファイル** (`*.db`) はgitignore済み — 追加しないこと
- **Playwrightにはシステム依存パッケージが必要** — SiteScanのDockerfileでインストール済み。ローカル開発では `playwright install chromium` を実行
- **llama.cppモデルダウンロード** は約4.5GB — Docker Composeが自動処理するが初回起動時に時間がかかる
- **メモリ制限**: llama.cppコンテナは6GB RAM必要、SiteScanバックエンドはPlaywrightに2GB必要
