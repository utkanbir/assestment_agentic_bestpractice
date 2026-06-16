// S7-FA-005: Report export — PDF üretimi (browser print API)
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchJSON } from "../api";

interface Report {
  id: string;
  assessment_id: string;
  title: string;
  executive_summary: string | null;
  created_at: string;
}

interface RoadmapItem {
  id: string;
  title: string;
  horizon: string;
  priority: number;
  effort?: string;
}

const HORIZON_LABEL: Record<string, string> = {
  short: "Kısa Vade (0–6 ay)",
  medium: "Orta Vade (6–18 ay)",
  long: "Uzun Vade (18+ ay)",
};

export default function ReportExport() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const [report, setReport] = useState<Report | null>(null);
  const [roadmap, setRoadmap] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);
  const printRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    Promise.all([
      fetchJSON<Report[]>(`/reports?assessment_id=${assessmentId}`).then((rs) => setReport(rs[0] ?? null)),
      fetchJSON<RoadmapItem[]>(`/orchestrator/${assessmentId}/roadmap`).then(setRoadmap).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [assessmentId]);

  const exportPDF = () => {
    const content = printRef.current;
    if (!content) return;
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>AAKP Raporu — ${report?.title ?? assessmentId}</title>
        <style>
          body { font-family: Arial, sans-serif; color: #1e293b; margin: 40px; line-height: 1.6; }
          h1 { font-size: 24px; color: #1d4ed8; margin-bottom: 4px; }
          h2 { font-size: 18px; color: #334155; margin-top: 28px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }
          .meta { color: #64748b; font-size: 13px; margin-bottom: 20px; }
          .summary { background: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; font-size: 14px; }
          table { width: 100%; border-collapse: collapse; margin-top: 12px; }
          th { background: #f1f5f9; padding: 8px 12px; text-align: left; font-size: 12px; }
          td { padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
          .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 700; }
          .short { background: #dcfce7; color: #166534; }
          .medium { background: #fef9c3; color: #854d0e; }
          .long { background: #dbeafe; color: #1d4ed8; }
          @media print { body { margin: 0; } }
        </style>
      </head>
      <body>${content.innerHTML}</body>
      </html>
    `);
    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); win.close(); }, 500);
  };

  const groupedRoadmap = roadmap.reduce<Record<string, RoadmapItem[]>>((acc, item) => {
    if (!acc[item.horizon]) acc[item.horizon] = [];
    acc[item.horizon].push(item);
    return acc;
  }, {});

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Rapor Dışa Aktarma</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            PDF olarak indirmek için Dışa Aktar düğmesine basın.
          </p>
        </div>
        <button
          onClick={exportPDF}
          disabled={!report || loading}
          style={{
            background: "#3b82f6", border: "none", borderRadius: 8,
            padding: "10px 20px", color: "#fff", cursor: "pointer",
            fontSize: 14, fontWeight: 700,
            opacity: !report || loading ? 0.5 : 1,
          }}
        >
          PDF Dışa Aktar
        </button>
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : !report ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>📄</p>
          <p>Bu assessment için henüz rapor üretilmedi.</p>
        </div>
      ) : (
        /* Print-ready content */
        <div ref={printRef} style={{ background: "#fff", color: "#1e293b", borderRadius: 10, padding: 32, border: "1px solid #e2e8f0" }}>
          <h1 style={{ fontSize: 26, color: "#1d4ed8", marginBottom: 4 }}>{report.title}</h1>
          <p className="meta" style={{ color: "#64748b", fontSize: 13, marginBottom: 20 }}>
            Assessment ID: {report.assessment_id} &nbsp;|&nbsp;
            Oluşturulma: {new Date(report.created_at).toLocaleDateString("tr-TR")}
          </p>

          {report.executive_summary && (
            <>
              <h2 style={{ fontSize: 18, color: "#334155", marginTop: 24, borderBottom: "1px solid #e2e8f0", paddingBottom: 6 }}>
                Yönetici Özeti
              </h2>
              <div style={{ background: "#f8fafc", borderLeft: "4px solid #3b82f6", padding: 16, borderRadius: 4, fontSize: 14, marginTop: 12 }}>
                {report.executive_summary}
              </div>
            </>
          )}

          {roadmap.length > 0 && (
            <>
              <h2 style={{ fontSize: 18, color: "#334155", marginTop: 28, borderBottom: "1px solid #e2e8f0", paddingBottom: 6 }}>
                Konsolide Yol Haritası
              </h2>
              {Object.entries(groupedRoadmap).map(([horizon, items]) => (
                <div key={horizon} style={{ marginTop: 16 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#475569", marginBottom: 8 }}>
                    {HORIZON_LABEL[horizon] ?? horizon}
                  </h3>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ background: "#f1f5f9" }}>
                        <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12 }}>Öneri</th>
                        <th style={{ padding: "8px 12px", textAlign: "center", fontSize: 12, width: 80 }}>Öncelik</th>
                        <th style={{ padding: "8px 12px", textAlign: "center", fontSize: 12, width: 100 }}>Çaba</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <tr key={item.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                          <td style={{ padding: "8px 12px", fontSize: 13 }}>{item.title}</td>
                          <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "center" }}>P{item.priority}</td>
                          <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "center", color: "#64748b" }}>{item.effort ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </>
          )}

          <div style={{ marginTop: 32, paddingTop: 16, borderTop: "1px solid #e2e8f0", fontSize: 11, color: "#94a3b8" }}>
            AAKP — AI Assessment Knowledge Platform | Migros Ticaret A.Ş.
          </div>
        </div>
      )}
    </div>
  );
}
