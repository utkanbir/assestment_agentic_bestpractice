import { useNavigate } from "react-router-dom";

import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";



export default function ChatWidget() {

  const { assessmentId } = useAssessment();

  const navigate = useNavigate();

  const withAssessment = useAssessmentNavLink();



  return (

    <button

      type="button"

      data-testid="chat-fab"

      onClick={() => navigate(withAssessment("/chat"))}

      title={assessmentId ? "Chat sayfasına git" : "Önce assessment seçin"}

      style={{

        position: "fixed",

        right: 24,

        bottom: 24,

        zIndex: 300,

        width: 52,

        height: 52,

        borderRadius: "50%",

        border: "none",

        background: assessmentId ? "#2563eb" : "#475569",

        color: "#fff",

        fontWeight: 700,

        cursor: assessmentId ? "pointer" : "not-allowed",

        boxShadow: "0 8px 24px rgba(0,0,0,0.35)",

      }}

    >

      AI

    </button>

  );

}

