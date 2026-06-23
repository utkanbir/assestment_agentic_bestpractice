import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getTransaction, listTransactions, LayerTransaction, LayerTransactionDetail } from "../api";
import { RequireAssessment, useAssessment } from "../context/AssessmentContext";

function short(id: string): string {
  return `${id.slice(0, 8)}...`;
}

function ExecutionPlanInner() {
  const { assessmentId } = useAssessment();
  const [searchParams] = useSearchParams();
  const [transactions, setTransactions] = useState<LayerTransaction[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [selected, setSelected] = useState<LayerTransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTechnical, setShowTechnical] = useState(false);

  useEffect(() => {
    if (!assessmentId) return;
    setLoading(true);
    listTransactions(assessmentId)
      .then((res) => {
        setTransactions(res);
        const fromQuery = searchParams.get("transaction_id");
        if (fromQuery && res.some((tx) => tx.id === fromQuery)) {
          setSelectedId(fromQuery);
        } else if (res.length > 0) {
          setSelectedId((old) => old || res[0].id);
        }
      })
      .catch(() => setTransactions([]))
      .finally(() => setLoading(false));
  }, [assessmentId, searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    getTransaction(selectedId).then(setSelected).catch(() => setSelected(null));
  }, [selectedId]);

  if (loading) return <p style={{ color: "#64748b" }}>Transaction listesi yükleniyor…</p>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "380px 1fr", gap: 14 }}>
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, maxHeight: "72vh", overflow: "auto" }}>
        {transactions.length === 0 ? (
          <p style={{ padding: 14, color: "#64748b" }}>Henüz transaction kaydı yok.</p>
        ) : (
          transactions.map((tx) => (
            <button
              key={tx.id}
              type="button"
              onClick={() => setSelectedId(tx.id)}
              style={{
                width: "100%",
                textAlign: "left",
                border: "none",
                borderBottom: "1px solid #334155",
                background: tx.id === selectedId ? "#0f172a" : "transparent",
                color: "#e2e8f0",
                padding: "10px 12px",
                cursor: "pointer",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                <strong>{tx.operation}</strong>
                <span style={{ color: "#94a3b8" }}>{tx.total_duration_ms ?? "-"} ms</span>
              </div>
              <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
                {short(tx.id)} — {new Date(tx.started_at).toLocaleString("tr-TR")}
              </div>
            </button>
          ))
        )}
      </div>

      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 14 }}>
        {!selected ? (
          <p style={{ color: "#64748b" }}>Soldan bir transaction seçin.</p>
        ) : (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>{selected.operation}</h2>
            <p style={{ color: "#94a3b8", fontSize: 12 }}>
              Transaction: <code>{selected.id}</code> | Kaynak: {selected.source} | Süre:{" "}
              {selected.total_duration_ms ?? "-"} ms
            </p>

            <h3 style={{ fontSize: 14, marginTop: 14 }}>EXPLAIN PLAN</h3>
            <div
              data-testid="explain-narrative"
              style={{
                color: "#e2e8f0",
                fontSize: 14,
                lineHeight: 1.65,
                marginBottom: 16,
                padding: "12px 14px",
                background: "#0f1117",
                borderRadius: 8,
                border: "1px solid #334155",
              }}
            >
              {selected.narrative || "Bu işlem için anlatım üretilemedi."}
            </div>

            <button
              type="button"
              onClick={() => setShowTechnical((v) => !v)}
              style={{
                background: "transparent",
                border: "1px solid #334155",
                borderRadius: 6,
                color: "#94a3b8",
                padding: "6px 10px",
                fontSize: 12,
                cursor: "pointer",
                marginBottom: 10,
              }}
            >
              {showTechnical ? "Teknik adımları gizle" : "Teknik adımları göster"}
            </button>

            {showTechnical && (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#0f1117", fontSize: 12, color: "#94a3b8" }}>
                    <th style={{ padding: "8px 10px", textAlign: "left" }}>Step</th>
                    <th style={{ padding: "8px 10px", textAlign: "left" }}>Layer</th>
                    <th style={{ padding: "8px 10px", textAlign: "left" }}>Technology</th>
                    <th style={{ padding: "8px 10px", textAlign: "left" }}>Action</th>
                    <th style={{ padding: "8px 10px", textAlign: "left" }}>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.steps.map((step) => (
                    <tr key={step.id} style={{ borderTop: "1px solid #334155", fontSize: 12 }}>
                      <td style={{ padding: "8px 10px" }}>{step.step_order ?? "-"}</td>
                      <td style={{ padding: "8px 10px" }}>{step.layer}</td>
                      <td style={{ padding: "8px 10px" }}>{step.technology}</td>
                      <td style={{ padding: "8px 10px" }}>{step.action}</td>
                      <td style={{ padding: "8px 10px" }}>{step.duration_ms ?? "-"} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ExecutionPlan() {
  return (
    <RequireAssessment>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <h1 style={{ marginTop: 0 }}>Yürütme Planı</h1>
        <p style={{ color: "#94a3b8", fontSize: 13 }}>
          Her işlemin katman bazlı adımlarını cümle bazlı anlatımla izleyin.
        </p>
        <ExecutionPlanInner />
      </div>
    </RequireAssessment>
  );
}
