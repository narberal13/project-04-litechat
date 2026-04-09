export default function LegalPage() {
  const rows = [
    ["販売事業者", "ToolLab"],
    ["所在地", "請求があった場合、遅滞なく開示いたします。"],
    ["電話番号", "請求があった場合、遅滞なく開示いたします。"],
    ["メールアドレス", "toollab13@gmail.com"],
    ["販売URL", "https://pik-tal.com"],
    ["販売価格", "まいにちプラン: 500円/月（税込）"],
    ["支払い方法", "クレジットカード（Stripe経由）"],
    ["サービス提供時期", "決済完了後、即時にサービスをご利用いただけます。"],
    ["返品・キャンセル", "月額サブスクリプションのため、次回更新日までにキャンセルすることで翌月以降の課金を停止できます。日割り返金はいたしかねます。"],
    ["動作環境", "モダンブラウザ（Chrome, Firefox, Safari, Edge の最新版）"],
    ["サービス内容", "AI傾聴サービス「きくよ」。Claude Haiku AIによる共感的な会話機能の提供。"],
  ];

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "60px 20px" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: 32 }}>特定商取引法に基づく表記</h1>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, lineHeight: 1.8 }}>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label} style={{ borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "12px 16px", textAlign: "left", width: 160, verticalAlign: "top", background: "var(--surface)" }}>
                {label}
              </th>
              <td style={{ padding: "12px 16px" }}>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ marginTop: 32, color: "var(--text-muted)", fontSize: 12 }}>最終更新日: 2026年4月9日</p>
      <a href="/" style={{ display: "inline-block", marginTop: 16, fontSize: 13 }}>← トップに戻る</a>
    </main>
  );
}
