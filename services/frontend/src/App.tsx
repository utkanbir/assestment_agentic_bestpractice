import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import AssessmentOverview from "./pages/AssessmentOverview";
import RiskHeatmap from "./pages/RiskHeatmap";
import ExecutiveSummaryPage from "./pages/ExecutiveSummary";
import ConsolidatedRoadmap from "./pages/ConsolidatedRoadmap";
import CrossTaskDependencies from "./pages/CrossTaskDependencies";
import ApprovalQueue from "./pages/ApprovalQueue";
import MaturityDashboard from "./pages/MaturityDashboard";
import ReportStudio from "./pages/ReportStudio";
import ChatPage from "./pages/ChatPage";
import CatalogLink from "./pages/CatalogLink";
import InterviewRoom from "./pages/InterviewRoom";
import QuestionManagement from "./pages/QuestionManagement";
import ConsultantManagement from "./pages/ConsultantManagement";
import AjanYonetimi from "./pages/AjanYonetimi";
import KnowledgeArchitecture from "./pages/KnowledgeArchitecture";
import OntologyBrowser from "./pages/OntologyBrowser";
import KnowledgeGraphExplorer from "./pages/KnowledgeGraphExplorer";
import AgentKnowledgeGraphPage from "./pages/AgentKnowledgeGraphPage";
import TechStackPage from "./pages/TechStackPage";
import ExecutionPlan from "./pages/ExecutionPlan";
import ChatWidget from "./components/ChatWidget";
import AppSidebar, { type NavItem } from "./components/AppSidebar";
import { AssessmentProvider, RequireAssessment, useAssessment, useAssessmentNavLink } from "./context/AssessmentContext";
import { getPendingApprovals, getPendingQuestions, getSimulationStatus, type SimulationProgress } from "./api";

