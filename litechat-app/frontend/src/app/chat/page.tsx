"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./chat.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatItem {
  id: string;
  title: string;
  updated_at: string;
}

interface Mode {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const DEFAULT_MODES: Mode[] = [
  { id: "free", name: "フリーチャット", icon: "💬", description: "なんでも自由に聞けるAIチャット" },
  { id: "brainstorm", name: "壁打ち・ブレスト", icon: "💡", description: "アイデアを広げる壁打ち相手" },
  { id: "english", name: "英会話練習", icon: "🇬🇧", description: "英語で会話して、間違いを優しく訂正" },
  { id: "interview", name: "面接練習", icon: "💼", description: "面接官として質問し、フィードバック" },
  { id: "writing", name: "文章作成", icon: "✍️", description: "メール・ブログの下書きを一緒に作成" },
  { id: "story", name: "ストーリー", icon: "📖", description: "AIと一緒に物語を作る対話型ゲーム" },
  { id: "task", name: "タスク管理", icon: "📋", description: "やることを整理して優先度をつける" },
  { id: "schedule", name: "スケジュール整理", icon: "📅", description: "予定を整理してタイムラインを作成" },
];

export default function ChatPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(false);
  const [authError, setAuthError] = useState("");
  const [plan, setPlan] = useState("free");
  const [chatId, setChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState("free");
  const [showModes, setShowModes] = useState(false);
  const [modes] = useState<Mode[]>(DEFAULT_MODES);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem("litechat_user");
    if (saved) {
      const user = JSON.parse(saved);
      setUserId(user.user_id);
      setPlan(user.plan);
      loadChats(user.user_id);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isAdmin = email === "gamma.narberal@gmail.com" ||
    (typeof window !== "undefined" && localStorage.getItem("litechat_user")?.includes("gamma.narberal"));

  const handleAuth = async () => {
    setAuthError("");
    const endpoint = isLogin ? "login" : "register";
    try {
      const res = await fetch(`${API_URL}/api/users/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json();
        setAuthError(err.detail || "エラーが発生しました");
        return;
      }
      const data = await res.json();
      setUserId(data.user_id);
      setPlan(data.plan);
      localStorage.setItem("litechat_user", JSON.stringify({ ...data, email }));
      loadChats(data.user_id);
    } catch {
      setAuthError("接続エラー");
    }
  };

  const loadChats = async (uid: string) => {
    const res = await fetch(`${API_URL}/api/chat/list/${uid}`);
    const data = await res.json();
    setChats(data.chats);
  };

  const loadChat = async (cid: string) => {
    setChatId(cid);
    const res = await fetch(`${API_URL}/api/chat/history/${cid}`);
    const data = await res.json();
    setMessages(
      data.messages.map((m: { role: string; content: string }) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }))
    );
    setSidebarOpen(false);
  };

  const newChat = () => {
    setChatId(null);
    setMessages([]);
    setSidebarOpen(false);
    setShowModes(true);
  };

  const selectMode = (modeId: string) => {
    setCurrentMode(modeId);
    setShowModes(false);
    setChatId(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const sendMessage = async () => {
    if (!input.trim() || loading || !userId) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          message: userMsg,
          user_id: userId,
          mode: currentMode,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${err.detail}` },
        ]);
        setLoading(false);
        return;
      }

      const newChatId = res.headers.get("X-Chat-Id");
      if (newChatId && !chatId) setChatId(newChatId);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          for (const line of chunk.split("\n")) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") break;
              assistantContent += data;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: "assistant", content: assistantContent };
                return updated;
              });
            }
          }
        }
      }

      if (userId) loadChats(userId);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Connection error." }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const currentModeInfo = modes.find((m) => m.id === currentMode) || modes[0];

  // Login screen
  if (!userId) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <h1 className={styles.loginTitle}>LiteChat</h1>
          <p className={styles.loginSub}>{isLogin ? "ログイン" : "無料で始める"}</p>
          <input
            type="email"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.loginInput}
          />
          <input
            type="password"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.loginInput}
            onKeyDown={(e) => e.key === "Enter" && handleAuth()}
          />
          {authError && <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 8 }}>{authError}</p>}
          <button className="btn btn-primary" onClick={handleAuth} style={{ width: "100%" }}>
            {isLogin ? "ログイン" : "新規登録（無料）"}
          </button>
          <p className={styles.loginNote}>
            <button
              onClick={() => { setIsLogin(!isLogin); setAuthError(""); }}
              style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontSize: 13 }}
            >
              {isLogin ? "アカウントをお持ちでない方 → 新規登録" : "既にアカウントをお持ちの方 → ログイン"}
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Sidebar */}
      <div className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ""}`}>
        <div className={styles.sidebarHeader}>
          <h2>LiteChat</h2>
          <button className={styles.newChatBtn} onClick={newChat}>
            + 新しいチャット
          </button>
        </div>

        {/* Mode selector in sidebar */}
        <div className={styles.modeSection}>
          <div className={styles.modeSectionTitle}>モード</div>
          <div className={styles.modeList}>
            {modes.map((m) => (
              <button
                key={m.id}
                className={`${styles.modeItem} ${m.id === currentMode ? styles.modeItemActive : ""}`}
                onClick={() => selectMode(m.id)}
              >
                <span className={styles.modeIcon}>{m.icon}</span>
                <span>{m.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.chatListSection}>
          <div className={styles.modeSectionTitle}>履歴</div>
          <div className={styles.chatList}>
            {chats.map((c) => (
              <button
                key={c.id}
                className={`${styles.chatItem} ${c.id === chatId ? styles.chatItemActive : ""}`}
                onClick={() => loadChat(c.id)}
              >
                {c.title}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.sidebarFooter}>
          <span className={styles.planBadge}>{plan === "free" ? "Free" : plan}</span>
          {isAdmin && (
            <a href="/admin" className={styles.adminLink}>Admin Dashboard</a>
          )}
        </div>
      </div>

      {/* Main */}
      <div className={styles.main}>
        <div className={styles.topBar}>
          <button className={styles.menuBtn} onClick={() => setSidebarOpen(!sidebarOpen)}>
            &#9776;
          </button>
          <span className={styles.topMode}>
            {currentModeInfo.icon} {currentModeInfo.name}
          </span>
        </div>

        {/* Mode selection overlay */}
        {showModes && (
          <div className={styles.modeOverlay}>
            <h2>モードを選んでください</h2>
            <div className={styles.modeGrid}>
              {modes.map((m) => (
                <button key={m.id} className={styles.modeCard} onClick={() => selectMode(m.id)}>
                  <div className={styles.modeCardIcon}>{m.icon}</div>
                  <div className={styles.modeCardName}>{m.name}</div>
                  <div className={styles.modeCardDesc}>{m.description}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 && !showModes && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>{currentModeInfo.icon}</div>
              <h2>{currentModeInfo.name}</h2>
              <p>{currentModeInfo.description}</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`${styles.message} ${msg.role === "user" ? styles.messageUser : styles.messageAssistant}`}
            >
              <div className={styles.messageContent}>
                {msg.content || (loading && i === messages.length - 1 ? "..." : "")}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className={styles.inputArea}>
          <div className={styles.inputWrapper}>
            <textarea
              ref={inputRef}
              className={styles.input}
              placeholder={
                currentMode === "english"
                  ? "Type in English..."
                  : "メッセージを入力..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button className={styles.sendBtn} onClick={sendMessage} disabled={loading || !input.trim()}>
              &#9654;
            </button>
          </div>
          <p className={styles.disclaimer}>
            AIの回答は参考情報です。重要な判断にはご自身で確認してください。
          </p>
        </div>
      </div>
    </div>
  );
}
