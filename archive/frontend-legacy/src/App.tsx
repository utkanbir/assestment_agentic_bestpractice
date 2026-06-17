import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AssessmentList } from "./pages/AssessmentList";
import { AssessmentDetail } from "./pages/AssessmentDetail";
import { InterviewRoom } from "./pages/InterviewRoom";
import { FindingsDashboard } from "./pages/FindingsDashboard";
import { ReportViewer } from "./pages/ReportViewer";
import { MaturityInputPage } from "./pages/MaturityInputPage";
import { ApprovalQueuePage } from "./pages/ApprovalQueuePage";
import { ExecutiveSummaryPage } from "./pages/ExecutiveSummaryPage";
import { RiskHeatmapPage } from "./pages/RiskHeatmapPage";

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<AssessmentList />} />
          <Route path="/assessments/:id" element={<AssessmentDetail />} />
          <Route path="/assessments/:id/maturity" element={<MaturityInputPage />} />
          <Route path="/assessments/:id/executive-summary" element={<ExecutiveSummaryPage />} />
          <Route path="/assessments/:id/risk-heatmap" element={<RiskHeatmapPage />} />
          <Route path="/tasks/:taskId/interview" element={<InterviewRoom />} />
          <Route path="/tasks/:taskId/findings" element={<FindingsDashboard />} />
          <Route path="/tasks/:taskId/report" element={<ReportViewer />} />
          <Route path="/findings" element={<FindingsDashboard />} />
          <Route path="/reports" element={<ReportViewer />} />
          <Route path="/approvals" element={<ApprovalQueuePage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
