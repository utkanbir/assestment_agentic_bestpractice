// S11-FA-004 + S24 + S30: Ajan Yönetimi — eğitim + Agent Knowledge panel
import { useState, useEffect, useRef } from "react";
import {
  WORKSTREAMS,
  AgentMetrics, KnowledgeDocument, Consultant, LearningEvent, DocumentUploadResult,
  getAllAgentMetrics,
  listDocuments, uploadDocument, deleteDocument,
  generateAahaQuestion, generateAahaAiAnswer, submitAahaAnswer, trainTextKnowledge,
  listAllConsultants, listTrainingEvents, downloadOntologyExport,
} from "../api";
import AgentKnowledgePanel from "../components/AgentKnowledgePanel";
import AgentKnowledgeArchitecture from "../components/AgentKnowledgeArchitecture";

const WS_LABEL: Record<string, string> = Object.fromEntries(
  WORKSTREAMS.map(w => [w.id, w.label])
);

type TabId = "aaha" | "text" | "docs" | "architecture";

function authorLabel(ev: LearningEvent, consultants: Consultant[]): string {
  if (ev.answer_author === "ai") return "AI";
  if (ev.consultant_id) {
    const c = consultants.find(x => x.id === ev.consultant_id);
    if (c) return `${c.first_name} ${c.last_name}`.trim();
  }
  return "—";
}

// ── Döküman yükleme alanı ────────────────────────────────────────────────────

