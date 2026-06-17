import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Printer,
  AlertCircle,
  FileText,
  Loader2,
} from "lucide-react";
import { api } from "../api/client";
import type { ExecutiveSummaryOut } from "../api/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("tr-TR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ExecutiveSummaryPage() {
  const { id } = useParams<{ id: string }>();

  const [assessmentName, setAssessmentName] = useState<string | null>(null);
  const [summary, setSummary] = useState<ExecutiveSummaryOut | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Load assessment name + existing summary on mount
  useEffect(() => {
    if (!id) return;

    async function load() {
      setLoading(true);
      setLoadError(null);

      // Load assessment name
      try {
        const assessment = await api.assessments.get(id!);
        setAssessmentName(`${assessment.project_name} — ${assessment.client_name}`);
      } catch {
        // Not critical — continue without name
      }

      // Try to load existing summary (404 is not an error here)
      try {
        const data = await api.orchestrator.getSummary(id!);
        setSummary(data);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "";
        if (!msg.startsWith("404")) {
          setLoadError(msg || "Özet yüklenirken hata oluştu");
        }
        // 404 → summary doesn't exist yet, that's fine
      }

      setLoading(false);
    }

    load();
  }, [id]);

  async function handleGenerate() {
    if (!id) return;
    setGenerating(true);
    setGenError(null);
    try {
      const data = await api.orchestrator.generateSummary(id);
      setSummary(data);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : "Özet oluşturulamadı");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-400 text-sm py-8">
        <Loader2 size={16} className="animate-spin" />
        Yükleniyor...
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-red-700 text-sm flex items-center gap-2">
        <AlertCircle size={16} />
        {loadError}
      </div>
    );
  }

  return (
    <div>
      {/* Back link — hidden in print */}
      <Link
        to={`/assessments/${id}`}
        className="print:hidden flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeft size={14} /> Geri
      </Link>

      {/* Header card */}
      <div className="bg-white border border-gray-200 rounded-xl px-6 py-5 mb-6 print:border-none print:px-0">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Executive Summary</h1>
            {assessmentName && (
              <p className="text-sm text-gray-500 mt-0.5">{assessmentName}</p>
            )}
          </div>

          {/* Actions — hidden in print */}
          <div className="print:hidden flex items-center gap-2 flex-wrap">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
            >
              {generating ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Oluşturuluyor...
                </>
              ) : (
                <>
                  <RefreshCw size={14} />
                  Executive Summary Oluştur
                </>
              )}
            </button>

            {summary && (
              <button
                onClick={() => window.print()}
                className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 hover:border-gray-400 rounded-lg px-4 py-2 transition-colors"
              >
                <Printer size={14} />
                PDF İndir
              </button>
            )}
          </div>
        </div>

        {/* Generation error */}
        {genError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm flex items-center gap-2">
            <AlertCircle size={14} />
            {genError}
          </div>
        )}
      </div>

      {/* No summary yet */}
      {!summary && (
        <div className="text-center py-20 text-gray-400">
          <FileText size={36} className="mx-auto mb-3 text-gray-300" />
          <p className="text-sm font-medium">Henüz özet oluşturulmadı</p>
          <p className="text-xs mt-1">
            Yukarıdaki butona tıklayarak assessment için executive summary oluşturabilirsiniz.
          </p>
        </div>
      )}

      {/* Summary content */}
      {summary && (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl px-5 py-4 text-center">
              <p className="text-xs text-gray-500 mb-1">Toplam Bulgu</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_risks}</p>
            </div>
            <div className="bg-white border border-red-200 rounded-xl px-5 py-4 text-center">
              <p className="text-xs text-gray-500 mb-1">Kritik</p>
              <p className="text-2xl font-bold text-red-600">{summary.critical_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl px-5 py-4 text-center">
              <p className="text-xs text-gray-500 mb-1">Oluşturulma</p>
              <p className="text-sm font-medium text-gray-700 leading-tight">
                {formatDate(summary.generated_at)}
              </p>
            </div>
          </div>

          {/* Summary text */}
          <div className="bg-white border-2 border-blue-200 rounded-xl px-6 py-5">
            <h2 className="text-sm font-semibold text-blue-700 mb-3 uppercase tracking-wide">
              Yönetici Özeti
            </h2>
            <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
              {summary.summary}
            </p>
          </div>

          {/* Extra stats row */}
          {(summary.dependency_count > 0 || summary.conflict_count > 0) && (
            <div className="grid grid-cols-2 gap-4">
              {summary.dependency_count > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl px-5 py-4">
                  <p className="text-xs text-gray-500 mb-1">Bağımlılık Sayısı</p>
                  <p className="text-xl font-bold text-gray-800">{summary.dependency_count}</p>
                </div>
              )}
              {summary.conflict_count > 0 && (
                <div className="bg-white border border-orange-200 rounded-xl px-5 py-4">
                  <p className="text-xs text-gray-500 mb-1">Çakışma Sayısı</p>
                  <p className="text-xl font-bold text-orange-600">{summary.conflict_count}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
