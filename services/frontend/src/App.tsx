// S7-FA-006: Assessment overview general status dashboard
// S7-FA-008: Responsive design and UX polish
import { useState } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import AssessmentOverview from "./pages/AssessmentOverview";
import AgentSelection from "./pages/AgentSelection";
import ParallelSessions from "./pages/ParallelSessions";
import RiskHeatmap from "./pages/RiskHeatmap";
import ExecutiveSummaryPage from "./pages/ExecutiveSummary";
import ConsolidatedRoadmap from "./pages/ConsolidatedRoadmap";
import CrossTaskDependencies from "./pages/CrossTaskDependencies";
import ApprovalQueue from "./pages/ApprovalQueue";
import MaturityDashboard from "./pages/MaturityDashboard";
import ReportExport from "./pages/ReportExport";
import CatalogLink from "./pages/CatalogLink";
import InterviewRoom from "./pages/InterviewRoom";
import QuestionManagement from "./pages/QuestionManagement";
import AjanYonetimi from "./pages/AjanYonetimi";

const navStyle = (active: boolean): React.CSSProperties => ({
  padding: "7px 14px",
  borderRadius: 6,
  textDecoration: "none",
  color: active ? "#fff" : "#94a3b8",
  background: active ? "#3b82f6" : "transparent",
  fontWeight: active ? 600 : 400,
  fontSize: 13,
  transition: "all 0.15s",
  whiteSpace: "nowrap",
});

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { to: "/", label: "Genel Bakış", end: true },
    { to: "/interview", label: "Interview" },
    { to: "/questions", label: "Sorular" },
    { to: "/ajan-yonetimi", label: "Ajan Yönetimi" },
    { to: "/approvals", label: "Onay Kuyruğu" },
    { to: "/heatmap", label: "Risk Heatmap" },
    { to: "/maturity", label: "Olgunluk" },
    { to: "/executive", label: "Executive" },
    { to: "/roadmap", label: "Roadmap" },
    { to: "/dependencies", label: "Bağımlılıklar" },
    { to: "/report", label: "PDF Rapor" },
    { to: "/catalog", label: "Katalog" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "#0b0f1a", color: "#e2e8f0" }}>
      {/* Top nav — S7-FA-008: responsive */}
      <nav style={{
        display: "flex",
        alignItems: "center",
        gap: 4,
        padding: "10px 20px",
        borderBottom: "1px solid #1e293b",
        background: "#0f1117",
        flexWrap: "wrap",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        <span style={{ fontWeight: 800, fontSize: 17, marginRight: 16, color: "#60a5fa", flexShrink: 0 }}>
          AAKP
        </span>

        {/* Desktop nav */}
        <div style={{ display: "flex", gap: 2, flexWrap: "wrap", flex: 1 }}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              style={({ isActive }) => navStyle(isActive)}
            >
              {l.label}
            </NavLink>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen((v) => !v)}
          style={{
            display: "none",
            background: "transparent",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "6px 10px",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: 18,
          }}
          aria-label="Menu"
        >
          ☰
        </button>
      </nav>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div style={{
          background: "#0f1117",
          borderBottom: "1px solid #1e293b",
          padding: "8px 20px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              onClick={() => setMenuOpen(false)}
              style={({ isActive }) => ({ ...navStyle(isActive), display: "block" })}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      )}

      {/* Page content */}
      <main style={{ flex: 1, padding: "24px 20px", maxWidth: "100%", boxSizing: "border-box" }}>
        <Routes>
          <Route path="/" element={<AssessmentOverview />} />
          <Route path="/agents" element={<AgentSelection />} />
          <Route path="/sessions" element={<ParallelSessions />} />
          <Route path="/interview" element={<InterviewRoom />} />
          <Route path="/questions" element={<QuestionManagement />} />
          <Route path="/ajan-yonetimi" element={<AjanYonetimi />} />
          <Route path="/approvals" element={<ApprovalQueue />} />
          <Route path="/heatmap" element={<RiskHeatmap />} />
          <Route path="/maturity" element={<MaturityDashboard />} />
          <Route path="/executive" element={<ExecutiveSummaryPage />} />
          <Route path="/roadmap" element={<ConsolidatedRoadmap />} />
          <Route path="/dependencies" element={<CrossTaskDependencies />} />
          <Route path="/report" element={<ReportExport />} />
          <Route path="/catalog" element={<CatalogLink />} />
        </Routes>
      </main>

      {/* Footer — S7-FA-008: UX polish */}
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
  );
}
