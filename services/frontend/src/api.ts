const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail)) {
        detail = body.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ");
      } else if (body?.detail && typeof body.detail === "object") {
        detail = (body.detail as { message?: string }).message ?? JSON.stringify(body.detail);
      } else if (typeof body?.message === "string") detail = body.message;
    } catch {
      /* non-JSON error body */
    }
    const msg = detail ? `${res.status} ${detail}` : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, msg, detail);
  }
  return res.json();
}

// ── Assessment ──────────────────────────────────────────────────────────────

export interface Assessment {
  id: string;
  client_name: string;
  project_name: string;
  status: string;
  assessment_mode?: string;
  simulation_status?: string | null;
  simulation_progress?: SimulationProgress | null;
  company_profile?: Record<string, unknown> | null;
  created_at: string;
}

export const listAssessments = () => fetchJSON<Assessment[]>("/assessments");
export const createAssessment = (body: { client_name: string; project_name: string; description?: string }) =>
  fetchJSON<Assessment>("/assessments", { method: "POST", body: JSON.stringify(body) });

export const deleteAssessment = (assessmentId: string) =>
  fetch(`${BASE}/assessments/${assessmentId}`, { method: "DELETE" }).then((res) => {
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  });

export const duplicateAssessment = (
  assessmentId: string,
  body: { include_qa?: boolean; include_tasks?: boolean } = {},
) =>
  fetchJSON<Assessment>(`/assessments/${assessmentId}/duplicate`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export interface LatestInterview {
  interview_id: string;
  task_id: string;
  workstream: string;
  created_at: string;
}

export const getLatestInterview = (assessmentId: string) =>
  fetchJSON<LatestInterview>(`/assessments/${assessmentId}/interviews/latest`);

// ── Consultants (S23) ───────────────────────────────────────────────────────

export interface Consultant {
  id: string;
  first_name: string;
  last_name: string;
  role: string | null;
  expertise: string[];
  created_at: string;
}

export interface ExpertiseGroup {
  id: string;
  name: string;
  tags: string[];
}

export interface ExpertiseCatalog {
  groups: ExpertiseGroup[];
}

export const getExpertiseCatalog = () =>
  fetchJSON<ExpertiseCatalog>("/consultants/expertise-catalog");

export const listAllConsultants = () => fetchJSON<Consultant[]>("/consultants");

export const createConsultant = (body: {
  first_name: string;
  last_name: string;
  role?: string;
  expertise?: string[];
}) =>
  fetchJSON<Consultant>("/consultants", { method: "POST", body: JSON.stringify(body) });

export const generateConsultantSynthesis = (assessmentId: string) =>
  fetchJSON<{ assessment_id: string; consultant_synthesis: string }>(
    `/assessments/${assessmentId}/consultant-synthesis`,
    { method: "POST" },
  );

export const aiSuggestMaturity = (assessmentId: string, workstream: string) =>
  fetchJSON<{ workstream: string; score: number; maturity_level: string; notes: string }>(
    `/assessments/${assessmentId}/maturity/${workstream}/ai-suggest`,
    { method: "POST" },
  );

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

export const createFinding = (body: {
  task_id: string;
  evidence_id: string;
  description: string;
  severity: Finding["severity"];
  confidence?: number;
}) =>
  fetchJSON<Finding>("/findings", { method: "POST", body: JSON.stringify(body) });

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
  layer_trace?: LayerTouch[];
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

export const createWorkstreamQuestion = (
  workstream: string,
  text: string,
  order: number,
  area = "general",
) =>
  fetchJSON<WorkstreamQuestion>("/question-bank", {
    method: "POST",
    body: JSON.stringify({ workstream, area, text, order, is_active: true }),
  });

export const deleteWorkstreamQuestion = (questionId: string) =>
  fetch(`${BASE}/question-bank/${questionId}`, { method: "DELETE" }).then((res) => {
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  });

// ── Maturity ─────────────────────────────────────────────────────────────────

export interface MaturityScoreItem {
  id: string;
  workstream: string;
  score: number;
  maturity_level: string;
  notes: string | null;
  target_score?: number | null;
}

export const getMaturityScores = (assessmentId: string) =>
  fetchJSON<MaturityScoreItem[]>(`/assessments/${assessmentId}/maturity`);

export const upsertMaturityScore = (assessmentId: string, workstream: string, body: { score: number; maturity_level: string; notes?: string; target_score?: number }) =>
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

export interface HeatmapFinding {
  id: string;
  description: string;
  severity: string;
  confidence: number;
  workstream: string;
  approval_status: string;
}

export const getHeatmapFindings = (
  assessmentId: string,
  capabilityArea: string,
  severity: string,
  approvedOnly = false,
) => {
  const params = new URLSearchParams({
    capability_area: capabilityArea,
    severity,
    approved_only: String(approvedOnly),
  });
  return fetchJSON<HeatmapFinding[]>(
    `/orchestrator/${assessmentId}/risk-heatmap/findings?${params}`,
  );
};

// ── Executive Summary (S4-FA-002) ──────────────────────────────────────────

export interface WorkstreamSummary {
  workstream: string;
  task_status: string;
  maturity_score: number | null;
  finding_count: number;
  critical_count: number;
  high_count: number;
}

export interface TopRisk {
  id: string;
  description: string;
  severity: string;
  workstream: string;
  confidence: number;
}

export interface TopRecommendation {
  id: string;
  title: string;
  description: string;
  priority: number;
  effort: string;
}

export interface ExecutiveSummary {
  assessment_id: string;
  summary: string;
  generated_at: string | null;
  total_risks: number;
  critical_count: number;
  high_count: number;
  dependency_count: number;
  conflict_count: number;
  avg_maturity: number | null;
  pending_approvals: number;
  tasks_completed: number;
  tasks_total: number;
  workstream_summaries: WorkstreamSummary[];
  top_risks: TopRisk[];
  top_recommendations: TopRecommendation[];
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
  finding_id?: string | null;
}

export const getConsolidatedRoadmap = (assessmentId: string) =>
  fetchJSON<RoadmapItem[]>(`/orchestrator/${assessmentId}/roadmap`);

export const generateRoadmap = (assessmentId: string) =>
  fetchJSON<RoadmapItem[]>(`/orchestrator/${assessmentId}/generate-roadmap`, { method: "POST" });

export const generateRecommendations = (assessmentId: string) =>
  fetchJSON<{ created: number; recommendations: { id: string; finding_id: string; description: string }[] }>(
    `/orchestrator/${assessmentId}/generate-recommendations`,
    { method: "POST" },
  );

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

export interface AnswerConsultantComment {
  id: string;
  answer_id: string;
  consultant_id: string;
  comment: string | null;
  consultant_review_feedback: string | null;
  created_at: string;
}

export interface AnswerWithEval {
  id: string;
  question_id: string;
  text: string;
  evaluation: string | null;
  consultant_id?: string | null;
  consultant_comment?: string | null;
  consultant_review_feedback?: string | null;
  consultant_comments?: AnswerConsultantComment[];
  created_at: string;
  layer_trace?: LayerTouch[];
  transaction_id?: string | null;
}

export const addAnswerFull = (
  questionId: string,
  text: string,
  opts?: { consultant_id?: string; consultant_comment?: string },
) =>
  fetchJSON<AnswerWithEval>(`/interviews/questions/${questionId}/answers`, {
    method: "POST",
    body: JSON.stringify({
      question_id: questionId,
      text,
      consultant_id: opts?.consultant_id ?? null,
      consultant_comment: opts?.consultant_comment ?? null,
    }),
  });

export const listAnswers = (questionId: string) =>
  fetchJSON<AnswerWithEval[]>(`/interviews/questions/${questionId}/answers`);

export const updateAnswer = (
  answerId: string,
  body: { consultant_id?: string | null; consultant_comment?: string | null },
) =>
  fetchJSON<AnswerWithEval>(`/interviews/answers/${answerId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const consultantReviewAnswer = (
  answerId: string,
  body?: { consultant_comment?: string | null },
) =>
  fetchJSON<{ consistent: boolean; feedback: string }>(
    `/interviews/answers/${answerId}/consultant-review`,
    { method: "POST", body: JSON.stringify(body ?? {}) },
  );

export const addAnswerConsultantComment = (
  answerId: string,
  body: { consultant_id: string; comment?: string | null },
) =>
  fetchJSON<AnswerConsultantComment>(`/interviews/answers/${answerId}/consultant-comments`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const updateAnswerConsultantComment = (
  answerId: string,
  commentId: string,
  body: { consultant_id?: string; comment?: string | null },
) =>
  fetchJSON<AnswerConsultantComment>(
    `/interviews/answers/${answerId}/consultant-comments/${commentId}`,
    { method: "PATCH", body: JSON.stringify(body) },
  );

export const consultantReviewAnswerComment = (
  answerId: string,
  commentId: string,
  body?: { consultant_comment?: string | null },
) =>
  fetchJSON<{ consistent: boolean; feedback: string }>(
    `/interviews/answers/${answerId}/consultant-comments/${commentId}/consultant-review`,
    { method: "POST", body: JSON.stringify(body ?? {}) },
  );

// ── Knowledge Architecture types (S15) ───────────────────────────────────────

export interface LayerTouch {
  id: string;
  assessment_id: string | null;
  interview_id: string | null;
  transaction_id: string | null;
  step_order: number | null;
  operation: string;
  layer: string;
  technology: string;
  action: string;
  detail: Record<string, unknown> | null;
  duration_ms: number | null;
  created_at: string;
}

/** Qdrant + LLM evaluation can take up to ~30s; allow headroom for slow networks. */
const EVALUATE_TIMEOUT_MS = 90_000;

export const evaluateAnswer = async (answerId: string) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), EVALUATE_TIMEOUT_MS);
  try {
    return await fetchJSON<{ answer_id: string; evaluation: string; layer_trace?: LayerTouch[]; transaction_id?: string }>(
      `/interviews/answers/${answerId}/evaluate`,
      { method: "POST", signal: controller.signal },
    );
  } finally {
    clearTimeout(timer);
  }
};

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

export interface LearningHistoryItem {
  answer_id: string;
  question_text: string;
  answer_text: string;
  evaluation: string;
  created_at: string;
}

export const getLearningHistory = (workstream: string) =>
  fetchJSON<LearningHistoryItem[]>(`/agents/${workstream}/learning-history`);

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
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : undefined;
    } catch { /* ignore */ }
    throw new Error(detail ? `${res.status} ${detail}` : `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<DocumentUploadResult>;
};

export const deleteDocument = (workstream: string, docId: string) =>
  fetch(`/api/v1/agents/${workstream}/documents/${docId}`, { method: "DELETE" });

// ── Agent Training (S24) ─────────────────────────────────────────────────────

export interface LearningEvent {
  id: string;
  workstream: string;
  mode: string;
  question_text: string | null;
  answer_text: string | null;
  source_doc_id: string | null;
  consultant_id?: string | null;
  answer_author?: string;
  approved_by_consultant_id?: string | null;
  created_at: string;
}

export interface DocumentUploadResult extends KnowledgeDocument {
  learning_summary?: {
    event_id: string;
    mode: string;
    workstream: string;
    chunks: number;
    characters: number;
    filename: string;
    preview?: string;
    qdrant_embedded: boolean;
  };
}

export interface AgentGraphNode {
  id: string;
  label: string;
  type: string;
  mode?: string | null;
  answer_author?: string | null;
  created_at?: string | null;
}

export interface AgentGraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface AgentGraph {
  nodes: AgentGraphNode[];
  edges: AgentGraphEdge[];
}

export interface AgentKnowledgeSummary {
  workstream: string;
  stats: {
    total_events: number;
    aaha_count: number;
    aaha_ai_count: number;
    aaha_consultant_count: number;
    text_count: number;
    document_count: number;
    chunk_estimate: number;
    knowledge_pieces: number;
  };
  recent_events: Array<{
    id: string;
    label: string;
    mode: string;
    author_display: string;
    created_at: string;
  }>;
  graph: AgentGraph;
  ontology_classes: Array<{ id: string; label: string; comment: string }>;
}

export interface SubmitAahaOptions {
  consultantId?: string;
  answerAuthor?: "consultant" | "ai";
  approvedByConsultantId?: string;
}

export const generateAahaQuestion = (workstream: string) =>
  fetchJSON<{ question: string }>(`/agents/${workstream}/train/aaha`, { method: "POST" });

export const generateAahaAiAnswer = (workstream: string, question: string) =>
  fetchJSON<{ answer: string }>(`/agents/${workstream}/train/aaha/ai-answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

export const submitAahaAnswer = (
  workstream: string,
  question: string,
  answer: string,
  options?: SubmitAahaOptions | string,
) => {
  const opts: SubmitAahaOptions = typeof options === "string"
    ? { consultantId: options }
    : (options ?? {});
  return fetchJSON<LearningEvent>(`/agents/${workstream}/train/aaha/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      answer,
      consultant_id: opts.consultantId ?? null,
      answer_author: opts.answerAuthor ?? "consultant",
      approved_by_consultant_id: opts.approvedByConsultantId ?? null,
    }),
  });
};

