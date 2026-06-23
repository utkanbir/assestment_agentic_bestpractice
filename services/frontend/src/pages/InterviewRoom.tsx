// S10-FA-001 v2 / S11-FA-002 / S21 / S22: Interview Room
import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  WORKSTREAMS,
  Interview, Question, Task, AgentStatusItem, AnswerWithEval, LayerTouch, Consultant,
  listInterviews, createInterview,
  listQuestions, addQuestion, addAnswerFull, listAnswers, evaluateAnswer,
  addAnswerConsultantComment, updateAnswerConsultantComment, consultantReviewAnswerComment,
  listTasks, createTask,
  listWorkstreamQuestions,
  WorkstreamQuestion,
  getAgentStatus, suggestFollowup, approveQuestion,
  getSimulationStatus, stopSimulation, finalizeSimulation,
  SimulationProgress,
  listAllConsultants, createEvidence, createFinding, createWorkstreamQuestion,
  generateConsultantSynthesis,
} from "../api";
import { Link } from "react-router-dom";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";

const STATUS_COLOR: Record<string, string> = {
  in_progress: "#3b82f6",
  completed:   "#22c55e",
  pending:     "#64748b",
  skipped:     "#94a3b8",
};

// ─── Agent öneri kartı ────────────────────────────────────────────────────────

