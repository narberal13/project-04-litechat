"use client";

import { useEffect, useState } from "react";
import styles from "./toswatch.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ServiceInfo {
  id: string;
  name: string;
  url: string;
  category: string;
  impact: string;
  last_checked: string | null;
}

interface KeyChange {
  what: string;
  impact: string;
}

interface ChangeAnalysis {
  impact_level: string;
  summary: string;
  key_changes: KeyChange[];
  action_required: string | null;
}

interface TosChange {
  target_id: string;
  service_name: string;
  category: string;
  analysis: ChangeAnalysis | null;
  impact_level: string;
  detected_at: string;
}

function ImpactBadge({ level }: { level: string }) {
  const cls =
    level === "high"
      ? styles.impactHigh
      : level === "medium"
        ? styles.impactMid
        : styles.impactLow;
  const label = level === "high" ? "高" : level === "medium" ? "中" : "低";
  return <span className={`${styles.impactBadge} ${cls}`}>{label}</span>;
}

function CategoryBadge({ category }: { category: string }) {
  return <span className={styles.categoryBadge}>{category}</span>;
}

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return `${diff}秒前`;
  if (diff < 3600) return `${Math.floor(diff / 60)}分前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}時間前`;
  return `${Math.floor(diff / 86400)}日前`;
}

export default function ToSWatchPage() {
  const [services, setServices] = useState<ServiceInfo[]>([]);
  const [changes, setChanges] = useState<TosChange[]>([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [svcRes, chgRes] = await Promise.all([
        fetch(`${API_URL}/api/toswatch/services`),
        fetch(`${API_URL}/api/toswatch/changes`),
      ]);
      if (svcRes.ok) setServices(await svcRes.json());
      if (chgRes.ok) setChanges(await chgRes.json());
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  const runCheck = async () => {
    setChecking(true);
    try {
      await fetch(`${API_URL}/api/toswatch/check`, { method: "POST" });
      await fetchData();
    } finally {
      setChecking(false);
    }
  };

  if (loading) {
    return (
      <main className="container" style={{ padding: "80px 0", textAlign: "center" }}>
        <div className={styles.spinner} />
        <p style={{ marginTop: 16, color: "var(--text-muted)" }}>読み込み中...</p>
      </main>
    );
  }

  return (
    <main className="container" style={{ padding: "40px 0" }}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1>ToSWatch</h1>
          <p className={styles.subtitle}>
            フリーランスが使うサービスの利用規約変更を自動監視
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={runCheck}
          disabled={checking}
        >
          {checking ? "チェック中..." : "今すぐチェック"}
        </button>
      </div>

      {/* Changes */}
      <section style={{ marginBottom: 48 }}>
        <h2 style={{ marginBottom: 20 }}>変更履歴</h2>
        {changes.length === 0 ? (
          <div className={`card ${styles.emptyState}`}>
            <p>変更は検出されていません</p>
            <p className={styles.emptyHint}>
              監視対象サービスの利用規約が変更されると、ここに表示されます。
              チェックは毎日06:00 JSTに自動実行されます。
            </p>
          </div>
        ) : (
          <div className={styles.changeList}>
            {changes.map((change, i) => (
              <div key={i} className={`card ${styles.changeCard}`}>
                <div className={styles.changeHeader}>
                  <div className={styles.changeMeta}>
                    <strong>{change.service_name}</strong>
                    <CategoryBadge category={change.category} />
                    <ImpactBadge level={change.impact_level} />
                  </div>
                  <span className={styles.changeDate}>
                    {timeAgo(change.detected_at)}
                  </span>
                </div>
                {change.analysis && (
                  <>
                    <p className={styles.changeSummary}>
                      {change.analysis.summary}
                    </p>
                    {change.analysis.key_changes.length > 0 && (
                      <div className={styles.keyChanges}>
                        {change.analysis.key_changes.map((kc, j) => (
                          <div key={j} className={styles.keyChange}>
                            <strong>{kc.what}</strong>
                            <p>{kc.impact}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {change.analysis.action_required && (
                      <div className={styles.actionRequired}>
                        <strong>要対応:</strong> {change.analysis.action_required}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Monitored Services */}
      <section>
        <h2 style={{ marginBottom: 20 }}>監視対象サービス</h2>
        <div className={styles.serviceGrid}>
          {services.map((svc) => (
            <div key={svc.id} className={`card ${styles.serviceCard}`}>
              <div className={styles.serviceHeader}>
                <strong>{svc.name}</strong>
                <CategoryBadge category={svc.category} />
              </div>
              <p className={styles.serviceImpact}>{svc.impact}</p>
              <div className={styles.serviceFooter}>
                <span className={styles.lastChecked}>
                  {svc.last_checked
                    ? `最終チェック: ${timeAgo(svc.last_checked)}`
                    : "未チェック"}
                </span>
                <a
                  href={svc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.viewLink}
                >
                  規約を見る
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
