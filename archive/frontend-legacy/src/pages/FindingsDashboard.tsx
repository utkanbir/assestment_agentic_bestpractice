import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle } from "lucide-react";
import { api } from "../api/client";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";
import type { FindingSeverity } from "../api/types";

const SEVERITY_ORDER: FindingSeverity[] = ["critical", "high", "medium", "low", "info"];

export function FindingsDashboard() {
  const { taskId } = useParams<{ taskId: string }>();
  const qc = useQueryClient();

  const { data: findings = [], isLoading } = useQuery({
    queryKey: ["findings", taskId],
    queryFn: () => api.findings.list(taskId),
    enabled: true,
    refetchInterval: 5000,
  });

  const approve = useMutation({
    mutationFn: (id: string) => api.findings.approve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["findings", taskId] }),
  });

  const grouped = SEVERITY_ORDER.reduce<Record<string, typeof findings>>(
    (acc, sev) => {
      acc[sev] = findings.filter((f) => f.severity === sev);
      return acc;
    },
    {} as Record<string, typeof findings>,
  );

  const total = findings.length;
  const pending = findings.filter((f) => f.approval_status === "pending").length;

  return (
    <div>
      {taskId && (
        <Link to="/" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft size={14} /> Back
        </Link>
      )}

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Findings</h1>
        <div className="flex gap-4 text-sm text-gray-500">
          <span>{total} total</span>
          <span className="text-yellow-600 font-medium">{pending} pending review</span>
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : total === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-sm">No findings yet. Run an interview to generate findings.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {SEVERITY_ORDER.filter((sev) => grouped[sev].length > 0).map((sev) => (
            <div key={sev}>
              <div className="flex items-center gap-2 mb-3">
                <SeverityBadge severity={sev} />
                <span className="text-xs text-gray-400">{grouped[sev].length} findings</span>
              </div>
              <div className="space-y-2">
                {grouped[sev].map((f) => (
                  <div
                    key={f.id}
                    className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1">
                      <p className="text-sm text-gray-800">{f.description}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <StatusBadge status={f.approval_status} />
                        <span className="text-xs text-gray-400">
                          Confidence: {Math.round(f.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    {f.approval_status === "pending" && (
                      <button
                        onClick={() => approve.mutate(f.id)}
                        disabled={approve.isPending}
                        className="flex items-center gap-1 text-xs text-green-600 hover:text-green-800 font-medium shrink-0 mt-0.5"
                      >
                        <CheckCircle size={14} /> Approve
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
