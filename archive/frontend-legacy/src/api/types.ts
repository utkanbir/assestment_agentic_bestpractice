export type AssessmentStatus = "draft" | "in_progress" | "completed" | "archived";
export type TaskStatus = "pending" | "in_progress" | "completed" | "skipped";
export type InterviewStatus = "scheduled" | "in_progress" | "completed" | "cancelled";
export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type EvidenceType = "interview" | "document" | "observation" | "automated";

export interface Assessment {
  id: string;
  client_name: string;
  project_name: string;
  status: AssessmentStatus;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  assessment_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  agent_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface Interview {
  id: string;
  task_id: string;
  status: InterviewStatus;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface Question {
  id: string;
  interview_id: string;
  text: string;
  order: number;
  created_at: string;
}

export interface Answer {
  id: string;
  question_id: string;
  interview_id: string;
  text: string;
  created_at: string;
}

export interface Evidence {
  id: string;
  interview_id: string | null;
  source: string;
  content: string;
  evidence_type: EvidenceType;
  kg_uri: string | null;
  created_at: string;
}

export interface Finding {
  id: string;
  task_id: string;
  evidence_id: string;
  description: string;
  severity: FindingSeverity;
  confidence: number;
  approval_status: ApprovalStatus;
  kg_uri: string | null;
  created_at: string;
  updated_at: string;
}

// WebSocket event types
export type WSEventType =
  | "answer.submitted"
  | "question.suggested"
  | "finding.detected"
  | "error";

export interface WSMessage {
  event: WSEventType;
  payload: Record<string, unknown>;
}

// Sprint 9 types

export type MaturityLevel = "initial" | "developing" | "defined" | "managed" | "optimized";

export interface MaturityScore {
  id: string;
  assessment_id: string;
  workstream: string;
  score: number;
  maturity_level: MaturityLevel;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalFinding {
  id: string;
  description: string;
  severity: string;
  confidence: number;
}

export interface ApprovalRisk {
  id: string;
  title: string | null;
  description: string;
  level: string;
}

export interface ApprovalRecommendation {
  id: string;
  description: string;
  priority: number;
  effort: string | null;
}

export interface ApprovalQueue {
  pending_findings: ApprovalFinding[];
  pending_risks: ApprovalRisk[];
  pending_recommendations: ApprovalRecommendation[];
  total: number;
}

export interface Report {
  id: string;
  assessment_id: string;
  title: string;
  executive_summary: string | null;
  content_json: string | null;
  created_at: string;
  updated_at: string;
}

// Sprint 9 Wave 2 types

export interface ExecutiveSummaryOut {
  assessment_id: string;
  summary: string;
  generated_at: string;
  total_risks: number;
  critical_count: number;
  dependency_count: number;
  conflict_count: number;
}

export interface RiskHeatmapCell {
  capability_area: string;
  severity: string;
  risk_count: number;
  workstreams: string[];
  max_confidence: number;
}
