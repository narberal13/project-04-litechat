"use client";

import { useState } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    scan_id: string;
    message: string;
  } | null>(null);
  const [error, setError] = useState("");

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/api/scans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, email }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "エラーが発生しました");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      {/* Hero */}
      <section className={styles.hero}>
        <div className="container">
          <h1 className={styles.heroTitle}>
            あなたのWebサイト、
            <br />
            <span className={styles.accent}>AIが無料で診断します</span>
          </h1>
          <p className={styles.heroSub}>
            URLを入力するだけ。SEO・パフォーマンス・アクセシビリティを
            <br />
            AIが分析し、具体的な改善アクションをレポートします。
          </p>

          {/* Scan Form */}
          <div className={styles.formCard}>
            {result ? (
              <div className={styles.successBox}>
                <h3>診断を開始しました</h3>
                <p>{result.message}</p>
                <a
                  href={`/report/${result.scan_id}/`}
                  className="btn btn-primary"
                  style={{ marginTop: 16 }}
                >
                  レポートページへ
                </a>
              </div>
            ) : (
              <form onSubmit={handleScan}>
                <div className={styles.inputGroup}>
                  <label htmlFor="url">診断するURL</label>
                  <input
                    id="url"
                    type="text"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                    className={styles.input}
                  />
                </div>
                <div className={styles.inputGroup}>
                  <label htmlFor="email">メールアドレス（結果通知用）</label>
                  <input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className={styles.input}
                  />
                </div>
                {error && <p className={styles.error}>{error}</p>}
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                  style={{ width: "100%", marginTop: 8 }}
                >
                  {loading ? "診断中..." : "無料で診断する"}
                </button>
                <p className={styles.freeNote}>
                  月3回まで無料 / クレジットカード不要
                </p>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: 48 }}>
            SiteScan でできること
          </h2>
          <div className={styles.featureGrid}>
            <div className="card">
              <h3>SEO分析</h3>
              <p>
                タイトル・メタディスクリプション・見出し構造・構造化データを
                チェックし、検索順位を上げるための具体策を提示します。
              </p>
            </div>
            <div className="card">
              <h3>パフォーマンス診断</h3>
              <p>
                読み込み速度・ページサイズを計測。
                画像最適化・JS遅延読み込みなど、すぐに実行できる改善策を提案。
              </p>
            </div>
            <div className="card">
              <h3>アクセシビリティ</h3>
              <p>
                alt属性の不足・コントラスト比・タップターゲットサイズを検出。
                すべてのユーザーがアクセスしやすいサイトに。
              </p>
            </div>
            <div className="card">
              <h3>コンテンツ品質</h3>
              <p>
                読みやすさ・CTA配置・情報設計を評価。
                訪問者を行動に導くサイト構成をアドバイスします。
              </p>
            </div>
            <div className="card">
              <h3>モバイル対応</h3>
              <p>
                レスポンシブ対応・viewport設定・タッチ操作性を確認。
                スマホユーザーの体験を改善します。
              </p>
            </div>
            <div className="card">
              <h3>優先度付きアクションリスト</h3>
              <p>
                数値の羅列ではなく「何を・どう直すか」を優先度順に提示。
                技術者でなくてもすぐに実行できます。
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className={styles.pricing}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: 48 }}>料金プラン</h2>
          <div className={styles.pricingGrid}>
            <div className={`card ${styles.pricingCard}`}>
              <h3>Free</h3>
              <p className={styles.price}>
                <span className={styles.priceAmount}>&#165;0</span>
              </p>
              <ul className={styles.pricingList}>
                <li>月3回まで診断</li>
                <li>簡易レポート（スコア + 上位3項目）</li>
                <li>メール通知</li>
              </ul>
              <a href="#top" className="btn btn-outline" style={{ width: "100%" }}>
                今すぐ試す
              </a>
            </div>
            <div
              className={`card ${styles.pricingCard} ${styles.pricingFeatured}`}
            >
              <div className={styles.badge}>おすすめ</div>
              <h3>単発診断</h3>
              <p className={styles.price}>
                <span className={styles.priceAmount}>&#165;1,000</span>
                <span className={styles.pricePer}>/回</span>
              </p>
              <ul className={styles.pricingList}>
                <li>完全レポート（全項目）</li>
                <li>優先度付きアクションリスト</li>
                <li>PDF出力</li>
                <li>メール通知</li>
              </ul>
              <button className="btn btn-primary" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed" }} disabled>
                準備中
              </button>
            </div>
            <div className={`card ${styles.pricingCard}`}>
              <h3>月額プラン</h3>
              <p className={styles.price}>
                <span className={styles.priceAmount}>&#165;2,980</span>
                <span className={styles.pricePer}>/月</span>
              </p>
              <ul className={styles.pricingList}>
                <li>月5回まで完全診断</li>
                <li>月次定点観測レポート</li>
                <li>改善トラッキング</li>
                <li>優先サポート</li>
              </ul>
              <button className="btn btn-outline" style={{ width: "100%", opacity: 0.6, cursor: "not-allowed" }} disabled>
                準備中
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section style={{ padding: "80px 0" }}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: 48 }}>
            よくある質問
          </h2>
          <div className={styles.faqList}>
            <div className={styles.faqItem}>
              <h3>診断にどのくらい時間がかかりますか？</h3>
              <p>
                通常1〜3分で完了します。完了次第、メールでお知らせします。
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>どんなサイトでも診断できますか？</h3>
              <p>
                公開されているWebサイトであれば診断可能です。
                自分のサイトはもちろん、競合サイトの分析や参考サイトの調査にもご活用いただけます。
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>診断結果は正確ですか？</h3>
              <p>
                AIによる分析結果は参考情報としてご活用ください。
                具体的な施策の実行前に、必要に応じて専門家にご相談されることをお勧めします。
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>無料プランで十分ですか？</h3>
              <p>
                無料プランではスコアと上位3つの改善ポイントを確認できます。
                すべての診断項目と詳細なアクションリストが必要な場合は有料プランをご検討ください。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
