// S4-FA-003: Consolidated Roadmap görünümü (horizon bazlı)
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getConsolidatedRoadmap, type RoadmapItem } from "../api";

const HORIZON_LABELS: Record<string, string> = {
  short:  "Kısa Vade (0-3 ay)",
  medium: "Orta Vade (3-12 ay)",
  long:   "Uzun Vade (12+ ay)",
};

const HORIZON_COLOR: Record<string, string> = {
  short:  "border-red-400 bg-red-50",
  medium: "border-yellow-400 bg-yellow-50",
  long:   "border-blue-400 bg-blue-50",
};

export default function ConsolidatedRoadmap() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterHorizon, setFilterHorizon] = useState<string>("all");

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    getConsolidatedRoadmap(assessmentId)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  if (loading) return <p className="p-6 text-gray-500">Yükleniyor…</p>;
  if (!assessmentId)
    return <p className="p-6 text-red-500">assessment_id parametresi gerekli.</p>;

  const horizons = ["short", "medium", "long"] as const;
  const filtered = filterHorizon === "all" ? items : items.filter((i) => i.horizon === filterHorizon);

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Konsolide Roadmap</h1>

      {/* Horizon filter tabs */}
      <div className="flex gap-2 mb-6">
        {["all", ...horizons].map((h) => (
          <button
            key={h}
            onClick={() => setFilterHorizon(h)}
            className={`px-3 py-1 rounded text-sm border ${
              filterHorizon === h ? "bg-gray-800 text-white border-gray-800" : "border-gray-300 text-gray-700"
            }`}
          >
            {h === "all" ? "Tümü" : HORIZON_LABELS[h]}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-gray-500">
          {items.length === 0
            ? "Orchestrator henüz roadmap üretmedi."
            : "Bu horizon için item yok."}
        </p>
      ) : (
        <div className="space-y-3">
          {filtered.map((item, idx) => (
            <div
              key={item.id ?? idx}
              className={`border-l-4 rounded p-4 ${HORIZON_COLOR[item.horizon] ?? ""}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold px-2 py-0.5 bg-white border rounded">
                      P{item.priority}
                    </span>
                    <span className="text-xs text-gray-500">{HORIZON_LABELS[item.horizon]}</span>
                    {item.addresses_conflict && (
                      <span className="text-xs px-2 py-0.5 bg-yellow-200 text-yellow-800 rounded">
                        Çelişki çözümü
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-gray-800">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.workstreams.map((ws) => (
                      <span key={ws} className="text-xs px-2 py-0.5 bg-white border rounded text-gray-600">
                        {ws}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-gray-500">Efor</p>
                  <p className="text-sm font-medium text-gray-700">{item.effort || "—"}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
