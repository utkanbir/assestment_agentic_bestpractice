import { useEffect, useState } from "react";
import { Consultant, createConsultant, listAllConsultants } from "../api";
import ExpertiseMultiSelect from "./ExpertiseMultiSelect";

const COPIED_KEY = "aakp_last_copied_assessment_id";

export function getCopiedAssessmentId(): string | null {
  try {
    return sessionStorage.getItem(COPIED_KEY);
  } catch {
    return null;
  }
}

export function setCopiedAssessmentId(id: string) {
  try {
    sessionStorage.setItem(COPIED_KEY, id);
  } catch { /* ignore */ }
}

function ExpertiseChips({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <span style={{ display: "inline-flex", flexWrap: "wrap", gap: 4, marginLeft: 6 }}>
      {tags.map((t) => (
        <span
          key={t}
          style={{
            background: "#1e3a5f",
            color: "#93c5fd",
            borderRadius: 8,
            padding: "1px 6px",
            fontSize: 10,
          }}
        >
          {t}
        </span>
      ))}
    </span>
  );
}

export default function ConsultantPanel() {
  const [allConsultants, setAllConsultants] = useState<Consultant[]>([]);
  const [form, setForm] = useState({ first_name: "", last_name: "", role: "", expertise: [] as string[] });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const reload = () => {
    listAllConsultants().then(setAllConsultants).catch(() => setAllConsultants([]));
  };

  useEffect(() => { reload(); }, []);

  const handleCreate = async () => {
    if (!form.first_name.trim() || !form.last_name.trim()) return;
    setBusy(true);
    setMsg("");
    try {
      await createConsultant({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        role: form.role.trim() || undefined,
        expertise: form.expertise,
      });
      setForm({ first_name: "", last_name: "", role: "", expertise: [] });
      setMsg("Danışman oluşturuldu.");
      reload();
    } catch {
      setMsg("Danışman oluşturulamadı.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      data-testid="consultant-panel"
      style={{
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 10,
        padding: 16,
        marginBottom: 20,
      }}
    >
      <h3 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 12px" }}>Danışman Havuzu</h3>

      {allConsultants.length > 0 ? (
        <ul style={{ margin: "0 0 16px", paddingLeft: 18, fontSize: 13, color: "#cbd5e1" }}>
          {allConsultants.map((c) => (
            <li key={c.id} data-testid={`consultant-listed-${c.id.slice(0, 8)}`} style={{ marginBottom: 6 }}>
              {c.first_name} {c.last_name}
              {c.role ? <span style={{ color: "#64748b" }}> — {c.role}</span> : null}
              <ExpertiseChips tags={c.expertise ?? []} />
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ fontSize: 12, color: "#64748b", margin: "0 0 16px" }}>Henüz danışman tanımlanmadı.</p>
      )}

      <div style={{ borderTop: "1px solid #334155", paddingTop: 12 }}>
        <p style={{ fontSize: 12, color: "#94a3b8", margin: "0 0 8px" }}>Yeni danışman oluştur</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
          <input
            data-testid="consultant-first-name"
            placeholder="Ad *"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            style={inputStyle}
          />
          <input
            data-testid="consultant-last-name"
            placeholder="Soyad *"
            value={form.last_name}
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="Rol"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            style={inputStyle}
          />
          <ExpertiseMultiSelect
            value={form.expertise}
            onChange={(expertise) => setForm({ ...form, expertise })}
          />
        </div>
        <button
          data-testid="consultant-create-btn"
          onClick={handleCreate}
          disabled={busy}
          style={btnStyle}
        >
          {busy ? "…" : "Oluştur"}
        </button>
      </div>

      {msg && <p style={{ fontSize: 11, color: "#4ade80", marginTop: 10, marginBottom: 0 }}>{msg}</p>}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  flex: 1,
  minWidth: 140,
  background: "#0f1117",
  border: "1px solid #334155",
  borderRadius: 6,
  padding: "6px 10px",
  color: "#e2e8f0",
  fontSize: 12,
};

const btnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  padding: "6px 14px",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};
