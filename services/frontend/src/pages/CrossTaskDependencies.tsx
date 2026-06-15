// S4-FA-004: Cross-task dependency panel
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getCrossTaskDependencies, type Dependency } from "../api";

export default function CrossTaskDependencies() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [deps, setDeps] = useState<Dependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "conflicts">("all");

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    getCrossTaskDependencies(assessmentId)
      .then(setDeps)
      .catch(() => setDeps([]))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  if (loading) return <p className="p-6 text-gray-500">Yükleniyor…</p>;
  if (!assessmentId)
    return <p className="p-6 text-red-500">assessment_id parametresi gerekli.</p>;

  const conflicts = deps.filter((d) => d.conflict_signal?.startsWith("SEVERITY_CONFLICT"));
  const displayed = filter === "conflicts" ? conflicts : deps;

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-2">Cross-Task Bağımlılıklar</h1>
      <p className="text-sm text-gray-500 mb-4">
        {deps.length} bağımlılık — {conflicts.length} çelişki (human review gerekiyor)
      </p>

      <div className="flex gap-2 mb-4">
        {(["all", "conflicts"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm border ${
              filter === f ? "bg-gray-800 text-white border-gray-800" : "border-gray-300"
            }`}
          >
            {f === "all" ? "Tümü" : `Çelişkiler (${conflicts.length})`}
          </button>
        ))}
      </div>

      {displayed.length === 0 ? (
        <p className="text-gray-500">
          {deps.length === 0 ? "Orchestrator henüz analiz yapmadı." : "Çelişki bulunamadı."}
        </p>
      ) : (
        <div className="space-y-2">
          {displayed.map((dep, idx) => {
            const isConflict = dep.conflict_signal?.startsWith("SEVERITY_CONFLICT");
            return (
              <div
                key={idx}
                className={`rounded border p-4 ${
                  isConflict ? "border-red-400 bg-red-50" : "border-gray-200 bg-white"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-gray-800">{dep.workstream_a}</span>
                  <span className="text-gray-400">→</span>
                  <span className="font-semibold text-gray-800">{dep.workstream_b}</span>
                  <span className="text-xs text-gray-500 ml-2">
                    [{dep.dependency_type}]
                  </span>
                  {isConflict && (
                    <span className="ml-auto text-xs px-2 py-0.5 bg-red-200 text-red-800 rounded font-bold">
                      ÇELIŞKI
                    </span>
                  )}
                </div>
                {dep.shared_capability_area && (
                  <p className="mt-1 text-sm text-gray-600">
                    Paylaşılan alan: <strong>{dep.shared_capability_area}</strong>
                  </p>
                )}
                {dep.conflict_signal && (
                  <p className="mt-1 text-xs text-red-700">{dep.conflict_signal}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
