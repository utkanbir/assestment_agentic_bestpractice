import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Save, CheckCircle, AlertCircle } from "lucide-react";
import { api } from "../api/client";
import type { MaturityLevel, MaturityScore } from "../api/types";

const WORKSTREAMS = [
  { key: "kubernetes", label: "Kubernetes" },
  { key: "cloud_strategy", label: "Cloud Strategy" },
  { key: "ingestion", label: "Ingestion" },
  { key: "teradata_dr", label: "Teradata DR" },
  { key: "lakehouse", label: "Lakehouse" },
  { key: "governance", label: "Governance" },
  { key: "data_product", label: "Data Product" },
  { key: "cdp", label: "CDP" },
] as const;

const MATURITY_LEVELS: MaturityLevel[] = [
  "initial",
  "developing",
  "defined",
  "managed",
  "optimized",
];

const LEVEL_COLORS: Record<MaturityLevel, string> = {
  initial: "bg-red-100 text-red-700",
  developing: "bg-orange-100 text-orange-700",
  defined: "bg-yellow-100 text-yellow-700",
  managed: "bg-blue-100 text-blue-700",
  optimized: "bg-green-100 text-green-700",
};

const SCORE_COLORS = ["", "bg-red-400", "bg-orange-400", "bg-yellow-400", "bg-blue-400", "bg-green-400"];

interface WorkstreamFormState {
  score: number;
  maturity_level: MaturityLevel;
  notes: string;
  saving: boolean;
  saved: boolean;
  error: string | null;
}

const DEFAULT_STATE: WorkstreamFormState = {
  score: 1,
  maturity_level: "initial",
  notes: "",
  saving: false,
  saved: false,
  error: null,
};

