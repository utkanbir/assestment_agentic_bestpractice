import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AssessmentList } from "./pages/AssessmentList";
import { AssessmentDetail } from "./pages/AssessmentDetail";
import { InterviewRoom } from "./pages/InterviewRoom";
import { FindingsDashboard } from "./pages/FindingsDashboard";
import { ReportViewer } from "./pages/ReportViewer";

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<AssessmentList />} />
          <Route path="/assessments/:id" element={<AssessmentDetail />} />
          <Route path="/tasks/:taskId/interview" element={<InterviewRoom />} />
          <Route path="/tasks/:taskId/findings" element={<FindingsDashboard />} />
          <Route path="/tasks/:taskId/report" element={<ReportViewer />} />
          <Route path="/findings" element={<FindingsDashboard />} />
          <Route path="/reports" element={<ReportViewer />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