export const trainTextKnowledge = (workstream: string, content: string, consultantId?: string) =>
  fetchJSON<LearningEvent>(`/agents/${workstream}/train/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, consultant_id: consultantId ?? null }),
  });

export const listTrainingEvents = (workstream: string) =>
  fetchJSON<LearningEvent[]>(`/agents/${workstream}/training-events`);

export const downloadOntologyExport = async () => {
  const res = await fetch(`${BASE}/knowledge/ontology/export.ttl`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.text();
};

export const getAgentGraph = (workstream: string) =>
  fetchJSON<AgentGraph>(`/agents/${workstream}/graph`);

export const getAgentKnowledgeSummary = (workstream: string) =>
  fetchJSON<AgentKnowledgeSummary>(`/agents/${workstream}/knowledge-summary`);

export const downloadAgentProtegeExport = async (workstream: string) => {
  const res = await fetch(`${BASE}/agents/${workstream}/protege-export.ttl`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `aakp-agent-${workstream}-protege.ttl`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

export interface AgentKgStats {
  source: string;
  collected_at: string;
  totals: {
    individuals: number;
    triples_total: number;
    triples_assessment_graph: number;
    triples_agents_graph: number;
    assessments: number;
    tasks: number;
    interviews: number;
    questions: number;
    answers: number;
    evaluations: number;
    findings: number;
    consultants: number;
    evidence: number;
    assessment_agents: number;
    training_interactions: number;
    agent_knowledge: number;
    concept_links: number;
    learning_pieces: number;
    ontology_classes: number;
  };
  postgres: {
    learning_events: number;
    aaha_count: number;
    text_count: number;
    document_count: number;
    answers: number;
    questions: number;
    evaluations: number;
  };
  by_workstream: Array<{
    workstream: string;
    answer_count: number;
    question_count: number;
    training_count: number;
    knowledge_count: number;
    total_pieces: number;
  }>;
}

export const getAgentKgStats = () => fetchJSON<AgentKgStats>("/agents/kg-stats");

export const downloadAgentKgProtegeExport = async () => {
  const res = await fetch(`${BASE}/agents/kg-protege-export.ttl`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "aakp-agent-kg-full.ttl";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

// ── Knowledge Architecture (S15) ─────────────────────────────────────────────

export interface ArchitectureTechnology {
  id: string;
  name: string;
  role: string;
  configured: boolean;
  active_in_api: boolean;
  console_url?: string | null;
  notes?: string | null;
  link_mode?: string | null;
}

export interface ArchitectureLayer {
  id: string;
  name: string;
  description: string;
  namespace: string;
  technologies: ArchitectureTechnology[];
}

export interface LayerTouchSummary {
  layer: string;
  touch_count: number;
  last_operation: string | null;
  last_at: string | null;
}

export const getArchitectureLayers = () =>
  fetchJSON<{ layers: ArchitectureLayer[] }>("/architecture/layers");

export const listLayerTouches = (assessmentId?: string, interviewId?: string, layer?: string, limit = 100) => {
  const params = new URLSearchParams();
  if (assessmentId) params.set("assessment_id", assessmentId);
  if (interviewId) params.set("interview_id", interviewId);
  if (layer) params.set("layer", layer);
  params.set("limit", String(limit));
  return fetchJSON<LayerTouch[]>(`/architecture/touches?${params}`);
};

export const getLayerTouchSummary = (assessmentId?: string, interviewId?: string) => {
  const params = new URLSearchParams();
  if (assessmentId) params.set("assessment_id", assessmentId);
  if (interviewId) params.set("interview_id", interviewId);
  const qs = params.toString();
  return fetchJSON<LayerTouchSummary[]>(`/architecture/touches/summary${qs ? `?${qs}` : ""}`);
};

// ── Sprint 16: Ontology + Knowledge Graph ────────────────────────────────────

export interface OntologyClass {
  id: string;
  label: string;
  comment: string;
  parents: string[];
}

export interface OntologyProperty {
  id: string;
  label: string;
  comment: string;
  kind: "object" | "datatype";
  domain: string[];
  range: string[];
}

export interface OntologySchema {
  sources: string[];
  classes: OntologyClass[];
  properties: OntologyProperty[];
}

export interface KnowledgeGraphNode {
  id: string;
  type: string;
  label: string;
}

export interface KnowledgeGraphEdge {
  from: string;
  to: string;
  predicate: string;
}

export interface KnowledgeGraphResponse {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export const getOntologySchema = () =>
  fetchJSON<OntologySchema>("/knowledge/ontology/schema");

export const getAssessmentKnowledgeGraph = (assessmentId: string) =>
  fetchJSON<KnowledgeGraphResponse>(`/knowledge/graph/assessment/${assessmentId}`);

// ── Sprint 16: Execution plan ────────────────────────────────────────────────

export interface LayerTransaction {
  id: string;
  operation: string;
  source: string;
  assessment_id: string | null;
  interview_id: string | null;
  chat_session_id: string | null;
  status: string;
  summary: string | null;
  started_at: string;
  ended_at: string | null;
  total_duration_ms: number | null;
}

export interface LayerTransactionDetail extends LayerTransaction {
  steps: LayerTouch[];
  narrative?: string;
}

export const listTransactions = (assessmentId?: string, source?: string, limit = 100) => {
  const params = new URLSearchParams();
  if (assessmentId) params.set("assessment_id", assessmentId);
  if (source) params.set("source", source);
  params.set("limit", String(limit));
  return fetchJSON<LayerTransaction[]>(`/architecture/transactions?${params.toString()}`);
};

export const getTransaction = (transactionId: string) =>
  fetchJSON<LayerTransactionDetail>(`/architecture/transactions/${transactionId}`);

// ── Sprint 16: Standalone chat ───────────────────────────────────────────────

export interface ChatSession {
  id: string;
  assessment_id: string;
  workstream: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatExchange {
  session_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  layer_trace?: LayerTouch[];
  transaction_id?: string | null;
}

export const createChatSession = (assessmentId: string, workstream: string, title?: string) =>
  fetchJSON<ChatSession>("/chat/sessions", {
    method: "POST",
    body: JSON.stringify({
      assessment_id: assessmentId,
      workstream,
      title: title ?? "Yeni Sohbet",
    }),
  });

export const listChatSessions = (assessmentId?: string) => {
  const params = new URLSearchParams();
  if (assessmentId) params.set("assessment_id", assessmentId);
  const qs = params.toString();
  return fetchJSON<ChatSession[]>(`/chat/sessions${qs ? `?${qs}` : ""}`);
};

export const postChatMessage = (sessionId: string, content: string) =>
  fetchJSON<ChatExchange>(`/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });

