"use client";

import { useState } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const handleCheckout = async () => {
    const saved = localStorage.getItem("kikuyo_user");
    if (!saved) {
      window.location.href = "/chat";
      return;
    }

    const user = JSON.parse(saved);
    setCheckoutLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/stripe/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.user_id }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "エラーが発生しました");
        return;
      }

      const data = await res.json();
      window.location.href = data.url;
    } catch {
      alert("接続エラーが発生しました");
    } finally {
      setCheckoutLoading(false);
    }
  };

  return (
    <main>
      <section className={styles.hero}>
        <h1 className={styles.title}>
          あなたの話を
          <br />
          <span className={styles.titleAccent}>ただ、聴く。</span>
        </h1>
        <p className={styles.sub}>
          愚痴も、悩みも、何でも。
          <br />
          全力で肯定してくれるAI「きくよ」
        </p>
        <div className={styles.cta}>
          <a href="/chat" className="btn btn-primary" style={{ fontSize: 18, padding: "14px 40px" }}>
            無料で話してみる
          </a>
          <p className={styles.ctaNote}>1日3回まで無料 / 登録10秒</p>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <h2>きくよの特徴</h2>
        <div className={styles.featureGrid}>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>👂</span>
            <h3>ただ聴く</h3>
            <p>アドバイスしない。否定しない。あなたの言葉をそのまま受け止めます。</p>
          </div>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>💚</span>
            <h3>全力で肯定</h3>
            <p>怒りも悲しみも「そうだよね」と受け止める。感情を安心して出せる場所。</p>
          </div>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>🔒</span>
            <h3>7日で自動消去</h3>
            <p>会話は7日後に完全削除。誰にも見られない、残らない安心感。</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className={styles.howItWorks}>
        <h2>使い方</h2>
        <div className={styles.stepList}>
          <div className={styles.step}>
            <div className={styles.stepNum}>1</div>
            <div>
              <strong>話しかける</strong>
              <p>何でも好きなことを。愚痴でも、悩みでも、嬉しいことでも。</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>2</div>
            <div>
              <strong>きくよが聴く</strong>
              <p>あなたの気持ちに寄り添って、ただ受け止めます。</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>3</div>
            <div>
              <strong>気分を記録</strong>
              <p>今の気分を絵文字でタップ。自分の変化が見えてきます。</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className={styles.pricing}>
        <h2>料金</h2>
        <div className={styles.pricingGrid}>
          <div className={styles.pricingCard}>
            <h3>おためし</h3>
            <p className={styles.pricingAmount}>&#165;0</p>
            <ul>
              <li>1日3回まで</li>
              <li>気分記録</li>
              <li>7日で自動消去</li>
            </ul>
            <a href="/chat" className="btn btn-primary" style={{ width: "100%", background: "transparent", border: "1px solid var(--primary)", color: "var(--primary)" }}>
              無料で試す
            </a>
          </div>
          <div className={`${styles.pricingCard} ${styles.pricingFeatured}`}>
            <div className={styles.badge}>おすすめ</div>
            <h3>まいにち</h3>
            <p className={styles.pricingAmount}>&#165;500<span>/月</span></p>
            <ul>
              <li>週70回まで</li>
              <li>気分記録 + 週次ふりかえり</li>
              <li>AI人格カスタマイズ</li>
              <li>7日で自動消去</li>
            </ul>
            <button
              className="btn btn-primary"
              style={{ width: "100%" }}
              onClick={handleCheckout}
              disabled={checkoutLoading}
            >
              {checkoutLoading ? "処理中..." : "まいにちプランに登録"}
            </button>
          </div>
        </div>
        <p className={styles.privacyNote}>
          * きくよはClaude Haiku AIを利用しています。会話内容はAI処理のために送信されますが、7日後に完全削除されます。
        </p>
      </section>

      {/* Safety */}
      <section className={styles.safety}>
        <div className={styles.safetyBox}>
          <h3>つらいとき、ひとりで抱え込まないでね</h3>
          <p>
            いのちの電話: 0120-783-556 / よりそいホットライン: 0120-279-338（24時間）
          </p>
        </div>
      </section>

      <footer className={styles.footer}>
        <a href="/chat">きくよと話す</a>
        <a href="/legal">特定商取引法に基づく表記</a>
        <a href="/privacy">プライバシーポリシー</a>
        <p>&copy; 2026 きくよ by pik-tal.com</p>
      </footer>
    </main>
  );
}
