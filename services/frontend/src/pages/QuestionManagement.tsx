// S10-FA-002 / S11-FA-003: Question Management — agent önerisi + soru bankası
import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import {
  listWorkstreamQuestions,
  createWorkstreamQuestion,
  listQuestions,
  approveQuestion,
  suggestBankQuestions,
  WorkstreamQuestion,
  Question,
  WORKSTREAMS,
} from "../api";

type TabFilter = "all" | "manual" | "agent";

// ── Yardımcı bileşenler ──────────────────────────────────────────────────────

function Badge({
  children,
  bg = "#334155",
  color = "#94a3b8",
  border,
}: {
  children: React.ReactNode;
  bg?: string;
  color?: string;
  border?: string;
}) {
  return (
    <span
      style={{
        background: bg,
        color,
        border: border ? `1px solid ${border}` : undefined,
        borderRadius: 4,
        padding: "1px 8px",
        fontSize: 10,
        fontWeight: 700,
        textTransform: "uppercase" as const,
        letterSpacing: "0.05em",
      }}
    >
      {children}
    </span>
  );
}

function TabButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? "#3b82f6" : "#1e293b",
        border: "1px solid #334155",
        borderRadius: 6,
        padding: "5px 14px",
        color: active ? "#fff" : "#94a3b8",
        cursor: "pointer",
        fontSize: 12,
        fontWeight: active ? 700 : 400,
        transition: "background 0.15s",
      }}
    >
      {label}{" "}
      <span style={{ color: active ? "#bfdbfe" : "#60a5fa", fontWeight: 700 }}>
        {count}
      </span>
    </button>
  );
}

// ── Sol panel: Soru bankası sorusu kartı ────────────────────────────────────

function BankQuestionCard({
  q,
  index,
  onDelete,
}: {
  q: WorkstreamQuestion;
  index: number;
  onDelete: (id: string) => void;
}) {
  return (
    <div
      style={{
        background: "#0f172a",
        border: "1px solid #334155",
        borderRadius: 8,
        padding: "10px 14px",
        marginBottom: 8,
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
      }}
    >
      {/* Sıra numarası */}
      <span
        style={{
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: 4,
          padding: "1px 7px",
          fontSize: 11,
          fontWeight: 700,
          color: "#60a5fa",
          minWidth: 28,
          textAlign: "center",
          flexShrink: 0,
          marginTop: 1,
        }}
      >
        {q.order ?? index + 1}
      </span>

      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.55, margin: 0 }}>
          {q.text}
        </p>
        {q.area && (
          <span
            style={{
              display: "inline-block",
              marginTop: 5,
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 3,
              padding: "1px 6px",
              fontSize: 10,
              color: "#64748b",
            }}
          >
            {q.area}
          </span>
        )}
      </div>

      <button
        onClick={() => onDelete(q.id)}
        title="Sil"
        style={{
          background: "transparent",
          border: "1px solid #334155",
          borderRadius: 5,
          padding: "3px 9px",
          color: "#ef4444",
          cursor: "pointer",
          fontSize: 11,
          fontWeight: 600,
          flexShrink: 0,
          transition: "background 0.15s",
        }}
        onMouseEnter={(e) =>
          ((e.currentTarget as HTMLButtonElement).style.background = "#ef444422")
        }
        onMouseLeave={(e) =>
          ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
        }
      >
        Sil
      </button>
    </div>
  );
}

// ── Sağ panel: Agent önerisi kartı ──────────────────────────────────────────

