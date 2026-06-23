import { useEffect, useState } from "react";
import { getAgentKnowledgeSummary, type AgentKnowledgeSummary } from "../api";

function KpiCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{
      background: "#0f1117", borderRadius: 8, padding: "10px 12px",
      border: "1px solid #334155", flex: "1 1 45%", minWidth: 120,
    }}>
      <p style={{ fontSize: 10, color: "#64748b", margin: "0 0 4px", textTransform: "uppercase" }}>{label}</p>
      <p style={{ fontSize: 18, fontWeight: 700, margin: 0, color: "#e2e8f0" }}>{value}</p>
    </div>
  );
}

export default function AgentKnowledgePanel({
  workstream,
  refreshKey,
}: {
  workstream: string;
  refreshKey: number;
}) {
  const [data, setData] = useState<AgentKnowledgeSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAgentKnowledgeSummary(workstream)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [workstream, refreshKey]);

  const stats = data?.stats;

  return (
    <div
      data-testid="agent-knowledge-panel"
      style={{
        width: 320, flexShrink: 0, background: "#0f1117",
        borderLeft: "1px solid #1e293b", overflowY: "auto", padding: 16,
      }}
    >
      <h2 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 4px", color: "#a78bfa" }}>Agent Knowledge</h2>
      <p style={{ fontSize: 11, color: "#64748b", margin: "0 0 12px", lineHeight: 1.5 }}>
        Bu agent&apos;ın öğretim özeti — tüm KG metrikleri için sol menüden Knowledge Graph&apos;a gidin.
      </p>

      {loading && <p style={{ fontSize: 12, color: "#475569" }}>Yükleniyor…</p>}

      {!loading && stats && (
        <div>
          <p style={{ fontSize: 12, color: "#cbd5e1", margin: "0 0 12px", lineHeight: 1.6 }}>
            Bu agent <strong>{stats.knowledge_pieces}</strong> bilgi parçası öğrendi.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
            <KpiCard label="AAHA" value={stats.aaha_count} />
            <KpiCard label="AAHA (AI)" value={stats.aaha_ai_count} />
            <KpiCard label="Metin" value={stats.text_count} />
            <KpiCard label="Döküman" value={stats.document_count} />
            <KpiCard label="Chunk" value={stats.chunk_estimate} />
          </div>
          {stats.knowledge_pieces === 0 && (
            <p style={{ fontSize: 11, color: "#fbbf24", background: "#422006", padding: 8, borderRadius: 6 }}>
              Henüz öğrenme kaydı yok — AAHA veya döküman ekleyin.
            </p>
          )}
          {data.recent_events.length > 0 && (
            <div>
              <h4 style={{ fontSize: 11, color: "#94a3b8", margin: "0 0 8px" }}>Son öğrenmeler</h4>
              {data.recent_events.map((ev) => (
                <div key={ev.id} style={{
                  fontSize: 11, padding: "6px 8px", marginBottom: 4,
                  background: "#1e293b", borderRadius: 6, border: "1px solid #334155",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
                    <span style={{ color: "#60a5fa" }}>{ev.mode}</span>
                    <span style={{ color: ev.author_display === "AI" ? "#a78bfa" : "#94a3b8" }}>{ev.author_display}</span>
                  </div>
                  <p style={{ margin: "4px 0 0", color: "#cbd5e1", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {ev.label}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