// ── Sprint 17: Approvals + pending questions ───────────────────────────────

export interface PendingQuestion {
  id: string;
  interview_id: string;
  text: string;
  workstream: string;
  order: number;
}

export interface ApprovalQueueData {
  pending_findings: { id: string; description: string; severity: string; confidence?: number }[];
  pending_risks: { id: string; title?: string; description: string; level: string }[];
  pending_recommendations: { id: string; description: string; priority?: number; effort?: string }[];
  total: number;
}

export const getPendingApprovals = (assessmentId: string) =>
  fetchJSON<ApprovalQueueData>(`/approvals/pending?assessment_id=${assessmentId}`);

export const getPendingQuestions = (assessmentId: string) =>
  fetchJSON<PendingQuestion[]>(`/approvals/pending-questions?assessment_id=${assessmentId}`);

export const patchApproval = (type: "finding" | "risk" | "recommendation", id: string, decision: "approved" | "rejected", reviewer_note?: string) =>
  fetchJSON(`/approvals/${type}s/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ decision, reviewer_note: reviewer_note ?? "" }),
  });

// ── Sprint 18: Reports ─────────────────────────────────────────────────────

export interface ReportRecord {
  id: string;
  assessment_id: string;
  title: string;
  executive_summary: string | null;
  content_json: string | null;
  kg_uri?: string | null;
  created_at: string;
}

export interface ReportSection {
  id: string;
  type: string;
  title?: string;
  body?: string;
  client?: string;
  project?: string;
  date?: string;
  columns?: string[];
  rows?: string[][];
  items?: { label: string; value: string }[];
  data?: {
    labels?: string[];
    values?: number[];
    cells?: { capability_area: string; severity: string; risk_count: number }[];
  };
  commentary?: string;
  subtitle?: string;
  consultant_comment?: string;
  consultant_opinions?: { consultant_id: string; comment: string }[];
  consultant_approved?: boolean;
}

export interface ReportContent {
  version: number;
  sections: ReportSection[];
}

export const listReports = (assessmentId: string) =>
  fetchJSON<ReportRecord[]>(`/reports?assessment_id=${assessmentId}`);

export const getReport = (reportId: string) =>
  fetchJSON<ReportRecord>(`/reports/${reportId}`);

export const composeReport = (assessmentId: string) =>
  fetchJSON<ReportRecord>(`/reports/assessment/${assessmentId}/compose`, { method: "POST" });

export const patchReport = (reportId: string, body: { title?: string; executive_summary?: string; content_json?: string }) =>
  fetchJSON<ReportRecord>(`/reports/${reportId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const aiEditReport = (
  reportId: string,
  body: { section_id?: string | null; instruction: string; mode?: string },
) =>
  fetchJSON<{ report_id: string; updated_sections: string[]; content_json: string }>(
    `/reports/${reportId}/ai-edit`,
    { method: "POST", body: JSON.stringify(body) },
  );

export const aiGenerateReport = (
  reportId: string,
  body: { section_id?: string | null; instruction?: string; mode?: string },
) =>
  fetchJSON<{ report_id: string; updated_sections: string[]; content_json: string; total_sections: number }>(
    `/reports/${reportId}/ai-generate`,
    { method: "POST", body: JSON.stringify(body) },
  );

export const consultantReviewSection = (
  reportId: string,
  body: { section_id: string; consultant_comment: string },
) =>
  fetchJSON<{
    report_id: string;
    section_id: string;
    consistent: boolean;
    feedback: string;
    content_json: string;
  }>(`/reports/${reportId}/consultant-review`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export async function downloadReportBlob(reportId: string, format: "pdf" | "docx", force = false) {
  const res = await fetch(`${BASE}/reports/${reportId}/export/${format}?force=${force}`, { method: "POST" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report-${reportId}.${format === "pdf" ? "pdf" : "docx"}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Sprint 18: Chat history ────────────────────────────────────────────────

export const getChatSession = (sessionId: string) =>
  fetchJSON<ChatSession>(`/chat/sessions/${sessionId}`);

export const getChatMessages = (sessionId: string, limit = 50) =>
  fetchJSON<ChatMessage[]>(`/chat/sessions/${sessionId}/messages?limit=${limit}`);

export const patchChatSession = (sessionId: string, body: { title?: string; workstream?: string }) =>
  fetchJSON<ChatSession>(`/chat/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

// ── Sprint 21: AI Simulated Assessment ───────────────────────────────────────

export interface SimulationProgress {
  workstreams_total: number;
  workstreams_completed: number;
  current_workstream?: string | null;
  current_interview_id?: string | null;
  primary_interview_id?: string | null;
  questions_asked: number;
  questions_evaluated: number;
  total_questions_planned: number;
  steps?: {
    workstream: string;
    question_id: string;
    answer_id: string;
    evaluation_id?: string;
    status: string;
    at?: string;
    text?: string;
    evaluation?: string;
  }[];
}

export interface SimulationStartResult {
  id: string;
  client_name: string;
  project_name: string;
  status: string;
  assessment_mode: string;
  simulation_status: string | null;
  simulation_progress: SimulationProgress | null;
  primary_interview_id: string | null;
  created_at: string;
}

export interface SimulationStatus {
  assessment_id: string;
  assessment_mode: string;
  simulation_status: string | null;
  simulation_progress: SimulationProgress | null;
  primary_interview_id: string | null;
}

export interface SimulationFinalizeResult {
  assessment_id: string;
  report_id: string;
  executive_summary: string;
  simulation_status: string;
  ai_sections_updated: number;
}

export const startSimulation = (body: {
  client_name: string;
  project_name: string;
  description?: string;
  company_profile?: Record<string, unknown>;
}) =>
  fetchJSON<SimulationStartResult>("/assessments/simulated", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const stopSimulation = (assessmentId: string) =>
  fetchJSON<SimulationStatus>(`/assessments/${assessmentId}/simulation/stop`, { method: "POST" });

export const getSimulationStatus = (assessmentId: string) =>
  fetchJSON<SimulationStatus>(`/assessments/${assessmentId}/simulation/status`);

export const finalizeSimulation = (assessmentId: string) =>
  fetchJSON<SimulationFinalizeResult>(`/assessments/${assessmentId}/simulation/finalize`, { method: "POST" });
