// S17: İnceleme Merkezi — 3 sekme
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getPendingApprovals, getPendingQuestions, patchApproval, approveQuestion,
  PendingQuestion,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444", high: "#f97316", medium: "#eab308", low: "#22c55e", info: "#60a5fa",
};

type Tab = "questions" | "findings" | "all";

interface QueueItem {
  id: string;
  type: "finding" | "risk" | "recommendation";
  description: string;
  severity?: string;
  level?: string;
  title?: string;
  confidence?: number;
}

export default function ApprovalQueue() {
  const { assessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [tab, setTab] = useState<Tab>("all");
  const [items, setItems] = useState<QueueItem[]>([]);
  const [questions, setQuestions] = useState<PendingQuestion[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    if (!assessmentId) return;
    setLoading(true);
    try {
      const [data, qs] = await Promise.all([
        getPendingApprovals(assessmentId),
        getPendingQuestions(assessmentId),
      ]);
      const collected: QueueItem[] = [];
      for (const f of data.pending_findings) {
        collected.push({ id: f.id, type: "finding", description: f.description, severity: f.severity, confidence: f.confidence });
      }
      for (const r of data.pending_risks) {
        collected.push({ id: r.id, type: "risk", title: r.title, description: r.description, level: r.level });
      }
      for (const r of data.pending_recommendations) {
        collected.push({ id: r.id, type: "recommendation", description: r.description, severity: "info" });
      }
      setItems(collected);
      setQuestions(qs);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [assessmentId]);

  const decideItem = async (item: QueueItem, decision: "approved" | "rejected", note: string) => {
    await patchApproval(item.type, item.id, decision, note);
    setItems((prev) => prev.filter((i) => i.id !== item.id));
  };

  const decideQuestion = async (q: PendingQuestion, action: "approved" | "rejected") => {
    await approveQuestion(q.id, action);
    setQuestions((prev) => prev.filter((x) => x.id !== q.id));
  };

  const showQueue = tab !== "questions";
  const visible = items;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="İnceleme Merkezi"
        subtitle={`${items.length + questions.length} öğe bekliyor`}
        actions={
          <button onClick={load} style={ghostBtn}>Yenile</button>
        }
      />

      <div
        data-testid="hitl-flow-banner"
        style={{
          marginBottom: 20,
          padding: "14px 16px",
          background: "#0f172a",
          border: "1px solid #1d4ed8",
          borderRadius: 10,
          fontSize: 13,
          color: "#cbd5e1",
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: "#60a5fa" }}>HITL Akışı:</strong> Ajan bulguları ve önerileri burada insan onayından geçer.
        Onaylanan bulgulardan öneri üretilir; öneriler onaylandıktan sonra{" "}
        <Link to={withAssessment("/roadmap")} style={{ color: "#60a5fa" }}>Roadmap</Link>
        {" "}ve{" "}
        <Link to={withAssessment("/heatmap")} style={{ color: "#60a5fa" }}>Risk Heatmap</Link>
        {" "}güncellenir.
      </div>

      <div style={{ display: "flex", gap: 6, marginBottom: 20, flexWrap: "wrap" }}>
        {([
          ["questions", `Ajan Önerileri (${questions.length})`],
          ["findings", `Bulgular/Risk/Öneri (${items.length})`],
          ["all", "Tümü"],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              background: tab === key ? "#3b82f6" : "#1e293b",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "6px 14px",
              color: tab === key ? "#fff" : "#94a3b8",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: tab === key ? 700 : 400,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : tab === "questions" ? (
        questions.length === 0 ? (
          <EmptyState text="Bekleyen ajan önerisi yok." />
        ) : (
          questions.map((q) => (
            <QuestionCard key={q.id} q={q} onDecide={decideQuestion} />
          ))
        )
      ) : showQueue && visible.length === 0 ? (
        <EmptyState text="Bekleyen onay yok." />
      ) : (
        visible.map((item) => (
          <ItemCard key={item.id} item={item} onDecide={decideItem} />
        ))
      )}
    </div>
  );
}

function QuestionCard({ q, onDecide }: { q: PendingQuestion; onDecide: (q: PendingQuestion, a: "approved" | "rejected") => void }) {
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 10, color: "#64748b", marginBottom: 6 }}>{q.workstream} · sıra {q.order}</div>
      <p style={{ margin: "0 0 10px", fontSize: 13 }}>{q.text}</p>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => onDecide(q, "approved")} style={approveBtn}>Onayla</button>
        <button onClick={() => onDecide(q, "rejected")} style={rejectBtn}>Reddet</button>
      </div>
    </div>
  );
}

function ItemCard({ item, onDecide }: { item: QueueItem; onDecide: (i: QueueItem, d: "approved" | "rejected", n: string) => void }) {
  const [note, setNote] = useState("");
  const sev = item.severity ?? item.level ?? "info";
  const color = SEV_COLOR[sev] ?? "#60a5fa";
  return (
    <div style={{ ...cardStyle, borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", marginBottom: 6, textTransform: "uppercase" }}>{item.type}</div>
      <p style={{ margin: "0 0 10px", fontSize: 13 }}>{item.title ?? item.description}</p>
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Gözlemci notu…" style={inputStyle} />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button onClick={() => onDecide(item, "approved", note)} style={approveBtn}>Onayla</button>
        <button onClick={() => onDecide(item, "rejected", note)} style={rejectBtn}>Reddet</button>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
      <p style={{ fontSize: 36, marginBottom: 12 }}>✅</p>
      <p>{text}</p>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 14, marginBottom: 10,
};
const inputStyle: React.CSSProperties = {
  width: "100%", background: "#0f1117", border: "1px solid #334155", borderRadius: 6,
  padding: "5px 10px", color: "#e2e8f0", fontSize: 12, boxSizing: "border-box",
};
const approveBtn: React.CSSProperties = {
  background: "#16a34a22", border: "1px solid #16a34a88", borderRadius: 6,
  padding: "5px 14px", color: "#4ade80", cursor: "pointer", fontSize: 12, fontWeight: 700,
};
const rejectBtn: React.CSSProperties = {
  background: "#dc262622", border: "1px solid #dc262688", borderRadius: 6,
  padding: "5px 14px", color: "#f87171", cursor: "pointer", fontSize: 12, fontWeight: 700,
};
const ghostBtn: React.CSSProperties = {
  background: "transparent", border: "1px solid #334155", borderRadius: 6,
  padding: "6px 12px", color: "#94a3b8", cursor: "pointer", fontSize: 12,
};
