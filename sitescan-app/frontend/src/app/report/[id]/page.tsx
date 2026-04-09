"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import styles from "./report.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ReportItem {
  label: string;
  status: "good" | "warning" | "critical";
  current_value: string;
  recommendation: string | null;
}

interface ReportSection {
  name: string;
  score: number;
  items: ReportItem[];
}

interface ActionItem {
  priority: "high" | "medium" | "low";
  action: string;
  section: string;
}

interface Report {
  summary: string;
  overall_score: number;
  sections: ReportSection[];
  action_list: ActionItem[];
}

interface ScanData {
  id: string;
  url: string;
  status: string;
  report?: Report;
  scores?: { overall: number };
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

function ScoreCircle({ score }: { score: number }) {
  const cls =
    score >= 80 ? styles.scoreHigh : score >= 50 ? styles.scoreMid : styles.scoreLow;
  return <div className={`${styles.scoreCircle} ${cls}`}>{score}</div>;
}

function StatusIcon({ status }: { status: string }) {
  if (status === "good") return <span className={styles.statusGood}>OK</span>;
  if (status === "warning") return <span className={styles.statusWarning}>注意</span>;
  return <span className={styles.statusCritical}>要改善</span>;
}

function PriorityBadge({ priority }: { priority: string }) {
  const cls =
    priority === "high"
      ? styles.priorityHigh
      : priority === "medium"
        ? styles.priorityMid
        : styles.priorityLow;
  const label = priority === "high" ? "高" : priority === "medium" ? "中" : "低";
  return <span className={`${styles.priorityBadge} ${cls}`}>{label}</span>;
}

export default function ReportPage() {
  const params = useParams();
  const scanId = params.id as string;
  const [scan, setScan] = useState<ScanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const fetchScan = async () => {
      try {
        const res = await fetch(`${API_URL}/api/scans/${scanId}`);
        if (!res.ok) throw new Error("レポートが見つかりません");
        const data = await res.json();
        setScan(data);

        if (data.status === "completed" || data.status === "failed") {
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "エラー");
        setLoading(false);
        clearInterval(interval);
      }
    };

    fetchScan();
    interval = setInterval(fetchScan, 5000);

    return () => clearInterval(interval);
  }, [scanId]);

  if (error) {
    return (
      <main className="container" style={{ padding: "80px 0", textAlign: "center" }}>
        <h2>エラー</h2>
        <p style={{ color: "var(--text-muted)", marginTop: 12 }}>{error}</p>
        <a href="/" className="btn btn-primary" style={{ marginTop: 24 }}>
          トップに戻る
        </a>
      </main>
    );
  }

  if (!scan || scan.status === "pending" || scan.status === "processing") {
    return (
      <main className="container" style={{ padding: "80px 0", textAlign: "center" }}>
        <div className={styles.spinner} />
        <h2 style={{ marginTop: 24 }}>診断中...</h2>
        <p style={{ color: "var(--text-muted)", marginTop: 12 }}>
          {scan?.url || "サイト"}を分析しています。通常1〜3分で完了します。
        </p>
      </main>
    );
  }

  if (scan.status === "failed") {
    return (
      <main className="container" style={{ padding: "80px 0", textAlign: "center" }}>
        <h2>診断に失敗しました</h2>
        <p style={{ color: "var(--text-muted)", marginTop: 12 }}>
          {scan.error_message || "予期しないエラーが発生しました。"}
        </p>
        <a href="/" className="btn btn-primary" style={{ marginTop: 24 }}>
          再診断する
        </a>
      </main>
    );
  }

  const report = scan.report!;

  return (
    <main className="container" style={{ padding: "40px 0" }}>
      {/* Header */}
      <div className={styles.reportHeader}>
        <div>
          <h1 className={styles.reportTitle}>診断レポート</h1>
          <p className={styles.reportUrl}>{scan.url}</p>
          <p className={styles.reportDate}>
            診断日: {new Date(scan.completed_at!).toLocaleDateString("ja-JP")}
          </p>
        </div>
        <ScoreCircle score={report.overall_score} />
      </div>

      {/* Summary */}
      <div className={`card ${styles.summaryCard}`}>
        <h2>エグゼクティブサマリー</h2>
        <p>{report.summary}</p>
      </div>

      {/* Sections */}
      {report.sections.map((section) => (
        <div key={section.name} className={`card ${styles.sectionCard}`}>
          <div className={styles.sectionHeader}>
            <h2>{section.name}</h2>
            <ScoreCircle score={section.score} />
          </div>
          <div className={styles.itemList}>
            {section.items.map((item, i) => (
              <div key={i} className={styles.item}>
                <div className={styles.itemHeader}>
                  <StatusIcon status={item.status} />
                  <span className={styles.itemLabel}>{item.label}</span>
                </div>
                <p className={styles.itemValue}>{item.current_value}</p>
                {item.recommendation && (
                  <p className={styles.itemRec}>
                    <strong>改善策:</strong> {item.recommendation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Action List */}
      <div className={`card ${styles.actionCard}`}>
        <h2>改善アクションリスト（優先度順）</h2>
        <div className={styles.actionList}>
          {report.action_list.map((action, i) => (
            <div key={i} className={styles.actionItem}>
              <span className={styles.actionNum}>{i + 1}</span>
              <PriorityBadge priority={action.priority} />
              <span className={styles.actionText}>{action.action}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className={styles.cta}>
        <p>より詳細な診断が必要ですか？</p>
        <a href="/" className="btn btn-primary">
          有料プランで完全診断する
        </a>
      </div>
    </main>
  );
}
