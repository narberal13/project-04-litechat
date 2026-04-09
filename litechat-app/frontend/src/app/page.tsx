import styles from "./page.module.css";

export default function Home() {
  return (
    <main>
      <section className={styles.hero}>
        <h1 className={styles.title}>
          月<span className={styles.price}>300</span>円で
          <br />
          AI相棒
        </h1>
        <p className={styles.sub}>
          会話も、練習も、創作も。8つのモードで何でもAIと。
          <br />
          データは外部に出ません。
        </p>
        <div className={styles.cta}>
          <a href="/chat" className="btn btn-primary" style={{ fontSize: 18, padding: "14px 40px" }}>
            無料で試す
          </a>
          <p className={styles.ctaNote}>1日10メッセージ無料 / 登録10秒</p>
        </div>
      </section>

      {/* Modes */}
      <section className={styles.modes}>
        <h2>8つのモード</h2>
        <div className={styles.modeGrid}>
          {[
            { icon: "💬", name: "フリーチャット", desc: "何でも自由に聞ける" },
            { icon: "💡", name: "壁打ち", desc: "アイデアを広げる相棒" },
            { icon: "🇬🇧", name: "英会話練習", desc: "間違いを優しく訂正" },
            { icon: "💼", name: "面接練習", desc: "面接官がフィードバック" },
            { icon: "✍️", name: "文章作成", desc: "メール・ブログの下書き" },
            { icon: "📖", name: "ストーリー", desc: "対話型ゲーム" },
            { icon: "📋", name: "タスク管理", desc: "優先度付きリスト作成" },
            { icon: "📅", name: "スケジュール", desc: "予定を整理" },
          ].map((m) => (
            <div key={m.name} className={styles.modeItem}>
              <span className={styles.modeIcon}>{m.icon}</span>
              <strong>{m.name}</strong>
              <p>{m.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className={styles.compare}>
        <h2>なぜLiteChat？</h2>
        <div className={styles.grid}>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#128274;</div>
            <h3>プライバシー</h3>
            <p>あなたのデータは外部に送信されません。サーバー内で完結。AI補助も選択制。</p>
          </div>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#128176;</div>
            <h3>月300円から</h3>
            <p>ChatGPT Plusの1/10。必要な機能だけ、必要な分だけ。</p>
          </div>
          <div className={styles.card}>
            <div className={styles.cardIcon}>&#129504;</div>
            <h3>学習するAI</h3>
            <p>あなたの情報を記憶してパーソナライズ。使うほど賢くなります。</p>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className={styles.pricing}>
        <h2>料金プラン</h2>
        <div className={styles.pricingGrid}>
          <div className={styles.pricingCard}>
            <h3>Free</h3>
            <p className={styles.pricingAmount}>&#165;0</p>
            <ul>
              <li>ローカルAI: 10メッセージ/日</li>
              <li>高精度AI補助: 5回/日</li>
              <li>8モード全て利用可</li>
              <li>データ外部送信なし</li>
            </ul>
            <a href="/chat" className="btn btn-primary" style={{ width: "100%", background: "transparent", border: "1px solid var(--primary)", color: "var(--primary)" }}>
              今すぐ試す
            </a>
          </div>
          <div className={`${styles.pricingCard} ${styles.pricingFeatured}`}>
            <div className={styles.badge}>人気</div>
            <h3>Lite</h3>
            <p className={styles.pricingAmount}>&#165;300<span>/月</span></p>
            <ul>
              <li>ローカルAI: 無制限</li>
              <li>高精度AI補助: 30回/週</li>
              <li>チャット履歴7日</li>
              <li>ユーザーメモリ機能</li>
            </ul>
            <button className="btn btn-primary" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed" }} disabled>
              準備中
            </button>
          </div>
          <div className={styles.pricingCard}>
            <h3>Pro</h3>
            <p className={styles.pricingAmount}>&#165;600<span>/月</span></p>
            <ul>
              <li>ローカルAI: 無制限</li>
              <li>高精度AI補助: 無制限</li>
              <li>チャット履歴30日</li>
              <li>優先レスポンス</li>
            </ul>
            <button className="btn btn-primary" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed", background: "transparent", border: "1px solid var(--primary)", color: "var(--primary)" }} disabled>
              準備中
            </button>
          </div>
        </div>
        <p className={styles.privacyNote}>
          * 高精度AI補助は外部AIを使用します。利用時にデータの一部（トピックのキーワードのみ）が外部に送信されます。
          <br />
          設定でON/OFFを切り替えられます。OFFの場合、データは一切外部に出ません。
        </p>
      </section>

      <footer className={styles.footer}>
        <a href="/chat">チャット</a>
        <a href="/legal">特定商取引法に基づく表記</a>
        <a href="/privacy">プライバシーポリシー</a>
        <p>&copy; 2026 LiteChat by pik-tal.com</p>
      </footer>
    </main>
  );
}
