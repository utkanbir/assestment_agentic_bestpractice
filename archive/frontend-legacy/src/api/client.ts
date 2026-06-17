import type {
  Assessment,
  Task,
  Interview,
  Question,
  Answer,
  Evidence,
  Finding,
  MaturityScore,
  ApprovalQueue,
  Report,
  ExecutiveSummaryOut,
  RiskHeatmapCell,
} from "./types";

const BASE = "/api/v1";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Assessments
export const api = {
  assessments: {
    list: () => req<Assessment[]>("/assessments"),
    get: (id: string) => req<Assessment>(`/assessments/${id}`),
    create: (body: { client_name: string; project_name: string; description?: string }) =>
      req<Assessment>("/assessments", { method: "POST", body: JSON.stringify(body) }),
    update: (id: string, body: Partial<Assessment>) =>
      req<Assessment>(`/assessments/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => req<void>(`/assessments/${id}`, { method: "DELETE" }),
  },

  tasks: {
    list: (assessmentId: string) =>
      req<Task[]>(`/tasks?assessment_id=${assessmentId}`),
    get: (id: string) => req<Task>(`/tasks/${id}`),
    create: (body: { assessment_id: string; title: string; description?: string; agent_type?: string }) =>
      req<Task>("/tasks", { method: "POST", body: JSON.stringify(body) }),
  },

  interviews: {
    list: (taskId: string) => req<Interview[]>(`/interviews?task_id=${taskId}`),
    get: (id: string) => req<Interview>(`/interviews/${id}`),
    create: (body: { task_id: string }) =>
      req<Interview>("/interviews", { method: "POST", body: JSON.stringify(body) }),
    questions: (interviewId: string) =>
      req<Question[]>(`/interviews/${interviewId}/questions`),
    answers: (interviewId: string) =>
      req<Answer[]>(`/interviews/${interviewId}/answers`),
  },

  findings: {
    list: (taskId?: string) =>
      req<Finding[]>(`/findings${taskId ? `?task_id=${taskId}` : ""}`),
    get: (id: string) => req<Finding>(`/findings/${id}`),
    approve: (id: string) =>
      req<void>(`/knowledge/findings/${id}/approve`, { method: "POST" }),
  },

  evidence: {
    list: (interviewId: string) =>
      req<Evidence[]>(`/evidences?interview_id=${interviewId}`),
  },

  knowledge: {
    taskFindings: (taskId: string) =>
      req<Finding[]>(`/knowledge/tasks/${taskId}/findings`),
  },

  maturity: {
    list: (assessmentId: string) =>
      req<MaturityScore[]>(`/assessments/${assessmentId}/maturity`),
    upsert: (
      assessmentId: string,
      workstream: string,
      body: { score: number; maturity_level: string; notes?: string },
    ) =>
      req<MaturityScore>(`/assessments/${assessmentId}/maturity/${workstream}`, {
        method: "PUT",
        body: JSON.stringify(body),
      }),
  },

  approvals: {
    pending: (assessmentId?: string) =>
      req<ApprovalQueue>(
        `/approvals/pending${assessmentId ? `?assessment_id=${assessmentId}` : ""}`,
      ),
    approveFind: (id: string, decision: "approved" | "rejected") =>
      req<void>(`/approvals/findings/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ decision }),
      }),
    approveRisk: (id: string, decision: "approved" | "rejected") =>
      req<void>(`/approvals/risks/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ decision }),
      }),
    approveRec: (id: string, decision: "approved" | "rejected") =>
      req<void>(`/approvals/recommendations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ decision }),
      }),
  },

  reports: {
    list: (assessmentId?: string) =>
      req<Report[]>(`/reports${assessmentId ? `?assessment_id=${assessmentId}` : ""}`),
    get: (id: string) => req<Report>(`/reports/${id}`),
  },

  orchestrator: {
    generateSummary: (assessmentId: string) =>
      req<ExecutiveSummaryOut>(`/orchestrator/${assessmentId}/generate-summary`, { method: "POST" }),
    getSummary: (assessmentId: string) =>
      req<ExecutiveSummaryOut>(`/orchestrator/${assessmentId}/executive-summary`),
    getRiskHeatmap: (assessmentId: string) =>
      req<RiskHeatmapCell[]>(`/orchestrator/${assessmentId}/risk-heatmap`),
  },
};
