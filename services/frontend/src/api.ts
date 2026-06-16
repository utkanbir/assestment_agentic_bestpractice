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
export const registerAgents = () =>
  fetchJSON<{ status: string }>("/knowledge/agents/register", { method: "POST" });

// ── Interview ────────────────────────────────────────────────────────────────

export interface Interview {
  id: string;
  task_id: string;
  interviewee_name: string;
  interviewee_role: string | null;
  status: string;
  created_at: string;
}

export interface Question {
  id: string;
  interview_id: string;
  text: string;
  order: number;
  agent_suggested: boolean;
  approval_status?: string; // "approved" | "pending" | "rejected"
}

export interface Answer {
  id: string;
  question_id: string;
  text: string;
  created_at: string;
}

export const listInterviews = (taskId: string) =>
  fetchJSON<Interview[]>(`/interviews?task_id=${taskId}`);

export const createInterview = (body: { task_id: string; interviewee_name: string; interviewee_role?: string }) =>
  fetchJSON<Interview>("/interviews", { method: "POST", body: JSON.stringify(body) });

export const listQuestions = (interviewId: string) =>
  fetchJSON<Question[]>(`/interviews/${interviewId}/questions`);

export const addQuestion = (interviewId: string, text: string, order = 0) =>
  fetchJSON<Question>(`/interviews/${interviewId}/questions`, {
    method: "POST",
    body: JSON.stringify({ interview_id: interviewId, text, order, agent_suggested: false }),
  });

export const addAnswer = (questionId: string, text: string) =>
  fetchJSON<Answer>(`/interviews/questions/${questionId}/answers`, {
    method: "POST",
    body: JSON.stringify({ question_id: questionId, text }),
  });

// ── Evidence ─────────────────────────────────────────────────────────────────

export interface Evidence {
  id: string;
  source: string;
  content: string;
  evidence_type: string;
  interview_id: string | null;
}

export const createEvidence = (body: { source: string; content: string; evidence_type: string; interview_id?: string | null }) =>
  fetchJSON<Evidence>("/evidences", { method: "POST", body: JSON.stringify(body) });

// ── Question Bank ────────────────────────────────────────────────────────────

export interface WorkstreamQuestion {
  id: string;
  workstream: string;
  area: string;
  text: string;
  follow_ups: string | null;
  order: number;
}

export const listWorkstreamQuestions = (workstream: string) =>
  fetchJSON<WorkstreamQuestion[]>(`/question-bank?workstream=${workstream}`);

// ── Maturity ─────────────────────────────────────────────────────────────────

export interface MaturityScoreItem {
  id: string;
  workstream: string;
  score: number;
  maturity_level: string;
  notes: string | null;
}

export const getMaturityScores = (assessmentId: string) =>
  fetchJSON<MaturityScoreItem[]>(`/assessments/${assessmentId}/maturity`);

export const upsertMaturityScore = (assessmentId: string, workstream: string, body: { score: number; maturity_level: string; notes?: string }) =>
  fetchJSON<MaturityScoreItem>(`/assessments/${assessmentId}/maturity/${workstream}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });

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

export const generateExecutiveSummary = (assessmentId: string) =>
  fetchJSON<ExecutiveSummary>(`/orchestrator/${assessmentId}/generate-summary`, { method: "POST" });

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

// ── Agent Status (S10-BA-002) ────────────────────────────────────────────────

export interface AgentStatusItem {
  task_id: string;
  workstream: string;
  agent_type: string;
  status: string; // "pending" | "in_progress" | "completed" | "skipped"
}

export const getAgentStatus = (assessmentId: string) =>
  fetchJSON<AgentStatusItem[]>(`/assessments/${assessmentId}/agent-status`);

// ── Question Suggest / Approve (S10-BA-001) ──────────────────────────────────

export const suggestFollowup = (interviewId: string, text?: string) =>
  fetchJSON<Question>(`/interviews/${interviewId}/suggest-followup`, {
    method: "POST",
    body: JSON.stringify({ text: text ?? "" }),
  });

export const approveQuestion = (questionId: string, action: "approved" | "rejected") =>
  fetchJSON<Question>(`/interviews/questions/${questionId}/approval`, {
    method: "PATCH",
    body: JSON.stringify({ action }),
  });

// ── Answer with evaluation (S11-BA-002) ─────────────────────────────────────

export interface AnswerWithEval {
  id: string;
  question_id: string;
  text: string;
  evaluation: string | null;
  created_at: string;
}

export const addAnswerFull = (questionId: string, text: string) =>
  fetchJSON<AnswerWithEval>(`/interviews/questions/${questionId}/answers`, {
    method: "POST",
    body: JSON.stringify({ question_id: questionId, text }),
  });

export const listAnswers = (questionId: string) =>
  fetchJSON<AnswerWithEval[]>(`/interviews/questions/${questionId}/answers`);

export const evaluateAnswer = (answerId: string) =>
  fetchJSON<{ answer_id: string; evaluation: string }>(`/interviews/answers/${answerId}/evaluate`, {
    method: "POST",
  });

// ── Question bank agent suggestions (S11-BA-003) ─────────────────────────────

export const suggestBankQuestions = (workstream: string, count = 5) =>
  fetchJSON<{ text: string }[]>(`/question-bank/suggest`, {
    method: "POST",
    body: JSON.stringify({ workstream, count }),
  });

// ── Agent Yönetimi / Metrics (S11-BA-004) ────────────────────────────────────

export interface AgentMetrics {
  workstream: string;
  interviews_conducted: number;
  questions_total: number;
  questions_agent_suggested: number;
  suggestions_approved: number;
  suggestions_rejected: number;
  suggestions_pending: number;
  answers_total: number;
  answers_evaluated: number;
  documents_loaded: number;
}

export const getAllAgentMetrics = () =>
  fetchJSON<AgentMetrics[]>("/agents/metrics");

export const getWorkstreamMetrics = (workstream: string) =>
  fetchJSON<AgentMetrics>(`/agents/metrics/${workstream}`);

// ── Knowledge Documents (S11-BA-005) ─────────────────────────────────────────

export interface KnowledgeDocument {
  id: string;
  workstream: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  description: string | null;
  created_at: string;
}

export const listDocuments = (workstream: string) =>
  fetchJSON<KnowledgeDocument[]>(`/agents/${workstream}/documents`);

export const uploadDocument = async (workstream: string, file: File, description?: string) => {
  const form = new FormData();
  form.append("file", file);
  if (description) form.append("description", description);
  const res = await fetch(`/api/v1/agents/${workstream}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<KnowledgeDocument>;
};

export const deleteDocument = (workstream: string, docId: string) =>
  fetch(`/api/v1/agents/${workstream}/documents/${docId}`, { method: "DELETE" });
