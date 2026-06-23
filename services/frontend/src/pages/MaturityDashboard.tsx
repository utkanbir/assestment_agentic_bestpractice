// S17: Olgunluk — radar + workstream kartları
import { useEffect, useState } from "react";
import {
  getMaturityScores, upsertMaturityScore, listTasks, listFindings,
  aiSuggestMaturity,
  MaturityScoreItem, WORKSTREAMS,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const LEVEL_LABELS: Record<string, { label: string; color: string }> = {
  initial:    { label: "Başlangıç",  color: "#dc2626" },
  developing: { label: "Gelişmekte", color: "#ea580c" },
  defined:    { label: "Tanımlı",    color: "#ca8a04" },
  managed:    { label: "Yönetilen",  color: "#65a30d" },
  optimizing: { label: "Optimize",   color: "#16a34a" },
};

function scoreColor(score: number): string {
  if (score >= 4) return "#16a34a";
  if (score >= 3) return "#65a30d";
  if (score >= 2) return "#ca8a04";
  if (score >= 1) return "#ea580c";
  return "#dc2626";
}

function RadarChart({ scores }: { scores: { label: string; value: number }[] }) {
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 90;
  const n = scores.length || 1;
  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const point = (i: number, v: number) => {
    const r = (v / 5) * maxR;
    return { x: cx + r * Math.cos(angle(i)), y: cy + r * Math.sin(angle(i)) };
  };

  const gridLevels = [1, 2, 3, 4, 5];
  const dataPoints = scores.map((s, i) => point(i, s.value));
  const poly = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <svg width={size} height={size} style={{ display: "block", margin: "0 auto" }}>
      {gridLevels.map((lvl) => (
        <polygon
          key={lvl}
          points={scores.map((_, i) => {
            const p = point(i, lvl);
            return `${p.x},${p.y}`;
          }).join(" ")}
          fill="none"
          stroke="#334155"
          strokeWidth={1}
        />
      ))}
      {scores.map((s, i) => {
        const p = point(i, 5);
        return (
          <text key={s.label} x={p.x} y={p.y} fill="#64748b" fontSize={8} textAnchor="middle" dominantBaseline="middle">
            {s.label.slice(0, 8)}
          </text>
        );
      })}
      <polygon points={poly} fill="#3b82f633" stroke="#3b82f6" strokeWidth={2} />
    </svg>
  );
}

function WorkstreamRow({
  ws,
  score,
  findingCount,
  onSave,
  onInterview,
  onAiSuggest,
}: {
  ws: typeof WORKSTREAMS[number];
  score: MaturityScoreItem | undefined;
  findingCount: number;
  onSave: (workstream: string, s: number, level: string, notes: string, target?: number) => Promise<void>;
  onInterview: () => void;
  onAiSuggest: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(score?.score?.toString() ?? "2.0");
  const [target, setTarget] = useState(score?.target_score?.toString() ?? "4.0");
  const [level, setLevel] = useState(score?.maturity_level ?? "initial");
  const [notes, setNotes] = useState(score?.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);

  const pct = score ? (score.score / 5) * 100 : 0;
  const color = score ? scoreColor(score.score) : "#334155";

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(ws.id, parseFloat(val), level, notes, parseFloat(target));
      setEditing(false);
    } finally { setSaving(false); }
  };

  const handleAi = async () => {
    setAiBusy(true);
    try {
      await onAiSuggest();
    } finally { setAiBusy(false); }
  };

  return (
    <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 14, marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 22 }}>{ws.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <strong style={{ fontSize: 14 }}>{ws.label}</strong>
            <span style={{ fontSize: 12, color: "#64748b" }}>{findingCount} bulgu</span>
          </div>
          <div style={{ height: 8, background: "#0f1117", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4 }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 11, color: "#64748b" }}>
            <span>{score ? `${score.score}/5 — ${LEVEL_LABELS[score.maturity_level]?.label ?? score.maturity_level}` : "Skor girilmedi"}</span>
            {score?.target_score != null && <span>Hedef: {score.target_score}/5</span>}
          </div>
        </div>
        <button onClick={() => setEditing((v) => !v)} style={ghostBtn}>{editing ? "İptal" : "Düzenle"}</button>
        <button onClick={handleAi} disabled={aiBusy} style={{ ...ghostBtn, color: "#a78bfa", borderColor: "#7c3aed" }}>
          {aiBusy ? "…" : "AI Öner"}
        </button>
        <button onClick={onInterview} style={ghostBtn}>Interview</button>
      </div>
      {editing && (
        <div style={{ marginTop: 12, display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr" }}>
          <input value={val} onChange={(e) => setVal(e.target.value)} placeholder="Skor 0-5" style={inputStyle} />
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Hedef skor" style={inputStyle} />
          <select value={level} onChange={(e) => setLevel(e.target.value)} style={inputStyle}>
            {Object.keys(LEVEL_LABELS).map((l) => <option key={l} value={l}>{LEVEL_LABELS[l].label}</option>)}
          </select>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Notlar" style={inputStyle} />
          <button onClick={handleSave} disabled={saving} style={{ ...ghostBtn, gridColumn: "span 2", background: "#3b82f6", color: "#fff", border: "none" }}>
            {saving ? "…" : "Kaydet"}
          </button>
        </div>
      )}
    </div>
  );
}

