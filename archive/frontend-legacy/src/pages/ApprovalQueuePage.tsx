import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, XCircle, RefreshCw, AlertTriangle, FileText, Star } from "lucide-react";
import { api } from "../api/client";
import type { ApprovalFinding, ApprovalRisk, ApprovalRecommendation } from "../api/types";

type TabKey = "findings" | "risks" | "recommendations";

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: "findings", label: "Bulgular", icon: AlertTriangle },
  { key: "risks", label: "Riskler", icon: FileText },
  { key: "recommendations", label: "Öneriler", icon: Star },
];

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
  info: "bg-gray-100 text-gray-600",
};

const LEVEL_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-orange-100 text-orange-700",
  low: "bg-yellow-100 text-yellow-700",
};

const EFFORT_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-green-700",
};

function PriorityDots({ priority }: { priority: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          className={`w-2 h-2 rounded-full ${i <= priority ? "bg-brand-600" : "bg-gray-200"}`}
        />
      ))}
    </span>
  );
}

export function ApprovalQueuePage() {
  const qc = useQueryClient();
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<TabKey>("findings");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load assessment list for dropdown
  const { data: assessments = [] } = useQuery({
    queryKey: ["assessments"],
    queryFn: api.assessments.list,
  });

  // Load approval queue — manual fetch with polling
  const {
    data: queue,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["approvals", selectedAssessmentId],
    queryFn: () => api.approvals.pending(selectedAssessmentId || undefined),
    enabled: true,
    refetchInterval: false, // we manage polling manually
  });

  // Polling: every 5s when an assessment is selected
  const doRefetch = useCallback(() => {
    refetch();
    setLastRefresh(new Date());
  }, [refetch]);

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(doRefetch, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [doRefetch]);

  // Invalidate and refetch after mutations
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["approvals", selectedAssessmentId] });
    setLastRefresh(new Date());
  };

  const approveFind = useMutation({
    mutationFn: (args: { id: string; decision: "approved" | "rejected" }) =>
      api.approvals.approveFind(args.id, args.decision),
    onSuccess: invalidate,
  });

  const approveRisk = useMutation({
    mutationFn: (args: { id: string; decision: "approved" | "rejected" }) =>
      api.approvals.approveRisk(args.id, args.decision),
    onSuccess: invalidate,
  });

  const approveRec = useMutation({
    mutationFn: (args: { id: string; decision: "approved" | "rejected" }) =>
      api.approvals.approveRec(args.id, args.decision),
    onSuccess: invalidate,
  });

  const findings: ApprovalFinding[] = queue?.pending_findings ?? [];
  const risks: ApprovalRisk[] = queue?.pending_risks ?? [];
  const recs: ApprovalRecommendation[] = queue?.pending_recommendations ?? [];
  const total = queue?.total ?? 0;

  const tabCounts: Record<TabKey, number> = {
    findings: findings.length,
    risks: risks.length,
    recommendations: recs.length,
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Onay Kuyruğu</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Son güncelleme: {lastRefresh.toLocaleTimeString("tr-TR")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {total > 0 && (
            <span className="inline-flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6">
              {total}
            </span>
          )}
          <button
            onClick={doRefetch}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg px-3 py-1.5 transition-colors"
          >
            <RefreshCw size={13} /> Yenile
          </button>
        </div>
      </div>

      {/* Assessment Selector */}
      <div className="bg-white border border-gray-200 rounded-xl px-5 py-4 mb-6">
        <label className="block text-xs text-gray-500 mb-1.5 font-medium">Assessment Seç</label>
        <select
          value={selectedAssessmentId}
          onChange={(e) => setSelectedAssessmentId(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600 bg-white"
        >
          <option value="">Tüm Assessmentlar</option>
          {assessments.map((a) => (
            <option key={a.id} value={a.id}>
              {a.project_name} — {a.client_name}
            </option>
          ))}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-xl p-1">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex-1 flex items-center justify-center gap-1.5 text-sm font-medium py-2 rounded-lg transition-colors ${
              activeTab === key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={14} />
            {label}
            {tabCounts[key] > 0 && (
              <span
                className={`inline-flex items-center justify-center text-xs font-bold rounded-full w-5 h-5 ${
                  activeTab === key ? "bg-brand-600 text-white" : "bg-gray-300 text-gray-600"
                }`}
              >
                {tabCounts[key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <p className="text-gray-400 text-sm">Yükleniyor...</p>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-red-700 text-sm">
          {error instanceof Error ? error.message : "Veri yüklenemedi"}
        </div>
      ) : (
        <div className="space-y-3">
          {/* Findings Tab */}
          {activeTab === "findings" && (
            <>
              {findings.length === 0 ? (
                <EmptyState label="Bekleyen bulgu yok." />
              ) : (
                findings.map((f) => (
                  <div
                    key={f.id}
                    className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            SEVERITY_COLORS[f.severity] ?? "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {f.severity}
                        </span>
                        <span className="text-xs text-gray-400">
                          Güven: {Math.round(f.confidence * 100)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-800">{f.description}</p>
                    </div>
                    <ApproveRejectButtons
                      onApprove={() => approveFind.mutate({ id: f.id, decision: "approved" })}
                      onReject={() => approveFind.mutate({ id: f.id, decision: "rejected" })}
                      disabled={approveFind.isPending}
                    />
                  </div>
                ))
              )}
            </>
          )}

          {/* Risks Tab */}
          {activeTab === "risks" && (
            <>
              {risks.length === 0 ? (
                <EmptyState label="Bekleyen risk yok." />
              ) : (
                risks.map((r) => (
                  <div
                    key={r.id}
                    className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            LEVEL_COLORS[r.level] ?? "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {r.level}
                        </span>
                        {r.title && (
                          <span className="text-xs font-medium text-gray-700">{r.title}</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-800">{r.description}</p>
                    </div>
                    <ApproveRejectButtons
                      onApprove={() => approveRisk.mutate({ id: r.id, decision: "approved" })}
                      onReject={() => approveRisk.mutate({ id: r.id, decision: "rejected" })}
                      disabled={approveRisk.isPending}
                    />
                  </div>
                ))
              )}
            </>
          )}

          {/* Recommendations Tab */}
          {activeTab === "recommendations" && (
            <>
              {recs.length === 0 ? (
                <EmptyState label="Bekleyen öneri yok." />
              ) : (
                recs.map((rec) => (
                  <div
                    key={rec.id}
                    className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <PriorityDots priority={rec.priority} />
                        <span className="text-xs text-gray-500">Öncelik: {rec.priority}</span>
                        {rec.effort && (
                          <span
                            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                              EFFORT_COLORS[rec.effort] ?? "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {rec.effort} efor
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-800">{rec.description}</p>
                    </div>
                    <ApproveRejectButtons
                      onApprove={() => approveRec.mutate({ id: rec.id, decision: "approved" })}
                      onReject={() => approveRec.mutate({ id: rec.id, decision: "rejected" })}
                      disabled={approveRec.isPending}
                    />
                  </div>
                ))
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <CheckCircle size={32} className="mx-auto mb-3 text-green-300" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

function ApproveRejectButtons({
  onApprove,
  onReject,
  disabled,
}: {
  onApprove: () => void;
  onReject: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-2 shrink-0">
      <button
        onClick={onApprove}
        disabled={disabled}
        className="flex items-center gap-1 text-xs font-medium text-green-600 hover:text-green-800 border border-green-300 hover:border-green-500 rounded-lg px-3 py-1.5 disabled:opacity-50 transition-colors"
      >
        <CheckCircle size={13} /> Onayla
      </button>
      <button
        onClick={onReject}
        disabled={disabled}
        className="flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-800 border border-red-300 hover:border-red-500 rounded-lg px-3 py-1.5 disabled:opacity-50 transition-colors"
      >
        <XCircle size={13} /> Reddet
      </button>
    </div>
  );
}
