const API_BASE = process.env.API_BASE ?? "http://localhost:8000/api/v1";

export interface Assessment {
  id: string;
  client_name: string;
  project_name: string;
  status: string;
}

export interface Task {
  id: string;
  assessment_id: string;
  agent_type: string;
  workstream: string;
  scope: string | null;
  status: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} → ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} → ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export async function createAssessment(clientName = "E2E-MultiAgent"): Promise<Assessment> {
  const suffix = Math.random().toString(36).slice(2, 8);
  return post<Assessment>("/assessments", {
    client_name: clientName,
    project_name: `E2E-${suffix}`,
    status: "active",
  });
}

export async function createTaskForWorkstream(
  assessmentId: string,
  workstream: string,
  status = "in_progress",
): Promise<Task> {
  return post<Task>("/tasks", {
    assessment_id: assessmentId,
    agent_type: workstream === "kubernetes" ? "kubernetes" : "workstream",
    workstream,
    scope: null,
    status,
  });
}

export async function seedAssessmentWithTasks(workstreams: string[]) {
  const assessment = await createAssessment();
  const tasks = await Promise.all(
    workstreams.map((ws) => createTaskForWorkstream(assessment.id, ws)),
  );
  return { assessmentId: assessment.id, assessment, tasks };
}

export async function listTasks(assessmentId: string): Promise<Task[]> {
  return get<Task[]>(`/tasks?assessment_id=${assessmentId}`);
}

export const ALL_WORKSTREAMS = [
  "kubernetes",
  "cloud_strategy",
  "ingestion",
  "teradata_dr",
  "lakehouse",
  "governance",
  "data_product",
  "cdp",
] as const;

export const WORKSTREAM_LABELS: Record<string, string> = {
  kubernetes: "Kubernetes",
  cloud_strategy: "Cloud Strategy",
  ingestion: "Data Ingestion",
  teradata_dr: "Teradata DR",
  lakehouse: "Lakehouse",
  governance: "Governance",
  data_product: "Data Product",
  cdp: "CDP",
};
