// S7-FA-004: Maturity dashboard — capability × dimension ısı haritası
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchJSON } from "../api";

interface MaturityScore {
  capability_area: string;
  dimension: string;
  score: number;         // 0.0 – 5.0
  max_score: number;
  workstream: string;
}

const DIMENSIONS = ["People", "Process", "Technology", "Data", "Governance"];

const CAPABILITY_AREAS = [
  "Data Ingestion", "Data Storage", "Data Processing",
  "Data Quality", "Data Governance", "Data Security",
  "Analytics", "Platform Operations",
];

function scoreColor(score: number): string {
  if (score >= 4) return "#16a34a";
  if (score >= 3) return "#65a30d";
  if (score >= 2) return "#ca8a04";
  if (score >= 1) return "#ea580c";
  return "#dc2626";
}

function HeatCell({ score, max }: { score: number | undefined; max: number }) {
  if (score === undefined) {
    return (
      <td style={{
        width: 72, height: 52,
        background: "#1e293b",
        border: "1px solid #334155",
        textAlign: "center",
        verticalAlign: "middle",
        fontSize: 11,
        color: "#475569",
      }}>—</td>
    );
  }
  const pct = score / max;
  const bg = scoreColor(score);
  return (
    <td
      title={`${score.toFixed(1)} / ${max}`}
      style={{
        width: 72, height: 52,
        background: bg + Math.round(pct * 200 + 30).toString(16).padStart(2, "0"),
        border: "1px solid #0f1117",
        textAlign: "center",
        verticalAlign: "middle",
        cursor: "default",
        transition: "opacity 0.15s",
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 700, color: "#fff" }}>{score.toFixed(1)}</div>
      <div style={{ fontSize: 9, color: "rgba(255,255,255,0.6)" }}>{(pct * 100).toFixed(0)}%</div>
    </td>
  );
}

export default function MaturityDashboard() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const [scores, setScores] = useState<MaturityScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    fetchJSON<MaturityScore[]>(`/assessments/${assessmentId}/maturity`)
      .then(setScores)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [assessmentId]);

  // Build lookup: capability → dimension → score
  const lookup: Record<string, Record<string, number>> = {};
  for (const s of scores) {
    if (!lookup[s.capability_area]) lookup[s.capability_area] = {};
    lookup[s.capability_area][s.dimension] = s.score;
  }

  // Dynamic rows/cols from actual data or fallbacks
  const capabilities = scores.length
    ? [...new Set(scores.map((s) => s.capability_area))]
    : CAPABILITY_AREAS;
  const dimensions = scores.length
    ? [...new Set(scores.map((s) => s.dimension))]
    : DIMENSIONS;

  const avgScore = scores.length
    ? scores.reduce((a, s) => a + s.score, 0) / scores.length
    : 0;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Olgunluk Matrisi</h1>
        <p style={{ color: "#94a3b8", fontSize: 14 }}>
          Yetenek alanı × Boyut ısı haritası
          {assessmentId && ` — ${assessmentId.slice(0, 8)}…`}
        </p>
      </div>

      {!assessmentId ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>📊</p>
          <p>Assessment seçilmedi. Genel Bakış'tan bir proje seçin.</p>
        </div>
      ) : loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : (
        <>
          {/* Summary stats */}
          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            {[
              { label: "Ortalama Skor", value: avgScore.toFixed(2), color: scoreColor(avgScore) },
              { label: "Değerlendirilen Alan", value: capabilities.length, color: "#60a5fa" },
              { label: "Boyut Sayısı", value: dimensions.length, color: "#a78bfa" },
              { label: "Toplam Ölçüm", value: scores.length, color: "#34d399" },
            ].map((s) => (
              <div key={s.label} style={{
                flex: 1, background: "#1e293b", border: "1px solid #334155",
                borderRadius: 8, padding: "12px 16px",
              }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Heat map table */}
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead>
                <tr>
                  <th style={{
                    padding: "8px 12px", fontSize: 12, color: "#64748b",
                    borderBottom: "1px solid #334155", textAlign: "left", minWidth: 160,
                  }}>
                    Yetenek Alanı
                  </th>
                  {dimensions.map((d) => (
                    <th key={d} style={{
                      padding: "8px 8px", fontSize: 11, color: "#94a3b8",
                      borderBottom: "1px solid #334155", textAlign: "center", width: 72,
                    }}>
                      {d}
                    </th>
                  ))}
                  <th style={{
                    padding: "8px 8px", fontSize: 11, color: "#94a3b8",
                    borderBottom: "1px solid #334155", textAlign: "center", width: 72,
                  }}>
                    Ort.
                  </th>
                </tr>
              </thead>
              <tbody>
                {capabilities.map((cap) => {
                  const row = lookup[cap] ?? {};
                  const rowScores = dimensions.map((d) => row[d]).filter((v) => v !== undefined) as number[];
                  const rowAvg = rowScores.length ? rowScores.reduce((a, b) => a + b, 0) / rowScores.length : undefined;
                  return (
                    <tr key={cap}>
                      <td style={{
                        padding: "8px 12px", fontSize: 12, color: "#e2e8f0",
                        borderBottom: "1px solid #1e293b",
                      }}>
                        {cap}
                      </td>
                      {dimensions.map((d) => (
                        <HeatCell key={d} score={row[d]} max={5} />
                      ))}
                      {rowAvg !== undefined
                        ? <HeatCell score={rowAvg} max={5} />
                        : <td style={{ textAlign: "center", fontSize: 11, color: "#475569" }}>—</td>
                      }
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div style={{ display: "flex", gap: 16, marginTop: 16, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#64748b" }}>Skor:</span>
            {[
              { label: "0–1 Başlangıç", color: "#dc2626" },
              { label: "1–2 Gelişmekte", color: "#ea580c" },
              { label: "2–3 Tanımlı", color: "#ca8a04" },
              { label: "3–4 Yönetilen", color: "#65a30d" },
              { label: "4–5 Optimize", color: "#16a34a" },
            ].map((l) => (
              <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <div style={{ width: 12, height: 12, borderRadius: 2, background: l.color }} />
                <span style={{ fontSize: 11, color: "#94a3b8" }}>{l.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