function SuggestionCard({
  q,
  onAction,
}: {
  q: Question;
  onAction: (id: string, action: "approved" | "rejected") => void;
}) {
  const [loading, setLoading] = useState(false);

  const handle = async (action: "approved" | "rejected") => {
    setLoading(true);
    try {
      await approveQuestion(q.id, action);
      onAction(q.id, action);
    } catch {
      /* sessizce geç */
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: "#eab30811",
        border: "1px solid #eab30844",
        borderLeft: "3px solid #eab308",
        borderRadius: 8,
        padding: "12px 14px",
        marginBottom: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        <Badge bg="#eab30822" color="#eab308" border="#eab30866">
          Agent Önerisi
        </Badge>
        {q.approval_status && (
          <Badge bg="#334155" color="#94a3b8">
            {q.approval_status}
          </Badge>
        )}
      </div>

      <p style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.55, margin: "0 0 10px 0" }}>
        {q.text}
      </p>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => handle("approved")}
          disabled={loading}
          style={{
            background: "#16a34a22",
            border: "1px solid #16a34a88",
            borderRadius: 6,
            padding: "5px 16px",
            color: "#4ade80",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 12,
            fontWeight: 700,
            opacity: loading ? 0.6 : 1,
          }}
        >
          Onayla
        </button>
        <button
          onClick={() => handle("rejected")}
          disabled={loading}
          style={{
            background: "#dc262622",
            border: "1px solid #dc262688",
            borderRadius: 6,
            padding: "5px 16px",
            color: "#f87171",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 12,
            fontWeight: 700,
            opacity: loading ? 0.6 : 1,
          }}
        >
          Reddet
        </button>
      </div>
    </div>
  );
}

// ── Ana bileşen ──────────────────────────────────────────────────────────────

