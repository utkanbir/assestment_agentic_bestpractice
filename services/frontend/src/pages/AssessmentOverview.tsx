import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Assessment,
  listAssessments, createAssessment,
  deleteAssessment, duplicateAssessment,
  startSimulation,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";
import { getCopiedAssessmentId, setCopiedAssessmentId } from "../components/ConsultantPanel";

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "#94a3b8", in_progress: "#3b82f6", completed: "#22c55e", failed: "#ef4444",
    running: "#3b82f6", stopped: "#f97316", finalized: "#22c55e",
  };
  const c = colors[status] ?? "#94a3b8";
  return (
    <span style={{
      background: c + "22", color: c, border: `1px solid ${c}44`,
      borderRadius: 12, padding: "2px 10px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
    }}>
      {status.replace("_", " ")}
    </span>
  );
}

const EMPTY_FORM = { client_name: "", project_name: "", description: "" };
const EMPTY_SIM_FORM = { client_name: "", project_name: "", industry: "perakende", size: "buyuk" };

function SimulatedBadge() {
  return (
    <span
      data-testid="ai-simulated-badge"
      style={{
        background: "#581c8722", color: "#c084fc", border: "1px solid #7e22ce66",
        borderRadius: 12, padding: "2px 10px", fontSize: 10, fontWeight: 700,
        textTransform: "uppercase", marginLeft: 8,
      }}
    >
      AI Simulated
    </span>
  );
}

