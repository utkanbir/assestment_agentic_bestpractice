import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, RefreshCw, X, AlertCircle, Loader2, BarChart2 } from "lucide-react";
import { api } from "../api/client";
import type { RiskHeatmapCell } from "../api/types";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
type Severity = (typeof SEVERITIES)[number];

const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "Kritik",
  high: "Yüksek",
  medium: "Orta",
  low: "Düşük",
  info: "Bilgi",
};

// Cell background colours (filled cell)
const CELL_BG: Record<Severity, string> = {
  critical: "bg-red-500 text-white",
  high: "bg-orange-400 text-white",
  medium: "bg-yellow-400 text-gray-900",
  low: "bg-green-400 text-white",
  info: "bg-gray-300 text-gray-700",
};

// Badge colours for header row
const HEADER_BADGE: Record<Severity, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-green-700",
  info: "bg-gray-100 text-gray-600",
};

interface SelectedCell {
  cell: RiskHeatmapCell;
}

export function RiskHeatmapPage() {
  const { id } = useParams<{ id: string }>();

  const [assessmentName, setAssessmentName] = useState<string | null>(null);
  const [cells, setCells] = useState<RiskHeatmapCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SelectedCell | null>(null);

  const loadData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    try {
      const [assessment, heatmap] = await Promise.all([
        api.assessments.get(id),
        api.orchestrator.getRiskHeatmap(id),
      ]);
      setAssessmentName(`${assessment.project_name} — ${assessment.client_name}`);
      setCells(heatmap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Veri yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Build lookup: capability_area -> severity -> cell
  const lookup = new Map<string, Map<string, RiskHeatmapCell>>();
  const capabilityAreas: string[] = [];
  for (const cell of cells) {
    if (!lookup.has(cell.capability_area)) {
      lookup.set(cell.capability_area, new Map());
      capabilityAreas.push(cell.capability_area);
    }
    lookup.get(cell.capability_area)!.set(cell.severity, cell);
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-400 text-sm py-8">
        <Loader2 size={16} className="animate-spin" />
        Yükleniyor...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-red-700 text-sm flex items-center gap-2">
        <AlertCircle size={16} />
        {error}
      </div>
    );
  }

  return (
    <div>
      {/* Back link */}
      <Link
        to={`/assessments/${id}`}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeft size={14} /> Geri
      </Link>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl px-6 py-5 mb-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Risk Heatmap</h1>
            {assessmentName && (
              <p className="text-sm text-gray-500 mt-0.5">{assessmentName}</p>
            )}
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 hover:border-gray-400 rounded-lg px-3 py-2 transition-colors"
          >
            <RefreshCw size={13} />
            Yenile
          </button>
        </div>
      </div>

      {/* Empty state */}
      {capabilityAreas.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <BarChart2 size={36} className="mx-auto mb-3 text-gray-300" />
          <p className="text-sm font-medium">Henüz risk verisi yok.</p>
          <p className="text-xs mt-1">
            Interview yapılıp finding oluşturulduktan sonra heatmap görünür.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider min-w-[160px]">
                    Workstream
                  </th>
                  {SEVERITIES.map((sev) => (
                    <th key={sev} className="px-4 py-3 text-center">
                      <span
                        className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${HEADER_BADGE[sev]}`}
                      >
                        {SEVERITY_LABELS[sev]}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {capabilityAreas.map((area, idx) => (
                  <tr
                    key={area}
                    className={idx % 2 === 0 ? "bg-white" : "bg-gray-50"}
                  >
                    <td className="px-4 py-3 font-medium text-gray-800 border-b border-gray-100">
                      {area}
                    </td>
                    {SEVERITIES.map((sev) => {
                      const cell = lookup.get(area)?.get(sev);
                      return (
                        <td
                          key={sev}
                          className="px-4 py-3 text-center border-b border-gray-100"
                        >
                          {cell ? (
                            <button
                              onClick={() => setSelected({ cell })}
                              className={`inline-flex items-center justify-center w-9 h-9 rounded-lg font-bold text-sm cursor-pointer hover:opacity-80 transition-opacity ${CELL_BG[sev as Severity]}`}
                              title={`${area} / ${SEVERITY_LABELS[sev as Severity]}: ${cell.risk_count} risk`}
                            >
                              {cell.risk_count}
                            </button>
                          ) : (
                            <span className="text-gray-300 text-base">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail panel / modal */}
      {selected && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-start justify-between mb-5">
              <div>
                <h2 className="font-semibold text-gray-900 text-base">
                  {selected.cell.capability_area}
                </h2>
                <span
                  className={`mt-1 inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${HEADER_BADGE[selected.cell.severity as Severity] ?? "bg-gray-100 text-gray-600"}`}
                >
                  {SEVERITY_LABELS[selected.cell.severity as Severity] ?? selected.cell.severity}
                </span>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="text-gray-400 hover:text-gray-700 transition-colors ml-4"
                aria-label="Kapat"
              >
                <X size={20} />
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-gray-50 rounded-xl px-4 py-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Risk Sayısı</p>
                <p className="text-2xl font-bold text-gray-900">{selected.cell.risk_count}</p>
              </div>
              <div className="bg-gray-50 rounded-xl px-4 py-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Maks. Güven</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(selected.cell.max_confidence * 100)}%
                </p>
              </div>
            </div>

            {/* Workstreams */}
            {selected.cell.workstreams.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  İlgili Workstream'ler
                </p>
                <ul className="space-y-1.5">
                  {selected.cell.workstreams.map((ws) => (
                    <li
                      key={ws}
                      className="flex items-center gap-2 text-sm text-gray-700"
                    >
                      <span className="w-2 h-2 rounded-full bg-brand-600 shrink-0" />
                      {ws}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Close button */}
            <button
              onClick={() => setSelected(null)}
              className="mt-6 w-full border border-gray-300 hover:border-gray-400 text-sm font-medium text-gray-600 hover:text-gray-800 rounded-lg py-2 transition-colors"
            >
              Kapat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
