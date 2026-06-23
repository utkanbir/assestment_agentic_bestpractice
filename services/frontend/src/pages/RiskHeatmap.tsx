// S17: Risk Heatmap — KPI + drill-down
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getRiskHeatmap, getHeatmapFindings, getMaturityScores, getPendingApprovals,
  type RiskHeatmapCell, type HeatmapFinding,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
type Sev = (typeof SEVERITIES)[number];

const SEV_STYLE: Record<Sev, React.CSSProperties> = {
  critical: { background: "#7f1d1d", color: "#fca5a5" },
  high:     { background: "#7c2d12", color: "#fdba74" },
  medium:   { background: "#713f12", color: "#fde68a" },
  low:      { background: "#14532d", color: "#86efac" },
  info:     { background: "#1e3a5f", color: "#93c5fd" },
};

export default function RiskHeatmap() {
  const { assessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [cells, setCells] = useState<RiskHeatmapCell[]>([]);
  const [maturity, setMaturity] = useState<Record<string, number>>({});
  const [pending, setPending] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<RiskHeatmapCell | null>(null);
  const [drillFindings, setDrillFindings] = useState<HeatmapFinding[]>([]);
  const [approvedOnly, setApprovedOnly] = useState(false);
  const [wsFilter, setWsFilter] = useState("all");

  const load = async () => {
    if (!assessmentId) return;
    setLoading(true);
    try {
      const [heatmap, mat, queue] = await Promise.all([
        getRiskHeatmap(assessmentId),
        getMaturityScores(assessmentId),
        getPendingApprovals(assessmentId),
      ]);
      setCells(heatmap);
      setMaturity(Object.fromEntries(mat.map((m) => [m.workstream, m.score])));
      setPending(queue.total);
    } catch {
      setCells([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [assessmentId]);

  const openCell = async (cell: RiskHeatmapCell) => {
    setSelected(cell);
    if (!assessmentId) return;
    try {
      const findings = await getHeatmapFindings(
        assessmentId,
        cell.capability_area,
        cell.severity,
        approvedOnly,
      );
      setDrillFindings(findings);
    } catch {
      setDrillFindings([]);
    }
  };

  useEffect(() => {
    if (selected && assessmentId) openCell(selected);
  }, [approvedOnly]);

  const areas = [...new Set(cells.map((c) => c.capability_area))].sort();
  const filteredAreas = wsFilter === "all" ? areas : areas.filter((a) => a === wsFilter);
  const totalFindings = cells.reduce((s, c) => s + c.risk_count, 0);
  const criticalHigh = cells
    .filter((c) => c.severity === "critical" || c.severity === "high")
    .reduce((s, c) => s + c.risk_count, 0);

  const matrix: Record<string, Record<Sev, RiskHeatmapCell | undefined>> = {};
  for (const area of filteredAreas) {
    matrix[area] = {} as Record<Sev, RiskHeatmapCell | undefined>;
    for (const sev of SEVERITIES) {
      matrix[area][sev] = cells.find((c) => c.capability_area === area && c.severity === sev);
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Risk Heatmap"
        subtitle="Workstream × severity risk postürü"
        actions={
          <label style={{ fontSize: 12, color: "#94a3b8", display: "flex", alignItems: "center", gap: 6 }}>
            <input type="checkbox" checked={approvedOnly} onChange={(e) => setApprovedOnly(e.target.checked)} />
            Sadece onaylı
          </label>
        }
      />

      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        {[
          { label: "Toplam Bulgu", value: totalFindings },
          { label: "Critical+High", value: criticalHigh },
          { label: "Onay Bekleyen", value: pending },
        ].map((k) => (
          <div key={k.label} style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "8px 14px" }}>
            <span style={{ fontSize: 20, fontWeight: 800, color: "#60a5fa" }}>{k.value}</span>
            <span style={{ fontSize: 11, color: "#64748b", marginLeft: 8 }}>{k.label}</span>
          </div>
        ))}
        <select
          value={wsFilter}
          onChange={(e) => setWsFilter(e.target.value)}
          style={{ background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", fontSize: 12 }}
        >
          <option value="all">Tüm workstream</option>
          {areas.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
      ) : cells.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p>Henüz bulgu yok.</p>
          <Link to={withAssessment("/interview")} style={{ color: "#60a5fa", fontSize: 13 }}>Interview&apos;de bulgu oluşturun</Link>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 12 }}>
            <thead>
              <tr>
                <th style={thStyle}>Workstream</th>
                {SEVERITIES.map((s) => (
                  <th key={s} style={{ ...thStyle, ...SEV_STYLE[s], textAlign: "center" }}>{s.toUpperCase()}</th>
                ))}
                <th style={thStyle}>Olgunluk</th>
              </tr>
            </thead>
            <tbody>
              {filteredAreas.map((area) => {
                const mat = maturity[area];
                const lowMat = mat !== undefined && mat < 2.5;
                return (
                  <tr key={area}>
                    <td style={thStyle}>{area}</td>
                    {SEVERITIES.map((sev) => {
                      const cell = matrix[area][sev];
                      const count = cell?.risk_count ?? 0;
                      const hot = count > 0 && (sev === "critical" || sev === "high") && lowMat;
                      return (
                        <td
                          key={sev}
                          onClick={() => cell && count > 0 && openCell(cell)}
                          style={{
                            ...thStyle,
                            ...(cell ? SEV_STYLE[sev] : {}),
                            textAlign: "center",
                            cursor: count > 0 ? "pointer" : "default",
                            opacity: count ? 1 : 0.3,
                            outline: hot ? "2px solid #ef4444" : undefined,
                          }}
                        >
                          {count || "—"}
                        </td>
                      );
                    })}
                    <td style={thStyle}>{mat?.toFixed(1) ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <div style={modalOverlay} onClick={() => setSelected(null)}>
          <div style={modalBox} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 12px" }}>
              {selected.capability_area} · {selected.severity.toUpperCase()} ({selected.risk_count})
            </h3>
            {drillFindings.length === 0 ? (
              <p style={{ color: "#64748b", fontSize: 13 }}>Bulgu listesi boş.</p>
            ) : (
              drillFindings.map((f) => (
                <div key={f.id} style={{ background: "#0f1117", border: "1px solid #334155", borderRadius: 6, padding: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: 10, color: "#94a3b8" }}>{f.approval_status}</span>
                  <p style={{ margin: "4px 0 0", fontSize: 13 }}>{f.description}</p>
                </div>
              ))
            )}
            <button onClick={() => setSelected(null)} style={{ marginTop: 12, ...ghostBtn }}>Kapat</button>
          </div>
        </div>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = { padding: "8px 10px", border: "1px solid #334155" };
const modalOverlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 300,
  display: "flex", alignItems: "center", justifyContent: "center",
};
const modalBox: React.CSSProperties = {
  background: "#1e293b", border: "1px solid #334155", borderRadius: 10,
  padding: 20, maxWidth: 520, width: "90vw", maxHeight: "70vh", overflow: "auto",
};
const ghostBtn: React.CSSProperties = {
  background: "transparent", border: "1px solid #334155", borderRadius: 6,
  padding: "6px 12px", color: "#94a3b8", cursor: "pointer",
};
