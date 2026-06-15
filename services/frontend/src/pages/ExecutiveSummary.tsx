// S4-FA-002: Executive Summary sayfası
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getExecutiveSummary, type ExecutiveSummary } from "../api";

export default function ExecutiveSummaryPage() {
  const [params] = useSearchParams();
  const assessmentId = params.get("assessment_id") ?? "";
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) { setLoading(false); return; }
    getExecutiveSummary(assessmentId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  if (loading) return <p className="p-6 text-gray-500">Yükleniyor…</p>;
  if (!assessmentId)
    return <p className="p-6 text-red-500">assessment_id parametresi gerekli.</p>;

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-xl font-bold mb-4">Executive Summary</h1>

      {!data ? (
        <p className="text-gray-500">
          Orchestrator henüz bu assessment için summary üretmedi.
          Tüm workstream interview'ları tamamlandığında otomatik oluşturulacak.
        </p>
      ) : (
        <>
          {/* Stats bar */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <StatCard label="Toplam Risk" value={data.total_risks} color="text-red-600" />
            <StatCard label="Critical Risk" value={data.critical_count} color="text-red-800 font-bold" />
            <StatCard label="Bağımlılık" value={data.dependency_count} color="text-orange-600" />
            <StatCard label="Çelişki" value={data.conflict_count} color="text-yellow-700" />
          </div>

          {/* Summary text */}
          <div className="bg-white border rounded-lg p-6 whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
            {data.summary}
          </div>

          <p className="mt-3 text-xs text-gray-400">
            Üretilme tarihi: {new Date(data.generated_at).toLocaleString("tr-TR")}
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
