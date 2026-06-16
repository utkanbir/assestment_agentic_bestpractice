// S7-FA-001: Interview UI alt panel — findings + evidence full view
// S7-FA-002: Interview UI right panel — agent suggestions (risk signal, missing evidence)
// S8-FA-002: Manual interview Q&A panel (create interview + question bank questions)
// S8-FA-003: Evidence upload form
// S8-FA-004: Finding creation form
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Task, Finding, listTasks, listFindings, WORKSTREAMS, fetchJSON,
  createInterview, listInterviews, Interview,
  listWorkstreamQuestions, WorkstreamQuestion,
  createEvidence,
} from "../api";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
  info:     "#60a5fa",
};

const panelInputStyle: React.CSSProperties = {
  background: "#1e293b", border: "1px solid #334155", borderRadius: 6,
  padding: "6px 10px", color: "#e2e8f0", fontSize: 12, outline: "none", width: "100%",
  boxSizing: "border-box",
};

const panelBtnStyle: React.CSSProperties = {
  background: "#3b82f6", color: "#fff", border: "none", borderRadius: 6,
  padding: "6px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600,
};

interface Evidence {
  id: string;
  source: string;
  content: string;
  evidence_type: string;
}

interface WsMessage {
  event: string;
  payload: {
    question?: string;
    answer?: string;
    source?: string;
    workstream?: string;
    risk_signal?: string;
    missing_evidence?: string[];
    confidence?: number;
  };
}

interface AgentSuggestion {
  type: "risk_signal" | "missing_evidence" | "confidence";
  message: string;
  severity?: string;
}

