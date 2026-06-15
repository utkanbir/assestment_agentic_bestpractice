import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus } from "lucide-react";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data: assessment } = useQuery({
    queryKey: ["assessment", id],
    queryFn: () => api.assessments.get(id!),
    enabled: !!id,
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks", id],
    queryFn: () => api.tasks.list(id!),
    enabled: !!id,
  });

  const createTask = useMutation({
    mutationFn: () =>
      api.tasks.create({
        assessment_id: id!,
        title: "Kubernetes Assessment",
        agent_type: "kubernetes",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", id] }),
  });

  if (!assessment) return <p className="text-gray-400 text-sm">Loading...</p>;

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ArrowLeft size={14} /> Back
      </Link>

      <div className="bg-white border border-gray-200 rounded-xl px-6 py-5 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{assessment.project_name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">{assessment.client_name}</p>
            {assessment.description && (
              <p className="text-sm text-gray-600 mt-2">{assessment.description}</p>
            )}
          </div>
          <StatusBadge status={assessment.status} />
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-medium text-gray-800">Tasks</h2>
        <button
          onClick={() => createTask.mutate()}
          disabled={createTask.isPending}
          className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50"
        >
          <Plus size={13} /> Add K8s Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <p className="text-sm text-gray-400">No tasks yet.</p>
      ) : (
        <div className="space-y-2">
          {tasks.map((t) => (
            <div
              key={t.id}
              className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium text-sm text-gray-900">{t.title}</p>
                {t.agent_type && (
                  <p className="text-xs text-gray-400 mt-0.5">Agent: {t.agent_type}</p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={t.status} />
                <Link
                  to={`/tasks/${t.id}/interview`}
                  className="text-xs text-brand-600 hover:underline font-medium"
                >
                  Interview
                </Link>
                <Link
                  to={`/tasks/${t.id}/findings`}
                  className="text-xs text-gray-500 hover:underline"
                >
                  Findings
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
