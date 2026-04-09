export default function PrivacyPage() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "60px 20px", fontSize: 14, lineHeight: 2 }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: 32 }}>プライバシーポリシー</h1>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>1. 基本方針</h2>
        <p>LiteChatは、ユーザーのプライバシーを最優先に設計されたAIチャットサービスです。デフォルトではユーザーデータは一切外部に送信されません。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>2. 収集する情報</h2>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>メールアドレス（アカウント識別・通知に使用）</li>
          <li>チャット内容（サービス提供のために保存）</li>
          <li>ユーザーメモリ情報（パーソナライズのために保存）</li>
          <li>決済情報（Stripe/PayPalを通じて処理。当サービスではカード情報を保持しません）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>3. データの処理場所</h2>
        <p><strong>ローカルAI処理:</strong> チャット内容はサーバー内のローカルLLMで処理されます。データは外部に送信されません。</p>
        <p style={{ marginTop: 8 }}><strong>高精度AI補助（オプション）:</strong> ユーザーが設定で有効にした場合のみ、質問のキーワード（トピックのみ）が外部AI（Anthropic Claude）に送信されます。ユーザーの会話内容全文が送信されることはありません。この機能はデフォルトで無効です。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>4. データの保存期間</h2>
        <ul style={{ paddingLeft: 20 }}>
          <li>Freeプラン: チャット履歴はセッション中のみ</li>
          <li>Liteプラン: チャット履歴7日間保存後、自動削除</li>
          <li>Proプラン: チャット履歴30日間保存後、自動削除</li>
          <li>ユーザーメモリ: ユーザーが手動で削除可能</li>
          <li>アカウント情報: ユーザーからの削除リクエストに基づき速やかに削除</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>5. 第三者提供</h2>
        <p>以下の場合を除き、個人情報を第三者に提供しません。</p>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>ユーザーの同意がある場合</li>
          <li>法令に基づく場合</li>
          <li>決済処理に必要な範囲（Stripe/PayPal）</li>
          <li>ユーザーが高精度AI補助を有効にした場合（Anthropic Claude — キーワードのみ）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>6. AI学習への利用</h2>
        <p>ユーザーのチャットデータをAIモデルの学習に使用することはありません。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>7. セキュリティ</h2>
        <p>SSL/TLS暗号化通信、アクセス制限、定期バックアップ等の安全管理措置を講じます。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>8. お問い合わせ</h2>
        <p>メール: <a href="mailto:support@pik-tal.com">support@pik-tal.com</a></p>
      </section>

      <p style={{ marginTop: 32, color: "var(--text-muted)", fontSize: 12 }}>最終更新日: 2026年4月9日</p>
      <a href="/" style={{ display: "inline-block", marginTop: 16, fontSize: 13 }}>← トップに戻る</a>
    </main>
  );
}