export function MaturityInputPage() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<{ project_name: string; client_name: string } | null>(null);
  const [forms, setForms] = useState<Record<string, WorkstreamFormState>>(
    () =>
      Object.fromEntries(WORKSTREAMS.map((ws) => [ws.key, { ...DEFAULT_STATE }])) as Record<
        string,
        WorkstreamFormState
      >,
  );
  const [savingAll, setSavingAll] = useState(false);
  const [allSaved, setAllSaved] = useState(false);

  // Load assessment info + existing maturity scores
  useEffect(() => {
    if (!id) return;

    async function load() {
      setLoading(true);
      setLoadError(null);
      try {
        const [assessmentData, scores] = await Promise.all([
          api.assessments.get(id!),
          api.maturity.list(id!),
        ]);
        setAssessment({ project_name: assessmentData.project_name, client_name: assessmentData.client_name });

        // Pre-fill form from existing scores
        if (scores.length > 0) {
          setForms((prev) => {
            const next = { ...prev };
            scores.forEach((s: MaturityScore) => {
              if (next[s.workstream]) {
                next[s.workstream] = {
                  ...next[s.workstream],
                  score: s.score,
                  maturity_level: s.maturity_level as MaturityLevel,
                  notes: s.notes ?? "",
                };
              }
            });
            return next;
          });
        }
      } catch (err) {
        setLoadError(err instanceof Error ? err.message : "Yüklenirken hata oluştu");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id]);

  function setField<K extends keyof WorkstreamFormState>(
    workstream: string,
    field: K,
    value: WorkstreamFormState[K],
  ) {
    setForms((prev) => ({
      ...prev,
      [workstream]: { ...prev[workstream], [field]: value, saved: false, error: null },
    }));
  }

  async function saveWorkstream(workstream: string) {
    const f = forms[workstream];
    setForms((prev) => ({ ...prev, [workstream]: { ...prev[workstream], saving: true, error: null } }));
    try {
      await api.maturity.upsert(id!, workstream, {
        score: f.score,
        maturity_level: f.maturity_level,
        notes: f.notes || undefined,
      });
      setForms((prev) => ({ ...prev, [workstream]: { ...prev[workstream], saving: false, saved: true } }));
    } catch (err) {
      setForms((prev) => ({
        ...prev,
        [workstream]: {
          ...prev[workstream],
          saving: false,
          error: err instanceof Error ? err.message : "Kayıt hatası",
        },
      }));
    }
  }

  async function saveAll() {
    setSavingAll(true);
    setAllSaved(false);
    for (const ws of WORKSTREAMS) {
      await saveWorkstream(ws.key);
    }
    setSavingAll(false);
    setAllSaved(true);
    setTimeout(() => setAllSaved(false), 3000);
  }

  if (loading) {
    return <p className="text-gray-400 text-sm">Yükleniyor...</p>;
  }

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-red-700 text-sm">
        {loadError}
      </div>
    );
  }

  return (
    <div>
      <Link
        to={`/assessments/${id}`}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeft size={14} /> Geri
      </Link>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl px-6 py-5 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Maturity Skorları</h1>
            {assessment && (
              <p className="text-sm text-gray-500 mt-0.5">
                {assessment.project_name} — {assessment.client_name}
              </p>
            )}
          </div>
          <button
            onClick={saveAll}
            disabled={savingAll}
            className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
          >
            {savingAll ? (
              <>Kaydediliyor...</>
            ) : allSaved ? (
              <>
                <CheckCircle size={14} /> Tümü Kaydedildi
              </>
            ) : (
              <>
                <Save size={14} /> Tümünü Kaydet
              </>
            )}
          </button>
        </div>
      </div>

      {/* Workstream Cards */}
      <div className="space-y-4">
        {WORKSTREAMS.map((ws) => {
          const f = forms[ws.key];
          return (
            <div
              key={ws.key}
              className="bg-white border border-gray-200 rounded-xl px-6 py-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-4">
                    <h2 className="font-semibold text-gray-800">{ws.label}</h2>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${LEVEL_COLORS[f.maturity_level]}`}
                    >
                      {f.maturity_level}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Score */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1 font-medium">
                        Skor (1–5)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min={1}
                          max={5}
                          step={1}
                          value={f.score}
                          onChange={(e) =>
                            setField(ws.key, "score", Number(e.target.value))
                          }
                          className="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-brand-600"
                        />
                        <span
                          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-white font-bold text-sm ${SCORE_COLORS[f.score]}`}
                        >
                          {f.score}
                        </span>
                      </div>
                    </div>

                    {/* Maturity Level */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1 font-medium">
                        Olgunluk Seviyesi
                      </label>
                      <select
                        value={f.maturity_level}
                        onChange={(e) =>
                          setField(ws.key, "maturity_level", e.target.value as MaturityLevel)
                        }
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600 bg-white"
                      >
                        {MATURITY_LEVELS.map((level) => (
                          <option key={level} value={level}>
                            {level.charAt(0).toUpperCase() + level.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Notes */}
                    <div className="sm:col-span-2">
                      <label className="block text-xs text-gray-500 mb-1 font-medium">
                        Notlar (opsiyonel)
                      </label>
                      <textarea
                        value={f.notes}
                        onChange={(e) => setField(ws.key, "notes", e.target.value)}
                        rows={2}
                        placeholder="Ek açıklamalar..."
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600 resize-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Per-row save button */}
                <div className="flex flex-col items-end gap-2 pt-8">
                  <button
                    onClick={() => saveWorkstream(ws.key)}
                    disabled={f.saving}
                    className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-800 border border-brand-600 hover:border-brand-800 rounded-lg px-3 py-1.5 disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    {f.saving ? "Kaydediliyor..." : "Kaydet"}
                  </button>
                  {f.saved && (
                    <span className="flex items-center gap-1 text-xs text-green-600">
                      <CheckCircle size={12} /> Kaydedildi
                    </span>
                  )}
                  {f.error && (
                    <span className="flex items-center gap-1 text-xs text-red-600">
                      <AlertCircle size={12} /> {f.error}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
