// S4-FA-001 / S9-FA-005: Risk Heatmap — interaktif hücre tıklaması ile detay modal
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getRiskHeatmap, type RiskHeatmapCell } from "../api";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
type Sev = (typeof SEVERITIES)[number];

const SEV_STYLE: Record<Sev, React.CSSProperties> = {
  critical: { background: "#7f1d1d", color: "#fca5a5" },
  high:     { background: "#7c2d12", color: "#fdba74" },
  medium:   { background: "#713f12", color: "#fde68a" },
  low:      { background: "#14532d", color: "#86efac" },
  info:     { background: "#1e3a5f", color: "#93c5fd" },
};

const SEV_HEADER: Record<Sev, React.CSSProperties> = {
  critical: { color: "#fca5a5", fontWeight: 700 },
  high:     { color: "#fdba74", fontWeight: 700 },
  medium:   { color: "#fde68a", fontWeight: 700 },
  low:      { color: "#86efac", fontWeight: 700 },
  info:     { color: "#93c5fd", fontWeight: 700 },
};

export default function RiskHeatmap() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [cells, setCells] = useState<RiskHeatmapCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<RiskHeatmapCell | null>(null);

  const load = () => {
    if (!assessmentId) { setLoading(false); return; }
    setLoading(true);
    getRiskHeatmap(assessmentId)
      .then(setCells)
      .catch(() => setCells([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [assessmentId]);

  const areas = [...new Set(cells.map((c) => c.capability_area))].sort();
  const matrix: Record<string, Record<Sev, RiskHeatmapCell | undefined>> = {};
  for (const area of areas) {
    matrix[area] = {} as Record<Sev, RiskHeatmapCell | undefined>;
    for (const sev of SEVERITIES) {
      matrix[area][sev] = cells.find((c) => c.capability_area === area && c.severity === sev);
    }
  }

  if (!assessmentId)
    return <p style={{ color: "#ef4444", padding: 20 }}>assessment_id parametresi gerekli.</p>;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Risk Heatmap</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>Hücreye tıklayın → detay</p>
        </div>
        <button onClick={load} style={{ background: "transparent", border: "1px solid #334155", borderRadius: 6, padding: "6px 14px", color: "#94a3b8", cursor: "pointer", fontSize: 12 }}>
          Yenile
        </button>
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : areas.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>🔲</p>
          <p>Henüz risk verisi yok. Interview yapılıp finding oluşturulduktan sonra heatmap görünür.</p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #334155" }}>
                <th style={{ padding: "10px 14px", textAlign: "left", color: "#94a3b8", fontWeight: 600 }}>Capability Area</th>
                {SEVERITIES.map((s) => (
                  <th key={s} style={{ padding: "10px 14px", textAlign: "center", textTransform: "capitalize", ...SEV_HEADER[s] }}>{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {areas.map((area) => (
                <tr key={area} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "10px 14px", fontWeight: 600, color: "#cbd5e1" }}>{area}</td>
                  {SEVERITIES.map((sev) => {
                    const cell = matrix[area][sev];
                    return (
                      <td key={sev} style={{ padding: "8px", textAlign: "center" }}>
                        {cell ? (
                          <button
                            onClick={() => setSelected(cell)}
                            style={{
                              ...SEV_STYLE[sev],
                              border: "none", borderRadius: 6,
                              padding: "6px 14px", fontWeight: 800, fontSize: 15,
                              cursor: "pointer", minWidth: 40,
                            }}
                          >
                            {cell.risk_count}
                          </button>
                        ) : (
                          <span style={{ color: "#334155" }}>—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ marginTop: 8, fontSize: 11, color: "#475569" }}>
            Hücredeki sayı = o severity'deki risk adedi. Tıklayın → workstream detayı.
          </p>
        </div>
      )}

      {/* Detail Modal */}
      {selected && (
        <div
          onClick={() => setSelected(null)}
          style={{ position: "fixed", inset: 0, background: "#000000aa", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 12, padding: 28, minWidth: 340, maxWidth: 480 }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                {selected.capability_area} — <span style={{ ...SEV_STYLE[selected.severity as Sev], borderRadius: 4, padding: "2px 8px", fontSize: 13 }}>{selected.severity}</span>
              </h2>
              <button onClick={() => setSelected(null)} style={{ background: "transparent", border: "none", color: "#64748b", cursor: "pointer", fontSize: 20, lineHeight: 1 }}>✕</button>
            </div>
            <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
              <div style={{ flex: 1, background: "#0f1117", borderRadius: 8, padding: 14, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: "#f87171" }}>{selected.risk_count}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>Risk Sayısı</div>
              </div>
              <div style={{ flex: 1, background: "#0f1117", borderRadius: 8, padding: 14, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: "#60a5fa" }}>{(selected.max_confidence * 100).toFixed(0)}%</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>Max Güven</div>
              </div>
            </div>
            <div>
              <p style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Etkilenen Workstream'ler:</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {selected.workstreams.map((ws) => (
                  <span key={ws} style={{ background: "#334155", borderRadius: 4, padding: "3px 10px", fontSize: 12, color: "#cbd5e1" }}>{ws}</span>
                ))}
              </div>
            </div>
            <button onClick={() => setSelected(null)} style={{ marginTop: 20, width: "100%", background: "#334155", border: "none", borderRadius: 8, padding: "8px 0", color: "#94a3b8", cursor: "pointer", fontSize: 13 }}>
              Kapat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
