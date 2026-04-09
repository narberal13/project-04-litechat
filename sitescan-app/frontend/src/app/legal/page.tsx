export default function LegalPage() {
  return (
    <main className="container" style={{ padding: "60px 0", maxWidth: 720 }}>
      <h1 style={{ marginBottom: 32 }}>特定商取引法に基づく表記</h1>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 14,
          lineHeight: 1.8,
        }}
      >
        <tbody>
          {[
            ["販売事業者", "ToolLab"],
            [
              "所在地",
              "請求があった場合、遅滞なく開示いたします。",
            ],
            [
              "電話番号",
              "請求があった場合、遅滞なく開示いたします。",
            ],
            ["メールアドレス", "toollab13@gmail.com"],
            ["販売URL", "https://pik-tal.com"],
            [
              "販売価格",
              "単発診断: 1,000円（税込）/ 月額プラン: 2,980円（税込）",
            ],
            [
              "支払い方法",
              "クレジットカード（Stripe経由）",
            ],
            [
              "商品の引渡時期",
              "決済完了後、即時に診断を開始します。通常1〜3分でレポートが生成されます。",
            ],
            [
              "返品・キャンセル",
              "デジタルサービスの性質上、診断実行後の返金はいたしかねます。診断が正常に完了しなかった場合は、再診断または返金にて対応いたします。",
            ],
            [
              "動作環境",
              "モダンブラウザ（Chrome, Firefox, Safari, Edge の最新版）",
            ],
          ].map(([label, value]) => (
            <tr
              key={label}
              style={{ borderBottom: "1px solid var(--border)" }}
            >
              <th
                style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  width: 160,
                  verticalAlign: "top",
                  background: "#f9fafb",
                }}
              >
                {label}
              </th>
              <td style={{ padding: "12px 16px" }}>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p
        style={{
          marginTop: 32,
          color: "var(--text-muted)",
          fontSize: 13,
        }}
      >
        最終更新日: 2026年4月9日
      </p>
    </main>
  );
}
