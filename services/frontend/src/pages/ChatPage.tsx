import { useCallback, useEffect, useRef, useState } from "react";
import AssessmentPageHeader from "../components/AssessmentPageHeader";
import {
  ChatMessage,
  ChatSession,
  createChatSession,
  getChatMessages,
  listChatSessions,
  postChatMessage,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";

const GENERAL_WORKSTREAM = "general";

export default function ChatPage() {
  const { assessmentId } = useAssessment();
  const navLink = useAssessmentNavLink();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [lastTransactionId, setLastTransactionId] = useState<string | null>(null);
  const loadGenRef = useRef(0);

  const loadMessagesSafe = useCallback(async (sessionId: string) => {
    const gen = ++loadGenRef.current;
    const msgs = await getChatMessages(sessionId);
    if (gen !== loadGenRef.current) return;
    setMessages(msgs);
  }, []);

  const loadSessions = useCallback(async () => {
    if (!assessmentId) return;
    const list = await listChatSessions(assessmentId);
    setSessions(list);
    return list;
  }, [assessmentId]);

  useEffect(() => {
    if (!assessmentId) {
      setSessions([]);
      setActiveSession(null);
      setMessages([]);
      return;
    }
    loadSessions()
      .then((list) => {
        if (!list?.length) {
          setActiveSession(null);
          setMessages([]);
          return;
        }
        const match =
          list.find((s) => s.workstream === GENERAL_WORKSTREAM) ?? list[0];
        setActiveSession(match);
        loadMessagesSafe(match.id);
      })
      .catch(() => {
        setSessions([]);
        setActiveSession(null);
        setMessages([]);
      });
  }, [assessmentId, loadSessions, loadMessagesSafe]);

  const ensureSession = async (): Promise<ChatSession | null> => {
    if (!assessmentId) return null;
    if (activeSession) return activeSession;
    const created = await createChatSession(
      assessmentId,
      GENERAL_WORKSTREAM,
      "Genel Sohbet",
    );
    setActiveSession(created);
    setSessions((prev) => [created, ...prev]);
    return created;
  };

  const send = async () => {
    if (!text.trim() || sending) return;
    const content = text.trim();
    const pendingId = `pending-${crypto.randomUUID()}`;
    const optimistic: ChatMessage = {
      id: pendingId,
      session_id: activeSession?.id ?? "pending",
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setText("");
    setMessages((prev) => [...prev, optimistic]);
    setSending(true);
    try {
      const sess = await ensureSession();
      if (!sess) {
        setMessages((prev) => prev.filter((m) => m.id !== pendingId));
        return;
      }
      const res = await postChatMessage(sess.id, content);
      setMessages((prev) => {
        const base = prev.filter((m) => m.id !== pendingId);
        return [...base, res.user_message, res.assistant_message];
      });
      setLastTransactionId(res.transaction_id ?? null);
    } catch {
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== pendingId),
        {
          id: crypto.randomUUID(),
          session_id: activeSession?.id ?? "local",
          role: "assistant",
          content: "Mesaj gönderilirken hata oluştu.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const selectSession = async (s: ChatSession) => {
    setActiveSession(s);
    setLastTransactionId(null);
    await loadMessagesSafe(s.id);
  };

  const newChat = async () => {
    if (!assessmentId) return;
    const created = await createChatSession(
      assessmentId,
      GENERAL_WORKSTREAM,
      `Sohbet — ${new Date().toLocaleTimeString("tr-TR")}`,
    );
    setSessions((prev) => [created, ...prev]);
    setActiveSession(created);
    setMessages([]);
    setLastTransactionId(null);
  };

  return (
    <div
      data-testid="chat-page"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 140px)",
        minHeight: 400,
      }}
    >
      <AssessmentPageHeader
        title="Chat"
        subtitle="Assessment kapsamında genel AI sohbet"
        actions={
          <button
            type="button"
            onClick={newChat}
            style={{
              background: "#2563eb",
              border: "none",
              borderRadius: 6,
              padding: "8px 14px",
              color: "#fff",
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            Yeni Sohbet
          </button>
        }
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "220px 1fr",
          gap: 12,
          flex: 1,
          minHeight: 0,
        }}
      >
        <aside
          style={{
            borderRight: "1px solid #1e293b",
            overflowY: "auto",
            paddingRight: 8,
          }}
        >
          <p style={{ fontSize: 11, color: "#64748b", marginBottom: 8 }}>Oturumlar</p>
          {sessions.length === 0 ? (
            <p style={{ fontSize: 12, color: "#64748b" }}>Henüz oturum yok</p>
          ) : (
            sessions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => selectSession(s)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "8px 10px",
                  marginBottom: 4,
                  borderRadius: 6,
                  border:
                    activeSession?.id === s.id
                      ? "1px solid #3b82f6"
                      : "1px solid #334155",
                  background: activeSession?.id === s.id ? "#1e3a5f" : "#1e293b",
                  color: "#e2e8f0",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                <div style={{ fontWeight: 600 }}>{s.title}</div>
                <div style={{ color: "#64748b", fontSize: 10 }}>
                  {new Date(s.updated_at).toLocaleString("tr-TR")}
                </div>
              </button>
            ))
          )}
        </aside>

        <div style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div
            data-testid="chat-messages"
            style={{
              flex: 1,
              overflowY: "auto",
              border: "1px solid #1e293b",
              borderRadius: 8,
              padding: 12,
              marginBottom: 8,
            }}
          >
            {!assessmentId ? (
              <p style={{ color: "#64748b", fontSize: 13 }}>Önce assessment seçin.</p>
            ) : messages.length === 0 ? (
              <p style={{ color: "#64748b", fontSize: 13 }}>
                Sohbet başlatmak için mesaj yazın.
              </p>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  data-testid={`chat-msg-${m.role}`}
                  style={{
                    marginBottom: 10,
                    display: "flex",
                    justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "75%",
                      padding: "10px 12px",
                      borderRadius: 8,
                      background: m.role === "user" ? "#1d4ed8" : "#1e293b",
                      fontSize: 13,
                      whiteSpace: "pre-wrap",
                      opacity: m.id.startsWith("pending-") ? 0.85 : 1,
                    }}
                  >
                    {m.content}
                  </div>
                </div>
              ))
            )}
          </div>

          {lastTransactionId && (
            <a
              href={navLink(`/yurutme-plani?transaction_id=${lastTransactionId}`)}
              style={{ fontSize: 11, color: "#60a5fa", marginBottom: 8 }}
            >
              Yürütme planını gör ({lastTransactionId.slice(0, 8)}…)
            </a>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <input
              data-testid="chat-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())
              }
              placeholder="Mesajınızı yazın…"
              disabled={!assessmentId}
              style={{
                flex: 1,
                background: "#1e293b",
                color: "#e2e8f0",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "10px 12px",
                fontSize: 13,
              }}
            />
            <button
              type="button"
              data-testid="chat-send"
              onClick={send}
              disabled={sending || !text.trim() || !assessmentId}
              style={{
                background: "#2563eb",
                border: "none",
                borderRadius: 8,
                padding: "10px 16px",
                color: "#fff",
                cursor: "pointer",
                opacity: sending ? 0.7 : 1,
              }}
            >
              {sending ? "…" : "Gönder"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
