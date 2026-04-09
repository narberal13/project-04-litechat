export default function PrivacyPage() {
  return (
    <main
      className="container"
      style={{ padding: "60px 0", maxWidth: 720, fontSize: 14, lineHeight: 2 }}
    >
      <h1 style={{ marginBottom: 32 }}>プライバシーポリシー</h1>

      <section style={{ marginBottom: 32 }}>
        <h2>1. 収集する情報</h2>
        <p>当サービス（SiteScan）では、以下の情報を収集します。</p>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>メールアドレス（診断結果の通知に使用）</li>
          <li>診断対象のURL</li>
          <li>決済情報（Stripeを通じて処理。当サービスではカード情報を保持しません）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>2. 情報の利用目的</h2>
        <ul style={{ paddingLeft: 20 }}>
          <li>Webサイト診断レポートの生成・提供</li>
          <li>診断完了通知の送信</li>
          <li>サービス改善のための統計分析（個人を特定しない形式）</li>
        </ul>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>3. 第三者提供</h2>
        <p>
          お客様の個人情報を、以下の場合を除き第三者に提供することはありません。
        </p>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>お客様の同意がある場合</li>
          <li>法令に基づく場合</li>
          <li>
            サービス提供に必要な範囲で業務委託先に共有する場合
            （Stripe: 決済処理、Resend: メール送信）
          </li>
        </ul>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>4. データの保持期間</h2>
        <p>
          診断レポートのデータは、診断日から90日間保持した後、自動的に削除します。
          アカウント情報は、ユーザーからの削除リクエストに基づき速やかに削除します。
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>5. 診断対象サイトの情報</h2>
        <p>
          診断のためにアクセスしたWebサイトのHTML・メタデータは、
          レポート生成の目的にのみ使用し、第三者に提供・公開することはありません。
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>6. セキュリティ</h2>
        <p>
          お客様の情報を保護するために、SSL/TLS暗号化通信、
          アクセス制限、定期的なバックアップ等の適切な安全管理措置を講じます。
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>7. お問い合わせ</h2>
        <p>
          個人情報の取り扱いに関するお問い合わせは、以下までご連絡ください。
        </p>
        <p style={{ marginTop: 8 }}>
          メール:{" "}
          <a href="mailto:support@pik-tal.com">support@pik-tal.com</a>
        </p>
      </section>

      <section>
        <h2>8. ポリシーの変更</h2>
        <p>
          本ポリシーは、法令の改正やサービスの変更に伴い、予告なく改定する場合があります。
          改定後のポリシーは本ページに掲載した時点で効力を生じます。
        </p>
      </section>

      <p
        style={{
          marginTop: 40,
          color: "var(--text-muted)",
          fontSize: 13,
        }}
      >
        最終更新日: 2026年4月9日
      </p>
    </main>
  );
}
