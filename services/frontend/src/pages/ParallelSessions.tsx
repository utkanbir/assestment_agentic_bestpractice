import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Task, Finding, listTasks, listFindings, WORKSTREAMS } from "../api";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
  info:     "#60a5fa",
};

interface WsMessage {
  event: string;
  payload: { question?: string; answer?: string; source?: string; workstream?: string };
}

function SessionPanel({ task }: { task: Task }) {
  const ws = WORKSTREAMS.find((w) => w.id === task.workstream);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [messages, setMessages] = useState<{ role: "agent" | "user"; text: string }[]>([]);
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listFindings(task.id).then(setFindings).catch(() => {});
  }, [task.id]);

  // WebSocket — subscribe to interview events for this task
  useEffect(() => {
    if (!task.id) return;
    // interview_id would come from task or a dedicated endpoint; use task_id as proxy
    const wsUrl = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/interviews/${task.id}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data);
        if (msg.event === "question.suggested" && msg.payload.question) {
          setMessages((prev) => [...prev, { role: "agent", text: msg.payload.question! }]);
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
    } catch { /* ignore */ } finally {
      setSending(false);
    }
  };

  const statusColor: Record<string, string> = {
    pending:     "#94a3b8",
    in_progress: "#3b82f6",
    completed:   "#22c55e",
    failed:      "#ef4444",
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
      height: 480,
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "12px 16px",
        borderBottom: "1px solid #334155",
        background: "#0f1117",
      }}>
        <span style={{ fontSize: 20 }}>{ws?.icon ?? "🤖"}</span>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>{ws?.label ?? task.workstream}</h3>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 6, height: 6, borderRadius: "50%",
              background: sColor, display: "inline-block",
            }} />
            <span style={{ fontSize: 11, color: sColor, textTransform: "uppercase", fontWeight: 600 }}>
              {task.status.replace("_", " ")}
            </span>
          </div>
        </div>
        <div style={{ textAlign: "right", fontSize: 12, color: "#64748b" }}>
          <div>{findings.length} bulgu</div>
        </div>
      </div>

      {/* Findings summary */}
      {findings.length > 0 && (
        <div style={{ padding: "8px 12px", borderBottom: "1px solid #334155", display: "flex", gap: 6, flexWrap: "wrap" }}>
          {Object.entries(
            findings.reduce<Record<string, number>>((acc, f) => {
              acc[f.severity] = (acc[f.severity] ?? 0) + 1;
              return acc;
            }, {})
          ).map(([sev, cnt]) => (
            <span key={sev} style={{
              background: SEV_COLOR[sev] + "22",
              color: SEV_COLOR[sev],
              border: `1px solid ${SEV_COLOR[sev]}44`,
              borderRadius: 4,
              padding: "1px 6px",
              fontSize: 11,
              fontWeight: 600,
            }}>
              {sev.toUpperCase()} {cnt}
            </span>
          ))}
        </div>
      )}

      {/* Chat area */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}>
        {messages.length === 0 && (
          <p style={{ fontSize: 12, color: "#64748b", textAlign: "center", padding: 20 }}>
            {task.status === "pending"
              ? "Task bekleniyor — ajan başlatılmamış"
              : "Mesaj bekleniyor…"}
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === "agent" ? "flex-start" : "flex-end",
              maxWidth: "85%",
              background: m.role === "agent" ? "#0f1117" : "#1d4ed8",
              border: m.role === "agent" ? "1px solid #334155" : "none",
              borderRadius: m.role === "agent" ? "4px 12px 12px 12px" : "12px 4px 12px 12px",
              padding: "8px 12px",
              fontSize: 13,
              lineHeight: 1.5,
              color: "#e2e8f0",
            }}
          >
            {m.role === "agent" && (
              <span style={{ fontSize: 10, color: "#94a3b8", display: "block", marginBottom: 4, fontWeight: 600 }}>
                AJAN
              </span>
            )}
            {m.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        display: "flex",
        gap: 8,
        padding: "10px 12px",
        borderTop: "1px solid #334155",
        background: "#0f1117",
      }}>
        <input
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendAnswer()}
          placeholder="Yanıtınızı yazın…"
          disabled={task.status === "completed" || task.status === "pending"}
          style={{
            flex: 1,
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "6px 10px",
            color: "#e2e8f0",
            fontSize: 13,
            outline: "none",
          }}
        />
        <button
          onClick={sendAnswer}
          disabled={!answer.trim() || sending || task.status === "completed"}
          style={{
            background: "#3b82f6",
            border: "none",
            borderRadius: 6,
            padding: "6px 14px",
            color: "#fff",
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600,
            opacity: !answer.trim() || sending ? 0.5 : 1,
          }}
        >
          →
        </button>
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
      listTasks(assessmentId)
        .then(setTasks)
        .catch(() => {})
        .finally(() => setLoading(false));
    };
    poll();
    // Poll every 10s for status updates
    const interval = setInterval(poll, 10_000);
    return () => clearInterval(interval);
  }, [assessmentId]);

  const activeTasks = tasks.filter((t) => t.status !== "cancelled");

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
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
              <span style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: s === "pending" ? "#94a3b8" : s === "in_progress" ? "#3b82f6" : "#22c55e",
                display: "inline-block",
              }} />
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
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 16,
        }}>
          {activeTasks.map((task) => (
            <SessionPanel key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
