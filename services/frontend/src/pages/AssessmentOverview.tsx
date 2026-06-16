import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Assessment, Task, Finding,
  listAssessments, listTasks, listFindings,
  createAssessment,
} from "../api";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
  info:     "#60a5fa",
};

function Badge({ sev, count }: { sev: string; count: number }) {
  return (
    <span style={{
      background: SEV_COLOR[sev] + "22",
      color: SEV_COLOR[sev],
      border: `1px solid ${SEV_COLOR[sev]}44`,
      borderRadius: 4,
      padding: "2px 8px",
      fontSize: 12,
      fontWeight: 600,
    }}>
      {sev.toUpperCase()} {count}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending:     "#94a3b8",
    in_progress: "#3b82f6",
    completed:   "#22c55e",
    failed:      "#ef4444",
  };
  const c = colors[status] ?? "#94a3b8";
  return (
    <span style={{
      background: c + "22",
      color: c,
      border: `1px solid ${c}44`,
      borderRadius: 12,
      padding: "2px 10px",
      fontSize: 11,
      fontWeight: 600,
      textTransform: "uppercase",
    }}>
      {status.replace("_", " ")}
    </span>
  );
}

interface AssessmentCardProps {
  assessment: Assessment;
  onClick: () => void;
}

function AssessmentCard({ assessment, onClick }: AssessmentCardProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);

  useEffect(() => {
    listTasks(assessment.id).then(setTasks).catch(() => {});
  }, [assessment.id]);

  useEffect(() => {
    if (!tasks.length) return;
    Promise.all(tasks.map((t) => listFindings(t.id)))
      .then((all) => setFindings(all.flat()))
      .catch(() => {});
  }, [tasks]);

  const sevCounts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] ?? 0) + 1;
    return acc;
  }, {});

  const completedTasks = tasks.filter((t) => t.status === "completed").length;

  return (
    <div
      onClick={onClick}
      style={{
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 10,
        padding: "20px",
        cursor: "pointer",
        transition: "border-color 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3b82f6")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#334155")}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{assessment.client_name}</h3>
          <p style={{ fontSize: 13, color: "#94a3b8" }}>{assessment.project_name}</p>
        </div>
        <StatusPill status={assessment.status ?? "pending"} />
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
        {Object.entries(sevCounts).map(([sev, cnt]) => (
          <Badge key={sev} sev={sev} count={cnt} />
        ))}
        {findings.length === 0 && <span style={{ fontSize: 12, color: "#64748b" }}>Henüz bulgu yok</span>}
      </div>

      <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#64748b" }}>
        <span>📋 {tasks.length} task</span>
        <span>✅ {completedTasks} tamamlandı</span>
        <span>🔍 {findings.length} bulgu</span>
        <span style={{ marginLeft: "auto" }}>{new Date(assessment.created_at).toLocaleDateString("tr-TR")}</span>
      </div>
    </div>
  );
}

const EMPTY_FORM = { client_name: "", project_name: "", description: "" };

export default function AssessmentOverview() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    listAssessments()
      .then(setAssessments)
      .catch(() => setAssessments([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openModal = () => { setForm(EMPTY_FORM); setError(""); setShowModal(true); };
  const closeModal = () => setShowModal(false);

  const handleCreate = async () => {
    if (!form.client_name.trim() || !form.project_name.trim()) {
      setError("Müşteri adı ve proje adı zorunludur.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body: any = { client_name: form.client_name.trim(), project_name: form.project_name.trim() };
      if (form.description.trim()) body.description = form.description.trim();
      await createAssessment(body);
      closeModal();
      load();
    } catch {
      setError("Assessment oluşturulamadı. Tekrar deneyin.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* Modal overlay — S8-FA-001 */}
      {showModal && (
        <div
          onClick={closeModal}
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)",
            zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#1e293b", border: "1px solid #3b82f6",
              borderRadius: 12, padding: 28, width: 480, maxWidth: "90vw",
              boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
            }}
          >
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>Yeni Assessment Oluştur</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>Müşteri Adı *</label>
                <input
                  autoFocus
                  placeholder="örn. Migros Ticaret A.Ş."
                  value={form.client_name}
                  onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>Proje Adı *</label>
                <input
                  placeholder="örn. Data Platform Assessment 2026"
                  value={form.project_name}
                  onChange={(e) => setForm({ ...form, project_name: e.target.value })}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>Açıklama</label>
                <textarea
                  placeholder="Projenin kapsamı ve hedefleri…"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  style={{ ...inputStyle, resize: "vertical" }}
                />
              </div>
              {error && <p style={{ color: "#f87171", fontSize: 12, margin: 0 }}>{error}</p>}
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 20, justifyContent: "flex-end" }}>
              <button onClick={closeModal} style={{ ...btnStyle, background: "#334155" }}>İptal</button>
              <button
                onClick={handleCreate}
                disabled={saving}
                style={{ ...btnStyle, opacity: saving ? 0.6 : 1, minWidth: 100 }}
              >
                {saving ? "Oluşturuluyor…" : "Oluştur"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Assessment Genel Bakış</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>Tüm değerlendirme projeleri ve bulgu özeti</p>
        </div>
        <button
          onClick={openModal}
          style={{
            background: "#3b82f6", color: "#fff", border: "none",
            borderRadius: 8, padding: "10px 20px", cursor: "pointer",
            fontWeight: 600, fontSize: 14,
          }}
        >
          + Yeni Assessment
        </button>
      </div>

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
      ) : assessments.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 40, marginBottom: 12 }}>📊</p>
          <p style={{ fontSize: 16 }}>Henüz assessment yok.</p>
          <p style={{ fontSize: 13, marginTop: 6 }}>Yeni assessment oluşturarak başlayın.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 16 }}>
          {assessments.map((a) => (
            <AssessmentCard
              key={a.id}
              assessment={a}
              onClick={() => navigate(`/interview?assessment_id=${a.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: "#0f1117",
  border: "1px solid #334155",
  borderRadius: 6,
  padding: "8px 12px",
  color: "#e2e8f0",
  fontSize: 14,
  width: "100%",
};

const btnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  padding: "8px 18px",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 14,
};
