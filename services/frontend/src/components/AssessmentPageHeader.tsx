import { ReactNode } from "react";
import { useAssessment } from "../context/AssessmentContext";

const statusColor: Record<string, string> = {
  active: "#22c55e",
  in_progress: "#3b82f6",
  completed: "#94a3b8",
  pending: "#eab308",
};

interface Props {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  taskCount?: number;
}

export default function AssessmentPageHeader({ title, subtitle, actions, taskCount }: Props) {
  const { selectedAssessment } = useAssessment();
  if (!selectedAssessment) return null;

  const status = selectedAssessment.status ?? "pending";
  const color = statusColor[status] ?? "#94a3b8";

  return (
    <div
      data-testid="assessment-page-header"
      style={{
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 10,
        padding: "14px 18px",
        marginBottom: 20,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 16,
        flexWrap: "wrap",
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, color: "#60a5fa", fontWeight: 700, letterSpacing: 0.5 }}>
            {selectedAssessment.client_name}
          </span>
          <span style={{ color: "#475569" }}>·</span>
          <span style={{ fontSize: 11, color: "#94a3b8" }}>{selectedAssessment.project_name}</span>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color,
              border: `1px solid ${color}66`,
              borderRadius: 999,
              padding: "2px 8px",
              textTransform: "uppercase",
            }}
          >
            {status.replace("_", " ")}
          </span>
          {taskCount !== undefined && (
            <span style={{ fontSize: 10, color: "#64748b" }}>{taskCount} workstream</span>
          )}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{title}</h1>
        {subtitle && <p style={{ margin: "4px 0 0", fontSize: 13, color: "#94a3b8" }}>{subtitle}</p>}
      </div>
      {actions && <div style={{ display: "flex", gap: 8, alignItems: "center" }}>{actions}</div>}
    </div>
  );
}
