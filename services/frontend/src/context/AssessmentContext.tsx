import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Assessment, listAssessments } from "../api";

const STORAGE_KEY = "aakp_assessment_id";

type AssessmentContextValue = {
  assessmentId: string;
  setAssessmentId: (id: string) => void;
  assessments: Assessment[];
  selectedAssessment: Assessment | null;
  loading: boolean;
};

const AssessmentContext = createContext<AssessmentContextValue | null>(null);

export function AssessmentProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [assessmentId, setAssessmentIdState] = useState("");
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAssessments().then(setAssessments).catch(() => setAssessments([])).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const fromUrl = params.get("assessment_id");
    if (fromUrl) {
      setAssessmentIdState(fromUrl);
      localStorage.setItem(STORAGE_KEY, fromUrl);
      return;
    }
    const fromStorage = localStorage.getItem(STORAGE_KEY) ?? "";
    if (fromStorage && fromStorage !== assessmentId) {
      setAssessmentIdState(fromStorage);
      const next = new URLSearchParams(location.search);
      next.set("assessment_id", fromStorage);
      navigate(`${location.pathname}?${next.toString()}`, { replace: true });
    }
  }, [location.pathname, location.search, navigate, assessmentId]);

  const setAssessmentId = (id: string) => {
    setAssessmentIdState(id);
    if (id) localStorage.setItem(STORAGE_KEY, id);
    const params = new URLSearchParams(location.search);
    if (id) params.set("assessment_id", id);
    else params.delete("assessment_id");
    const qs = params.toString();
    navigate(`${location.pathname}${qs ? `?${qs}` : ""}`);
  };

  const selectedAssessment = useMemo(
    () => assessments.find((a) => a.id === assessmentId) ?? null,
    [assessments, assessmentId],
  );

  return (
    <AssessmentContext.Provider
      value={{ assessmentId, setAssessmentId, assessments, selectedAssessment, loading }}
    >
      {children}
    </AssessmentContext.Provider>
  );
}

export function useAssessment() {
  const ctx = useContext(AssessmentContext);
  if (!ctx) throw new Error("useAssessment must be used within AssessmentProvider");
  return ctx;
}

export function useAssessmentNavLink() {
  const { assessmentId, selectedAssessment } = useAssessment();
  return (to: string) => {
    if (!assessmentId) return to;
    const [pathname, query] = to.split("?");
    const params = new URLSearchParams(query ?? "");
    params.set("assessment_id", assessmentId);
    if (
      selectedAssessment?.assessment_mode === "simulated"
      && pathname.replace(/\/+$/, "") === "/interview"
    ) {
      params.set("simulation", "1");
    }
    return `${pathname}?${params.toString()}`;
  };
}

export function RequireAssessment({ children }: { children: ReactNode }) {
  const { assessmentId, assessments, setAssessmentId, loading } = useAssessment();
  if (assessmentId) return <>{children}</>;

  if (loading) {
    return <p style={{ color: "#64748b" }}>Assessment listesi yukleniyor...</p>;
  }
  return (
    <div style={{ maxWidth: 680, margin: "40px auto", background: "#1e293b", border: "1px solid #334155", borderRadius: 12, padding: 24 }}>
      <h2 style={{ marginTop: 0, fontSize: 20 }}>Bu sayfa assessment gerektiriyor</h2>
      <p style={{ color: "#94a3b8", fontSize: 13 }}>Devam etmek icin bir assessment secin.</p>
      <select
        value={assessmentId}
        onChange={(e) => setAssessmentId(e.target.value)}
        style={{ width: "100%", marginTop: 10, background: "#0f1117", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px" }}
      >
        <option value="">Assessment secin</option>
        {assessments.map((a) => (
          <option key={a.id} value={a.id}>
            {a.assessment_mode === "simulated" ? "🤖 " : ""}{a.client_name} - {a.project_name}
          </option>
        ))}
      </select>
      <div style={{ marginTop: 14 }}>
        <Link to="/" style={{ color: "#60a5fa", fontSize: 13 }}>
          Genel bakisa don
        </Link>
      </div>
    </div>
  );
}