export default function MaturityDashboard() {
  const { assessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [scores, setScores] = useState<MaturityScoreItem[]>([]);
  const [findingsByWs, setFindingsByWs] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [readOnly] = useState(false);

  const load = async () => {
    if (!assessmentId) return;
    setLoading(true);
    try {
      const [mat, tasks] = await Promise.all([
        getMaturityScores(assessmentId),
        listTasks(assessmentId),
      ]);
      setScores(mat);
      const counts: Record<string, number> = {};
      await Promise.all(tasks.map(async (t) => {
        try {
          const f = await listFindings(t.id);
          counts[t.workstream] = f.length;
        } catch { counts[t.workstream] = 0; }
      }));
      setFindingsByWs(counts);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [assessmentId]);

  const scoreByWs = Object.fromEntries(scores.map((s) => [s.workstream, s]));
  const radarData = WORKSTREAMS.map((ws) => ({
    label: ws.label,
    value: scoreByWs[ws.id]?.score ?? 0,
  }));
  const avg = scores.length
    ? (scores.reduce((s, x) => s + x.score, 0) / scores.length).toFixed(2)
    : "—";

  const handleSave = async (workstream: string, score: number, maturity_level: string, notes: string, target_score?: number) => {
    if (!assessmentId) return;
    await upsertMaturityScore(assessmentId, workstream, { score, maturity_level, notes, target_score });
    load();
  };

  const handleAiSuggest = async (workstream: string) => {
    if (!assessmentId) return;
    await aiSuggestMaturity(assessmentId, workstream);
    load();
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Olgunluk Değerlendirmesi"
        subtitle={`Genel olgunluk: ${avg}/5`}
      />

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
      ) : (
        <>
          <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16, marginBottom: 20 }}>
            <h2 style={{ fontSize: 14, fontWeight: 700, textAlign: "center", marginBottom: 8 }}>Workstream Radar</h2>
            <RadarChart scores={radarData} />
          </div>

          {WORKSTREAMS.map((ws) => (
            <WorkstreamRow
              key={ws.id}
              ws={ws}
              score={scoreByWs[ws.id]}
              findingCount={findingsByWs[ws.id] ?? 0}
              onSave={readOnly ? async () => {} : handleSave}
              onInterview={() => window.location.assign(withAssessment("/interview"))}
              onAiSuggest={() => handleAiSuggest(ws.id)}
            />
          ))}
        </>
      )}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: "#0f1117", border: "1px solid #334155", borderRadius: 6,
  padding: "6px 10px", color: "#e2e8f0", fontSize: 12,
};
const ghostBtn: React.CSSProperties = {
  background: "transparent", border: "1px solid #334155", borderRadius: 6,
  padding: "5px 10px", color: "#94a3b8", fontSize: 11, cursor: "pointer",
};
