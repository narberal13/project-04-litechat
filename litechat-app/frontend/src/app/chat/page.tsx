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

const MOOD_EMOJIS = [
  { score: 1, emoji: "😢", label: "つらい" },
  { score: 2, emoji: "😔", label: "もやもや" },
  { score: 3, emoji: "😐", label: "ふつう" },
  { score: 4, emoji: "😊", label: "まあまあ" },
  { score: 5, emoji: "😄", label: "いい感じ" },
];

export default function ChatPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [plan, setPlan] = useState("free");
  const [nickname, setNickname] = useState("");
  const [chatId, setChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");

  // Settings
  const [showSettings, setShowSettings] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [settingsMsg, setSettingsMsg] = useState("");
  const [settingsError, setSettingsError] = useState("");
  const [paymentNotice, setPaymentNotice] = useState("");
  const [editNickname, setEditNickname] = useState("");
  const [personality, setPersonality] = useState("");
  const [retroResult, setRetroResult] = useState("");

  // Rate limit
  const [messagesToday, setMessagesToday] = useState(0);
  const [messagesWeek, setMessagesWeek] = useState(0);

  // Mood
  const [selectedMood, setSelectedMood] = useState<number | null>(null);

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
        setNickname(data.nickname || "");
        setMessagesToday(data.messages_today || 0);
        setMessagesWeek(data.messages_week || 0);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("kikuyo_user");
    if (saved) {
      const user = JSON.parse(saved);
      setUserId(user.user_id);
      setPlan(user.plan);
      setEmail(user.email || "");
      setNickname(user.nickname || "");
      loadChats(user.user_id);
      loadUserInfo(user.user_id);
    }

    const params = new URLSearchParams(window.location.search);
    const payment = params.get("payment");
    if (payment === "success") {
      setPaymentNotice("決済が完了しました！まいにちプランが有効になります。");
      window.history.replaceState({}, "", "/chat");
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

  const isAdmin = email === "gamma.narberal@gmail.com";

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
      setNickname(data.nickname || "");
      localStorage.setItem("kikuyo_user", JSON.stringify({ ...data, email }));
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
      setAuthSuccess(`仮パスワード: ${data.temporary_password}\nこのパスワードでログインしてください。`);
      setShowForgot(false);
      setIsLogin(true);
    } catch {
      setAuthError("接続エラー");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("kikuyo_user");
    setUserId(null);
    setEmail("");
    setPassword("");
    setPlan("free");
    setNickname("");
    setChatId(null);
    setChats([]);
    setMessages([]);
    setIsLogin(true);
    setSelectedMood(null);
  };

  const loadChat = async (cid: string) => {
    setChatId(cid);
    try {
      const res = await fetch(`${API_URL}/api/chat/history/${cid}`);
      const data = await res.json();
      setMessages(
        data.messages.map((m: { role: string; content: string }) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
        }))
      );
    } catch { /* ignore */ }
    setSidebarOpen(false);
  };

  const newChat = () => {
    setChatId(null);
    setMessages([]);
    setSidebarOpen(false);
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

  const recordMood = async (score: number) => {
    if (!userId) return;
    setSelectedMood(score);
    try {
      await fetch(`${API_URL}/api/chat/mood`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, score }),
      });
    } catch { /* ignore */ }
    setTimeout(() => setSelectedMood(null), 2000);
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

  const saveNickname = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/users/${userId}/nickname`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nickname: editNickname }),
      });
      if (res.ok) {
        const data = await res.json();
        setNickname(data.nickname);
        setSettingsMsg("ニックネームを保存しました");
      }
    } catch { /* ignore */ }
  };

  const loadPersonality = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/users/${userId}/personality`);
      if (res.ok) {
        const data = await res.json();
        setPersonality(data.personality || "");
      }
    } catch { /* ignore */ }
  };

  const savePersonality = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/users/${userId}/personality`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ personality }),
      });
      if (res.ok) {
        setSettingsMsg("AI人格設定を保存しました");
      } else {
        const err = await res.json();
        setSettingsError(err.detail || "エラーが発生しました");
      }
    } catch {
      setSettingsError("接続エラー");
    }
  };

  const loadRetrospective = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_URL}/api/chat/retrospective/${userId}`);
      if (res.ok) {
        const data = await res.json();
        setRetroResult(data.retrospective);
      } else {
        const err = await res.json();
        setSettingsError(err.detail || "エラーが発生しました");
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
    setEditNickname(nickname);
    setRetroResult("");
    if (userId) {
      loadUserInfo(userId);
      if (plan !== "free") loadPersonality();
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
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: err.detail || "エラーが発生しました" },
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

      if (plan === "free") setMessagesToday((prev) => prev + 1);
      if (plan === "mainichi") setMessagesWeek((prev) => prev + 1);
      if (userId) loadChats(userId);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "接続エラーが発生しました。" }]);
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

  const freeLimit = 3;
  const weekLimit = 70;

  // Forgot password screen
  if (showForgot) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <h1 className={styles.loginTitle}>きくよ</h1>
          <p className={styles.loginSub}>パスワード再発行</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
            登録済みのメールアドレスを入力してください。
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
          <h1 className={styles.loginTitle}>きくよ</h1>
          <p className={styles.loginSub}>{isLogin ? "おかえりなさい" : "はじめまして"}</p>
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
            {isLogin ? "ログイン" : "無料ではじめる"}
          </button>
          <p className={styles.loginNote}>
            <button
              onClick={() => { setIsLogin(!isLogin); setAuthError(""); setAuthSuccess(""); }}
              style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontSize: 13 }}
            >
              {isLogin ? "はじめての方はこちら" : "アカウントをお持ちの方はこちら"}
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
          <h2>きくよ</h2>
          <button className={styles.newChatBtn} onClick={newChat}>
            + 新しい会話
          </button>
        </div>

        <div className={styles.chatListSection}>
          <div className={styles.chatListTitle}>履歴</div>
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
            <span className={styles.planBadge}>
              {plan === "free" ? "おためし" : "まいにち"}
            </span>
            {isAdmin && (
              <a href="/admin" className={styles.adminLink}>管理画面</a>
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
          <span className={styles.topTitle}>
            きくよ
          </span>
          {nickname && <span className={styles.topSub}>{nickname}さんの話を聴いてます</span>}
          {plan === "free" && !isAdmin && (
            <span className={styles.rateLimit}>
              残り {Math.max(0, freeLimit - messagesToday)}/{freeLimit} 回/日
            </span>
          )}
          {plan === "mainichi" && !isAdmin && (
            <span className={styles.rateLimit}>
              残り {Math.max(0, weekLimit - messagesWeek)}/{weekLimit} 回/週
            </span>
          )}
        </div>

        {paymentNotice && (
          <div className={styles.paymentNotice}>
            <span>{paymentNotice}</span>
            <button onClick={() => setPaymentNotice("")}>&times;</button>
          </div>
        )}

        {/* Mood bar */}
        <div className={styles.moodBar}>
          <span className={styles.moodLabel}>今の気分:</span>
          {MOOD_EMOJIS.map((m) => (
            <button
              key={m.score}
              className={`${styles.moodBtn} ${selectedMood === m.score ? styles.moodBtnActive : ""}`}
              onClick={() => recordMood(m.score)}
              title={m.label}
            >
              {m.emoji}
            </button>
          ))}
        </div>

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
                {settingsMsg && <p className={styles.successMsg}>{settingsMsg}</p>}
                {settingsError && <p className={styles.errorMsg}>{settingsError}</p>}

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
                        {plan === "free" ? "おためし" : "まいにち"}
                      </span>
                    </span>
                  </div>
                  {plan === "free" && !isAdmin && (
                    <div className={styles.settingsRow}>
                      <span className={styles.settingsLabel}>今日の使用</span>
                      <span className={styles.settingsValue}>{messagesToday} / {freeLimit} 回</span>
                    </div>
                  )}
                  {plan === "mainichi" && (
                    <>
                      <div className={styles.settingsRow}>
                        <span className={styles.settingsLabel}>今週の使用</span>
                        <span className={styles.settingsValue}>{messagesWeek} / {weekLimit} 回</span>
                      </div>
                      <button className={styles.settingsActionBtn} onClick={openStripePortal} style={{ marginTop: 8 }}>
                        サブスクリプション管理
                      </button>
                    </>
                  )}
                  {plan === "free" && !isAdmin && (
                    <a href="/" className={styles.settingsActionBtn} style={{ display: "block", textAlign: "center", marginTop: 8, textDecoration: "none" }}>
                      まいにちプランに登録
                    </a>
                  )}
                </div>

                {/* Nickname */}
                <div className={styles.settingsSection}>
                  <h3>ニックネーム</h3>
                  <p className={styles.settingsDesc}>きくよがこの名前で呼んでくれます。</p>
                  <input
                    type="text"
                    placeholder="ニックネーム（20文字まで）"
                    value={editNickname}
                    onChange={(e) => setEditNickname(e.target.value)}
                    className={styles.settingsInput}
                    maxLength={20}
                  />
                  <button className={styles.settingsActionBtn} onClick={saveNickname}>
                    保存
                  </button>
                </div>

                {/* Custom personality (paid only) */}
                <div className={styles.settingsSection}>
                  <h3>AI人格カスタマイズ</h3>
                  {plan === "free" ? (
                    <p className={styles.paidFeatureNote}>
                      まいにちプラン限定の機能です。きくよの話し方や性格をカスタマイズできます。
                    </p>
                  ) : (
                    <>
                      <p className={styles.settingsDesc}>
                        きくよの性格や話し方をカスタマイズできます。マークダウン形式で記述してください（最大2000文字）。
                      </p>
                      <textarea
                        className={styles.settingsTextarea}
                        placeholder={"例:\n# きくよの人格設定\n- 関西弁で話す\n- たまにダジャレを言う\n- 「〜やね」「〜やん」を使う"}
                        value={personality}
                        onChange={(e) => setPersonality(e.target.value)}
                        maxLength={2000}
                      />
                      <button className={styles.settingsActionBtn} onClick={savePersonality}>
                        AI人格を保存
                      </button>
                    </>
                  )}
                </div>

                {/* Weekly retrospective (paid only) */}
                <div className={styles.settingsSection}>
                  <h3>週次ふりかえり</h3>
                  {plan === "free" ? (
                    <p className={styles.paidFeatureNote}>
                      まいにちプラン限定の機能です。1週間の気分の変化を振り返れます。
                    </p>
                  ) : (
                    <>
                      <button className={styles.retroBtn} onClick={loadRetrospective}>
                        今週のふりかえりを見る
                      </button>
                      {retroResult && (
                        <div className={styles.retroResult}>{retroResult}</div>
                      )}
                    </>
                  )}
                </div>

                {/* Password change */}
                <div className={styles.settingsSection}>
                  <h3>パスワード変更</h3>
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
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>👂</div>
              <h2>きくよ</h2>
              <p>なんでも話してね。ただ聴くよ。</p>
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
              placeholder="なんでも話してね..."
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
            きくよは医療専門家ではありません。深刻な悩みは専門機関にご相談ください。
          </p>
        </div>
      </div>
    </div>
  );
}
