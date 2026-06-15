// S4-FA-001: Risk Heatmap (severity × capability matrisi)
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getRiskHeatmap, type RiskHeatmapCell } from "../api";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
type Sev = (typeof SEVERITIES)[number];

const SEV_COLOR: Record<Sev, string> = {
  critical: "bg-red-700 text-white",
  high:     "bg-orange-500 text-white",
  medium:   "bg-yellow-400 text-gray-900",
  low:      "bg-blue-300 text-gray-900",
  info:     "bg-gray-200 text-gray-700",
};

export default function RiskHeatmap() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [cells, setCells] = useState<RiskHeatmapCell[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    getRiskHeatmap(assessmentId)
      .then(setCells)
      .catch(() => setCells([]))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  const areas = [...new Set(cells.map((c) => c.capability_area))].sort();
  const matrix: Record<string, Record<Sev, RiskHeatmapCell | undefined>> = {};
  for (const area of areas) {
    matrix[area] = {} as Record<Sev, RiskHeatmapCell | undefined>;
    for (const sev of SEVERITIES) {
      matrix[area][sev] = cells.find(
        (c) => c.capability_area === area && c.severity === sev
      );
    }
  }

  if (loading) return <p className="p-6 text-gray-500">Yükleniyor…</p>;
  if (!assessmentId)
    return <p className="p-6 text-red-500">assessment_id parametresi gerekli.</p>;

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Risk Heatmap</h1>
      {areas.length === 0 ? (
        <p className="text-gray-500">Henüz risk verisi yok.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-3 py-2 text-left">Capability Area</th>
                {SEVERITIES.map((s) => (
                  <th key={s} className="border px-3 py-2 capitalize">{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {areas.map((area) => (
                <tr key={area} className="hover:bg-gray-50">
                  <td className="border px-3 py-2 font-medium">{area}</td>
                  {SEVERITIES.map((sev) => {
                    const cell = matrix[area][sev];
                    return (
                      <td key={sev} className="border px-3 py-2 text-center">
                        {cell ? (
                          <span
                            title={`Workstreams: ${cell.workstreams.join(", ")}`}
                            className={`inline-block px-2 py-1 rounded font-bold ${SEV_COLOR[sev]}`}
                          >
                            {cell.risk_count}
                          </span>
                        ) : (
                          <span className="text-gray-300">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-gray-400">
            Hücredeki sayı o severity'deki risk adedi. Üzerine gelin → etkilenen workstream'ler.
          </p>
        </div>
      )}
    </div>
  );
}
