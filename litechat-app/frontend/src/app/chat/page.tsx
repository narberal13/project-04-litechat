"use client";

import { useEffect, useRef, useState, useCallback } from "react";
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

interface Memory {
  id: number;
  fact: string;
  category: string;
  created_at: string;
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
  const [authSuccess, setAuthSuccess] = useState("");
  const [plan, setPlan] = useState("free");
  const [chatId, setChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState("free");
  const [showModes, setShowModes] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [modes] = useState<Mode[]>(DEFAULT_MODES);

  // Settings panel state
  const [showSettings, setShowSettings] = useState(false);
  const [externalAi, setExternalAi] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [settingsMsg, setSettingsMsg] = useState("");
  const [settingsError, setSettingsError] = useState("");
  const [paymentNotice, setPaymentNotice] = useState("");

  // Memory state
  const [memories, setMemories] = useState<Memory[]>([]);

  // Rate limit state
  const [messagesToday, setMessagesToday] = useState(0);
  const [freeLimit] = useState(10);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const loadChats = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_URL}/api/chat/list/${uid}`);
      const data = await res.json();
      setChats(data.chats);
    } catch { /* ignore */ }
  }, []);

  const loadUserInfo = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_URL}/api/users/${uid}`);
      if (res.ok) {
        const data = await res.json();
        setPlan(data.plan);
        setExternalAi(!!data.external_ai);
        setMessagesToday(data.messages_today || 0);
      }
    } catch { /* ignore */ }
  }, []);

  const loadMemories = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_URL}/api/chat/memory/${uid}`);
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("litechat_user");
    if (saved) {
      const user = JSON.parse(saved);
      setUserId(user.user_id);
      setPlan(user.plan);
      setEmail(user.email || "");
      loadChats(user.user_id);
      loadUserInfo(user.user_id);
    }

    // Handle payment redirect
    const params = new URLSearchParams(window.location.search);
    const payment = params.get("payment");
    if (payment === "success") {
      setPaymentNotice("決済が完了しました。プランがアップグレードされます。");
      window.history.replaceState({}, "", "/chat");
      // Reload user info to get updated plan
      if (saved) {
        const user = JSON.parse(saved);
        setTimeout(() => loadUserInfo(user.user_id), 2000);
      }
    } else if (payment === "cancel") {
      setPaymentNotice("決済がキャンセルされました。");
      window.history.replaceState({}, "", "/chat");
    }
  }, [loadChats, loadUserInfo]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isAdmin = email === "gamma.narberal@gmail.com" ||
    (typeof window !== "undefined" && localStorage.getItem("litechat_user")?.includes("gamma.narberal"));

  const handleAuth = async () => {
    setAuthError("");
    setAuthSuccess("");
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
      setExternalAi(!!data.external_ai);
      localStorage.setItem("litechat_user", JSON.stringify({ ...data, email }));
      loadChats(data.user_id);
      loadUserInfo(data.user_id);
    } catch {
      setAuthError("接続エラー");
    }
  };

  const handleForgotPassword = async () => {
    setAuthError("");
    setAuthSuccess("");
    try {
      const res = await fetch(`${API_URL}/api/users/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail }),
      });
      if (!res.ok) {
        const err = await res.json();
        setAuthError(err.detail || "エラーが発生しました");
        return;
      }
      const data = await res.json();
      setAuthSuccess(`仮パスワード: ${data.temporary_password}\nこのパスワードでログインし、設定から変更してください。`);
      setShowForgot(false);
      setIsLogin(true);
    } catch {
      setAuthError("接続エラー");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("litechat_user");
    setUserId(null);
    setEmail("");
    setPassword("");
    setPlan("free");
    setChatId(null);
    setChats([]);
    setMessages([]);
    setCurrentMode("free");
    setIsLogin(true);
    setExternalAi(false);
    setMemories([]);
    setMessagesToday(0);
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

  const deleteChat = async (e: React.MouseEvent, cid: string) => {
    e.stopPropagation();
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/chat/${cid}?user_id=${userId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setChats((prev) => prev.filter((c) => c.id !== cid));
        if (chatId === cid) {
          setChatId(null);
          setMessages([]);
        }
      }
    } catch { /* ignore */ }
  };

  const toggleExternalAi = async () => {
    if (!userId) return;
    const newVal = !externalAi;
    try {
      const res = await fetch(`${API_URL}/api/users/${userId}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ external_ai: newVal }),
      });
      if (res.ok) {
        setExternalAi(newVal);
      }
    } catch { /* ignore */ }
  };

  const handleChangePassword = async () => {
    setSettingsMsg("");
    setSettingsError("");
    if (!userId) return;
    if (newPassword.length < 4) {
      setSettingsError("新しいパスワードは4文字以上にしてください");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/users/${userId}/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json();
        setSettingsError(err.detail || "エラーが発生しました");
        return;
      }
      setSettingsMsg("パスワードを変更しました");
      setOldPassword("");
      setNewPassword("");
    } catch {
      setSettingsError("接続エラー");
    }
  };

  const deleteMemory = async (memoryId: number) => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/chat/memory/${userId}/${memoryId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setMemories((prev) => prev.filter((m) => m.id !== memoryId));
      }
    } catch { /* ignore */ }
  };

  const openStripePortal = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/stripe/portal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        const err = await res.json();
        setSettingsError(err.detail || "エラーが発生しました");
        return;
      }
      const data = await res.json();
      window.location.href = data.url;
    } catch {
      setSettingsError("接続エラー");
    }
  };

  const openSettings = () => {
    setShowSettings(true);
    setSettingsMsg("");
    setSettingsError("");
    setOldPassword("");
    setNewPassword("");
    if (userId) {
      loadMemories(userId);
      loadUserInfo(userId);
    }
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

      if (plan === "free") {
        setMessagesToday((prev) => prev + 1);
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
  const remainingMessages = Math.max(0, freeLimit - messagesToday);

  // Forgot password screen
  if (showForgot) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <h1 className={styles.loginTitle}>LiteChat</h1>
          <p className={styles.loginSub}>パスワード再発行</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
            登録済みのメールアドレスを入力してください。仮パスワードを発行します。
          </p>
          <input
            type="email"
            placeholder="メールアドレス"
            value={forgotEmail}
            onChange={(e) => setForgotEmail(e.target.value)}
            className={styles.loginInput}
            onKeyDown={(e) => e.key === "Enter" && handleForgotPassword()}
          />
          {authError && <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 8 }}>{authError}</p>}
          <button className="btn btn-primary" onClick={handleForgotPassword} style={{ width: "100%" }}>
            仮パスワードを発行
          </button>
          <p className={styles.loginNote}>
            <button
              onClick={() => { setShowForgot(false); setAuthError(""); }}
              style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontSize: 13 }}
            >
              ログインに戻る
            </button>
          </p>
        </div>
      </div>
    );
  }

  // Login screen
  if (!userId) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <h1 className={styles.loginTitle}>LiteChat</h1>
          <p className={styles.loginSub}>{isLogin ? "ログイン" : "無料で始める"}</p>
          {authSuccess && <p className={styles.successMsg} style={{ whiteSpace: "pre-line" }}>{authSuccess}</p>}
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
              onClick={() => { setIsLogin(!isLogin); setAuthError(""); setAuthSuccess(""); }}
              style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontSize: 13 }}
            >
              {isLogin ? "アカウントをお持ちでない方 → 新規登録" : "既にアカウントをお持ちの方 → ログイン"}
            </button>
          </p>
          {isLogin && (
            <button className={styles.forgotLink} onClick={() => { setShowForgot(true); setAuthError(""); setAuthSuccess(""); }}>
              パスワードを忘れた方
            </button>
          )}
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
              <div key={c.id} className={styles.chatItemRow}>
                <button
                  className={`${styles.chatItem} ${c.id === chatId ? styles.chatItemActive : ""}`}
                  onClick={() => loadChat(c.id)}
                >
                  {c.title}
                </button>
                <button
                  className={styles.chatDeleteBtn}
                  onClick={(e) => deleteChat(e, c.id)}
                  title="削除"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.sidebarFooter}>
          <div>
            <span className={styles.planBadge}>{plan === "free" ? "Free" : plan === "lite" ? "Lite" : "Pro"}</span>
            {isAdmin && (
              <a href="/admin" className={styles.adminLink}>Admin Dashboard</a>
            )}
          </div>
          <div className={styles.footerButtons}>
            <button className={styles.settingsBtn} onClick={openSettings} title="設定">
              &#9881;
            </button>
            <button className={styles.logoutBtn} onClick={handleLogout}>
              ログアウト
            </button>
          </div>
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
          {plan === "free" && !isAdmin && (
            <span className={styles.rateLimit}>
              残り {remainingMessages}/{freeLimit} 通/日
            </span>
          )}
        </div>

        {paymentNotice && (
          <div className={styles.paymentNotice}>
            <span>{paymentNotice}</span>
            <button onClick={() => setPaymentNotice("")}>&times;</button>
          </div>
        )}

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

        {/* Settings overlay */}
        {showSettings && (
          <div className={styles.settingsOverlay}>
            <div className={styles.settingsPanel}>
              <div className={styles.settingsHeader}>
                <h2>設定</h2>
                <button className={styles.settingsClose} onClick={() => setShowSettings(false)}>
                  &times;
                </button>
              </div>

              <div className={styles.settingsBody}>
                {/* Account info */}
                <div className={styles.settingsSection}>
                  <h3>アカウント</h3>
                  <div className={styles.settingsRow}>
                    <span className={styles.settingsLabel}>メール</span>
                    <span className={styles.settingsValue}>{email}</span>
                  </div>
                  <div className={styles.settingsRow}>
                    <span className={styles.settingsLabel}>プラン</span>
                    <span className={styles.settingsValue}>
                      <span className={styles.planBadge}>
                        {plan === "free" ? "Free" : plan === "lite" ? "Lite" : "Pro"}
                      </span>
                    </span>
                  </div>
                  {plan === "free" && !isAdmin && (
                    <div className={styles.settingsRow}>
                      <span className={styles.settingsLabel}>本日の使用量</span>
                      <span className={styles.settingsValue}>{messagesToday} / {freeLimit} メッセージ</span>
                    </div>
                  )}
                  {plan !== "free" && (
                    <button className={styles.settingsActionBtn} onClick={openStripePortal} style={{ marginTop: 8 }}>
                      サブスクリプション管理
                    </button>
                  )}
                </div>

                {/* External AI toggle */}
                <div className={styles.settingsSection}>
                  <h3>高精度AI補助（Claude Haiku）</h3>
                  <p className={styles.settingsDesc}>
                    ローカルAIが回答できない場合、キーワードのみを外部AIに送信して補足情報を取得します。
                    個人情報は送信されません。
                  </p>
                  <div className={styles.toggleRow}>
                    <span>外部AI補助を有効にする</span>
                    <button
                      className={`${styles.toggle} ${externalAi ? styles.toggleOn : ""}`}
                      onClick={toggleExternalAi}
                    >
                      <span className={styles.toggleKnob} />
                    </button>
                  </div>
                </div>

                {/* Password change */}
                <div className={styles.settingsSection}>
                  <h3>パスワード変更</h3>
                  {settingsMsg && <p className={styles.successMsg}>{settingsMsg}</p>}
                  {settingsError && <p className={styles.errorMsg}>{settingsError}</p>}
                  <input
                    type="password"
                    placeholder="現在のパスワード"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className={styles.settingsInput}
                  />
                  <input
                    type="password"
                    placeholder="新しいパスワード（4文字以上）"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={styles.settingsInput}
                    onKeyDown={(e) => e.key === "Enter" && handleChangePassword()}
                  />
                  <button className={styles.settingsActionBtn} onClick={handleChangePassword}>
                    パスワードを変更
                  </button>
                </div>

                {/* Memory management */}
                <div className={styles.settingsSection}>
                  <h3>AIが記憶した情報</h3>
                  <p className={styles.settingsDesc}>
                    会話から自動的に抽出された情報です。不要なものは削除できます。
                  </p>
                  {memories.length === 0 ? (
                    <p className={styles.settingsEmpty}>記憶された情報はまだありません</p>
                  ) : (
                    <div className={styles.memoryList}>
                      {memories.map((m) => (
                        <div key={m.id} className={styles.memoryItem}>
                          <div className={styles.memoryContent}>
                            <span className={styles.memoryCategory}>{m.category}</span>
                            <span>{m.fact}</span>
                          </div>
                          <button
                            className={styles.memoryDeleteBtn}
                            onClick={() => deleteMemory(m.id)}
                            title="削除"
                          >
                            &times;
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
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
