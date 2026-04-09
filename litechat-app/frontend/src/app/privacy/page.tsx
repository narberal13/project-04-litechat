export default function PrivacyPage() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "60px 20px", fontSize: 14, lineHeight: 2 }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: 32 }}>プライバシーポリシー</h1>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>1. 基本方針</h2>
        <p>「きくよ」は、ユーザーのプライバシーを重視したAI傾聴サービスです。会話内容は7日後に自動削除されます。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>2. 収集する情報</h2>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>メールアドレス（アカウント識別に使用）</li>
          <li>チャット内容（サービス提供のために一時保存、7日後に自動削除）</li>
          <li>気分記録（ユーザーが任意で記録した気分スコア）</li>
          <li>ニックネーム（任意設定）</li>
          <li>決済情報（Stripeを通じて処理。当サービスではカード情報を保持しません）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>3. データの処理</h2>
        <p>チャット内容はAnthropic社のClaude Haiku APIで処理されます。処理後のデータはAnthropic社で学習に使用されることはありません（API利用規約に基づく）。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>4. データの保存期間</h2>
        <ul style={{ paddingLeft: 20 }}>
          <li>チャット履歴: 7日間保存後、自動削除（全プラン共通）</li>
          <li>気分記録: ユーザーが手動で削除可能</li>
          <li>アカウント情報: ユーザーからの削除リクエストに基づき速やかに削除</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>5. 第三者提供</h2>
        <p>以下の場合を除き、個人情報を第三者に提供しません。</p>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>ユーザーの同意がある場合</li>
          <li>法令に基づく場合</li>
          <li>決済処理に必要な範囲（Stripe）</li>
          <li>AI応答生成のために必要な範囲（Anthropic — 会話内容）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>6. AI学習への利用</h2>
        <p>ユーザーのチャットデータをAIモデルの学習に使用することはありません。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>7. 注意事項</h2>
        <p>「きくよ」は医療機関ではありません。深刻な悩みや危機的状況では、いのちの電話（0120-783-556）やよりそいホットライン（0120-279-338）にご連絡ください。</p>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: "1.1rem" }}>8. お問い合わせ</h2>
        <p>メール: <a href="mailto:toollab13@gmail.com">toollab13@gmail.com</a></p>
      </section>

      <p style={{ marginTop: 32, color: "var(--text-muted)", fontSize: 12 }}>最終更新日: 2026年4月9日</p>
      <a href="/" style={{ display: "inline-block", marginTop: 16, fontSize: 13 }}>← トップに戻る</a>
    </main>
  );
}