function EvidenceTag({ ev }: { ev: Evidence }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{ marginTop: 6 }}>
      <button
        onClick={() => setExpanded((v) => !v)}
        style={{
          background: "#0f1117",
          border: "1px solid #334155",
          borderRadius: 4,
          padding: "2px 8px",
          color: "#94a3b8",
          cursor: "pointer",
          fontSize: 11,
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        <span>📎</span>
        <span>{ev.source}</span>
        <span style={{ color: "#64748b" }}>[{ev.evidence_type}]</span>
        <span>{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && (
        <div style={{
          marginTop: 4,
          padding: "6px 8px",
          background: "#0f1117",
          border: "1px solid #334155",
          borderRadius: 4,
          fontSize: 11,
          color: "#cbd5e1",
          whiteSpace: "pre-wrap",
          maxHeight: 120,
          overflowY: "auto",
        }}>
          {ev.content}
        </div>
      )}
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding & { evidence?: Evidence } }) {
  const c = SEV_COLOR[finding.severity] ?? "#94a3b8";
  return (
    <div style={{
      border: `1px solid ${c}44`,
      borderLeft: `3px solid ${c}`,
      borderRadius: 6,
      padding: "8px 10px",
      background: c + "0a",
      marginBottom: 6,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <span style={{ fontSize: 12, color: "#e2e8f0", lineHeight: 1.4, flex: 1 }}>
          {finding.description}
        </span>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, flexShrink: 0 }}>
          <span style={{ background: c + "22", color: c, borderRadius: 3, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>
            {finding.severity.toUpperCase()}
          </span>
          <span style={{ fontSize: 10, color: "#64748b" }}>
            conf: {(finding.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      {finding.evidence && <EvidenceTag ev={finding.evidence} />}
    </div>
  );
}

function AgentSuggestionPanel({ suggestions }: { suggestions: AgentSuggestion[] }) {
  if (suggestions.length === 0) return null;
  return (
    <div style={{
      width: 200,
      flexShrink: 0,
      borderLeft: "1px solid #334155",
      padding: "10px 10px",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      overflowY: "auto",
      background: "#0b1120",
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
        Ajan Önerileri
      </div>
      {suggestions.map((s, i) => {
        const icons = { risk_signal: "⚠️", missing_evidence: "📎", confidence: "📊" };
        const colors = { risk_signal: "#f97316", missing_evidence: "#eab308", confidence: "#60a5fa" };
        return (
          <div key={i} style={{
            background: "#1e293b",
            border: `1px solid ${colors[s.type]}44`,
            borderRadius: 6,
            padding: "6px 8px",
            fontSize: 11,
            color: "#cbd5e1",
            lineHeight: 1.4,
          }}>
            <div style={{ marginBottom: 4 }}>{icons[s.type]} <strong style={{ color: colors[s.type] }}>
              {s.type === "risk_signal" ? "Risk Sinyali" : s.type === "missing_evidence" ? "Eksik Kanıt" : "Güven Skoru"}
            </strong></div>
            {s.message}
          </div>
        );
      })}
    </div>
  );
}

type SessionTab = "chat" | "interview" | "evidence" | "findings";

function SessionPanel({ task }: { task: Task }) {
  const ws = WORKSTREAMS.find((w) => w.id === task.workstream);
  const [tab, setTab] = useState<SessionTab>("chat");
  const [findings, setFindings] = useState<(Finding & { evidence?: Evidence })[]>([]);
  const [messages, setMessages] = useState<{ role: "agent" | "user"; text: string }[]>([]);
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const [showFindings, setShowFindings] = useState(false);
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // S8-FA-002: Manual interview state
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [showNewInterview, setShowNewInterview] = useState(false);
  const [intervieweeName, setIntervieweeName] = useState("");
  const [intervieweeRole, setIntervieweeRole] = useState("");
  const [kbQuestions, setKbQuestions] = useState<WorkstreamQuestion[]>([]);
  const [activeInterview, setActiveInterview] = useState<Interview | null>(null);
  const [qAnswers, setQAnswers] = useState<Record<string, string>>({});
  const [savingAnswer, setSavingAnswer] = useState<string | null>(null);

  // S8-FA-003: Evidence state
  const [evSource, setEvSource] = useState("");
  const [evContent, setEvContent] = useState("");
  const [evType, setEvType] = useState("interview");
  const [uploadedEv, setUploadedEv] = useState<{ id: string; source: string }[]>([]);
  const [uploadingEv, setUploadingEv] = useState(false);

  // S8-FA-004: Finding state
  const [findDesc, setFindDesc] = useState("");
  const [findSev, setFindSev] = useState("medium");
  const [findConf, setFindConf] = useState("0.7");
  const [findEvId, setFindEvId] = useState("");
  const [creatingFind, setCreatingFind] = useState(false);

  const loadFindings = () => {
    listFindings(task.id).then(async (fs) => {
      const enriched = await Promise.all(
        fs.map(async (f) => {
          try {
            const ev = await fetchJSON<Evidence>(`/evidences/${(f as any).evidence_id}`);
            return { ...f, evidence: ev };
          } catch { return f; }
        })
      );
      setFindings(enriched);
    }).catch(() => {});
  };

  const loadInterviews = () => {
    listInterviews(task.id).then(setInterviews).catch(() => {});
  };

  useEffect(() => { loadFindings(); loadInterviews(); }, [task.id]);

  useEffect(() => {
    if (tab !== "interview") return;
    listWorkstreamQuestions(task.workstream).then(setKbQuestions).catch(() => {});
  }, [tab, task.workstream]);

  const handleCreateInterview = async () => {
    if (!intervieweeName.trim()) return;
    try {
      const intv = await createInterview({ task_id: task.id, interviewee_name: intervieweeName.trim(), interviewee_role: intervieweeRole.trim() || undefined });
      setActiveInterview(intv);
      setInterviews((prev) => [...prev, intv]);
      setShowNewInterview(false);
      setIntervieweeName(""); setIntervieweeRole("");
    } catch {}
  };

  const handleSaveAnswer = async (questionId: string) => {
    const text = qAnswers[questionId];
    if (!text?.trim()) return;
    setSavingAnswer(questionId);
    try {
      await fetchJSON(`/interviews/questions/${questionId}/answers`, {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, text: text.trim() }),
      });
    } catch {} finally { setSavingAnswer(null); }
  };

  const handleUploadEvidence = async () => {
    if (!evSource.trim() || !evContent.trim()) return;
    setUploadingEv(true);
    try {
      const ev = await createEvidence({ source: evSource.trim(), content: evContent.trim(), evidence_type: evType });
      setUploadedEv((prev) => [...prev, { id: ev.id, source: ev.source }]);
      setEvSource(""); setEvContent("");
      if (!findEvId) setFindEvId(ev.id);
    } catch {} finally { setUploadingEv(false); }
  };

  const handleCreateFinding = async () => {
    if (!findDesc.trim() || !findEvId) return;
    setCreatingFind(true);
    try {
      await fetchJSON("/findings", {
        method: "POST",
        body: JSON.stringify({
          task_id: task.id,
          evidence_id: findEvId,
          description: findDesc.trim(),
          severity: findSev,
          confidence: parseFloat(findConf),
        }),
      });
      setFindDesc(""); setFindEvId("");
      loadFindings();
    } catch {} finally { setCreatingFind(false); }
  };

  useEffect(() => {
    if (!task.id) return;
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${proto}//${location.host}/ws/interviews/${task.id}`);
    socketRef.current = socket;

    socket.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data);
        if (msg.event === "question.suggested" && msg.payload.question) {
          setMessages((prev) => [...prev, { role: "agent", text: msg.payload.question! }]);
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
        // S7-FA-002: capture agent suggestion signals
        if (msg.event === "risk.signal" && msg.payload.risk_signal) {
          setSuggestions((prev) => [...prev, {
            type: "risk_signal",
            message: msg.payload.risk_signal!,
            severity: msg.payload.workstream,
          }]);
        }
        if (msg.event === "evidence.missing" && msg.payload.missing_evidence) {
          setSuggestions((prev) => [...prev, {
            type: "missing_evidence",
            message: `Eksik kanıt alanları: ${msg.payload.missing_evidence!.join(", ")}`,
          }]);
        }
        if (msg.event === "finding.detected") {
          // Refresh findings panel
          setTimeout(loadFindings, 500);
          if (msg.payload.confidence !== undefined) {
            setSuggestions((prev) => [...prev, {
              type: "confidence",
              message: `Yeni bulgu güven skoru: ${((msg.payload.confidence ?? 0) * 100).toFixed(0)}%`,
            }]);
          }
        }
      } catch { /* ignore malformed */ }
    };

    socket.onerror = () => {};
    return () => { socket.close(); };
  }, [task.id]);

  const sendAnswer = async () => {
    if (!answer.trim() || sending) return;
    setSending(true);
    const text = answer.trim();
    setAnswer("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    try {
      await fetch(`/api/v1/interviews/${task.id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: text, task_id: task.id }),
      });
    } catch { /* ignore */ } finally { setSending(false); }
  };

  const statusColor: Record<string, string> = {
    pending: "#94a3b8", in_progress: "#3b82f6", completed: "#22c55e", failed: "#ef4444",
  };
  const sColor = statusColor[task.status] ?? "#94a3b8";

  return (
    <div style={{
      background: "#1e293b",
      border: "1px solid #334155",
      borderRadius: 10,
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
      height: 560,
    }}>
      {/* Header */}
      <div style={{ background: "#0f1117", borderBottom: "1px solid #334155" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 16px 0" }}>
          <span style={{ fontSize: 20 }}>{ws?.icon ?? "🤖"}</span>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>{ws?.label ?? task.workstream}</h3>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: sColor, display: "inline-block" }} />
              <span style={{ fontSize: 11, color: sColor, textTransform: "uppercase", fontWeight: 600 }}>
                {task.status.replace("_", " ")}
              </span>
            </div>
          </div>
        </div>
        {/* Tabs — S8-FA-002/003/004 */}
        <div style={{ display: "flex", gap: 0, padding: "6px 12px 0" }}>
          {([
            { id: "chat", label: "Canlı Chat" },
            { id: "interview", label: `Mülakat (${interviews.length})` },
            { id: "evidence", label: "Kanıt Yükle" },
            { id: "findings", label: `Bulgular (${findings.length})` },
          ] as { id: SessionTab; label: string }[]).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                background: tab === t.id ? "#1e293b" : "transparent",
                border: "1px solid " + (tab === t.id ? "#334155" : "transparent"),
                borderBottom: tab === t.id ? "1px solid #1e293b" : "1px solid transparent",
                borderRadius: "6px 6px 0 0",
                padding: "5px 12px",
                color: tab === t.id ? "#e2e8f0" : "#64748b",
                cursor: "pointer",
                fontSize: 11,
                fontWeight: tab === t.id ? 600 : 400,
                marginRight: 2,
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Body — sekme içeriği */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>

        {/* TAB: Canlı Chat (WS) */}
        {tab === "chat" && (
          <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
                {messages.length === 0 && (
                  <p style={{ fontSize: 12, color: "#64748b", textAlign: "center", padding: 20 }}>
                    {task.status === "pending" ? "Task bekleniyor — ajan başlatılmamış" : "Mesaj bekleniyor…"}
                  </p>
                )}
                {messages.map((m, i) => (
                  <div key={i} style={{
                    alignSelf: m.role === "agent" ? "flex-start" : "flex-end",
                    maxWidth: "85%",
                    background: m.role === "agent" ? "#0f1117" : "#1d4ed8",
                    border: m.role === "agent" ? "1px solid #334155" : "none",
                    borderRadius: m.role === "agent" ? "4px 12px 12px 12px" : "12px 4px 12px 12px",
                    padding: "8px 12px", fontSize: 13, lineHeight: 1.5, color: "#e2e8f0",
                  }}>
                    {m.role === "agent" && <span style={{ fontSize: 10, color: "#94a3b8", display: "block", marginBottom: 4, fontWeight: 600 }}>AJAN</span>}
                    {m.text}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              <div style={{ display: "flex", gap: 8, padding: "10px 12px", borderTop: "1px solid #334155", background: "#0f1117" }}>
                <input value={answer} onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendAnswer()}
                  placeholder="Yanıtınızı yazın…"
                  disabled={task.status === "completed" || task.status === "pending"}
                  style={{ flex: 1, background: "#1e293b", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", color: "#e2e8f0", fontSize: 13, outline: "none" }}
                />
                <button onClick={sendAnswer} disabled={!answer.trim() || sending || task.status === "completed"}
                  style={{ background: "#3b82f6", border: "none", borderRadius: 6, padding: "6px 14px", color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, opacity: !answer.trim() || sending ? 0.5 : 1 }}>→</button>
              </div>
            </div>
            <AgentSuggestionPanel suggestions={suggestions} />
          </div>
        )}

        {/* TAB: Mülakat — S8-FA-002 */}
        {tab === "interview" && (
          <div style={{ flex: 1, overflowY: "auto", padding: 14 }}>
            {/* New interview form */}
            {showNewInterview ? (
              <div style={{ background: "#0f1117", border: "1px solid #3b82f6", borderRadius: 8, padding: 14, marginBottom: 12 }}>
                <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Yeni Mülakat</h4>
                <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                  <input placeholder="Görüşülen kişi adı *" value={intervieweeName} onChange={(e) => setIntervieweeName(e.target.value)}
                    style={{ flex: 2, ...panelInputStyle }} />
                  <input placeholder="Rolü (opsiyonel)" value={intervieweeRole} onChange={(e) => setIntervieweeRole(e.target.value)}
                    style={{ flex: 1, ...panelInputStyle }} />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={handleCreateInterview} disabled={!intervieweeName.trim()}
                    style={{ ...panelBtnStyle, opacity: intervieweeName.trim() ? 1 : 0.5 }}>Oluştur</button>
                  <button onClick={() => setShowNewInterview(false)} style={{ ...panelBtnStyle, background: "#334155" }}>İptal</button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowNewInterview(true)} style={{ ...panelBtnStyle, marginBottom: 12 }}>+ Yeni Mülakat</button>
            )}

            {/* Existing interviews */}
            {interviews.map((intv) => (
              <div key={intv.id} style={{ border: "1px solid #334155", borderRadius: 8, marginBottom: 10, overflow: "hidden" }}>
                <div
                  onClick={() => setActiveInterview(activeInterview?.id === intv.id ? null : intv)}
                  style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "#0f1117", cursor: "pointer" }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{intv.interviewee_name}</span>
                  <span style={{ fontSize: 11, color: "#64748b" }}>{intv.interviewee_role ?? ""} {activeInterview?.id === intv.id ? "▲" : "▼"}</span>
                </div>
                {activeInterview?.id === intv.id && (
                  <div style={{ padding: 12 }}>
                    {kbQuestions.length === 0
                      ? <p style={{ fontSize: 12, color: "#64748b" }}>Soru bankasından sorular yükleniyor…</p>
                      : kbQuestions.map((q) => (
                        <div key={q.id} style={{ marginBottom: 12 }}>
                          <p style={{ fontSize: 12, color: "#e2e8f0", marginBottom: 4 }}><strong>{q.order}.</strong> {q.text}</p>
                          <div style={{ display: "flex", gap: 6 }}>
                            <input
                              placeholder="Yanıt…"
                              value={qAnswers[q.id] ?? ""}
                              onChange={(e) => setQAnswers((p) => ({ ...p, [q.id]: e.target.value }))}
                              style={{ flex: 1, ...panelInputStyle }}
                            />
                            <button
                              onClick={() => handleSaveAnswer(q.id)}
                              disabled={savingAnswer === q.id}
                              style={{ ...panelBtnStyle, fontSize: 11, padding: "4px 10px" }}>Kaydet</button>
                          </div>
                        </div>
                      ))
                    }
                  </div>
                )}
              </div>
            ))}
            {interviews.length === 0 && !showNewInterview && (
              <p style={{ fontSize: 12, color: "#64748b", textAlign: "center", padding: 20 }}>Henüz mülakat yok. Yeni mülakat oluşturun.</p>
            )}
          </div>
        )}

        {/* TAB: Kanıt Yükle — S8-FA-003 */}
        {tab === "evidence" && (
          <div style={{ flex: 1, overflowY: "auto", padding: 14 }}>
            <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Kanıt Yükle</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
              <input placeholder="Kaynak (örn. Interview-Ahmet, Document-DR-Plan.pdf)"
                value={evSource} onChange={(e) => setEvSource(e.target.value)} style={panelInputStyle} />
              <select value={evType} onChange={(e) => setEvType(e.target.value)} style={{ ...panelInputStyle, color: "#e2e8f0" }}>
                <option value="interview">Interview</option>
                <option value="document">Document</option>
                <option value="observation">Observation</option>
                <option value="metric">Metric</option>
              </select>
              <textarea placeholder="Kanıt içeriği / notlar…"
                value={evContent} onChange={(e) => setEvContent(e.target.value)}
                rows={4} style={{ ...panelInputStyle, resize: "vertical" }} />
              <button onClick={handleUploadEvidence} disabled={uploadingEv || !evSource.trim() || !evContent.trim()}
                style={{ ...panelBtnStyle, opacity: evSource.trim() && evContent.trim() ? 1 : 0.5 }}>
                {uploadingEv ? "Yükleniyor…" : "Kanıt Ekle"}
              </button>
            </div>
            {uploadedEv.length > 0 && (
              <div>
                <p style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>Bu oturumda yüklenen kanıtlar:</p>
                {uploadedEv.map((e) => (
                  <div key={e.id} style={{ fontSize: 11, color: "#22c55e", background: "#0f1117", borderRadius: 4, padding: "3px 8px", marginBottom: 3 }}>
                    ✓ {e.source} <span style={{ color: "#475569" }}>({e.id.slice(0, 8)}…)</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB: Bulgular — S8-FA-004 */}
        {tab === "findings" && (
          <div style={{ flex: 1, overflowY: "auto", padding: 14 }}>
            {/* Manual finding creation */}
            <div style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 8, padding: 12, marginBottom: 14 }}>
              <h4 style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: "#94a3b8" }}>Manuel Bulgu Ekle</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <input placeholder="Evidence ID (kanıt önce yüklenmelidir)" value={findEvId}
                  onChange={(e) => setFindEvId(e.target.value)} style={panelInputStyle} />
                <textarea placeholder="Bulgu açıklaması…" value={findDesc}
                  onChange={(e) => setFindDesc(e.target.value)} rows={2} style={{ ...panelInputStyle, resize: "none" }} />
                <div style={{ display: "flex", gap: 6 }}>
                  <select value={findSev} onChange={(e) => setFindSev(e.target.value)} style={{ ...panelInputStyle, flex: 1, color: "#e2e8f0" }}>
                    {["critical","high","medium","low","info"].map((s) => <option key={s}>{s}</option>)}
                  </select>
                  <input placeholder="Güven (0-1)" value={findConf}
                    onChange={(e) => setFindConf(e.target.value)} style={{ ...panelInputStyle, width: 80 }} />
                  <button onClick={handleCreateFinding} disabled={creatingFind || !findDesc.trim() || !findEvId.trim()}
                    style={{ ...panelBtnStyle, opacity: findDesc.trim() && findEvId.trim() ? 1 : 0.5 }}>
                    {creatingFind ? "…" : "Ekle"}
                  </button>
                </div>
              </div>
            </div>
            {/* Existing findings */}
            {findings.length === 0
              ? <p style={{ fontSize: 12, color: "#64748b", textAlign: "center", padding: 20 }}>Henüz bulgu yok.</p>
              : findings.map((f) => <FindingCard key={f.id} finding={f} />)
            }
          </div>
        )}
      </div>
    </div>
  );
}

export default function ParallelSessions() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    const poll = () => {
      listTasks(assessmentId).then(setTasks).catch(() => {}).finally(() => setLoading(false));
    };
    poll();
    const interval = setInterval(poll, 10_000);
    return () => clearInterval(interval);
  }, [assessmentId]);

  const activeTasks = tasks.filter((t) => t.status !== "cancelled");

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Paralel Oturumlar</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            {activeTasks.length > 0
              ? `${activeTasks.length} workstream ajanı eş zamanlı çalışıyor`
              : "Henüz aktif oturum yok"}
            {assessmentId && ` — ${assessmentId.slice(0, 8)}…`}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {["pending", "in_progress", "completed"].map((s) => (
            <div key={s} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "#94a3b8" }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: s === "pending" ? "#94a3b8" : s === "in_progress" ? "#3b82f6" : "#22c55e", display: "inline-block" }} />
              {tasks.filter((t) => t.status === s).length} {s.replace("_", " ")}
            </div>
          ))}
        </div>
      </div>

      {!assessmentId ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 40, marginBottom: 12 }}>🤖</p>
          <p>Assessment seçilmedi. Genel Bakış'tan bir proje seçin.</p>
        </div>
      ) : loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : activeTasks.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 40, marginBottom: 12 }}>📭</p>
          <p>Bu assessment için henüz task oluşturulmadı.</p>
          <p style={{ fontSize: 13, marginTop: 6 }}>Ajan Seçimi sayfasından ajanları başlatın.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(400px, 1fr))", gap: 16 }}>
          {activeTasks.map((task) => <SessionPanel key={task.id} task={task} />)}
        </div>
      )}
    </div>
  );
}
