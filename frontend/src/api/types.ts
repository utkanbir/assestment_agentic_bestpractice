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