function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [pendingBadge, setPendingBadge] = useState(0);
  const [simHeaderStatus, setSimHeaderStatus] = useState<string | null>(null);
  const [simHeaderProgress, setSimHeaderProgress] = useState<SimulationProgress | null>(null);
  const { assessmentId, assessments, selectedAssessment, setAssessmentId } = useAssessment();
  const withAssessment = useAssessmentNavLink();

  const links: NavItem[] = [
    { to: "/", label: "Genel Bakış", icon: "home", group: "Genel", end: true },
    { to: withAssessment("/interview"), label: "Interview", icon: "mic", group: "Genel" },
    { to: withAssessment("/questions"), label: "Sorular", icon: "list", group: "Genel" },
    { to: "/danisman", label: "Danışman", icon: "users", group: "Genel" },
    { to: withAssessment("/ajan-yonetimi"), label: "Ajan Yönetimi", icon: "bot", group: "Knowledge" },
    { to: withAssessment("/knowledge-graph"), label: "Knowledge Graph", icon: "graph", group: "Knowledge", indent: true },
    { to: withAssessment("/mimari"), label: "Mimari", icon: "layers", group: "Knowledge" },
    { to: "/teknoloji", label: "Teknoloji Stack", icon: "stack", group: "Knowledge" },
    { to: withAssessment("/yurutme-plani"), label: "Yürütme Planı", icon: "flow", group: "Operasyon" },
    { to: withAssessment("/approvals"), label: "İnceleme Merkezi", icon: "clipboard", group: "Analiz", badge: true },
    { to: withAssessment("/heatmap"), label: "Risk Heatmap", icon: "flame", group: "Analiz" },
    { to: withAssessment("/maturity"), label: "Olgunluk", icon: "chart", group: "Analiz" },
    { to: withAssessment("/executive"), label: "Yönetici Özeti", icon: "briefcase", group: "Analiz" },
    { to: withAssessment("/roadmap"), label: "Roadmap", icon: "map", group: "Analiz" },
    { to: withAssessment("/report"), label: "Rapor Stüdyosu", icon: "document", group: "Analiz" },
    { to: withAssessment("/chat"), label: "Chat", icon: "message", group: "Operasyon" },
  ];

  useEffect(() => {
    if (!assessmentId) {
      setPendingBadge(0);
      return;
    }
    const load = async () => {
      try {
        const [queue, questions] = await Promise.all([
          getPendingApprovals(assessmentId),
          getPendingQuestions(assessmentId),
        ]);
        setPendingBadge(queue.total + questions.length);
      } catch {
        setPendingBadge(0);
      }
    };
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [assessmentId]);

  useEffect(() => {
    if (!assessmentId || selectedAssessment?.assessment_mode !== "simulated") {
      setSimHeaderStatus(null);
      setSimHeaderProgress(null);
      return;
    }
    const poll = async () => {
      try {
        const st = await getSimulationStatus(assessmentId);
        setSimHeaderStatus(st.simulation_status);
        setSimHeaderProgress(st.simulation_progress);
      } catch {
        setSimHeaderStatus(null);
        setSimHeaderProgress(null);
      }
    };
    void poll();
    const t = setInterval(() => { void poll(); }, 3000);
    return () => clearInterval(t);
  }, [assessmentId, selectedAssessment?.assessment_mode]);

  const simHeaderPct = Math.min(
    100,
    ((simHeaderProgress?.questions_evaluated ?? 0) / Math.max(1, simHeaderProgress?.total_questions_planned ?? 1)) * 100,
  );
  const showSimHeaderProgress = selectedAssessment?.assessment_mode === "simulated" && simHeaderStatus === "running";

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0b0f1a", color: "#e2e8f0" }}>
      <AppSidebar
        items={links}
        pendingBadge={pendingBadge}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header
          data-testid="app-topbar"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 12,
            padding: "10px 20px",
            borderBottom: "1px solid #1e293b",
            background: "#0f1117",
            position: "sticky",
            top: 0,
            zIndex: 50,
          }}
        >
          <select
            data-testid="assessment-selector"
            value={assessmentId}
            onChange={(e) => setAssessmentId(e.target.value)}
            style={{
              background: "#1e293b",
              color: "#e2e8f0",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "6px 8px",
              fontSize: 12,
              minWidth: 220,
            }}
          >
            <option value="">Assessment seçin</option>
            {assessments.map((a) => (
              <option key={a.id} value={a.id} style={a.assessment_mode === "simulated" ? { color: "#c084fc" } : undefined}>
                {a.assessment_mode === "simulated" ? "🤖 " : ""}{a.client_name} - {a.project_name}
              </option>
            ))}
          </select>
          {showSimHeaderProgress && (
            <div
              data-testid="header-simulation-progress"
              style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 180 }}
            >
              <span style={{ fontSize: 11, color: "#c084fc", whiteSpace: "nowrap" }}>
                Sim {simHeaderProgress?.questions_evaluated ?? 0}/{simHeaderProgress?.total_questions_planned ?? "…"}
              </span>
              <div style={{ flex: 1, height: 5, background: "#581c87", borderRadius: 3, overflow: "hidden", minWidth: 80 }}>
                <div style={{ height: "100%", width: `${simHeaderPct}%`, background: "#a78bfa", transition: "width 0.3s" }} />
              </div>
            </div>
          )}
          {selectedAssessment && (
            <span style={{
              fontSize: 11,
              color: selectedAssessment.assessment_mode === "simulated" ? "#c084fc" : "#60a5fa",
              border: `1px solid ${selectedAssessment.assessment_mode === "simulated" ? "#7e22ce" : "#1d4ed8"}`,
              borderRadius: 999, padding: "4px 8px",
            }}>
              {selectedAssessment.assessment_mode === "simulated" ? "AI Simulated · " : ""}
              {selectedAssessment.client_name}
            </span>
          )}
        </header>

        <main style={{ flex: 1, padding: "24px 20px", overflow: "auto", boxSizing: "border-box" }}>
          <Routes>
            <Route path="/" element={<AssessmentOverview />} />
            <Route path="/interview" element={<RequireAssessment><InterviewRoom /></RequireAssessment>} />
            <Route path="/questions" element={<RequireAssessment><QuestionManagement /></RequireAssessment>} />
            <Route path="/danisman" element={<ConsultantManagement />} />
            <Route path="/ajan-yonetimi" element={<RequireAssessment><AjanYonetimi /></RequireAssessment>} />
            <Route path="/knowledge-graph" element={<RequireAssessment><AgentKnowledgeGraphPage /></RequireAssessment>} />
            <Route path="/mimari" element={<RequireAssessment><KnowledgeArchitecture /></RequireAssessment>} />
            <Route path="/teknoloji" element={<TechStackPage />} />
            <Route path="/ontoloji" element={<RequireAssessment><OntologyBrowser /></RequireAssessment>} />
            <Route path="/kg-graf" element={<RequireAssessment><KnowledgeGraphExplorer /></RequireAssessment>} />
            <Route path="/yurutme-plani" element={<RequireAssessment><ExecutionPlan /></RequireAssessment>} />
            <Route path="/approvals" element={<RequireAssessment><ApprovalQueue /></RequireAssessment>} />
            <Route path="/heatmap" element={<RequireAssessment><RiskHeatmap /></RequireAssessment>} />
            <Route path="/maturity" element={<RequireAssessment><MaturityDashboard /></RequireAssessment>} />
            <Route path="/executive" element={<RequireAssessment><ExecutiveSummaryPage /></RequireAssessment>} />
            <Route path="/roadmap" element={<RequireAssessment><ConsolidatedRoadmap /></RequireAssessment>} />
            <Route path="/dependencies" element={<RequireAssessment><CrossTaskDependencies /></RequireAssessment>} />
            <Route path="/report" element={<RequireAssessment><ReportStudio /></RequireAssessment>} />
            <Route path="/chat" element={<RequireAssessment><ChatPage /></RequireAssessment>} />
            <Route path="/catalog" element={<RequireAssessment><CatalogLink /></RequireAssessment>} />
          </Routes>
        </main>

        <footer style={{
          padding: "10px 20px",
          borderTop: "1px solid #1e293b",
          fontSize: 11,
          color: "#475569",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <span>AAKP — AI Assessment Knowledge Platform</span>
          <span>Migros Ticaret A.Ş. © 2026</span>
        </footer>
      </div>

      <ChatWidget />
    </div>
  );
}

export default function App() {
  return (
    <AssessmentProvider>
      <AppShell />
    </AssessmentProvider>
  );
}
