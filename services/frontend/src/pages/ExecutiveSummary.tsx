// S17: Yönetici Özeti — assessment değerlendirme dashboard
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getExecutiveSummary, generateExecutiveSummary, ApiError, type ExecutiveSummary } from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444", high: "#f97316", medium: "#eab308", low: "#22c55e", info: "#60a5fa",
};

export default function ExecutiveSummaryPage() {
  const { assessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const load = () => {
    if (!assessmentId) return;
    setLoading(true);
    getExecutiveSummary(assessmentId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [assessmentId]);

  const handleGenerate = async () => {
    if (!assessmentId || generating) return;
    setGenerating(true);
    setGenError(null);
    try {
      setData(await generateExecutiveSummary(assessmentId));
    } catch (e: unknown) {
      if (e instanceof ApiError) setGenError(e.message);
      else setGenError(e instanceof Error ? e.message : "Özet üretilemedi.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadTxt = () => {
    if (!data?.summary) return;
    const blob = new Blob([data.summary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `yonetici-ozeti-${assessmentId.slice(0, 8)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Yönetici Özeti"
        subtitle="Assessment değerlendirme özeti ve karar desteği"
        actions={
          <div style={{ display: "flex", gap: 8 }}>
            {data?.summary && (
              <button
                data-testid="export-summary-txt"
                onClick={handleDownloadTxt}
                style={{
                  background: "#334155", border: "none", borderRadius: 8, padding: "8px 18px",
                  color: "#e2e8f0", cursor: "pointer", fontWeight: 600, fontSize: 13,
                }}
              >
                .txt İndir
              </button>
            )}
            <button
            onClick={handleGenerate}
            disabled={generating || loading}
            style={{
              background: generating ? "#334155" : "#3b82f6",
              border: "none", borderRadius: 8, padding: "8px 18px",
              color: "#fff", cursor: generating ? "not-allowed" : "pointer", fontWeight: 700, fontSize: 13,
            }}
          >
            {generating ? "Üretiliyor…" : data?.summary ? "Yeniden Üret" : "Özet Oluştur"}
          </button>
          </div>
        }
      />

      {genError && (
        <div style={{ background: "#7f1d1d33", border: "1px solid #ef4444", borderRadius: 8, padding: 12, color: "#fca5a5", marginBottom: 16, fontSize: 13 }}>
          {genError}
        </div>
      )}

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
      ) : !data ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p>Dashboard verisi yüklenemedi.</p>
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10, marginBottom: 20 }}>
            {[
              { label: "Toplam Bulgu", value: data.total_risks, color: "#f87171" },
              { label: "Kritik", value: data.critical_count, color: "#ef4444" },
              { label: "Yüksek", value: data.high_count, color: "#f97316" },
              { label: "Olgunluk Ort.", value: data.avg_maturity?.toFixed(1) ?? "—", color: "#60a5fa" },
              { label: "Onay Bekleyen", value: data.pending_approvals, color: "#eab308" },
              { label: "Task Tamamlanma", value: `${data.tasks_completed}/${data.tasks_total}`, color: "#22c55e" },
              { label: "Bağımlılık", value: data.dependency_count, color: "#fb923c" },
              { label: "Çelişki", value: data.conflict_count, color: "#facc15" },
            ].map((s) => (
              <div key={s.label} style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 12, textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>

          {data.summary ? (
            <div style={{
              background: "#0f172a", border: "1px solid #3b82f644", borderLeft: "4px solid #3b82f6",
              borderRadius: 8, padding: 20, marginBottom: 20, whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.7,
            }}>
              {data.summary}
              {data.generated_at && (
                <p style={{ marginTop: 12, fontSize: 11, color: "#475569" }}>
                  Üretilme: {new Date(data.generated_at).toLocaleString("tr-TR")}
                </p>
              )}
            </div>
          ) : (
            <p style={{ color: "#64748b", fontSize: 13, marginBottom: 20 }}>
              LLM özeti henüz oluşturulmadı. Finding verisi varsa &quot;Özet Oluştur&quot; butonuna basın.
            </p>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
            <section>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Top 5 Kritik Bulgu</h2>
              {data.top_risks.length === 0 ? (
                <p style={{ color: "#64748b", fontSize: 13 }}>Bulgu yok.</p>
              ) : (
                data.top_risks.map((r) => (
                  <div key={r.id} style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 6, padding: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 10, color: SEV_COLOR[r.severity] ?? "#94a3b8", fontWeight: 700 }}>{r.severity.toUpperCase()}</span>
                    <span style={{ fontSize: 10, color: "#64748b", marginLeft: 8 }}>{r.workstream}</span>
                    <p style={{ margin: "6px 0 0", fontSize: 12 }}>{r.description}</p>
                  </div>
                ))
              )}
            </section>

            <section>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Workstream Özeti</h2>
              <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ color: "#64748b", textAlign: "left" }}>
                    <th style={thStyle}>WS</th>
                    <th style={thStyle}>Olgunluk</th>
                    <th style={thStyle}>Bulgu</th>
                    <th style={thStyle}>Durum</th>
                  </tr>
                </thead>
                <tbody>
                  {data.workstream_summaries.map((ws) => (
                    <tr key={ws.workstream} style={{ borderTop: "1px solid #334155" }}>
                      <td style={tdStyle}>{ws.workstream}</td>
                      <td style={tdStyle}>{ws.maturity_score?.toFixed(1) ?? "—"}</td>
                      <td style={tdStyle}>{ws.finding_count}</td>
                      <td style={tdStyle}>{ws.task_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>

          <section>
            <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Öne Çıkan Öneriler</h2>
            {data.top_recommendations.length === 0 ? (
              <p style={{ color: "#64748b", fontSize: 13 }}>
                Onaylı öneri yok. <Link to={withAssessment("/approvals")} style={{ color: "#60a5fa" }}>İnceleme Merkezi</Link>
              </p>
            ) : (
              data.top_recommendations.map((r) => (
                <div key={r.id} style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 6, padding: 10, marginBottom: 8 }}>
                  <strong style={{ fontSize: 13 }}>P{r.priority} — {r.title}</strong>
                  <p style={{ margin: "4px 0 0", fontSize: 12, color: "#94a3b8" }}>{r.description}</p>
                </div>
              ))
            )}
          </section>
        </>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = { padding: "6px 8px" };
const tdStyle: React.CSSProperties = { padding: "6px 8px" };
