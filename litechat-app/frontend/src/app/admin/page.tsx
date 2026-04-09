"use client";

import { useState, useEffect } from "react";
import styles from "./admin.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DailyMessage {
  date: string;
  cnt: number;
}

interface UserInfo {
  id: string;
  email: string;
  plan: string;
  messages_today: number;
  created_at: string;
}

interface Dashboard {
  total_users: number;
  paid_users: number;
  messages_today: number;
  total_messages: number;
  total_chats: number;
  daily_messages: DailyMessage[];
  recent_users: UserInfo[];
}

export default function AdminPage() {
  const [auth, setAuth] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const login = async () => {
    setError("");
    setLoading(true);
    const token = btoa(`${email}:${password}`);
    try {
      const res = await fetch(`${API_URL}/api/admin/dashboard`, {
        headers: { Authorization: `Basic ${token}` },
      });
      if (!res.ok) throw new Error("認証に失敗しました");
      const d = await res.json();
      setAuth(token);
      setData(d);
      localStorage.setItem("litechat_admin", token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラー");
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboard = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/admin/dashboard`, {
        headers: { Authorization: `Basic ${token}` },
      });
      if (!res.ok) { setAuth(null); return; }
      setData(await res.json());
    } catch { setAuth(null); }
  };

  useEffect(() => {
    const saved = localStorage.getItem("litechat_admin");
    if (saved) {
      setAuth(saved);
      fetchDashboard(saved);
    }
  }, []);

  if (!auth) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <h1>Admin</h1>
          <input
            type="email"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.input}
          />
          <input
            type="password"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            onKeyDown={(e) => e.key === "Enter" && login()}
          />
          {error && <p className={styles.error}>{error}</p>}
          <button className="btn btn-primary" onClick={login} disabled={loading} style={{ width: "100%" }}>
            {loading ? "..." : "ログイン"}
          </button>
        </div>
      </div>
    );
  }

  if (!data) return <div className={styles.loading}>読み込み中...</div>;

  return (
    <main className={styles.container}>
      <div className={styles.header}>
        <h1>LiteChat Admin</h1>
        <button
          className={styles.logoutBtn}
          onClick={() => { setAuth(null); localStorage.removeItem("litechat_admin"); }}
        >
          ログアウト
        </button>
      </div>

      {/* KPI Cards */}
      <div className={styles.kpiGrid}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiValue}>{data.total_users}</div>
          <div className={styles.kpiLabel}>総ユーザー</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiValue}>{data.paid_users}</div>
          <div className={styles.kpiLabel}>有料ユーザー</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiValue}>{data.messages_today}</div>
          <div className={styles.kpiLabel}>本日のメッセージ</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiValue}>{data.total_messages}</div>
          <div className={styles.kpiLabel}>総メッセージ</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiValue}>{data.total_chats}</div>
          <div className={styles.kpiLabel}>総チャット</div>
        </div>
      </div>

      {/* Daily Messages */}
      <div className={styles.section}>
        <h2>日別メッセージ数</h2>
        <div className={styles.barChart}>
          {data.daily_messages.map((d) => (
            <div key={d.date} className={styles.barItem}>
              <div className={styles.barValue}>{d.cnt}</div>
              <div
                className={styles.bar}
                style={{ height: `${Math.min(d.cnt * 3, 200)}px` }}
              />
              <div className={styles.barLabel}>{d.date.slice(5)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Users */}
      <div className={styles.section}>
        <h2>最近のユーザー</h2>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>メール</th>
              <th>プラン</th>
              <th>本日MSG</th>
              <th>登録日</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_users.map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>
                  <span className={`${styles.planBadge} ${u.plan !== "free" ? styles.planPaid : ""}`}>
                    {u.plan}
                  </span>
                </td>
                <td>{u.messages_today}</td>
                <td>{u.created_at.slice(0, 10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
