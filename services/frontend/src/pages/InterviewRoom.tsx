// S10-FA-001 v2 / S11-FA-002: Interview Room — evaluation + LLM follow-up
import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  WORKSTREAMS,
  Interview, Question, Task, AgentStatusItem, AnswerWithEval,
  listInterviews, createInterview,
  listQuestions, addQuestion, addAnswerFull, listAnswers, evaluateAnswer,
  listTasks, createTask,
  listWorkstreamQuestions,
  getAgentStatus, suggestFollowup, approveQuestion,
} from "../api";

const STATUS_COLOR: Record<string, string> = {
  in_progress: "#3b82f6",
  completed:   "#22c55e",
  pending:     "#64748b",
  skipped:     "#94a3b8",
};

// ─── Agent öneri kartı ────────────────────────────────────────────────────────

function SuggestionCard({ question, onApprove, onReject }: {
  question: Question;
  onApprove: (q: Question) => void;
  onReject: (q: Question) => void;
}) {
  const [busy, setBusy] = useState(false);
  const handle = async (action: "approved" | "rejected") => {
    setBusy(true);
    try {
      await approveQuestion(question.id, action);
      if (action === "approved") onApprove(question);
      else onReject(question);
    } catch { /* ignore */ } finally { setBusy(false); }
  };
  return (
    <div style={{ border: "1px solid #ca8a04", borderLeft: "3px solid #eab308", borderRadius: 8, padding: "12px 16px", marginBottom: 8, background: "#1c1a0e" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 10, fontWeight: 700, background: "#713f12", color: "#fde68a", borderRadius: 4, padding: "2px 8px", textTransform: "uppercase" }}>
          Agent Önerisi
        </span>
      </div>
      <p style={{ color: "#e2e8f0", fontSize: 13, margin: "0 0 10px 0", lineHeight: 1.5 }}>{question.text}</p>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => handle("approved")} disabled={busy}
          style={{ padding: "5px 12px", borderRadius: 6, border: "none", background: "#16a34a", color: "#fff", cursor: busy ? "not-allowed" : "pointer", fontSize: 12, fontWeight: 600 }}>
          Onayla
        </button>
        <button onClick={() => handle("rejected")} disabled={busy}
          style={{ padding: "5px 12px", borderRadius: 6, border: "1px solid #475569", background: "transparent", color: "#94a3b8", cursor: busy ? "not-allowed" : "pointer", fontSize: 12 }}>
          Reddet
        </button>
      </div>
    </div>
  );
}

// ─── Soru + cevap kartı ───────────────────────────────────────────────────────

function QuestionCard({ question, index }: { question: Question; index: number }) {
  const [text, setText] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState<AnswerWithEval[]>([]);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    listAnswers(question.id).then(setAnswers).catch(() => {});
  }, [question.id]);

  const save = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      const ans = await addAnswerFull(question.id, text.trim());
      setSaved(true);
      setText("");
      // Auto-evaluate in background
      setEvaluating(true);
      evaluateAnswer(ans.id)
        .then(ev => setAnswers(prev => prev.map(a => a.id === ans.id ? { ...a, evaluation: ev.evaluation } : a)))
        .catch(() => {})
        .finally(() => setEvaluating(false));
      setAnswers(prev => [...prev, ans]);
      setSaved(false);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  return (
    <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "16px", marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 10 }}>
        <span style={{ background: "#3b82f622", color: "#60a5fa", border: "1px solid #3b82f644", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 700, flexShrink: 0 }}>
          S{index + 1}
        </span>
        <p style={{ fontSize: 13, color: "#e2e8f0", margin: 0, lineHeight: 1.6, fontWeight: 500 }}>{question.text}</p>
      </div>

      {/* Mevcut yanıtlar + değerlendirme */}
      {answers.map(ans => (
        <div key={ans.id} style={{ marginBottom: 10 }}>
          <div style={{ background: "#0f1117", borderRadius: 6, padding: "8px 12px", marginBottom: 6 }}>
            <p style={{ fontSize: 11, color: "#475569", margin: "0 0 4px 0", textTransform: "uppercase", fontWeight: 700 }}>Yanıt</p>
            <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.6 }}>{ans.text}</p>
          </div>
          {ans.evaluation ? (
            <div style={{ background: "#0a1a2f", border: "1px solid #1e3a5f", borderLeft: "3px solid #3b82f6", borderRadius: 6, padding: "8px 12px" }}>
              <p style={{ fontSize: 11, color: "#60a5fa", margin: "0 0 4px 0", textTransform: "uppercase", fontWeight: 700 }}>Agent Değerlendirmesi</p>
              <p style={{ fontSize: 12, color: "#94a3b8", margin: 0, lineHeight: 1.6 }}>{ans.evaluation}</p>
            </div>
          ) : evaluating ? (
            <div style={{ fontSize: 11, color: "#475569", padding: "6px 12px", fontStyle: "italic" }}>
              ⏳ Agent değerlendiriyor…
            </div>
          ) : null}
        </div>
      ))}

      {/* Yeni yanıt girişi */}
      <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginTop: answers.length > 0 ? 8 : 0 }}>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Cevabınızı buraya yazın…"
          rows={3}
          style={{ flex: 1, background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px", color: "#e2e8f0", fontSize: 13, resize: "vertical", outline: "none" }}
          onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) save(); }}
        />
        <button onClick={save} disabled={saving || !text.trim()}
          style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: text.trim() ? "#3b82f6" : "#334155", color: text.trim() ? "#fff" : "#64748b", cursor: text.trim() ? "pointer" : "not-allowed", fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
          {saving ? "…" : "Kaydet"}
        </button>
      </div>
    </div>
  );
}

