import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { WORKSTREAMS, WorkstreamId, listAgents, AgentInfo, createTask, listTasks, Task } from "../api";

function AgentCard({
  ws,
  agentInfo,
  task,
  selected,
  onToggle,
}: {
  ws: typeof WORKSTREAMS[number];
  agentInfo: AgentInfo | undefined;
  task: Task | undefined;
  selected: boolean;
  onToggle: () => void;
}) {
  const isActive = agentInfo?.isActive?.value === "true";
  const taskStatus = task?.status;

  const borderColor = selected
    ? "#3b82f6"
    : taskStatus === "completed"
    ? "#22c55e"
    : taskStatus === "in_progress"
    ? "#f97316"
    : "#334155";

  return (
    <div
      onClick={onToggle}
      style={{
        background: selected ? "#1e3a5f" : "#1e293b",
        border: `2px solid ${borderColor}`,
        borderRadius: 10,
        padding: "16px 20px",
        cursor: "pointer",
        transition: "all 0.15s",
        position: "relative",
      }}
    >
      {taskStatus && (
        <span style={{
          position: "absolute",
          top: 10,
          right: 10,
          fontSize: 10,
          fontWeight: 700,
          color: taskStatus === "completed" ? "#22c55e" : taskStatus === "in_progress" ? "#f97316" : "#94a3b8",
          textTransform: "uppercase",
          letterSpacing: 1,
        }}>
          {taskStatus.replace("_", " ")}
        </span>
      )}
      <div style={{ fontSize: 28, marginBottom: 8 }}>{ws.icon}</div>
      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>{ws.label}</h3>
      <p style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.5 }}>
        {agentInfo?.description?.value ?? "Workstream değerlendirme ajanı"}
      </p>
      {selected && (
        <div style={{
          marginTop: 10,
          background: "#3b82f622",
          border: "1px solid #3b82f644",
          borderRadius: 4,
          padding: "4px 8px",
          fontSize: 11,
          color: "#60a5fa",
          fontWeight: 600,
        }}>
          ✓ Seçildi
        </div>
      )}
      {!isActive && agentInfo && (
        <div style={{ marginTop: 8, fontSize: 11, color: "#64748b" }}>⚠️ KG'de kayıtlı değil</div>
      )}
    </div>
  );
}

export default function AgentSelection() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const assessmentId = searchParams.get("assessment_id") ?? "";

  const [agentInfos, setAgentInfos] = useState<AgentInfo[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selected, setSelected] = useState<Set<WorkstreamId>>(new Set());
  const [launching, setLaunching] = useState(false);

  useEffect(() => {
    listAgents().then(setAgentInfos).catch(() => {});
    if (assessmentId) {
      listTasks(assessmentId).then(setTasks).catch(() => {});
    }
  }, [assessmentId]);

  const infoByWorkstream = Object.fromEntries(
    agentInfos.map((a) => [a.workstream?.value ?? "", a])
  );

  const taskByWorkstream = Object.fromEntries(
    tasks.map((t) => [t.workstream, t])
  );

  const toggleWorkstream = (wsId: WorkstreamId) => {
    const next = new Set(selected);
    if (next.has(wsId)) next.delete(wsId);
    else next.add(wsId);
    setSelected(next);
  };

  const handleLaunch = async () => {
    if (!assessmentId || selected.size === 0) return;
    setLaunching(true);
    try {
      await Promise.all(
        [...selected].map((wsId) =>
          createTask({
            assessment_id: assessmentId,
            agent_type: wsId === "kubernetes" ? "kubernetes" : "workstream",
            workstream: wsId,
            scope: null,
            status: "pending",
          })
        )
      );
      navigate(`/sessions?assessment_id=${assessmentId}`);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Ajan Seçimi</h1>
        <p style={{ color: "#94a3b8", fontSize: 14 }}>
          Değerlendirilecek workstream ajanlarını seçin
          {assessmentId && ` — Assessment: ${assessmentId.slice(0, 8)}…`}
        </p>
      </div>

      {!assessmentId && (
        <div style={{
          background: "#1e293b",
          border: "1px solid #f97316",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 20,
          fontSize: 14,
          color: "#f97316",
        }}>
          ⚠️ URL'de assessment_id parametresi eksik. Genel Bakış'tan bir assessment seçin.
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
        gap: 14,
        marginBottom: 24,
      }}>
        {WORKSTREAMS.map((ws) => (
          <AgentCard
            key={ws.id}
            ws={ws}
            agentInfo={infoByWorkstream[ws.id]}
            task={taskByWorkstream[ws.id]}
            selected={selected.has(ws.id)}
            onToggle={() => toggleWorkstream(ws.id)}
          />
        ))}
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <button
          onClick={handleLaunch}
          disabled={!assessmentId || selected.size === 0 || launching}
          style={{
            background: selected.size > 0 && assessmentId ? "#3b82f6" : "#334155",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "12px 28px",
            cursor: selected.size > 0 && assessmentId ? "pointer" : "not-allowed",
            fontWeight: 700,
            fontSize: 15,
            opacity: launching ? 0.6 : 1,
          }}
        >
          {launching ? "Task'lar oluşturuluyor…" : `${selected.size} Ajan Başlat`}
        </button>
        <span style={{ fontSize: 13, color: "#64748b" }}>
          {selected.size} workstream seçili
        </span>
        {selected.size > 0 && (
          <button
            onClick={() => setSelected(new Set())}
            style={{
              background: "transparent",
              color: "#94a3b8",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "8px 14px",
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            Seçimi Temizle
          </button>
        )}
      </div>
    </div>
  );
}
