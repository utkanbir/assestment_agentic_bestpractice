import type {
  Assessment,
  Task,
  Interview,
  Question,
  Answer,
  Evidence,
  Finding,
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
};