// ─── Ana sayfa ────────────────────────────────────────────────────────────────

export default function InterviewRoom() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";

  const [activeWs,           setActiveWs]           = useState<string>(WORKSTREAMS[0].id);
  const [task,               setTask]               = useState<Task | null>(null);
  const [interview,          setInterview]          = useState<Interview | null>(null);
  const [questions,          setQuestions]          = useState<Question[]>([]);
  const [pendingSuggestions, setPendingSuggestions] = useState<Question[]>([]);
  const [agentStatus,        setAgentStatus]        = useState<AgentStatusItem[]>([]);
  const [loading,            setLoading]            = useState(false);
  const [followupBusy,       setFollowupBusy]       = useState(false);

  // ── Workstream seçilince: task → interview → sorular ──────────────────────
  useEffect(() => {
    if (!assessmentId) return;
    (async () => {
      setLoading(true);
      setTask(null); setInterview(null); setQuestions([]); setPendingSuggestions([]);
      try {
        // 1. Bu workstream'e ait task bul ya da oluştur
        const tasks = await listTasks(assessmentId);
        let t = tasks.find(x => x.workstream === activeWs) ?? null;
        if (!t) {
          t = await createTask({
            assessment_id: assessmentId,
            agent_type: `${activeWs}_agent`,
            workstream: activeWs,
            scope: `${activeWs} assessment`,
            status: "in_progress",
          });
        }
        setTask(t);

        // 2. Interview bul ya da oluştur
        const existing = await listInterviews(t.id);
        const iv = existing.length > 0
          ? existing[0]
          : await createInterview({ task_id: t.id, interviewee_name: "Consultant" });
        setInterview(iv);

        // 3. Soruları yükle — yoksa question bank'ten doldur
        let qs = await listQuestions(iv.id);
        if (qs.length === 0) {
          const bank = await listWorkstreamQuestions(activeWs);
          for (const bq of bank) {
            await addQuestion(iv.id, bq.text, bq.order);
          }
          qs = await listQuestions(iv.id);
        }

        const pending = qs.filter(q => q.agent_suggested && q.approval_status === "pending");
        const normal  = qs.filter(q => !(q.agent_suggested && q.approval_status === "pending"));
        setQuestions(normal);
        setPendingSuggestions(pending);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, [assessmentId, activeWs]);

  // ── Agent status polling ────────────────────────────────────────────────────
  const fetchAgentStatus = useCallback(async () => {
    if (!assessmentId) return;
    try { setAgentStatus(await getAgentStatus(assessmentId)); } catch { /* silent */ }
  }, [assessmentId]);

  useEffect(() => {
    if (!assessmentId) return;
    fetchAgentStatus();
    const id = setInterval(fetchAgentStatus, 10_000);
    return () => clearInterval(id);
  }, [assessmentId, fetchAgentStatus]);

  // ── Follow-up öneri ────────────────────────────────────────────────────────
  const handleSuggestFollowup = async () => {
    if (!interview) return;
    setFollowupBusy(true);
    try {
      const newQ = await suggestFollowup(interview.id);
      setPendingSuggestions(p => [...p, newQ]);
    } catch { /* ignore */ } finally { setFollowupBusy(false); }
  };

  const handleApprove = (q: Question) => {
    setPendingSuggestions(p => p.filter(x => x.id !== q.id));
    setQuestions(prev => [...prev, { ...q, approval_status: "approved" }]);
  };
  const handleReject = (q: Question) => {
    setPendingSuggestions(p => p.filter(x => x.id !== q.id));
  };

  // ── Boş state ──────────────────────────────────────────────────────────────
  if (!assessmentId) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh" }}>
        <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 12, padding: 32, textAlign: "center" }}>
          <p style={{ fontSize: 32, marginBottom: 12 }}>🎙</p>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>Genel Bakış'tan bir assessment seçin.</p>
        </div>
      </div>
    );
  }

  const wsLabel = WORKSTREAMS.find(w => w.id === activeWs)?.label ?? activeWs;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 110px)", gap: 0 }}>

      {/* Ana içerik: sol panel + sağ Q&A */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", gap: 0 }}>

        {/* ── Sol panel: workstream tab listesi ── */}
        <div style={{
          width: 220, flexShrink: 0, background: "#0f1117",
          borderRight: "1px solid #1e293b", overflowY: "auto", padding: "12px 8px",
        }}>
          <p style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", padding: "0 8px 8px" }}>
            Workstream
          </p>
          {WORKSTREAMS.map(ws => {
            const isActive = ws.id === activeWs;
            const taskForWs = agentStatus.find(s => s.workstream === ws.id);
            const statusColor = taskForWs ? (STATUS_COLOR[taskForWs.status] ?? "#64748b") : "#334155";
            return (
              <button
                key={ws.id}
                onClick={() => setActiveWs(ws.id)}
                style={{
                  width: "100%", textAlign: "left", padding: "9px 12px",
                  borderRadius: 7, border: "none", marginBottom: 3,
                  background: isActive ? "#1e3a5f" : "transparent",
                  borderLeft: isActive ? "3px solid #3b82f6" : "3px solid transparent",
                  color: isActive ? "#e2e8f0" : "#94a3b8",
                  cursor: "pointer", fontSize: 13, display: "flex", alignItems: "center", gap: 8,
                  transition: "all 0.12s",
                }}
              >
                <span style={{ fontSize: 15 }}>{ws.icon}</span>
                <span style={{ flex: 1 }}>{ws.label}</span>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor, flexShrink: 0 }} />
              </button>
            );
          })}
        </div>

        {/* ── Sağ: Q&A alanı ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
          {/* Başlık */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 2 }}>{wsLabel}</h2>
              {interview && (
                <p style={{ fontSize: 12, color: "#64748b" }}>
                  Interview: {interview.id.slice(0, 8)}… — {interview.status}
                </p>
              )}
            </div>
            <button
              onClick={handleSuggestFollowup}
              disabled={followupBusy || !interview}
              style={{
                padding: "7px 14px", borderRadius: 7, border: "1px solid #334155",
                background: "transparent", color: "#94a3b8",
                cursor: interview && !followupBusy ? "pointer" : "not-allowed",
                fontSize: 12,
              }}
            >
              {followupBusy ? "⏳ Öneriyor…" : "+ Follow-up Öner"}
            </button>
          </div>

          {/* Agent önerileri */}
          {pendingSuggestions.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: "#eab308", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                Bekleyen Agent Önerileri ({pendingSuggestions.length})
              </p>
              {pendingSuggestions.map(q => (
                <SuggestionCard key={q.id} question={q} onApprove={handleApprove} onReject={handleReject} />
              ))}
            </div>
          )}

          {/* Sorular */}
          {loading ? (
            <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
              <p style={{ fontSize: 24, marginBottom: 8 }}>⏳</p>
              <p>Sorular yükleniyor…</p>
            </div>
          ) : questions.length === 0 ? (
            <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
              <p style={{ fontSize: 32, marginBottom: 8 }}>📋</p>
              <p>Bu workstream için soru bankasında soru bulunamadı.</p>
              <p style={{ fontSize: 12, marginTop: 6 }}>Sorular ekranından soru ekleyebilirsiniz.</p>
            </div>
          ) : (
            <>
              <p style={{ fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>
                Sorular ({questions.length})
              </p>
              {questions.map((q, i) => (
                <QuestionCard key={q.id} question={q} index={i} />
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── Alt bar: agent status ── */}
      {agentStatus.length > 0 && (
        <div style={{
          background: "#0f1117", borderTop: "1px solid #1e293b",
          padding: "8px 20px", display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap",
        }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", marginRight: 8 }}>Ajan Durumu</span>
          {agentStatus.map(s => {
            const color = STATUS_COLOR[s.status] ?? "#64748b";
            return (
              <span key={s.task_id} style={{
                display: "flex", alignItems: "center", gap: 4,
                background: "#1e293b", border: `1px solid ${color}44`,
                borderRadius: 5, padding: "3px 9px", fontSize: 11, color: "#94a3b8",
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
                {s.workstream}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
