"""ToSWatch monitoring targets — services whose ToS pages we track."""

TARGETS = [
    {
        "id": "lancers",
        "name": "Lancers",
        "url": "https://www.lancers.jp/help/terms",
        "category": "案件獲得",
        "impact": "手数料・支払い条件",
    },
    {
        "id": "slack",
        "name": "Slack",
        "url": "https://slack.com/intl/ja-jp/terms-of-service",
        "category": "業務",
        "impact": "料金・データポリシー・API制限",
    },
    {
        "id": "freee",
        "name": "freee",
        "url": "https://www.freee.co.jp/terms/",
        "category": "会計",
        "impact": "料金プラン・機能変更",
    },
    {
        "id": "moneyforward",
        "name": "マネーフォワード",
        "url": "https://biz.moneyforward.com/agreement",
        "category": "会計",
        "impact": "料金プラン・機能変更",
    },
    {
        "id": "stripe",
        "name": "Stripe",
        "url": "https://stripe.com/jp/legal/ssa",
        "category": "決済",
        "impact": "手数料・本人確認要件",
    },
    {
        "id": "paypal",
        "name": "PayPal",
        "url": "https://www.paypal.com/jp/legalhub/useragreement-full",
        "category": "決済",
        "impact": "手数料・凍結ポリシー",
    },
    {
        "id": "github",
        "name": "GitHub",
        "url": "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service",
        "category": "開発",
        "impact": "料金・利用制限",
    },
    {
        "id": "notion",
        "name": "Notion",
        "url": "https://www.notion.so/Terms-and-Privacy-28ffdd083dc3473e9c2da6ec011b58ac",
        "category": "業務",
        "impact": "料金・データポリシー",
    },
    {
        "id": "cloudflare",
        "name": "Cloudflare",
        "url": "https://www.cloudflare.com/terms/",
        "category": "インフラ",
        "impact": "料金・利用制限・サービス変更",
    },
    {
        "id": "vercel",
        "name": "Vercel",
        "url": "https://vercel.com/legal/terms",
        "category": "開発",
        "impact": "料金・利用制限・デプロイ制限",
    },
]