function SuggestionCard({ question, onApprove, onReject, workstream }: {
  question: Question;
  onApprove: (q: Question, addToBank: boolean) => void;
  onReject: (q: Question) => void;
  workstream: string;
}) {
  const [busy, setBusy] = useState(false);
  const [addToBank, setAddToBank] = useState(false);
  const handle = async (action: "approved" | "rejected") => {
    setBusy(true);
    try {
      await approveQuestion(question.id, action);
      if (action === "approved") {
        if (addToBank) {
          try {
            await createWorkstreamQuestion(workstream, question.text, question.order + 100);
          } catch { /* ignore */ }
        }
        onApprove(question, addToBank);
      } else onReject(question);
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
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94a3b8", marginBottom: 10, cursor: "pointer" }}>
        <input type="checkbox" checked={addToBank} onChange={e => setAddToBank(e.target.checked)} />
        Bankaya da ekle
      </label>
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

// ─── Danışman yorum satırı ───────────────────────────────────────────────────

type CommentEdit = { id?: string; consultantId: string; comment: string; feedback?: string | null };

function ConsultantCommentRows({
  answerId,
  comments,
  consultants,
  readOnly,
  onChange,
}: {
  answerId: string;
  comments: CommentEdit[];
  consultants: Consultant[];
  readOnly: boolean;
  onChange: (next: CommentEdit[]) => void;
}) {
  const consultantName = (id: string | null | undefined) => {
    if (!id) return null;
    const c = consultants.find(x => x.id === id);
    return c ? `${c.first_name} ${c.last_name}` : id.slice(0, 8);
  };
  const [busyId, setBusyId] = useState<string | null>(null);
  const [reviewingKey, setReviewingKey] = useState<string | null>(null);

  const rowKey = (row: CommentEdit, idx: number) => row.id ?? `new-${idx}`;

  const handleSave = async (row: CommentEdit, idx: number) => {
    if (!row.consultantId) return;
    const key = rowKey(row, idx);
    setBusyId(key);
    try {
      if (row.id) {
        const updated = await updateAnswerConsultantComment(answerId, row.id, {
          consultant_id: row.consultantId,
          comment: row.comment.trim() || null,
        });
        const next = [...comments];
        next[idx] = {
          id: updated.id,
          consultantId: updated.consultant_id,
          comment: updated.comment ?? "",
          feedback: updated.consultant_review_feedback,
        };
        onChange(next);
      } else {
        const created = await addAnswerConsultantComment(answerId, {
          consultant_id: row.consultantId,
          comment: row.comment.trim() || null,
        });
        const next = [...comments];
        next[idx] = {
          id: created.id,
          consultantId: created.consultant_id,
          comment: created.comment ?? "",
          feedback: created.consultant_review_feedback,
        };
        onChange(next);
      }
    } catch { /* ignore */ } finally { setBusyId(null); }
  };

  const handleAiKontrol = async (row: CommentEdit, idx: number) => {
    if (!row.id) return;
    const key = rowKey(row, idx);
    setReviewingKey(key);
    try {
      const result = await consultantReviewAnswerComment(answerId, row.id, {
        consultant_comment: row.comment.trim() || undefined,
      });
      const next = [...comments];
      next[idx] = { ...next[idx], feedback: result.feedback };
      onChange(next);
    } catch { /* ignore */ } finally { setReviewingKey(null); }
  };

  if (readOnly) {
    return (
      <>
        {comments.filter(c => c.comment.trim() || c.consultantId).map((row, idx) => (
          <div key={row.id ?? idx} style={{ background: "#0a1f14", border: "1px solid #14532d", borderLeft: "3px solid #22c55e", borderRadius: 6, padding: "8px 12px", marginBottom: 6 }}>
            <p style={{ fontSize: 11, color: "#4ade80", margin: "0 0 4px 0", textTransform: "uppercase", fontWeight: 700 }}>
              Danışman Yorumu{row.consultantId ? ` — ${consultantName(row.consultantId)}` : ""}
            </p>
            <p style={{ fontSize: 12, color: "#94a3b8", margin: 0, lineHeight: 1.6 }}>{row.comment}</p>
            {row.feedback ? (
              <p data-testid="ai-kontrol-feedback" style={{ fontSize: 11, color: "#c084fc", margin: "6px 0 0", lineHeight: 1.5 }}>{row.feedback}</p>
            ) : null}
          </div>
        ))}
      </>
    );
  }

  return (
    <div style={{ marginBottom: 8 }}>
      <p style={{ fontSize: 11, color: "#4ade80", margin: "0 0 6px 0", textTransform: "uppercase", fontWeight: 700 }}>Danışman Yorumları</p>
      {comments.map((row, idx) => {
        const key = rowKey(row, idx);
        return (
          <div key={key} data-testid={row.id ? `consultant-comment-${row.id.slice(0, 8)}` : "consultant-comment-new"} style={{ marginBottom: 10, padding: "8px 10px", background: "#0f1117", borderRadius: 6, border: "1px solid #334155" }}>
            {consultants.length > 0 ? (
              <select
                data-testid="consultant-select"
                value={row.consultantId}
                onChange={e => {
                  const next = [...comments];
                  next[idx] = { ...next[idx], consultantId: e.target.value };
                  onChange(next);
                }}
                style={{ width: "100%", background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "6px 8px", color: "#e2e8f0", fontSize: 12, marginBottom: 6 }}
              >
                <option value="">Danışman seç</option>
                {consultants.map(c => (
                  <option key={c.id} value={c.id}>{c.first_name} {c.last_name}{c.role ? ` — ${c.role}` : ""}</option>
                ))}
              </select>
            ) : (
              <Link to="/danisman" data-testid="add-consultant-link" style={{ fontSize: 12, color: "#60a5fa", display: "block", marginBottom: 6 }}>
                Danışman kaydı oluştur →
              </Link>
            )}
            <textarea
              data-testid="consultant-comment-field"
              value={row.comment}
              onChange={e => {
                const next = [...comments];
                next[idx] = { ...next[idx], comment: e.target.value };
                onChange(next);
              }}
              placeholder="Danışman yorumu"
              rows={2}
              style={{ width: "100%", background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", color: "#e2e8f0", fontSize: 12, marginBottom: 6, boxSizing: "border-box" }}
            />
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={() => handleSave(row, idx)} disabled={busyId !== null || !row.consultantId}
                style={{ padding: "5px 12px", borderRadius: 6, border: "none", background: "#16a34a", color: "#fff", fontSize: 12, cursor: "pointer" }}>
                {busyId === key ? "…" : "Güncelle"}
              </button>
              <button type="button" data-testid="ai-kontrol-btn" onClick={() => handleAiKontrol(row, idx)} disabled={reviewingKey !== null || !row.comment.trim() || !row.id}
                style={{ padding: "5px 12px", borderRadius: 6, border: "1px solid #7e22ce", background: "transparent", color: "#c084fc", fontSize: 12, cursor: "pointer" }}>
                {reviewingKey === key ? "…" : "AI Kontrol"}
              </button>
            </div>
            {row.feedback ? (
              <div data-testid="ai-kontrol-feedback" style={{ background: "#1a1033", border: "1px solid #581c87", borderRadius: 6, padding: "6px 10px", marginTop: 6 }}>
                <p style={{ fontSize: 11, color: "#c084fc", margin: 0, lineHeight: 1.5 }}>{row.feedback}</p>
              </div>
            ) : null}
          </div>
        );
      })}
      <button
        type="button"
        data-testid="add-consultant-comment-btn"
        onClick={() => onChange([...comments, { consultantId: "", comment: "" }])}
        style={{ padding: "5px 12px", borderRadius: 6, border: "1px solid #334155", background: "transparent", color: "#94a3b8", fontSize: 12, cursor: "pointer" }}
      >
        + Danışman yorumu ekle
      </button>
    </div>
  );
}

function LayerTraceMini({ trace, assessmentId, interviewId }: {
  trace: LayerTouch[];
  assessmentId: string;
  interviewId: string;
}) {
  if (trace.length === 0) return null;
  const mimariUrl = `/mimari?assessment_id=${assessmentId}&interview_id=${interviewId}`;
  return (
    <div
      data-testid="layer-trace-mini"
      style={{
        background: "#0a1628", border: "1px solid #1e40af44", borderRadius: 8,
        padding: "10px 14px", marginTop: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: "#60a5fa", textTransform: "uppercase" }}>
          Katman Dokunuşları
        </span>
        <Link to={mimariUrl} style={{ fontSize: 11, color: "#3b82f6" }}>Mimari'de gör →</Link>
      </div>
      {trace.slice(0, 4).map(t => (
        <p key={t.id} style={{ fontSize: 11, color: "#94a3b8", margin: "2px 0" }}>
          <span style={{ color: "#a855f7" }}>{t.layer}</span> · {t.technology} · {t.action}
        </p>
      ))}
    </div>
  );
}

function QuestionCard({ question, index, onLayerTrace, assessmentId, consultants, readOnly = false }: {
  question: Question;
  index: number;
  onLayerTrace?: (trace: LayerTouch[]) => void;
  assessmentId: string;
  consultants: Consultant[];
  readOnly?: boolean;
}) {
  const [text, setText] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState<AnswerWithEval[]>([]);
  const [commentEdits, setCommentEdits] = useState<Record<string, CommentEdit[]>>({});
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);
  const [evalErrors, setEvalErrors] = useState<Record<string, string>>({});

  const commentsFromAnswer = (a: AnswerWithEval): CommentEdit[] => {
    if (a.consultant_comments?.length) {
      return a.consultant_comments.map(c => ({
        id: c.id,
        consultantId: c.consultant_id,
        comment: c.comment ?? "",
        feedback: c.consultant_review_feedback,
      }));
    }
    if (a.consultant_id || a.consultant_comment) {
      return [{
        consultantId: a.consultant_id ?? "",
        comment: a.consultant_comment ?? "",
        feedback: a.consultant_review_feedback,
      }];
    }
    return [];
  };

  useEffect(() => {
    listAnswers(question.id).then((rows) => {
      setAnswers(rows);
      const edits: Record<string, CommentEdit[]> = {};
      rows.forEach((a) => {
        const loaded = commentsFromAnswer(a);
        edits[a.id] = loaded.length ? loaded : [{ consultantId: "", comment: "" }];
      });
      setCommentEdits(edits);
    }).catch(() => {});
  }, [question.id]);

  const save = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      const ans = await addAnswerFull(question.id, text.trim());
      setSaved(true);
      setText("");
      setAnswers(prev => [...prev, ans]);
      setCommentEdits(prev => ({
        ...prev,
        [ans.id]: commentsFromAnswer(ans).length ? commentsFromAnswer(ans) : [{ consultantId: "", comment: "" }],
      }));
      if (ans.layer_trace?.length && onLayerTrace) onLayerTrace(ans.layer_trace);
      setSaved(false);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const handleEvaluate = async (answerId: string) => {
    setEvaluatingId(answerId);
    setEvalErrors(prev => {
      const next = { ...prev };
      delete next[answerId];
      return next;
    });
    try {
      const ev = await evaluateAnswer(answerId);
      setAnswers(prev => prev.map(a => a.id === answerId ? { ...a, evaluation: ev.evaluation, transaction_id: ev.transaction_id ?? a.transaction_id } : a));
      if (ev.layer_trace?.length && onLayerTrace) onLayerTrace(ev.layer_trace);
    } catch (e) {
      const msg = e instanceof DOMException && e.name === "AbortError"
        ? "Değerlendirme zaman aşımına uğradı (90 sn). Tekrar deneyin."
        : "Değerlendirme başarısız oldu. Lütfen tekrar deneyin.";
      setEvalErrors(prev => ({ ...prev, [answerId]: msg }));
    } finally {
      setEvaluatingId(null);
    }
  };

  const handleUpdateComments = (answerId: string, next: CommentEdit[]) => {
    setCommentEdits(prev => ({ ...prev, [answerId]: next }));
    setAnswers(prev => prev.map(a => {
      if (a.id !== answerId) return a;
      const saved = next.filter(r => r.id);
      return {
        ...a,
        consultant_comments: saved.map(r => ({
          id: r.id!,
          answer_id: answerId,
          consultant_id: r.consultantId,
          comment: r.comment,
          consultant_review_feedback: r.feedback ?? null,
          created_at: a.consultant_comments?.find(c => c.id === r.id)?.created_at ?? a.created_at,
        })),
        consultant_id: saved[0]?.consultantId ?? null,
        consultant_comment: saved[0]?.comment ?? null,
        consultant_review_feedback: saved[0]?.feedback ?? null,
      };
    }));
  };

  const boxStyle = { background: "#0f1117", borderRadius: 6, padding: "8px 12px", marginBottom: 6 } as const;
  const labelStyle = { fontSize: 11, color: "#475569", margin: "0 0 4px 0", textTransform: "uppercase" as const, fontWeight: 700 };

  return (
    <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "16px", marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 10 }}>
        <span style={{ background: "#3b82f622", color: "#60a5fa", border: "1px solid #3b82f644", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 700, flexShrink: 0 }}>
          S{index + 1}
        </span>
        <p style={{ fontSize: 13, color: "#e2e8f0", margin: 0, lineHeight: 1.6, fontWeight: 500 }}>{question.text}</p>
      </div>

      {/* Mevcut yanıtlar */}
      {answers.map(ans => {
        const rows = commentEdits[ans.id] ?? commentsFromAnswer(ans);
        return (
        <div key={ans.id} data-testid={`answer-block-${ans.id.slice(0, 8)}`} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #334155" }}>
          <div style={boxStyle}>
            <p style={labelStyle}>Müşteri Yanıtı</p>
            <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.6 }}>{ans.text}</p>
          </div>

          <ConsultantCommentRows
            answerId={ans.id}
            comments={rows}
            consultants={consultants}
            readOnly={readOnly}
            onChange={next => handleUpdateComments(ans.id, next)}
          />

          <div style={{ display: "flex", gap: 10, alignItems: "flex-start", flexWrap: "wrap", marginTop: 8 }}>
            <button type="button" onClick={() => handleEvaluate(ans.id)} disabled={evaluatingId !== null} data-testid="ai-yorum-btn"
              style={{
                padding: "5px 12px", borderRadius: 6,
                border: ans.evaluation ? "1px solid #475569" : "none",
                background: evaluatingId !== null ? "#334155" : ans.evaluation ? "transparent" : "#3b82f6",
                color: evaluatingId !== null ? "#64748b" : ans.evaluation ? "#94a3b8" : "#fff",
                cursor: evaluatingId !== null ? "not-allowed" : "pointer",
                fontSize: 12, fontWeight: ans.evaluation ? 400 : 600,
              }}>
              {evaluatingId === ans.id ? "…" : ans.evaluation ? "Yeniden AI Yorum" : "AI Yorum"}
            </button>
            {ans.evaluation ? (
              <div data-testid="ai-yorum-text" style={{ flex: 1, minWidth: 200, background: "#0a1a2f", border: "1px solid #1e3a5f", borderRadius: 6, padding: "8px 12px" }}>
                <p style={{ fontSize: 11, color: "#60a5fa", margin: "0 0 4px 0", textTransform: "uppercase", fontWeight: 700 }}>AI Yorumu</p>
                <p style={{ fontSize: 12, color: "#94a3b8", margin: 0, lineHeight: 1.6 }}>{ans.evaluation}</p>
              </div>
            ) : null}
          </div>

          {evaluatingId === ans.id ? (
            <div style={{ fontSize: 11, color: "#475569", padding: "6px 0", fontStyle: "italic" }}>⏳ AI yorum üretiliyor…</div>
          ) : null}
          {evalErrors[ans.id] ? (
            <p style={{ fontSize: 11, color: "#f87171", margin: "6px 0 0" }}>{evalErrors[ans.id]}</p>
          ) : null}
          {ans.transaction_id ? (
            <Link to={`/yurutme-plani?assessment_id=${assessmentId}&transaction_id=${ans.transaction_id}`}
              style={{ display: "inline-block", fontSize: 11, color: "#60a5fa", marginTop: 6 }}>
              Plani gor ({ans.transaction_id.slice(0, 8)}...)
            </Link>
          ) : null}
        </div>
      );})}

      {/* Yeni yanıt girişi */}
      {!readOnly && (
      <div style={{ marginTop: answers.length > 0 ? 8 : 0 }}>
        <p style={labelStyle}>Müşteri Yanıtı</p>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Cevabınızı buraya yazın…"
          rows={3}
          style={{ width: "100%", background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px", color: "#e2e8f0", fontSize: 13, resize: "vertical", outline: "none", marginBottom: 10, boxSizing: "border-box" }}
          onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) save(); }}
        />
        <button onClick={save} disabled={saving || !text.trim()}
          style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: text.trim() ? "#3b82f6" : "#334155", color: text.trim() ? "#fff" : "#64748b", cursor: text.trim() ? "pointer" : "not-allowed", fontSize: 12, fontWeight: 600 }}>
          {saving ? "…" : "Kaydet"}
        </button>
      </div>
      )}
    </div>
  );
}