export default function AssessmentOverview() {
  const navigate = useNavigate();
  const { assessmentId, setAssessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showSimModal, setShowSimModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [simForm, setSimForm] = useState(EMPTY_SIM_FORM);
  const [saving, setSaving] = useState(false);
  const [simSaving, setSimSaving] = useState(false);
  const [error, setError] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [dupModal, setDupModal] = useState<Assessment | null>(null);
  const [dupIncludeQa, setDupIncludeQa] = useState(false);
  const [dupIncludeTasks, setDupIncludeTasks] = useState(true);
  const [dupBusy, setDupBusy] = useState(false);
  const [deleteBusy, setDeleteBusy] = useState<string | null>(null);
  const [pasteBusy, setPasteBusy] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(() => getCopiedAssessmentId());

  const loadAssessments = () => {
    setLoading(true);
    listAssessments().then(setAssessments).catch(() => setAssessments([])).finally(() => setLoading(false));
  };

  useEffect(() => { loadAssessments(); }, []);

  const handleCreate = async () => {
    if (!form.client_name.trim() || !form.project_name.trim()) {
      setError("Müşteri adı ve proje adı zorunludur.");
      return;
    }
    setSaving(true);
    try {
      const created = await createAssessment({
        client_name: form.client_name.trim(),
        project_name: form.project_name.trim(),
      });
      setShowModal(false);
      loadAssessments();
      setAssessmentId(created.id);
    } catch {
      setError("Assessment oluşturulamadı.");
    } finally {
      setSaving(false);
    }
  };

  const handleStartSimulation = async () => {
    if (!simForm.client_name.trim() || !simForm.project_name.trim()) {
      setError("Müşteri adı ve proje adı zorunludur.");
      return;
    }
    setSimSaving(true);
    setError("");
    try {
      const created = await startSimulation({
        client_name: simForm.client_name.trim(),
        project_name: simForm.project_name.trim(),
        company_profile: { industry: simForm.industry, size: simForm.size },
      });
      setShowSimModal(false);
      loadAssessments();
      navigate(`/interview?simulation=1&assessment_id=${created.id}`);
    } catch {
      setError("Simülasyon başlatılamadı.");
    } finally {
      setSimSaving(false);
    }
  };

  const handleGoInterview = (a: Assessment, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setAssessmentId(a.id);
    const sim = a.assessment_mode === "simulated" ? "?simulation=1" : "";
    navigate(withAssessment(`/interview${sim}`));
  };

  const handleCopyAssessment = (a: Assessment, e: React.MouseEvent) => {
    e.stopPropagation();
    setCopiedAssessmentId(a.id);
    setCopiedId(a.id);
    openDupModal(a, e);
  };

  const handlePaste = async () => {
    const sourceId = getCopiedAssessmentId();
    if (!sourceId) {
      setError("Panoda kopyalanmış assessment yok.");
      return;
    }
    setPasteBusy(true);
    setError("");
    try {
      const created = await duplicateAssessment(sourceId, {
        include_qa: true,
        include_tasks: true,
      });
      setCopiedAssessmentId(created.id);
      setCopiedId(created.id);
      loadAssessments();
      setAssessmentId(created.id);
    } catch {
      setError("Yapıştırma başarısız.");
    } finally {
      setPasteBusy(false);
    }
  };

  const handleDeleteAssessment = async (a: Assessment, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`"${a.client_name} — ${a.project_name}" silinsin mi?`)) return;
    setDeleteBusy(a.id);
    try {
      await deleteAssessment(a.id);
      if (assessmentId === a.id) setAssessmentId("");
      if (copiedId === a.id) {
        sessionStorage.removeItem("aakp_last_copied_assessment_id");
        setCopiedId(null);
      }
      loadAssessments();
    } catch {
      setError("Assessment silinemedi.");
    } finally {
      setDeleteBusy(null);
      setMenuOpenId(null);
    }
  };

  const handleDuplicate = async () => {
    if (!dupModal) return;
    setDupBusy(true);
    try {
      const created = await duplicateAssessment(dupModal.id, {
        include_qa: dupIncludeQa,
        include_tasks: dupIncludeTasks,
      });
      setCopiedAssessmentId(created.id);
      setCopiedId(created.id);
      setDupModal(null);
      loadAssessments();
      setAssessmentId(created.id);
    } catch {
      setError("Kopyalama başarısız.");
    } finally {
      setDupBusy(false);
    }
  };

  const openDupModal = (a: Assessment, e: React.MouseEvent) => {
    e.stopPropagation();
    setDupIncludeQa(false);
    setDupIncludeTasks(true);
    setDupModal(a);
    setMenuOpenId(null);
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      {showModal && (
        <div onClick={() => setShowModal(false)} style={modalOverlay}>
          <div onClick={(e) => e.stopPropagation()} style={modalBox}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>Yeni Assessment Oluştur</h2>
            <input placeholder="Müşteri Adı *" value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} style={inputStyle} />
            <input placeholder="Proje Adı *" value={form.project_name} onChange={(e) => setForm({ ...form, project_name: e.target.value })} style={{ ...inputStyle, marginTop: 10 }} />
            {error && <p style={{ color: "#f87171", fontSize: 12 }}>{error}</p>}
            <div style={{ display: "flex", gap: 10, marginTop: 16, justifyContent: "flex-end" }}>
              <button onClick={() => setShowModal(false)} style={{ ...btnStyle, background: "#334155" }}>İptal</button>
              <button onClick={handleCreate} disabled={saving} style={btnStyle}>{saving ? "…" : "Oluştur"}</button>
            </div>
          </div>
        </div>
      )}

      {dupModal && (
        <div onClick={() => setDupModal(null)} style={modalOverlay}>
          <div onClick={(e) => e.stopPropagation()} style={modalBox}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Assessment Kopyala</h2>
            <p style={{ color: "#94a3b8", fontSize: 13, marginBottom: 16 }}>
              {dupModal.client_name} — {dupModal.project_name}
            </p>
            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, fontSize: 13, color: "#e2e8f0" }}>
              <input type="checkbox" checked={dupIncludeTasks} onChange={(e) => setDupIncludeTasks(e.target.checked)} />
              Task&apos;ları kopyala
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, fontSize: 13, color: "#e2e8f0" }}>
              <input type="checkbox" checked={dupIncludeQa} onChange={(e) => setDupIncludeQa(e.target.checked)} disabled={!dupIncludeTasks} />
              Soru & cevapları kopyala
            </label>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button onClick={() => setDupModal(null)} style={{ ...btnStyle, background: "#334155" }}>İptal</button>
              <button data-testid="confirm-duplicate-btn" onClick={handleDuplicate} disabled={dupBusy} style={btnStyle}>
                {dupBusy ? "…" : "Kopyala"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showSimModal && (
        <div onClick={() => setShowSimModal(false)} style={modalOverlay}>
          <div onClick={(e) => e.stopPropagation()} style={{ ...modalBox, borderColor: "#7e22ce" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>AI Simülasyon Başlat</h2>
            <p style={{ color: "#94a3b8", fontSize: 13, marginBottom: 16 }}>
              8 workstream boyunca otomatik soru-cevap-değerlendirme çalışır. İzleme modunda canlı takip edebilirsiniz.
            </p>
            <input placeholder="Müşteri Adı *" value={simForm.client_name} onChange={(e) => setSimForm({ ...simForm, client_name: e.target.value })} style={inputStyle} />
            <input placeholder="Proje Adı *" value={simForm.project_name} onChange={(e) => setSimForm({ ...simForm, project_name: e.target.value })} style={{ ...inputStyle, marginTop: 10 }} />
            <input placeholder="Sektör" value={simForm.industry} onChange={(e) => setSimForm({ ...simForm, industry: e.target.value })} style={{ ...inputStyle, marginTop: 10 }} />
            {error && <p style={{ color: "#f87171", fontSize: 12 }}>{error}</p>}
            <div style={{ display: "flex", gap: 10, marginTop: 16, justifyContent: "flex-end" }}>
              <button onClick={() => setShowSimModal(false)} style={{ ...btnStyle, background: "#334155" }}>İptal</button>
              <button data-testid="start-simulation-btn" onClick={handleStartSimulation} disabled={simSaving} style={{ ...btnStyle, background: "#7e22ce" }}>
                {simSaving ? "…" : "Simülasyonu Başlat"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Assessment Genel Bakış</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>Assessment seçin veya yeni oluşturun</p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            data-testid="paste-assessment-btn"
            onClick={handlePaste}
            disabled={pasteBusy || !copiedId}
            style={{ ...btnStyle, background: copiedId ? "#0d9488" : "#334155" }}
            title={copiedId ? `Kaynak: ${copiedId.slice(0, 8)}…` : "Önce bir assessment kopyalayın"}
          >
            {pasteBusy ? "…" : "Yapıştır"}
          </button>
          <button data-testid="open-simulation-modal" onClick={() => { setError(""); setShowSimModal(true); }} style={{ ...btnStyle, background: "#7e22ce" }}>
            AI Simülasyon Başlat
          </button>
          <button onClick={() => setShowModal(true)} style={btnStyle}>+ Yeni Assessment</button>
        </div>
      </div>

      {error && !showModal && !showSimModal && !dupModal && (
        <p style={{ color: "#f87171", fontSize: 12, marginBottom: 12 }}>{error}</p>
      )}

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {assessments.map((a) => {
            const isSimulated = a.assessment_mode === "simulated";
            const isSelected = assessmentId === a.id;
            return (
              <div
                key={a.id}
                data-testid={isSimulated ? "assessment-card-simulated" : "assessment-card-live"}
                onClick={() => handleGoInterview(a)}
                style={{
                  background: isSelected
                    ? (isSimulated ? "#2e1065" : "#1e3a5f")
                    : (isSimulated ? "#1a1033" : "#1e293b"),
                  border: `1px solid ${isSelected
                    ? (isSimulated ? "#7e22ce" : "#3b82f6")
                    : (isSimulated ? "#581c87" : "#334155")}`,
                  borderRadius: 10,
                  padding: 16,
                  cursor: "pointer",
                  position: "relative",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <strong>{a.client_name}</strong>
                    <span style={{ color: "#94a3b8", marginLeft: 8, fontSize: 13 }}>{a.project_name}</span>
                    {isSimulated && <SimulatedBadge />}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <StatusPill status={a.simulation_status ?? a.status ?? "pending"} />
                    <button
                      data-testid={`copy-assessment-${a.id.slice(0, 8)}`}
                      onClick={(e) => handleCopyAssessment(a, e)}
                      style={cardActionStyle}
                    >
                      Kopyala
                    </button>
                    <button
                      data-testid={`interview-assessment-${a.id.slice(0, 8)}`}
                      onClick={(e) => handleGoInterview(a, e)}
                      style={cardActionStyle}
                    >
                      Interview&apos;a git
                    </button>
                    <button
                      data-testid={`assessment-menu-${a.id.slice(0, 8)}`}
                      onClick={(e) => { e.stopPropagation(); setMenuOpenId(menuOpenId === a.id ? null : a.id); }}
                      style={{
                        background: "transparent", border: "none", color: "#94a3b8",
                        cursor: "pointer", fontSize: 18, lineHeight: 1, padding: "0 4px",
                      }}
                      title="Menü"
                    >
                      ⋮
                    </button>
                  </div>
                </div>
                {menuOpenId === a.id && (
                  <div
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      position: "absolute", right: 12, top: 44, zIndex: 10,
                      background: "#0f172a", border: "1px solid #334155", borderRadius: 8,
                      minWidth: 140, boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                    }}
                  >
                    <button
                      data-testid="duplicate-assessment-btn"
                      onClick={(e) => openDupModal(a, e)}
                      style={menuItemStyle}
                    >
                      Kopyala…
                    </button>
                    <button
                      data-testid="delete-assessment-btn"
                      onClick={(e) => handleDeleteAssessment(a, e)}
                      disabled={deleteBusy === a.id}
                      style={{ ...menuItemStyle, color: "#f87171" }}
                    >
                      {deleteBusy === a.id ? "…" : "Sil"}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: "#0f1117", border: "1px solid #334155", borderRadius: 6,
  padding: "8px 12px", color: "#e2e8f0", fontSize: 14, width: "100%", boxSizing: "border-box",
};
const btnStyle: React.CSSProperties = {
  background: "#3b82f6", color: "#fff", border: "none", borderRadius: 8,
  padding: "10px 20px", cursor: "pointer", fontWeight: 600, fontSize: 14,
};
const cardActionStyle: React.CSSProperties = {
  background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 6,
  padding: "4px 10px", fontSize: 11, cursor: "pointer", fontWeight: 600,
};
const modalOverlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 200,
  display: "flex", alignItems: "center", justifyContent: "center",
};
const modalBox: React.CSSProperties = {
  background: "#1e293b", border: "1px solid #3b82f6", borderRadius: 12,
  padding: 28, width: 480, maxWidth: "90vw",
};
const menuItemStyle: React.CSSProperties = {
  display: "block", width: "100%", textAlign: "left",
  background: "transparent", border: "none", padding: "10px 14px",
  color: "#e2e8f0", cursor: "pointer", fontSize: 13,
};
