const BASE = "/api/v1";

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ── Assessment ──────────────────────────────────────────────────────────────

export interface Assessment {
  id: string;
  client_name: string;
  project_name: string;
  status: string;
  created_at: string;
}

export const listAssessments = () => fetchJSON<Assessment[]>("/assessments");
export const createAssessment = (body: Omit<Assessment, "id" | "created_at">) =>
  fetchJSON<Assessment>("/assessments", { method: "POST", body: JSON.stringify(body) });

// ── Task / Agent ────────────────────────────────────────────────────────────

export interface Task {
  id: string;
  assessment_id: string;
  agent_type: string;
  workstream: string;
  scope: string | null;
  status: string;
  created_at: string;
}

export const listTasks = (assessmentId: string) =>
  fetchJSON<Task[]>(`/tasks?assessment_id=${assessmentId}`);

export const createTask = (body: Omit<Task, "id" | "created_at">) =>
  fetchJSON<Task>("/tasks", { method: "POST", body: JSON.stringify(body) });

// ── Finding ─────────────────────────────────────────────────────────────────

export interface Finding {
  id: string;
  task_id: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  confidence: number;
  created_at: string;
}

export const listFindings = (taskId: string) =>
  fetchJSON<Finding[]>(`/findings?task_id=${taskId}`);

// ── Agent Registry (KG) ─────────────────────────────────────────────────────

export interface AgentInfo {
  agent: { value: string };
  agentId?: { value: string };
  workstream?: { value: string };
  displayName?: { value: string };
  description?: { value: string };
  isActive?: { value: string };
}

export const listAgents = () => fetchJSON<AgentInfo[]>("/knowledge/agents");

// ── Workstream options ───────────────────────────────────────────────────────

export const WORKSTREAMS = [
  { id: "kubernetes",      label: "Kubernetes",      icon: "⚙️" },
  { id: "cloud_strategy",  label: "Cloud Strategy",  icon: "☁️" },
  { id: "ingestion",       label: "Data Ingestion",  icon: "🔄" },
  { id: "teradata_dr",     label: "Teradata DR",     icon: "🗄️" },
  { id: "lakehouse",       label: "Lakehouse",       icon: "🏠" },
  { id: "governance",      label: "Governance",      icon: "📋" },
  { id: "data_product",    label: "Data Product",    icon: "📦" },
  { id: "cdp",             label: "CDP",             icon: "👤" },
] as const;

export type WorkstreamId = (typeof WORKSTREAMS)[number]["id"];

// ── Risk / Heatmap (S4-FA-001) ──────────────────────────────────────────────

export interface RiskHeatmapCell {
  capability_area: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  risk_count: number;
  workstreams: string[];
  max_confidence: number;
}

export const getRiskHeatmap = (assessmentId: string) =>
  fetchJSON<RiskHeatmapCell[]>(`/orchestrator/${assessmentId}/risk-heatmap`);

// ── Executive Summary (S4-FA-002) ──────────────────────────────────────────

export interface ExecutiveSummary {
  assessment_id: string;
  summary: string;
  generated_at: string;
  total_risks: number;
  critical_count: number;
  dependency_count: number;
  conflict_count: number;
}

export const getExecutiveSummary = (assessmentId: string) =>
  fetchJSON<ExecutiveSummary>(`/orchestrator/${assessmentId}/executive-summary`);

// ── Consolidated Roadmap (S4-FA-003) ────────────────────────────────────────

export interface RoadmapItem {
  id: string;
  title: string;
  description: string;
  horizon: "short" | "medium" | "long";
  priority: number;
  workstreams: string[];
  effort: string;
  addresses_conflict: boolean;
}

export const getConsolidatedRoadmap = (assessmentId: string) =>
  fetchJSON<RoadmapItem[]>(`/orchestrator/${assessmentId}/roadmap`);

// ── Cross-Task Dependencies (S4-FA-004) ─────────────────────────────────────

export interface Dependency {
  workstream_a: string;
  workstream_b: string;
  dependency_type: string;
  shared_capability_area?: string;
  conflict_signal?: string;
}

export const getCrossTaskDependencies = (assessmentId: string) =>
  fetchJSON<Dependency[]>(`/orchestrator/${assessmentId}/dependencies`);