export default function QuestionManagement() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const interviewId = searchParams.get("interview_id") ?? "";

  const [workstream, setWorkstream] = useState<string>("kubernetes");
  const [bankQuestions, setBankQuestions] = useState<WorkstreamQuestion[]>([]);
  const [pendingSuggestions, setPendingSuggestions] = useState<Question[]>([]);
  const [newQuestionText, setNewQuestionText] = useState("");
  const [adding, setAdding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [tabFilter, setTabFilter] = useState<TabFilter>("all");
  // Agent soru önerisi state
  const [agentSuggesting, setAgentSuggesting] = useState(false);
  const [agentSuggestedQuestions, setAgentSuggestedQuestions] = useState<{ text: string; accepted: boolean | null }[]>([]);
  const [showAgentSuggest, setShowAgentSuggest] = useState(false);

  // ── Soru bankası yükle ───────────────────────────────────────────────────
  const loadBankQuestions = () => {
    setLoading(true);
    listWorkstreamQuestions(workstream)
      .then(setBankQuestions)
      .catch(() => setBankQuestions([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadBankQuestions();
  }, [workstream]);

  // ── Agent önerileri yükle ────────────────────────────────────────────────
  const loadSuggestions = () => {
    if (!interviewId) {
      setPendingSuggestions([]);
      return;
    }
    setSuggestionsLoading(true);
    listQuestions(interviewId)
      .then((questions) => {
        const pending = questions.filter(
          (q) =>
            q.agent_suggested &&
            (q.approval_status === "pending" || !q.approval_status)
        );
        setPendingSuggestions(pending);
      })
      .catch(() => setPendingSuggestions([]))
      .finally(() => setSuggestionsLoading(false));
  };

  useEffect(() => {
    loadSuggestions();
  }, [interviewId]);

  // ── Yeni soru ekle ───────────────────────────────────────────────────────
  const handleAddQuestion = async () => {
    const text = newQuestionText.trim();
    if (!text) return;

    setAdding(true);
    try {
      await createWorkstreamQuestion(workstream, text, bankQuestions.length + 1);
      setNewQuestionText("");
      loadBankQuestions();
    } catch {
      alert("Soru eklenirken hata oluştu.");
    } finally {
      setAdding(false);
    }
  };

  // ── Agent soru önerisi ───────────────────────────────────────────────────
  const handleAgentSuggest = async () => {
    setAgentSuggesting(true);
    setShowAgentSuggest(true);
    setAgentSuggestedQuestions([]);
    try {
      const suggested = await suggestBankQuestions(workstream, 5);
      setAgentSuggestedQuestions(suggested.map(s => ({ text: s.text, accepted: null })));
    } catch {
      setAgentSuggestedQuestions([]);
    } finally {
      setAgentSuggesting(false);
    }
  };

  const handleAcceptSuggestion = async (index: number) => {
    const item = agentSuggestedQuestions[index];
    if (!item) return;
    try {
      await createWorkstreamQuestion(workstream, item.text, bankQuestions.length + index + 1);
      setAgentSuggestedQuestions(prev => prev.map((q, i) => i === index ? { ...q, accepted: true } : q));
      loadBankQuestions();
    } catch { /* ignore */ }
  };

  const handleRejectSuggestion = (index: number) => {
    setAgentSuggestedQuestions(prev => prev.map((q, i) => i === index ? { ...q, accepted: false } : q));
  };

  // ── Sil (API henüz yok) ──────────────────────────────────────────────────
  const handleDelete = (_id: string) => {
    alert("Bu özellik yakında geliyor");
  };

  // ── Onay/Red sonrası listeden kaldır ────────────────────────────────────
  const handleSuggestionAction = (id: string, _action: "approved" | "rejected") => {
    setPendingSuggestions((prev) => prev.filter((q) => q.id !== id));
  };

  // ── Tab filtresi ─────────────────────────────────────────────────────────
  // NOT: WorkstreamQuestion tipinde agent_suggested yok; bankQuestions hep "manuel"
  const visibleBankQuestions =
    tabFilter === "agent"
      ? [] // soru bankasında agent soruları yok
      : bankQuestions; // "all" ve "manual" aynı görünüm

  const tabCounts: Record<TabFilter, number> = {
    all: bankQuestions.length,
    manual: bankQuestions.length,
    agent: 0,
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ display: "flex", height: "calc(100vh - 110px)", color: "#e2e8f0", gap: 0 }}>

      {/* ── Sol: Workstream tab listesi ─────────────────────────────────── */}
      <div style={{
        width: 210, flexShrink: 0, background: "#0f1117",
        borderRight: "1px solid #1e293b", overflowY: "auto", padding: "16px 8px",
      }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", padding: "0 8px 10px" }}>
          Konu Başlıkları
        </p>
        {WORKSTREAMS.map((ws) => {
          const isActive = ws.id === workstream;
          return (
            <button
              key={ws.id}
              onClick={() => setWorkstream(ws.id)}
              style={{
                width: "100%", textAlign: "left", padding: "9px 12px",
                borderRadius: 7, border: "none", marginBottom: 3,
                background: isActive ? "#1e3a5f" : "transparent",
                borderLeft: `3px solid ${isActive ? "#3b82f6" : "transparent"}`,
                color: isActive ? "#e2e8f0" : "#94a3b8",
                cursor: "pointer", fontSize: 13,
                display: "flex", alignItems: "center", gap: 8,
                transition: "all 0.12s",
              }}
            >
              <span style={{ fontSize: 15 }}>{ws.icon}</span>
              <span>{ws.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── Sağ: İki panel (Soru Bankası + Agent Önerileri) ─────────────── */}
      <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
        <div style={{ marginBottom: 16 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 2px 0" }}>
            {WORKSTREAMS.find(w => w.id === workstream)?.label ?? workstream}
          </h1>
          <p style={{ color: "#64748b", fontSize: 12, margin: 0 }}>
            Soru bankası ve agent önerileri
            {assessmentId && <span style={{ color: "#60a5fa" }}> — {assessmentId.slice(0, 8)}…</span>}
          </p>
        </div>

      {/* İki sütun layout */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
          alignItems: "start",
        }}
      >
        {/* ── SOL: Soru Bankası ─────────────────────────────────────────── */}
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: 20,
          }}
        >
          {/* Panel başlık */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
              Soru Bankası
            </h2>
            <span
              style={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 6,
                padding: "2px 10px",
                fontSize: 12,
                color: "#60a5fa",
                fontWeight: 700,
              }}
            >
              {bankQuestions.length} soru
            </span>
          </div>

          {/* Tab filtresi */}
          <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
            <TabButton
              label="Tümü"
              count={tabCounts.all}
              active={tabFilter === "all"}
              onClick={() => setTabFilter("all")}
            />
            <TabButton
              label="Manuel"
              count={tabCounts.manual}
              active={tabFilter === "manual"}
              onClick={() => setTabFilter("manual")}
            />
            <TabButton
              label="Agent Önerisi"
              count={tabCounts.agent}
              active={tabFilter === "agent"}
              onClick={() => setTabFilter("agent")}
            />
          </div>

          {/* Soru listesi */}
          <div style={{ minHeight: 120 }}>
            {loading ? (
              <p
                style={{ textAlign: "center", color: "#64748b", padding: "30px 0" }}
              >
                Yükleniyor…
              </p>
            ) : visibleBankQuestions.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "30px 0",
                  color: "#64748b",
                }}
              >
                <p style={{ fontSize: 28, marginBottom: 8 }}>📋</p>
                <p style={{ fontSize: 13 }}>
                  {tabFilter === "agent"
                    ? "Soru bankasında agent sorusu bulunmuyor."
                    : "Bu workstream için henüz soru eklenmemiş."}
                </p>
              </div>
            ) : (
              <div style={{ maxHeight: 420, overflowY: "auto" }}>
                {visibleBankQuestions.map((q, i) => (
                  <BankQuestionCard
                    key={q.id}
                    q={q}
                    index={i}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Yeni soru ekleme alanı */}
          <div
            style={{
              borderTop: "1px solid #334155",
              marginTop: 16,
              paddingTop: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8", margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Yeni Soru Ekle
              </p>
              <button
                onClick={handleAgentSuggest}
                disabled={agentSuggesting}
                style={{
                  background: agentSuggesting ? "#1e293b" : "#7c3aed22",
                  border: "1px solid #7c3aed88",
                  borderRadius: 6,
                  padding: "4px 12px",
                  color: agentSuggesting ? "#64748b" : "#a78bfa",
                  cursor: agentSuggesting ? "not-allowed" : "pointer",
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                {agentSuggesting ? "⏳ Agent düşünüyor…" : "✨ Agent Önersin"}
              </button>
            </div>

            {/* Agent önerileri listesi */}
            {showAgentSuggest && agentSuggestedQuestions.length > 0 && (
              <div style={{ background: "#0f172a", border: "1px solid #7c3aed44", borderRadius: 8, padding: 12, marginBottom: 12 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#a78bfa", textTransform: "uppercase", marginBottom: 8, letterSpacing: "0.05em" }}>
                  Agent Önerileri ({agentSuggestedQuestions.filter(q => q.accepted === null).length} bekliyor)
                </p>
                {agentSuggestedQuestions.map((item, i) => (
                  <div key={i} style={{
                    background: item.accepted === true ? "#16a34a11" : item.accepted === false ? "#ef444411" : "#1e293b",
                    border: `1px solid ${item.accepted === true ? "#16a34a44" : item.accepted === false ? "#ef444444" : "#334155"}`,
                    borderRadius: 6, padding: "8px 10px", marginBottom: 6,
                    display: "flex", alignItems: "flex-start", gap: 10,
                  }}>
                    <p style={{ flex: 1, fontSize: 12, color: item.accepted !== null ? "#64748b" : "#e2e8f0", margin: 0, lineHeight: 1.5 }}>
                      {item.text}
                    </p>
                    {item.accepted === null ? (
                      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                        <button onClick={() => handleAcceptSuggestion(i)}
                          style={{ padding: "3px 10px", borderRadius: 5, border: "1px solid #16a34a88", background: "#16a34a22", color: "#4ade80", cursor: "pointer", fontSize: 11, fontWeight: 600 }}>
                          Ekle
                        </button>
                        <button onClick={() => handleRejectSuggestion(i)}
                          style={{ padding: "3px 10px", borderRadius: 5, border: "1px solid #334155", background: "transparent", color: "#94a3b8", cursor: "pointer", fontSize: 11 }}>
                          Geç
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: 11, color: item.accepted ? "#22c55e" : "#ef4444", flexShrink: 0 }}>
                        {item.accepted ? "✓ Eklendi" : "✗ Geçildi"}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
            <textarea
              value={newQuestionText}
              onChange={(e) => setNewQuestionText(e.target.value)}
              placeholder="Soru metnini buraya yazın…"
              rows={3}
              style={{
                width: "100%",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "8px 12px",
                color: "#e2e8f0",
                fontSize: 13,
                outline: "none",
                resize: "vertical",
                fontFamily: "inherit",
                lineHeight: 1.5,
                boxSizing: "border-box",
              }}
              onFocus={(e) =>
                (e.currentTarget.style.borderColor = "#3b82f6")
              }
              onBlur={(e) =>
                (e.currentTarget.style.borderColor = "#334155")
              }
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  handleAddQuestion();
                }
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: 8,
              }}
            >
              <span style={{ fontSize: 11, color: "#475569" }}>
                Ctrl+Enter ile hızlı ekle
              </span>
              <button
                onClick={handleAddQuestion}
                disabled={adding || !newQuestionText.trim()}
                style={{
                  background:
                    adding || !newQuestionText.trim() ? "#1e293b" : "#3b82f6",
                  border: "1px solid #334155",
                  borderRadius: 7,
                  padding: "6px 18px",
                  color:
                    adding || !newQuestionText.trim() ? "#64748b" : "#fff",
                  cursor:
                    adding || !newQuestionText.trim()
                      ? "not-allowed"
                      : "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                  transition: "background 0.15s",
                }}
              >
                {adding ? "Ekleniyor…" : "+ Ekle"}
              </button>
            </div>
          </div>
        </div>

        {/* ── SAĞ: Agent Önerileri ──────────────────────────────────────── */}
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: 20,
          }}
        >
          {/* Panel başlık */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
              Agent Önerileri
            </h2>
            {interviewId && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    background: "#eab30822",
                    border: "1px solid #eab30866",
                    borderRadius: 6,
                    padding: "2px 10px",
                    fontSize: 12,
                    color: "#eab308",
                    fontWeight: 700,
                  }}
                >
                  {pendingSuggestions.length} bekliyor
                </span>
                <button
                  onClick={loadSuggestions}
                  disabled={suggestionsLoading}
                  style={{
                    background: "transparent",
                    border: "1px solid #334155",
                    borderRadius: 6,
                    padding: "3px 10px",
                    color: "#94a3b8",
                    cursor: "pointer",
                    fontSize: 11,
                  }}
                >
                  Yenile
                </button>
              </div>
            )}
          </div>

          {/* interviewId yoksa bilgi mesajı */}
          {!interviewId ? (
            <div
              style={{
                background: "#0f172a",
                border: "1px dashed #334155",
                borderRadius: 10,
                padding: "40px 20px",
                textAlign: "center",
                color: "#64748b",
              }}
            >
              <p style={{ fontSize: 32, marginBottom: 12 }}>💬</p>
              <p style={{ fontSize: 14, marginBottom: 6, color: "#94a3b8" }}>
                Interview ID belirtilmedi
              </p>
              <p style={{ fontSize: 12 }}>
                Agent önerilerini görmek için URL'e{" "}
                <code
                  style={{
                    background: "#1e293b",
                    padding: "1px 6px",
                    borderRadius: 3,
                    color: "#60a5fa",
                  }}
                >
                  interview_id
                </code>{" "}
                parametresi ekleyin.
              </p>
            </div>
          ) : suggestionsLoading ? (
            <p
              style={{ textAlign: "center", color: "#64748b", padding: "40px 0" }}
            >
              Yükleniyor…
            </p>
          ) : pendingSuggestions.length === 0 ? (
            <div
              style={{
                background: "#0f172a",
                border: "1px dashed #334155",
                borderRadius: 10,
                padding: "40px 20px",
                textAlign: "center",
                color: "#64748b",
              }}
            >
              <p style={{ fontSize: 32, marginBottom: 12 }}>✅</p>
              <p style={{ fontSize: 14, color: "#94a3b8" }}>
                Bekleyen agent önerisi yok.
              </p>
              <p style={{ fontSize: 12, marginTop: 4 }}>
                Tüm öneriler incelenmiş veya henüz öneri oluşturulmamış.
              </p>
            </div>
          ) : (
            <div style={{ maxHeight: 560, overflowY: "auto" }}>
              {pendingSuggestions.map((q) => (
                <SuggestionCard
                  key={q.id}
                  q={q}
                  onAction={handleSuggestionAction}
                />
              ))}
            </div>
          )}

          {/* interviewId bilgi satırı */}
          {interviewId && (
            <div
              style={{
                borderTop: "1px solid #1e293b",
                marginTop: 14,
                paddingTop: 10,
              }}
            >
              <p style={{ fontSize: 11, color: "#475569", margin: 0 }}>
                Interview:{" "}
                <code
                  style={{
                    background: "#0f172a",
                    padding: "1px 5px",
                    borderRadius: 3,
                    color: "#94a3b8",
                  }}
                >
                  {interviewId.slice(0, 8)}…
                </code>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
  );
}
