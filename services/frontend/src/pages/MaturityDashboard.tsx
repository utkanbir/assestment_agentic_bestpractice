// S7-FA-004: Maturity dashboard — workstream olgunluk skorları (S8-BA-001 API)
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getMaturityScores, upsertMaturityScore, MaturityScoreItem, WORKSTREAMS } from "../api";

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

function WorkstreamRow({
  ws,
  score,
  onSave,
}: {
  ws: typeof WORKSTREAMS[number];
  score: MaturityScoreItem | undefined;
  onSave: (workstream: string, s: number, level: string, notes: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(score?.score?.toString() ?? "2.0");
  const [level, setLevel] = useState(score?.maturity_level ?? "initial");
  const [notes, setNotes] = useState(score?.notes ?? "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(ws.id, parseFloat(val), level, notes);
      setEditing(false);
    } finally { setSaving(false); }
  };

  const pct = score ? (score.score / 5) * 100 : 0;
  const color = score ? scoreColor(score.score) : "#334155";

  return (
    <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "12px 16px", marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: editing ? 12 : 0 }}>
        <span style={{ fontSize: 22 }}>{ws.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{ws.label}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {score && (
                <span style={{
                  background: LEVEL_LABELS[score.maturity_level]?.color + "22",
                  color: LEVEL_LABELS[score.maturity_level]?.color ?? "#94a3b8",
                  border: `1px solid ${LEVEL_LABELS[score.maturity_level]?.color ?? "#334155"}44`,
                  borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600,
                }}>
                  {LEVEL_LABELS[score.maturity_level]?.label ?? score.maturity_level}
                </span>
              )}
              <span style={{ fontSize: 16, fontWeight: 800, color: score ? scoreColor(score.score) : "#475569" }}>
                {score ? score.score.toFixed(1) : "—"} <span style={{ fontSize: 12, fontWeight: 400, color: "#64748b" }}>/ 5</span>
              </span>
              <button
                onClick={() => setEditing((v) => !v)}
                style={{
                  background: editing ? "#334155" : "transparent",
                  border: "1px solid #334155", borderRadius: 6,
                  padding: "3px 10px", color: "#94a3b8", cursor: "pointer", fontSize: 11,
                }}
              >
                {editing ? "Kapat" : score ? "Düzenle" : "Gir"}
              </button>
            </div>
          </div>
          {/* Progress bar */}
          <div style={{ height: 6, background: "#0f1117", borderRadius: 3, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3, transition: "width 0.3s" }} />
          </div>
          {score?.notes && <p style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{score.notes}</p>}
        </div>
      </div>

      {editing && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 100 }}>
            <label style={{ fontSize: 10, color: "#64748b" }}>Skor (0-5)</label>
            <input type="number" min="0" max="5" step="0.5" value={val}
              onChange={(e) => setVal(e.target.value)}
              style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "5px 8px", color: "#e2e8f0", fontSize: 13, width: 80 }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
            <label style={{ fontSize: 10, color: "#64748b" }}>Olgunluk Seviyesi</label>
            <select value={level} onChange={(e) => setLevel(e.target.value)}
              style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "5px 8px", color: "#e2e8f0", fontSize: 13 }}>
              {Object.entries(LEVEL_LABELS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, flex: 2 }}>
            <label style={{ fontSize: 10, color: "#64748b" }}>Not</label>
            <input placeholder="Opsiyonel not…" value={notes} onChange={(e) => setNotes(e.target.value)}
              style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: "5px 8px", color: "#e2e8f0", fontSize: 13 }} />
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button onClick={handleSave} disabled={saving}
              style={{ background: "#3b82f6", border: "none", borderRadius: 6, padding: "6px 14px", color: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 600, opacity: saving ? 0.6 : 1 }}>
              {saving ? "…" : "Kaydet"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MaturityDashboard() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const [scores, setScores] = useState<MaturityScoreItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!assessmentId) { setLoading(false); return; }
    getMaturityScores(assessmentId)
      .then(setScores)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [assessmentId]);

  const scoreByWs = Object.fromEntries(scores.map((s) => [s.workstream, s]));
  const avgScore = scores.length ? scores.reduce((a, s) => a + s.score, 0) / scores.length : 0;
  const covered = scores.length;

  const handleSave = async (workstream: string, score: number, maturity_level: string, notes: string) => {
    if (!assessmentId) return;
    const updated = await upsertMaturityScore(assessmentId, workstream, { score, maturity_level, notes: notes || undefined });
    setScores((prev) => {
      const idx = prev.findIndex((s) => s.workstream === workstream);
      if (idx >= 0) { const next = [...prev]; next[idx] = updated; return next; }
      return [...prev, updated];
    });
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Olgunluk Matrisi</h1>
        <p style={{ color: "#94a3b8", fontSize: 14 }}>
          Workstream bazlı olgunluk skorları (1–5)
          {assessmentId && ` — ${assessmentId.slice(0, 8)}…`}
        </p>
      </div>

      {!assessmentId ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>📊</p>
          <p>Assessment seçilmedi. URL'ye ?assessment_id= ekleyin.</p>
        </div>
      ) : loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : (
        <>
          {/* Summary */}
          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            {[
              { label: "Ortalama Skor", value: covered > 0 ? avgScore.toFixed(2) : "—", color: covered > 0 ? scoreColor(avgScore) : "#475569" },
              { label: "Değerlendirilen WS", value: `${covered} / ${WORKSTREAMS.length}`, color: "#60a5fa" },
              { label: "En Düşük", value: scores.length ? Math.min(...scores.map((s) => s.score)).toFixed(1) : "—", color: "#f97316" },
              { label: "En Yüksek", value: scores.length ? Math.max(...scores.map((s) => s.score)).toFixed(1) : "—", color: "#22c55e" },
            ].map((s) => (
              <div key={s.label} style={{ flex: 1, background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "12px 16px" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Workstream rows */}
          {WORKSTREAMS.map((ws) => (
            <WorkstreamRow
              key={ws.id}
              ws={ws}
              score={scoreByWs[ws.id]}
              onSave={handleSave}
            />
          ))}

          {/* Legend */}
          <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
            {Object.entries(LEVEL_LABELS).map(([k, v]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: v.color }} />
                <span style={{ fontSize: 11, color: "#94a3b8" }}>{v.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
