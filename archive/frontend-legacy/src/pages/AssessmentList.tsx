import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ChevronRight } from "lucide-react";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function AssessmentList() {
  const qc = useQueryClient();
  const { data: assessments = [], isLoading } = useQuery({
    queryKey: ["assessments"],
    queryFn: api.assessments.list,
  });

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ client_name: "", project_name: "", description: "" });

  const create = useMutation({
    mutationFn: api.assessments.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setShowForm(false);
      setForm({ client_name: "", project_name: "", description: "" });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Assessments</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={15} /> New Assessment
        </button>
      </div>

      {showForm && (
        <div className="mb-6 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-medium text-gray-800 mb-4">New Assessment</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Client Name</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
                value={form.client_name}
                onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                placeholder="Migros"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Project Name</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
                value={form.project_name}
                onChange={(e) => setForm({ ...form, project_name: e.target.value })}
                placeholder="Data Platform Assessment 2025"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-1">Description (optional)</label>
              <textarea
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
                rows={2}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => create.mutate(form)}
              disabled={!form.client_name || !form.project_name || create.isPending}
              className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
            >
              {create.isPending ? "Creating..." : "Create"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : assessments.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-sm">No assessments yet. Create your first one.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {assessments.map((a) => (
            <Link
              key={a.id}
              to={`/assessments/${a.id}`}
              className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-5 py-4 hover:border-brand-600 hover:shadow-sm transition-all"
            >
              <div>
                <p className="font-medium text-gray-900">{a.project_name}</p>
                <p className="text-sm text-gray-500">{a.client_name}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={a.status} />
                <ChevronRight size={16} className="text-gray-400" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