function DocumentUploader({ workstream, onUploaded }: {
  workstream: string;
  onUploaded: (summary?: DocumentUploadResult["learning_summary"]) => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [desc, setDesc] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    try {
      const result = await uploadDocument(workstream, file, desc || undefined);
      setDesc("");
      onUploaded(result.learning_summary);
    } catch (e) {
      alert(`Yükleme hatası: ${e}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.txt,.md"
        style={{ display: "none" }}
        onChange={e => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
          e.target.value = "";
        }}
      />
      <input
        value={desc}
        onChange={e => setDesc(e.target.value)}
        placeholder="Döküman açıklaması (isteğe bağlı)"
        style={{
          width: "100%", background: "#0f1117", border: "1px solid #334155",
          borderRadius: 6, padding: "6px 10px", color: "#e2e8f0", fontSize: 12,
          marginBottom: 8, boxSizing: "border-box" as const,
        }}
      />
      <div
        onClick={() => !uploading && fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files[0];
          if (f) handleFile(f);
        }}
        style={{
          border: `2px dashed ${dragOver ? "#3b82f6" : "#334155"}`,
          borderRadius: 8, padding: "20px", textAlign: "center",
          cursor: uploading ? "not-allowed" : "pointer",
          color: "#64748b", fontSize: 12, background: dragOver ? "#1e3a5f22" : "transparent",
        }}
      >
        {uploading ? "⏳ Yükleniyor…" : "📄 PDF veya metin dosyası yükle (sürükle bırak)"}
      </div>
    </div>
  );
}

function DocumentList({ docs, onDelete }: {
  docs: KnowledgeDocument[];
  onDelete: (id: string) => void;
}) {
  if (docs.length === 0) return (
    <p style={{ fontSize: 12, color: "#475569", padding: "16px 0", textAlign: "center" }}>
      Bu workstream için yüklenmiş döküman yok.
    </p>
  );
  return (
    <div style={{ marginTop: 8 }}>
      {docs.map(d => (
        <div key={d.id} style={{
          display: "flex", alignItems: "center", gap: 10,
          background: "#0f1117", borderRadius: 7, padding: "8px 12px", marginBottom: 6,
        }}>
          <span style={{ fontSize: 16 }}>{d.file_type === "pdf" ? "📕" : "📄"}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 12, color: "#e2e8f0", margin: 0, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {d.filename}
            </p>
            <p style={{ fontSize: 10, color: "#64748b", margin: "2px 0 0 0" }}>
              {d.chunk_count} chunk • {new Date(d.created_at).toLocaleDateString("tr-TR")}
            </p>
          </div>
          <button
            onClick={() => onDelete(d.id)}
            style={{ padding: "3px 10px", borderRadius: 5, border: "1px solid #334155", background: "transparent", color: "#ef4444", cursor: "pointer", fontSize: 11 }}
          >
            Sil
          </button>
        </div>
      ))}
    </div>
  );
}

// ── AAHA Eğitimi ─────────────────────────────────────────────────────────────

function TrainingHistoryTable({ events, consultants }: { events: LearningEvent[]; consultants: Consultant[] }) {
  if (events.length === 0) return null;
  return (
    <div data-testid="training-history-table" style={{ marginTop: 16, overflowX: "auto" }}>
      <h4 style={{ fontSize: 12, color: "#94a3b8", margin: "0 0 8px" }}>Eğitim Geçmişi</h4>
      <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: "#64748b", textAlign: "left" }}>
            <th style={{ padding: 6 }}>Tarih</th>
            <th style={{ padding: 6 }}>Mod</th>
            <th style={{ padding: 6 }}>Kaynak</th>
            <th style={{ padding: 6 }}>Soru / Özet</th>
            <th style={{ padding: 6 }}>Yanıt</th>
          </tr>
        </thead>
        <tbody>
          {events.map((ev) => (
            <tr key={ev.id} style={{ borderTop: "1px solid #334155" }}>
              <td style={{ padding: 6, whiteSpace: "nowrap" }}>{new Date(ev.created_at).toLocaleString("tr-TR")}</td>
              <td style={{ padding: 6 }}>{ev.mode}</td>
              <td style={{ padding: 6, color: ev.answer_author === "ai" ? "#a78bfa" : "#94a3b8" }}>
                {authorLabel(ev, consultants)}
              </td>
              <td style={{ padding: 6, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{ev.question_text ?? "—"}</td>
              <td style={{ padding: 6, maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis" }}>{(ev.answer_text ?? "").slice(0, 120)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AahaTrainingPanel({
  workstream,
  consultants,
  onKnowledgeChanged,
}: {
  workstream: string;
  consultants: Consultant[];
  onKnowledgeChanged: () => void;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [consultantId, setConsultantId] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiDraft, setAiDraft] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [history, setHistory] = useState<LearningEvent[]>([]);

  const loadHistory = () => {
    listTrainingEvents(workstream).then(setHistory).catch(() => setHistory([]));
  };

  const loadQuestion = async () => {
    setLoading(true);
    try {
      const data = await generateAahaQuestion(workstream);
      setQuestion(data.question);
      setAnswer("");
      setAiDraft(false);
    } catch (e) {
      alert(`Soru üretilemedi: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAiAnswer = async () => {
    if (!question.trim()) return;
    setAiGenerating(true);
    try {
      const data = await generateAahaAiAnswer(workstream, question);
      setAnswer(data.answer);
      setAiDraft(true);
    } catch (e) {
      alert(`AI yanıtı üretilemedi: ${e}`);
    } finally {
      setAiGenerating(false);
    }
  };

  const persistAnswer = async (asAi: boolean) => {
    if (!question.trim() || !answer.trim()) return;
    setSubmitting(true);
    try {
      const ev = await submitAahaAnswer(workstream, question, answer, asAi
        ? {
            answerAuthor: "ai",
            approvedByConsultantId: consultantId || undefined,
          }
        : {
            answerAuthor: "consultant",
            consultantId: consultantId || undefined,
          });
      setLastSaved(new Date(ev.created_at).toLocaleString("tr-TR"));
      setAnswer("");
      setAiDraft(false);
      loadHistory();
      onKnowledgeChanged();
    } catch (e) {
      alert(`Kayıt hatası: ${e}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = () => persistAnswer(false);
  const handleApproveAi = () => persistAnswer(true);

  useEffect(() => { loadHistory(); }, [workstream]);

  return (
    <div>
      <div style={{ background: "#0a1a2f", border: "1px solid #1e3a5f", borderRadius: 10, padding: 16, marginBottom: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 8px 0", color: "#60a5fa" }}>AAHA Eğitimi</h3>
        <p style={{ fontSize: 12, color: "#64748b", margin: 0, lineHeight: 1.7 }}>
          «Soru Sor» ile agent soru üretir; danışman yanıt yazar veya «AI yanıtlasın» ile taslak alır.
          AI yanıtını danışman onayladığında bilgi vektör veritabanına ve bilgi grafiğine kaydedilir.
        </p>
      </div>

      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>Agent Sorusu</h3>
          <button
            data-testid="aaha-ask-question"
            onClick={loadQuestion}
            disabled={loading}
            style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid #334155", background: "transparent", color: "#60a5fa", cursor: "pointer", fontSize: 12 }}
          >
            {loading ? "⏳" : "Soru Sor"}
          </button>
        </div>
        <p style={{ fontSize: 14, color: "#e2e8f0", lineHeight: 1.6, margin: "0 0 16px 0", minHeight: 48 }}>
          {loading ? "Soru üretiliyor…" : question || "Soru üretmek için «Soru Sor» butonuna tıklayın."}
        </p>
        {question && !loading && (
          <button
            data-testid="aaha-ai-answer-btn"
            onClick={handleAiAnswer}
            disabled={aiGenerating || submitting}
            style={{
              padding: "6px 14px", borderRadius: 6, border: "1px solid #334155",
              background: "#0f1117", color: "#a78bfa", cursor: aiGenerating ? "not-allowed" : "pointer",
              fontSize: 12, marginBottom: 16,
            }}
          >
            {aiGenerating ? "AI yanıt üretiliyor…" : "AI yanıtlasın"}
          </button>
        )}

        <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
          {aiDraft ? "Onaylayan danışman (opsiyonel)" : "Danışman (opsiyonel)"}
        </label>
        <select
          data-testid="aaha-consultant-select"
          value={consultantId}
          onChange={e => setConsultantId(e.target.value)}
          style={{
            width: "100%", background: "#0f1117", border: "1px solid #334155",
            borderRadius: 6, padding: "6px 10px", color: "#e2e8f0", fontSize: 12, marginBottom: 12,
          }}
        >
          <option value="">Seçilmedi</option>
          {consultants.map(c => (
            <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
          ))}
        </select>

        <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
          {aiDraft ? "AI Taslak Yanıt (danışman onayı gerekir)" : "Danışman Yanıtı"}
        </label>
        <textarea
          data-testid="aaha-answer-textarea"
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          rows={5}
          placeholder="Uzmanlık bilginizi buraya yazın…"
          style={{
            width: "100%", background: aiDraft ? "#1a1525" : "#0f1117",
            border: `1px solid ${aiDraft ? "#7c3aed" : "#334155"}`,
            borderRadius: 8, padding: 12, color: "#e2e8f0", fontSize: 13,
            resize: "vertical", boxSizing: "border-box" as const, marginBottom: 12,
          }}
        />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {aiDraft && (
            <button
              data-testid="aaha-approve-ai-btn"
              onClick={handleApproveAi}
              disabled={submitting || !answer.trim() || !question.trim()}
              style={{
                padding: "8px 20px", borderRadius: 8, border: "none",
                background: submitting ? "#334155" : "#22c55e",
                color: "#fff", cursor: submitting ? "not-allowed" : "pointer", fontWeight: 700,
              }}
            >
              {submitting ? "Onaylanıyor…" : "Onayla"}
            </button>
          )}
          <button
            data-testid="aaha-save-answer-btn"
            onClick={handleSubmit}
            disabled={submitting || !answer.trim() || !question.trim()}
            style={{
              padding: "8px 20px", borderRadius: 8, border: "none",
              background: submitting ? "#334155" : "#3b82f6",
              color: "#fff", cursor: submitting ? "not-allowed" : "pointer", fontWeight: 700,
            }}
          >
            {submitting ? "Kaydediliyor…" : "Yanıtı Kaydet"}
          </button>
        </div>
        {lastSaved && (
          <p style={{ fontSize: 11, color: "#22c55e", marginTop: 10 }}>✓ Son kayıt: {lastSaved}</p>
        )}
        <TrainingHistoryTable events={history.filter(e => e.mode === "aaha")} consultants={consultants} />
      </div>
    </div>
  );
}

// ── Metin Bilgi ──────────────────────────────────────────────────────────────

function TextTrainingPanel({
  workstream,
  consultants,
  onKnowledgeChanged,
}: {
  workstream: string;
  consultants: Consultant[];
  onKnowledgeChanged: () => void;
}) {
  const [content, setContent] = useState("");
  const [consultantId, setConsultantId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [history, setHistory] = useState<LearningEvent[]>([]);

  const loadHistory = () => {
    listTrainingEvents(workstream).then(setHistory).catch(() => setHistory([]));
  };

  useEffect(() => { loadHistory(); }, [workstream]);

  const handleSubmit = async () => {
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      const ev = await trainTextKnowledge(workstream, content, consultantId || undefined);
      setLastSaved(new Date(ev.created_at).toLocaleString("tr-TR"));
      setContent("");
      loadHistory();
      onKnowledgeChanged();
    } catch (e) {
      alert(`Kayıt hatası: ${e}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div style={{ background: "#0a1a2f", border: "1px solid #1e3a5f", borderRadius: 10, padding: 16, marginBottom: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 8px 0", color: "#60a5fa" }}>Metin Bilgi Girişi</h3>
        <p style={{ fontSize: 12, color: "#64748b", margin: 0, lineHeight: 1.7 }}>
          Serbest metin olarak know-how girin. İçerik parçalanır, vektör veritabanına ve KG'ye yazılır.
        </p>
      </div>
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
        <select
          data-testid="text-consultant-select"
          value={consultantId}
          onChange={e => setConsultantId(e.target.value)}
          style={{
            width: "100%", background: "#0f1117", border: "1px solid #334155",
            borderRadius: 6, padding: "6px 10px", color: "#e2e8f0", fontSize: 12, marginBottom: 12,
          }}
        >
          <option value="">Danışman (opsiyonel)</option>
          {consultants.map(c => (
            <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
          ))}
        </select>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          rows={10}
          placeholder="Best practice, mimari kararlar, operasyonel bilgiler…"
          style={{
            width: "100%", background: "#0f1117", border: "1px solid #334155",
            borderRadius: 8, padding: 12, color: "#e2e8f0", fontSize: 13,
            resize: "vertical", boxSizing: "border-box" as const, marginBottom: 12,
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={submitting || !content.trim()}
          style={{
            padding: "8px 20px", borderRadius: 8, border: "none",
            background: submitting ? "#334155" : "#3b82f6",
            color: "#fff", cursor: submitting ? "not-allowed" : "pointer", fontWeight: 700,
          }}
        >
          {submitting ? "Kaydediliyor…" : "Bilgiyi Kaydet"}
        </button>
        {lastSaved && (
          <p style={{ fontSize: 11, color: "#22c55e", marginTop: 10 }}>✓ Son kayıt: {lastSaved}</p>
        )}
        <TrainingHistoryTable events={history.filter(e => e.mode === "text")} consultants={consultants} />
      </div>
    </div>
  );
}

// ── Ana sayfa ─────────────────────────────────────────────────────────────────

const TABS: { id: TabId; label: string }[] = [
  { id: "aaha", label: "🎯 AAHA Eğitimi" },
  { id: "text", label: "✍️ Metin Bilgi" },
  { id: "docs", label: "📚 Bilgi Tabanı" },
  { id: "architecture", label: "🏗️ KM Mimarisi" },
];

export default function AjanYonetimi() {
  const [selectedWs, setSelectedWs] = useState<string>(WORKSTREAMS[0].id);
  const [allMetrics, setAllMetrics] = useState<AgentMetrics[]>([]);
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>("aaha");
  const [consultants, setConsultants] = useState<Consultant[]>([]);
  const [uploadSummary, setUploadSummary] = useState<DocumentUploadResult["learning_summary"] | null>(null);
  const [knowledgeRefreshKey, setKnowledgeRefreshKey] = useState(0);

  const refreshKnowledge = () => setKnowledgeRefreshKey(k => k + 1);

  useEffect(() => {
    getAllAgentMetrics().then(setAllMetrics).catch(() => setAllMetrics([]));
    listAllConsultants().then(setConsultants).catch(() => setConsultants([]));
  }, []);

  useEffect(() => {
    setDocs([]);
    loadDocs();
    refreshKnowledge();
  }, [selectedWs]);

  const loadDocs = () => {
    listDocuments(selectedWs).then(setDocs).catch(() => setDocs([]));
  };

  const handleDeleteDoc = async (docId: string) => {
    await deleteDocument(selectedWs, docId);
    loadDocs();
    refreshKnowledge();
  };

  const handleOwlExport = async () => {
    try {
      const ttl = await downloadOntologyExport();
      const blob = new Blob([ttl], { type: "text/turtle" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "aakp-ontology.ttl";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`OWL export hatası: ${e}`);
    }
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 110px)", color: "#e2e8f0" }}>
      <div style={{
        width: 210, flexShrink: 0, background: "#0f1117",
        borderRight: "1px solid #1e293b", overflowY: "auto", padding: "16px 8px",
      }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", padding: "0 8px 10px" }}>
          Ajanlar
        </p>
        {WORKSTREAMS.map(ws => {
          const m = allMetrics.find(x => x.workstream === ws.id);
          const isActive = ws.id === selectedWs;
          return (
            <button
              key={ws.id}
              onClick={() => setSelectedWs(ws.id)}
              style={{
                width: "100%", textAlign: "left", padding: "9px 12px",
                borderRadius: 7, border: "none", marginBottom: 3,
                background: isActive ? "#1e3a5f" : "transparent",
                borderLeft: `3px solid ${isActive ? "#3b82f6" : "transparent"}`,
                color: isActive ? "#e2e8f0" : "#94a3b8",
                cursor: "pointer", fontSize: 13,
                display: "flex", alignItems: "center", gap: 8,
              }}
            >
              <span style={{ fontSize: 15 }}>{ws.icon}</span>
              <span style={{ flex: 1 }}>{ws.label}</span>
              {m && m.documents_loaded > 0 && (
                <span style={{ fontSize: 10, background: "#3b82f622", color: "#60a5fa", borderRadius: 3, padding: "1px 5px" }}>
                  {m.documents_loaded}📄
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
        <div style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px 0" }}>
              {WORKSTREAMS.find(w => w.id === selectedWs)?.icon} {WS_LABEL[selectedWs] ?? selectedWs}
            </h1>
            <p style={{ fontSize: 12, color: "#64748b", margin: 0 }}>Ajan eğitimi ve bilgi yönetimi</p>
          </div>
          <button
            data-testid="owl-export-btn"
            onClick={handleOwlExport}
            style={{
              padding: "8px 14px", borderRadius: 8, border: "1px solid #334155",
              background: "#1e293b", color: "#60a5fa", cursor: "pointer", fontSize: 12, fontWeight: 600,
            }}
          >
            OWL Export (.ttl)
          </button>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid #1e293b", paddingBottom: 12, flexWrap: "wrap" }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "6px 16px", borderRadius: 6, border: "none",
                background: activeTab === tab.id ? "#3b82f6" : "transparent",
                color: activeTab === tab.id ? "#fff" : "#64748b",
                cursor: "pointer", fontSize: 13, fontWeight: activeTab === tab.id ? 700 : 400,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "aaha" && (
          <AahaTrainingPanel workstream={selectedWs} consultants={consultants} onKnowledgeChanged={refreshKnowledge} />
        )}
        {activeTab === "text" && (
          <TextTrainingPanel workstream={selectedWs} consultants={consultants} onKnowledgeChanged={refreshKnowledge} />
        )}

        {activeTab === "docs" && (
          <>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16, marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 12px 0" }}>Döküman Yükle</h3>
              <DocumentUploader
                workstream={selectedWs}
                onUploaded={(summary) => {
                  setUploadSummary(summary ?? null);
                  setActiveTab("docs");
                  loadDocs();
                  refreshKnowledge();
                }}
              />
              {uploadSummary && (
                <div
                  data-testid="doc-upload-summary"
                  style={{
                    marginTop: 16, padding: 16, background: "#0a1f14",
                    border: "2px solid #22c55e", borderRadius: 10, fontSize: 13, color: "#cbd5e1",
                  }}
                >
                  <strong style={{ color: "#4ade80", display: "block", marginBottom: 8, fontSize: 14 }}>
                    Yükleme tamamlandı — Öğrenme özeti
                  </strong>
                  <div style={{ marginBottom: 6 }}>
                    <strong>{uploadSummary.filename}</strong> — {uploadSummary.chunks} chunk, {uploadSummary.characters} karakter
                    {uploadSummary.qdrant_embedded ? " · Qdrant embed OK" : ""}
                    {" · KG AgentKnowledge triple"}
                  </div>
                  {uploadSummary.preview && (
                    <p
                      data-testid="doc-upload-preview"
                      style={{ margin: 0, fontSize: 12, color: "#94a3b8", lineHeight: 1.5, fontStyle: "italic" }}
                    >
                      &ldquo;{uploadSummary.preview}&rdquo;
                    </p>
                  )}
                </div>
              )}
            </div>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 12px 0" }}>
                Yüklü Dökümanlar ({docs.length})
              </h3>
              <DocumentList docs={docs} onDelete={handleDeleteDoc} />
            </div>
          </>
        )}

        {activeTab === "architecture" && <AgentKnowledgeArchitecture />}
      </div>

      <AgentKnowledgePanel workstream={selectedWs} refreshKey={knowledgeRefreshKey} />
    </div>
  );
}
