import { Routes, Route, NavLink } from "react-router-dom";
import AssessmentOverview from "./pages/AssessmentOverview";
import AgentSelection from "./pages/AgentSelection";
import ParallelSessions from "./pages/ParallelSessions";

const navStyle = (active: boolean): React.CSSProperties => ({
  padding: "8px 16px",
  borderRadius: 6,
  textDecoration: "none",
  color: active ? "#fff" : "#94a3b8",
  background: active ? "#3b82f6" : "transparent",
  fontWeight: active ? 600 : 400,
  fontSize: 14,
  transition: "all 0.15s",
});

export default function App() {
  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* Top nav */}
      <nav style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "12px 24px",
        borderBottom: "1px solid #1e293b",
        background: "#0f1117",
      }}>
        <span style={{ fontWeight: 700, fontSize: 18, marginRight: 24, color: "#60a5fa" }}>
          AAKP
        </span>
        <NavLink to="/" end style={({ isActive }) => navStyle(isActive)}>Genel Bakış</NavLink>
        <NavLink to="/agents" style={({ isActive }) => navStyle(isActive)}>Ajan Seçimi</NavLink>
        <NavLink to="/sessions" style={({ isActive }) => navStyle(isActive)}>Paralel Oturumlar</NavLink>
      </nav>

      {/* Page content */}
      <main style={{ flex: 1, padding: "24px" }}>
        <Routes>
          <Route path="/" element={<AssessmentOverview />} />
          <Route path="/agents" element={<AgentSelection />} />
          <Route path="/sessions" element={<ParallelSessions />} />
        </Routes>
      </main>
    </div>
  );
}
