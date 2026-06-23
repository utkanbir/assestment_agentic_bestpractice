import ConsultantPanel from "../components/ConsultantPanel";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

export default function ConsultantManagement() {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Danışman Yönetimi"
        subtitle="Danışman havuzuna yeni uzman ekleyin; mülakat yanıtlarında yorum için kullanılır"
      />
      <ConsultantPanel />
    </div>
  );
}
