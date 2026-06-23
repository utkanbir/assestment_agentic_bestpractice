import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  WORKSTREAMS,
  downloadAgentKgProtegeExport,
  getAgentKgStats,
  type AgentKgStats,
} from "../api";
import { RequireAssessment, useAssessmentNavLink } from "../context/AssessmentContext";

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div style={{
      background: "#0f1117", border: "1px solid #334155", borderRadius: 10,
      padding: "14px 16px", minWidth: 130, flex: "1 1 150px",
    }}>
      <p style={{ fontSize: 10, color: "#64748b", margin: "0 0 6px", textTransform: "uppercase", letterSpacing: 0.4 }}>
        {label}
      </p>
      <p style={{ fontSize: 26, fontWeight: 800, margin: 0, color: "#e2e8f0" }}>{value}</p>
      {hint && <p style={{ fontSize: 10, color: "#475569", margin: "6px 0 0" }}>{hint}</p>}
    </div>
  );
}

const WS_LABEL: Record<string, string> = Object.fromEntries(WORKSTREAMS.map((w) => [w.id, w.label]));

function KnowledgeGraphDashboard() {
  const withAssessment = useAssessmentNavLink();
  const [stats, setStats] = useState<AgentKgStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    getAgentKgStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    try {
      await downloadAgentKgProtegeExport();
    } catch {
      setExportError("Export başarısız — Fuseki bağlantısını kontrol edin.");
    } finally {
      setExporting(false);
    }
  };

  const t = stats?.totals;
  const pg = stats?.postgres;
  const collected = stats?.collected_at
    ? new Date(stats.collected_at).toLocaleString("tr-TR")
    : "—";

  return (
    <div data-testid="knowledge-graph-dashboard" style={{ maxWidth: 1140, margin: "0 auto" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: "0 0 6px", fontSize: 22 }}>Knowledge Graph</h1>
          <p style={{ margin: 0, color: "#94a3b8", fontSize: 13, lineHeight: 1.5 }}>
            Fuseki&apos;deki tüm veri — interview cevapları, AI yorumları, agent eğitimi, bulgular.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Link to={withAssessment("/kg-graf")} style={{ ...btnStyle("#334155"), textDecoration: "none", display: "inline-block" }}>
            KG Graf
          </Link>
          <button type="button" onClick={load} disabled={loading} style={btnStyle("#334155")}>
            Yenile
          </button>
          <button
            type="button"
            data-testid="kg-protege-download"
            onClick={handleExport}
            disabled={exporting}
            style={btnStyle("#6366f1")}
          >
            {exporting ? "Hazırlanıyor…" : "Protege için indir (.ttl)"}
          </button>
        </div>
      </div>

      {exportError && <p style={{ color: "#fbbf24", fontSize: 12, margin: "0 0 12px" }}>{exportError}</p>}

      <p style={{ fontSize: 11, color: "#64748b", margin: "0 0 16px" }}>
        Son ölçüm: {collected}{stats?.source ? ` · kaynak: ${stats.source}` : ""}
      </p>

      {loading && <p style={{ color: "#64748b" }}>İstatistikler yükleniyor…</p>}

      {!loading && stats && (
        <>
          <h2 style={{ fontSize: 14, color: "#a78bfa", margin: "0 0 10px" }}>Genel</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 24 }}>
            <StatCard label="Individuals" value={t?.individuals ?? 0} hint="Tüm RDF bireyleri" />
            <StatCard label="Toplam triple" value={t?.triples_total ?? 0} />
            <StatCard label="Triple (assessment)" value={t?.triples_assessment_graph ?? 0} />
            <StatCard label="Triple (agents)" value={t?.triples_agents_graph ?? 0} />
            <StatCard label="Ontoloji sınıfı" value={t?.ontology_classes ?? 0} hint="TBox" />
          </div>

          <h2 style={{ fontSize: 14, color: "#60a5fa", margin: "0 0 10px" }}>Assessment & Interview</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 24 }}>
            <StatCard label="Assessment" value={t?.assessments ?? 0} />
            <StatCard label="Task" value={t?.tasks ?? 0} />
            <StatCard label="Interview" value={t?.interviews ?? 0} />
            <StatCard label="Question" value={t?.questions ?? 0} />
            <StatCard label="Answer" value={t?.answers ?? 0} hint="Müşteri yanıtları" />
            <StatCard label="Evaluation" value={t?.evaluations ?? 0} hint="AI yorumları" />
            <StatCard label="Finding" value={t?.findings ?? 0} />
            <StatCard label="Consultant" value={t?.consultants ?? 0} />
            <StatCard label="Evidence" value={t?.evidence ?? 0} />
          </div>

          <h2 style={{ fontSize: 14, color: "#34d399", margin: "0 0 10px" }}>Agent eğitimi</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 24 }}>
            <StatCard label="AssessmentAgent" value={t?.assessment_agents ?? 0} />
            <StatCard label="TrainingInteraction" value={t?.training_interactions ?? 0} />
            <StatCard label="AgentKnowledge" value={t?.agent_knowledge ?? 0} />
            <StatCard label="Concept bağları" value={t?.concept_links ?? 0} />
          </div>

          <h2 style={{ fontSize: 14, color: "#94a3b8", margin: "0 0 10px" }}>PostgreSQL (karşılaştırma)</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 24 }}>
            <StatCard label="Soru (PG)" value={pg?.questions ?? 0} />
            <StatCard label="Cevap (PG)" value={pg?.answers ?? 0} />
            <StatCard label="AI yorum (PG)" value={pg?.evaluations ?? 0} />
            <StatCard label="Learning event" value={pg?.learning_events ?? 0} />
            <StatCard label="AAHA" value={pg?.aaha_count ?? 0} />
            <StatCard label="Döküman" value={pg?.document_count ?? 0} />
          </div>

          <h2 style={{ fontSize: 14, color: "#94a3b8", margin: "0 0 10px" }}>Workstream kırılımı</h2>
          <div style={{ border: "1px solid #334155", borderRadius: 10, overflow: "auto", marginBottom: 16 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, minWidth: 520 }}>
              <thead>
                <tr style={{ background: "#1e293b", color: "#94a3b8" }}>
                  <th style={thStyle}>Workstream</th>
                  <th style={thStyle}>Soru</th>
                  <th style={thStyle}>Cevap</th>
                  <th style={thStyle}>Training</th>
                  <th style={thStyle}>Knowledge</th>
                </tr>
              </thead>
              <tbody>
                {stats.by_workstream.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                      Henüz workstream verisi yok.
                    </td>
                  </tr>
                )}
                {stats.by_workstream.map((row) => (
                  <tr key={row.workstream} style={{ borderTop: "1px solid #1e293b" }}>
                    <td style={tdStyle}>{WS_LABEL[row.workstream] ?? row.workstream}</td>
                    <td style={tdStyle}>{row.question_count}</td>
                    <td style={tdStyle}>{row.answer_count}</td>
                    <td style={tdStyle}>{row.training_count}</td>
                    <td style={tdStyle}>{row.knowledge_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function btnStyle(bg: string): React.CSSProperties {
  return {
    padding: "8px 14px", borderRadius: 8, border: "none", fontSize: 12,
    fontWeight: 600, cursor: "pointer", background: bg, color: "#fff",
  };
}

const thStyle: React.CSSProperties = { padding: "10px 12px", textAlign: "left" };
const tdStyle: React.CSSProperties = { padding: "10px 12px", color: "#cbd5e1" };

export default function AgentKnowledgeGraphPage() {
  return (
    <RequireAssessment>
      <KnowledgeGraphDashboard />
    </RequireAssessment>
  );
}
