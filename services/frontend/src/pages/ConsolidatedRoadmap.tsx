// S17: Konsolide Roadmap — 3 şerit layout
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getConsolidatedRoadmap, generateRoadmap, type RoadmapItem } from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const HORIZON_LABELS: Record<string, string> = {
  short: "Kısa Vade (0-3 ay)",
  medium: "Orta Vade (3-12 ay)",
  long: "Uzun Vade (12+ ay)",
};

const HORIZON_COLORS: Record<string, string> = {
  short: "#ef4444",
  medium: "#eab308",
  long: "#3b82f6",
};

export default function ConsolidatedRoadmap() {
  const { assessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = () => {
    if (!assessmentId) return;
    setLoading(true);
    getConsolidatedRoadmap(assessmentId)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [assessmentId]);

  const handleGenerate = async () => {
    if (!assessmentId) return;
    setGenerating(true);
    try {
      setItems(await generateRoadmap(assessmentId));
    } finally {
      setGenerating(false);
    }
  };

  const lanes: ("short" | "medium" | "long")[] = ["short", "medium", "long"];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Dönüşüm Roadmap"
        subtitle="Onaylanmış önerilerden faz bazlı plan"
        actions={
          <button onClick={handleGenerate} disabled={generating} style={btnStyle}>
            {generating ? "…" : "Roadmap Güncelle"}
          </button>
        }
      />

      {loading ? (
        <p style={{ color: "#64748b", padding: 40, textAlign: "center" }}>Yükleniyor…</p>
      ) : items.length === 0 ? (
        <div data-testid="roadmap-empty-wizard" style={{ padding: "40px 20px" }}>
          <p style={{ textAlign: "center", color: "#94a3b8", marginBottom: 28 }}>
            Henüz roadmap öğesi yok. Aşağıdaki adımları izleyin:
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
            {[
              { step: 1, label: "Bulgu", desc: "Interview'da bulgu oluştur", to: withAssessment("/interview") },
              { step: 2, label: "Öneri", desc: "Onaylı bulgudan öneri üret", to: withAssessment("/approvals") },
              { step: 3, label: "İnceleme Merkezi", desc: "Önerileri onayla", to: withAssessment("/approvals") },
              { step: 4, label: "Roadmap", desc: "Faz planını oluştur", to: withAssessment("/roadmap") },
            ].map((s) => (
              <Link
                key={s.step}
                to={s.to}
                style={{
                  textDecoration: "none",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 10,
                  padding: "16px 18px",
                  minWidth: 150,
                  color: "#e2e8f0",
                }}
              >
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>Adım {s.step}</div>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 12, color: "#94a3b8" }}>{s.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, alignItems: "start" }}>
          {lanes.map((h) => {
            const laneItems = items.filter((i) => i.horizon === h);
            return (
              <div key={h} style={{ background: "#0f1117", border: `1px solid ${HORIZON_COLORS[h]}44`, borderRadius: 10, padding: 12 }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, color: HORIZON_COLORS[h], marginBottom: 12 }}>
                  {HORIZON_LABELS[h]}
                  <span style={{ color: "#64748b", fontWeight: 400, marginLeft: 8 }}>({laneItems.length})</span>
                </h2>
                {laneItems.length === 0 ? (
                  <p style={{ fontSize: 12, color: "#64748b" }}>Bu fazda öğe yok.</p>
                ) : (
                  laneItems.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        background: "#1e293b",
                        border: "1px solid #334155",
                        borderLeft: `3px solid ${HORIZON_COLORS[h]}`,
                        borderRadius: 6,
                        padding: 12,
                        marginBottom: 10,
                      }}
                    >
                      <div style={{ display: "flex", gap: 6, marginBottom: 6, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 10, fontWeight: 700, background: "#334155", padding: "2px 6px", borderRadius: 4 }}>
                          P{item.priority}
                        </span>
                        {item.workstreams.map((ws) => (
                          <span key={ws} style={{ fontSize: 10, color: "#60a5fa" }}>{ws}</span>
                        ))}
                        {item.addresses_conflict && (
                          <span style={{ fontSize: 10, color: "#eab308" }}>⚠ çakışma</span>
                        )}
                      </div>
                      <strong style={{ fontSize: 13 }}>{item.title || "Öneri"}</strong>
                      <p style={{ margin: "6px 0 0", fontSize: 12, color: "#94a3b8", lineHeight: 1.5 }}>{item.description}</p>
                      {item.effort && <p style={{ margin: "6px 0 0", fontSize: 10, color: "#64748b" }}>Efor: {item.effort}</p>}
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  background: "#3b82f6", color: "#fff", border: "none", borderRadius: 8,
  padding: "8px 16px", cursor: "pointer", fontWeight: 600, fontSize: 13,
};
