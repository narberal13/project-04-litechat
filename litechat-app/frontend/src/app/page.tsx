import styles from "./page.module.css";

export default function Home() {
  return (
    <main>
      <section className={styles.hero}>
        <h1 className={styles.title}>
          月<span className={styles.price}>500</span>円で
          <br />
          AI使い放題
        </h1>
        <p className={styles.sub}>
          会話も、練習も、創作も。なんでもAIと。ChatGPTの1/10の価格。
        </p>
        <div className={styles.cta}>
          <a href="/chat" className="btn btn-primary" style={{ fontSize: 18, padding: "14px 40px" }}>
            無料で試す
          </a>
          <p className={styles.ctaNote}>1日10メッセージまで無料 / 登録は10秒</p>
        </div>
      </section>

      <section className={styles.compare}>
        <h2>なぜLiteChat？</h2>
        <div className={styles.grid}>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#128176;</div>
            <h3>月500円</h3>
            <p>ChatGPT Plus（¥3,000）の1/6。缶コーヒー1本分でAIが使い放題。</p>
          </div>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#9854;</div>
            <h3>制限なし</h3>
            <p>メッセージ数の制限なし。遠慮なく何度でも質問できます。</p>
          </div>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#128274;</div>
            <h3>プライバシー</h3>
            <p>あなたのデータは外部に送信されません。サーバー内で完結。</p>
          </div>
        </div>
      </section>

      <section className={styles.pricing}>
        <h2>料金プラン</h2>
        <div className={styles.pricingGrid}>
          <div className={styles.pricingCard}>
            <h3>Free</h3>
            <p className={styles.pricingAmount}>¥0</p>
            <ul>
              <li>1日10メッセージ</li>
              <li>チャット履歴なし</li>
            </ul>
            <a href="/chat" className="btn btn-primary" style={{ width: "100%", background: "transparent", border: "1px solid var(--primary)", color: "var(--primary)" }}>
              今すぐ試す
            </a>
          </div>
          <div className={`${styles.pricingCard} ${styles.pricingFeatured}`}>
            <div className={styles.badge}>人気</div>
            <h3>Lite</h3>
            <p className={styles.pricingAmount}>¥300<span>/月</span></p>
            <ul>
              <li>メッセージ無制限</li>
              <li>チャット履歴7日</li>
            </ul>
            <button className="btn btn-primary" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed" }} disabled>
              準備中
            </button>
          </div>
          <div className={styles.pricingCard}>
            <h3>Pro</h3>
            <p className={styles.pricingAmount}>¥600<span>/月</span></p>
            <ul>
              <li>メッセージ無制限</li>
              <li>チャット履歴30日</li>
              <li>高精度AI補助</li>
            </ul>
            <button className="btn btn-primary" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed", background: "transparent", border: "1px solid var(--primary)", color: "var(--primary)" }} disabled>
              準備中
            </button>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <a href="/legal">特定商取引法に基づく表記</a>
        <a href="/privacy">プライバシーポリシー</a>
        <p>&copy; 2026 LiteChat by pik-tal.com</p>
      </footer>
    </main>
  );
}
