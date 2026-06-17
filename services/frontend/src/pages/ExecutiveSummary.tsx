// S4-FA-002 / S9-FA-003: Executive Summary sayfası + LLM üretme butonu
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getExecutiveSummary, generateExecutiveSummary, type ExecutiveSummary } from "../api";

const S = {
  wrap: { maxWidth: 800, margin: "0 auto" } as React.CSSProperties,
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 } as React.CSSProperties,
  title: { fontSize: 24, fontWeight: 700, marginBottom: 4 } as React.CSSProperties,
  sub: { color: "#94a3b8", fontSize: 14 } as React.CSSProperties,
  genBtn: (disabled: boolean): React.CSSProperties => ({
    background: disabled ? "#1e293b" : "#3b82f6",
    border: "none", borderRadius: 8, padding: "10px 20px",
    color: disabled ? "#64748b" : "#fff", cursor: disabled ? "not-allowed" : "pointer",
    fontSize: 14, fontWeight: 700, whiteSpace: "nowrap",
  }),
  errBox: { background: "#7f1d1d33", border: "1px solid #ef4444", borderRadius: 8, padding: "10px 14px", color: "#fca5a5", fontSize: 13, marginBottom: 16 } as React.CSSProperties,
  statsRow: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 } as React.CSSProperties,
  statCard: { background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "12px 16px", textAlign: "center" as const },
  summaryBox: { background: "#0f172a", border: "1px solid #3b82f644", borderLeft: "4px solid #3b82f6", borderRadius: 8, padding: 24, whiteSpace: "pre-wrap" as const, fontSize: 14, lineHeight: 1.7, color: "#e2e8f0" } as React.CSSProperties,
  meta: { marginTop: 10, fontSize: 11, color: "#475569" } as React.CSSProperties,
  emptyBox: { textAlign: "center" as const, padding: 60, color: "#64748b" },
};

export default function ExecutiveSummaryPage() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    getExecutiveSummary(assessmentId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  const handleGenerate = async () => {
    if (!assessmentId || generating) return;
    setGenerating(true);
    setGenError(null);
    try {
      const result = await generateExecutiveSummary(assessmentId);
      setData(result);
    } catch (e: any) {
      setGenError(e?.message ?? "Özet üretilemedi. Finding verisi olmayabilir.");
    } finally {
      setGenerating(false);
    }
  };

  if (!assessmentId)
    return <div style={S.wrap}><p style={{ color: "#ef4444", padding: 20 }}>assessment_id parametresi gerekli (?assessment_id=...)</p></div>;

  return (
    <div style={S.wrap}>
      <div style={S.header}>
        <div>
          <h1 style={S.title}>Executive Summary</h1>
          <p style={S.sub}>{assessmentId.slice(0, 8)}…</p>
        </div>
        <button onClick={handleGenerate} disabled={generating || loading} style={S.genBtn(generating || loading)}>
          {generating ? "⏳ Üretiliyor…" : data ? "🔄 Yeniden Üret" : "✨ Özet Oluştur"}
        </button>
      </div>

      {genError && <div style={S.errBox}>{genError}</div>}

      {loading ? (
        <p style={{ color: "#64748b", padding: 40, textAlign: "center" }}>Yükleniyor…</p>
      ) : !data ? (
        <div style={S.emptyBox}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>📄</p>
          <p>Henüz özet oluşturulmadı.</p>
          <p style={{ fontSize: 13, color: "#475569", marginTop: 8 }}>Finding'ler oluşturulup onaylandıktan sonra "Özet Oluştur" butonuna basın.</p>
        </div>
      ) : (
        <>
          <div style={S.statsRow}>
            {[
              { label: "Toplam Bulgu", value: data.total_risks, color: "#f87171" },
              { label: "Kritik", value: data.critical_count, color: "#ef4444" },
              { label: "Bağımlılık", value: data.dependency_count, color: "#fb923c" },
              { label: "Çelişki", value: data.conflict_count, color: "#facc15" },
            ].map((s) => (
              <div key={s.label} style={S.statCard}>
                <div style={{ fontSize: 26, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>

          <div style={S.summaryBox}>{data.summary}</div>

          <p style={S.meta}>
            Üretilme: {new Date(data.generated_at).toLocaleString("tr-TR")}
          </p>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-gray-50 border rounded p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}