// ─── Bulgu oluştur paneli ───────────────────────────────────────────────────

function FindingPanel({ taskId, interviewId }: { taskId: string; interviewId: string }) {
  const [open, setOpen] = useState(false);
  const [evidence, setEvidence] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const submit = async () => {
    if (!evidence.trim() || !description.trim()) return;
    setBusy(true);
    setMsg("");
    try {
      const ev = await createEvidence({
        source: "interview",
        content: evidence.trim(),
        evidence_type: "interview",
        interview_id: interviewId,
      });
      await createFinding({
        task_id: taskId,
        evidence_id: ev.id,
        description: description.trim(),
        severity: "medium",
        confidence: 0.8,
      });
      setEvidence("");
      setDescription("");
      setMsg("Bulgu oluşturuldu.");
    } catch {
      setMsg("Bulgu oluşturulurken hata.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="finding-panel" style={{ marginBottom: 16, background: "#1e293b", border: "1px solid #334155", borderRadius: 8, overflow: "hidden" }}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        style={{
          width: "100%", textAlign: "left", padding: "10px 14px", border: "none",
          background: "transparent", color: "#e2e8f0", fontSize: 13, fontWeight: 600, cursor: "pointer",
        }}
      >
        Bulgu Oluştur {open ? "▲" : "▼"}
      </button>
      {open && (
        <div style={{ padding: "0 14px 14px", display: "grid", gap: 8 }}>
          <textarea
            value={evidence}
            onChange={e => setEvidence(e.target.value)}
            placeholder="Kanıt metni (evidence)…"
            rows={2}
            style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px", color: "#e2e8f0", fontSize: 12, resize: "vertical" }}
          />
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Bulgu açıklaması…"
            rows={2}
            style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px", color: "#e2e8f0", fontSize: 12, resize: "vertical" }}
          />
          <button
            type="button"
            onClick={submit}
            disabled={busy || !evidence.trim() || !description.trim()}
            style={{ padding: "7px 14px", borderRadius: 6, border: "none", background: "#3b82f6", color: "#fff", fontSize: 12, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer", justifySelf: "start" }}
          >
            {busy ? "…" : "Bulgu Kaydet"}
          </button>
          {msg && <p style={{ fontSize: 11, color: msg.includes("Hata") ? "#f87171" : "#4ade80", margin: 0 }}>{msg}</p>}
        </div>
      )}
    </div>
  );
}

// ─── Ana sayfa ────────────────────────────────────────────────────────────────

export default function InterviewRoom() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const withAssessment = useAssessmentNavLink();
  const { selectedAssessment } = useAssessment();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const watchMode =
    searchParams.get("simulation") === "1"
    || selectedAssessment?.assessment_mode === "simulated";
  const workstreamParam = searchParams.get("workstream");

  const [activeWs,           setActiveWs]           = useState<string>(workstreamParam && WORKSTREAMS.some(w => w.id === workstreamParam) ? workstreamParam : WORKSTREAMS[0].id);
  const [task,               setTask]               = useState<Task | null>(null);
  const [interview,          setInterview]          = useState<Interview | null>(null);
  const [questions,          setQuestions]          = useState<Question[]>([]);
  const [pendingSuggestions, setPendingSuggestions] = useState<Question[]>([]);
  const [agentStatus,        setAgentStatus]        = useState<AgentStatusItem[]>([]);
  const [loading,            setLoading]            = useState(false);
  const [followupBusy,       setFollowupBusy]       = useState(false);
  const [lastLayerTrace,     setLastLayerTrace]     = useState<LayerTouch[]>([]);
  const [simStatus,          setSimStatus]          = useState<string | null>(null);
  const [simProgress,        setSimProgress]        = useState<SimulationProgress | null>(null);
  const [stopBusy,           setStopBusy]           = useState(false);
  const [finalizeBusy,       setFinalizeBusy]       = useState(false);
  const [finalizeDone,       setFinalizeDone]       = useState(false);
  const [missingBank,        setMissingBank]        = useState<WorkstreamQuestion[]>([]);
  const [syncBusy,           setSyncBusy]           = useState(false);
  const [consultants,        setConsultants]        = useState<Consultant[]>([]);
  const [synthesisBusy,      setSynthesisBusy]      = useState(false);
  const [synthesisText,      setSynthesisText]      = useState<string | null>(null);
  const [wsInterviewId,      setWsInterviewId]      = useState<string | null>(null);
  const [simInitialized,     setSimInitialized]     = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const prevSimStatusRef = useRef<string | null>(null);

  useEffect(() => {
    listAllConsultants().then(setConsultants).catch(() => setConsultants([]));
  }, []);

  useEffect(() => {
    if (!watchMode) {
      setSimInitialized(true);
      return;
    }
    setSimInitialized(false);
    if (selectedAssessment?.simulation_status) {
      setSimStatus(selectedAssessment.simulation_status);
    }
    if (selectedAssessment?.simulation_progress) {
      setSimProgress(selectedAssessment.simulation_progress as SimulationProgress);
    }
  }, [assessmentId, watchMode, selectedAssessment?.id, selectedAssessment?.simulation_status, selectedAssessment?.simulation_progress]);

  useEffect(() => {
    if (workstreamParam && WORKSTREAMS.some(w => w.id === workstreamParam)) {
      setActiveWs(workstreamParam);
    }
  }, [workstreamParam]);

  const findMissingBank = useCallback((existing: Question[], bank: WorkstreamQuestion[]) => {
    const texts = new Set(existing.map(q => q.text.trim().toLowerCase()));
    const orders = new Set(existing.map(q => q.order));
    return bank.filter(bq => !texts.has(bq.text.trim().toLowerCase()) && !orders.has(bq.order));
  }, []);

  const refreshQuestions = useCallback(async (ivId: string) => {
    const qs = await listQuestions(ivId);
    const pending = qs.filter(q => q.agent_suggested && q.approval_status === "pending");
    const normal = qs.filter(q => !(q.agent_suggested && q.approval_status === "pending"));
    setQuestions(normal);
    setPendingSuggestions(pending);
  }, []);

  const syncMissingQuestions = useCallback(async (ivId: string, missing: WorkstreamQuestion[]) => {
    if (!missing.length) return;
    setSyncBusy(true);
    try {
      for (const bq of missing) {
        await addQuestion(ivId, bq.text, bq.order);
      }
      await refreshQuestions(ivId);
      setMissingBank([]);
    } catch { /* ignore */ } finally { setSyncBusy(false); }
  }, [refreshQuestions]);

  // ── Workstream seçilince: task → interview → sorular ──────────────────────
  useEffect(() => {
    if (!assessmentId || (watchMode && !simInitialized)) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setTask(null); setInterview(null); setQuestions([]); setPendingSuggestions([]);
      try {
        const tasks = await listTasks(assessmentId);
        if (cancelled) return;
        let t = tasks.find(x => x.workstream === activeWs) ?? null;
        if (!t && !watchMode) {
          t = await createTask({
            assessment_id: assessmentId,
            agent_type: activeWs === "kubernetes" ? "kubernetes" : "workstream",
            workstream: activeWs,
            scope: `${activeWs} assessment`,
            status: "in_progress",
          });
        }
        if (cancelled) return;
        setTask(t);

        if (!t) {
          setLoading(false);
          return;
        }

        const existing = await listInterviews(t.id);
        if (cancelled) return;
        let iv = existing.length > 0 ? existing[0] : null;
        if (!iv && !watchMode) {
          iv = await createInterview({ task_id: t.id, interviewee_name: "Consultant" });
        }
        if (cancelled) return;
        setInterview(iv);

        if (!iv) {
          setLoading(false);
          return;
        }

        let qs = await listQuestions(iv.id);
        if (cancelled) return;
        const bank = await listWorkstreamQuestions(activeWs);
        if (cancelled) return;
        if (qs.length === 0 && !watchMode) {
          for (const bq of bank) {
            if (cancelled) return;
            await addQuestion(iv.id, bq.text, bq.order);
          }
          qs = await listQuestions(iv.id);
        } else if (!watchMode) {
          setMissingBank(findMissingBank(qs, bank));
        }
        if (cancelled) return;

        const pending = qs.filter(q => q.agent_suggested && q.approval_status === "pending");
        const normal  = qs.filter(q => !(q.agent_suggested && q.approval_status === "pending"));
        setQuestions(normal);
        setPendingSuggestions(pending);
      } catch (e) {
        if (!cancelled) console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [assessmentId, activeWs, watchMode, simInitialized, findMissingBank]);

  // ── Watch mode: initial status + default workstream ────────────────────────
  useEffect(() => {
    if (!watchMode || !assessmentId) {
      setSimInitialized(true);
      return;
    }
    let cancelled = false;
    const init = async () => {
      try {
        const st = await getSimulationStatus(assessmentId);
        if (cancelled) return;
        setSimStatus(st.simulation_status);
        setSimProgress(st.simulation_progress);
        const primaryId =
          st.primary_interview_id
          ?? st.simulation_progress?.primary_interview_id
          ?? st.simulation_progress?.current_interview_id
          ?? null;
        if (primaryId) setWsInterviewId(primaryId);

        const terminal = ["completed", "finalized", "stopped", "failed"].includes(st.simulation_status ?? "");
        if (!workstreamParam) {
          if (terminal) {
            const tasks = await listTasks(assessmentId);
            if (cancelled) return;
            if (tasks.length > 0) {
              const lastWs = st.simulation_progress?.current_workstream;
              const pick = lastWs && tasks.some(t => t.workstream === lastWs)
                ? lastWs
                : tasks[0].workstream;
              setActiveWs(pick);
            }
          } else if (st.simulation_progress?.current_workstream) {
            setActiveWs(st.simulation_progress.current_workstream);
          }
        }
      } catch { /* ignore */ } finally {
        if (!cancelled) setSimInitialized(true);
      }
    };
    void init();
    return () => { cancelled = true; };
  }, [watchMode, assessmentId, workstreamParam]);

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

  // ── Simulation watch mode: poll status while running ───────────────────────
  useEffect(() => {
    if (!watchMode || !assessmentId) return;
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const poll = async () => {
      try {
        const st = await getSimulationStatus(assessmentId);
        if (cancelled) return st.simulation_status;
        setSimStatus(st.simulation_status);
        setSimProgress(st.simulation_progress);
        const primaryId =
          st.primary_interview_id
          ?? st.simulation_progress?.primary_interview_id
          ?? st.simulation_progress?.current_interview_id
          ?? null;
        if (primaryId) setWsInterviewId(primaryId);
        if (st.simulation_progress?.current_workstream) {
          setActiveWs(st.simulation_progress.current_workstream);
        }
        return st.simulation_status;
      } catch {
        return null;
      }
    };

    const tick = async () => {
      const status = await poll();
      if (status && status !== "running" && intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    void tick();
    intervalId = setInterval(() => { void tick(); }, 3000);
    return () => {
      cancelled = true;
      if (intervalId) clearInterval(intervalId);
    };
  }, [watchMode, assessmentId]);

  // ── Refresh Q&A when simulation stops or completes ─────────────────────────
  useEffect(() => {
    const prev = prevSimStatusRef.current;
    prevSimStatusRef.current = simStatus;
    const terminal = simStatus && ["stopped", "completed", "failed", "finalized"].includes(simStatus);
    const transitioned = prev === "running" && terminal;
    const mountTerminal = !prev && terminal;
    if (!watchMode || !interview?.id || (!transitioned && !mountTerminal)) return;
    void refreshQuestions(interview.id);
  }, [simStatus, interview?.id, watchMode, refreshQuestions]);

  useEffect(() => {
    const ivId = watchMode
      ? (wsInterviewId ?? simProgress?.primary_interview_id ?? simProgress?.current_interview_id ?? null)
      : null;
    if (!watchMode || !ivId) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/interviews/${ivId}`);
    wsRef.current = ws;
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.event === "simulation.completed") {
          setSimStatus("completed");
        }
      } catch { /* ignore */ }
    };
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [watchMode, wsInterviewId, simProgress?.primary_interview_id, simProgress?.current_interview_id]);

  const handleStopSimulation = async () => {
    if (!assessmentId) return;
    setStopBusy(true);
    try {
      await stopSimulation(assessmentId);
      setSimStatus("stopped");
    } catch { /* ignore */ } finally { setStopBusy(false); }
  };

  const handleFinalizeSimulation = async () => {
    if (!assessmentId) return;
    setFinalizeBusy(true);
    try {
      await finalizeSimulation(assessmentId);
      setFinalizeDone(true);
      setSimStatus((prev) => (prev === "stopped" || prev === "completed" ? "finalized" : prev));
    } catch { /* ignore */ } finally { setFinalizeBusy(false); }
  };

  // ── Follow-up öneri ────────────────────────────────────────────────────────
  const handleSuggestFollowup = async () => {
    if (!interview) return;
    setFollowupBusy(true);
    try {
      const newQ = await suggestFollowup(interview.id);
      setPendingSuggestions(p => [...p, newQ]);
      if (newQ.layer_trace?.length) setLastLayerTrace(newQ.layer_trace);
    } catch { /* ignore */ } finally { setFollowupBusy(false); }
  };

  const handleApprove = (_q: Question, _addToBank: boolean) => {
    setPendingSuggestions(p => p.filter(x => x.id !== _q.id));
    setQuestions(prev => [...prev, { ..._q, approval_status: "approved" }]);
  };
  const handleReject = (q: Question) => {
    setPendingSuggestions(p => p.filter(x => x.id !== q.id));
  };

  const handleConsultantSynthesis = async () => {
    if (!assessmentId) return;
    setSynthesisBusy(true);
    try {
      const res = await generateConsultantSynthesis(assessmentId);
      setSynthesisText(res.consultant_synthesis);
    } catch { /* ignore */ } finally {
      setSynthesisBusy(false);
    }
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
  const simRunning = watchMode && simStatus === "running";
  const simFinished = watchMode && (simStatus === "completed" || simStatus === "finalized");
  const showWatchBar = watchMode && (simStatus === "running" || simStatus === "stopped" || simStatus === "pending");
  const simProgressPct = Math.min(
    100,
    ((simProgress?.questions_evaluated ?? 0) / Math.max(1, simProgress?.total_questions_planned ?? 1)) * 100,
  );
  const showSimProgressBar = showWatchBar && (simStatus === "running" || simStatus === "stopped");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 110px)", gap: 0 }}>

      {showWatchBar && (
        <div
          data-testid="simulation-watch-bar"
          style={{
            background: "#2e1065", borderBottom: "1px solid #7e22ce",
            padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 10, fontWeight: 700, background: "#581c87", color: "#e9d5ff", borderRadius: 4, padding: "2px 8px" }}>
              AI SIMULATED — İZLEME MODU
            </span>
            <span style={{ fontSize: 12, color: "#d8b4fe" }}>
              {simProgress?.questions_evaluated ?? 0} / {simProgress?.total_questions_planned ?? "…"} soru değerlendirildi
              {simStatus ? ` · ${simStatus}` : ""}
            </span>
            {showSimProgressBar && (
              <div data-testid="simulation-progress-bar" style={{ marginLeft: 12, minWidth: 160 }}>
                <div style={{ fontSize: 10, color: "#e9d5ff", marginBottom: 4 }}>
                  {stopBusy ? "Durduruluyor…" : simStatus === "stopped" ? "Durduruldu" : "İlerleme"}
                </div>
                <div style={{ height: 6, background: "#581c87", borderRadius: 3, overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${simProgressPct}%`,
                      background: "#a78bfa",
                      transition: "width 0.3s",
                    }}
                  />
                </div>
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {simStatus === "stopped" && (
              <>
                <button
                  data-testid="finalize-simulation-btn"
                  onClick={handleFinalizeSimulation}
                  disabled={finalizeBusy || finalizeDone}
                  style={{
                    padding: "6px 14px", borderRadius: 6, border: "none",
                    background: finalizeDone ? "#334155" : "#7e22ce", color: "#fff",
                    cursor: finalizeBusy || finalizeDone ? "not-allowed" : "pointer",
                    fontSize: 12, fontWeight: 600,
                  }}
                >
                  {finalizeBusy ? "Oluşturuluyor…" : finalizeDone ? "Rapor hazır" : "Raporu Oluştur"}
                </button>
                {finalizeDone && (
                  <Link
                    to={withAssessment("/report")}
                    data-testid="go-to-report-link"
                    style={{ fontSize: 12, color: "#c084fc" }}
                  >
                    Rapor Stüdyosu →
                  </Link>
                )}
              </>
            )}
            {(simStatus === "running" || simStatus === "pending") && (
              <button
                data-testid="stop-simulation-btn"
                onClick={handleStopSimulation}
                disabled={stopBusy}
                style={{
                  padding: "6px 14px", borderRadius: 6, border: "none",
                  background: "#dc2626", color: "#fff", cursor: stopBusy ? "not-allowed" : "pointer",
                  fontSize: 12, fontWeight: 600,
                }}
              >
                {stopBusy ? "Durduruluyor…" : "Durdur"}
              </button>
            )}
          </div>
        </div>
      )}

      {simFinished && (
        <div
          data-testid="simulation-completed-banner"
          style={{
            background: "#14532d", borderBottom: "1px solid #166534",
            padding: "8px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
          }}
        >
          <span style={{ fontSize: 12, color: "#bbf7d0" }}>
            Simülasyon tamamlandı — sonuçları workstream sekmelerinden inceleyebilirsiniz.
          </span>
          <Link
            to={withAssessment("/report")}
            style={{ fontSize: 12, color: "#86efac" }}
          >
            Rapor Stüdyosu →
          </Link>
        </div>
      )}

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
                data-testid={`ws-tab-${ws.id}`}
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
                  {" · "}
                  <Link
                    to={withAssessment(`/questions?interview_id=${interview.id}`)}
                    style={{ color: "#60a5fa", fontSize: 12 }}
                  >
                    Sorular →
                  </Link>
                </p>
              )}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {!watchMode && missingBank.length > 0 && interview && (
                <button
                  data-testid="sync-missing-questions-btn"
                  onClick={() => syncMissingQuestions(interview.id, missingBank)}
                  disabled={syncBusy}
                  style={{
                    padding: "7px 14px", borderRadius: 7, border: "1px solid #ca8a04",
                    background: "#713f1222", color: "#fde68a",
                    cursor: syncBusy ? "not-allowed" : "pointer", fontSize: 12, fontWeight: 600,
                  }}
                >
                  {syncBusy ? "…" : `Eksik soruları yükle (${missingBank.length})`}
                </button>
              )}
              <button
                onClick={handleSuggestFollowup}
                disabled={followupBusy || !interview || watchMode}
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
          </div>

          {/* Agent önerileri */}
          {pendingSuggestions.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: "#eab308", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                Bekleyen Agent Önerileri ({pendingSuggestions.length})
              </p>
              {pendingSuggestions.map(q => (
                <SuggestionCard key={q.id} question={q} onApprove={handleApprove} onReject={handleReject} workstream={activeWs} />
              ))}
            </div>
          )}

          {/* Sorular */}
          {loading ? (
            <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
              <p style={{ fontSize: 24, marginBottom: 8 }}>⏳</p>
              <p>Sorular yükleniyor…</p>
            </div>
          ) : simRunning ? (
            <div
              data-testid="simulation-running-message"
              style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 320, color: "#64748b" }}
            >
              <p style={{ fontSize: 32, marginBottom: 12 }}>⏳</p>
              <p style={{ fontSize: 16, color: "#d8b4fe", marginBottom: 8 }}>Simülasyon çalışıyor…</p>
              <p style={{ fontSize: 14 }}>
                {simProgress?.questions_evaluated ?? 0} / {simProgress?.total_questions_planned ?? "…"} soru değerlendirildi
              </p>
            </div>
          ) : questions.length === 0 ? (
            <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
              <p style={{ fontSize: 32, marginBottom: 8 }}>📋</p>
              {watchMode && !task ? (
                <>
                  <p>Bu workstream simülasyonda işlenmedi.</p>
                  <p style={{ fontSize: 12, marginTop: 6 }}>Sol menüden veri içeren bir workstream seçin.</p>
                </>
              ) : (
                <>
                  <p>Bu workstream için soru bankasında soru bulunamadı.</p>
                  <p style={{ fontSize: 12, marginTop: 6 }}>Sorular ekranından soru ekleyebilirsiniz.</p>
                </>
              )}
            </div>
          ) : (
            <>
              {!watchMode && task && interview && (
                <FindingPanel taskId={task.id} interviewId={interview.id} />
              )}
              <p style={{ fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>
                Sorular ({questions.length})
              </p>
              {questions.map((q, i) => (
                <QuestionCard key={q.id} question={q} index={i} onLayerTrace={setLastLayerTrace} assessmentId={assessmentId} consultants={consultants} readOnly={watchMode} />
              ))}
              {interview && (
                <LayerTraceMini
                  trace={lastLayerTrace}
                  assessmentId={assessmentId}
                  interviewId={interview.id}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Alt bar: agent status + AI synthesis ── */}
      <div style={{
        background: "#0f1117", borderTop: "1px solid #1e293b",
        padding: "8px 20px", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
      }}>
        {!watchMode && assessmentId && (
          <button
            data-testid="consultant-synthesis-btn"
            onClick={handleConsultantSynthesis}
            disabled={synthesisBusy}
            style={{
              padding: "6px 14px", borderRadius: 6, border: "none",
              background: "#7c3aed", color: "#fff", fontSize: 12, fontWeight: 600,
              cursor: synthesisBusy ? "not-allowed" : "pointer", marginRight: 8,
            }}
          >
            {synthesisBusy ? "…" : "AI Toplu Değerlendirme"}
          </button>
        )}
        {synthesisText && (
          <p style={{ fontSize: 11, color: "#a78bfa", margin: 0, flex: 1, maxWidth: 480, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {synthesisText.slice(0, 120)}…
          </p>
        )}
        {agentStatus.length > 0 && (
          <>
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
          </>
        )}
      </div>
    </div>
  );
}
