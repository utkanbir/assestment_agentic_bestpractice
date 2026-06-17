// S11-FA-004: Ajan Yönetimi — performans metrikleri + bilgi dökümanı yönetimi
import { useState, useEffect, useRef } from "react";
import {
  WORKSTREAMS,
  AgentMetrics, KnowledgeDocument,
  getAllAgentMetrics, getWorkstreamMetrics,
  listDocuments, uploadDocument, deleteDocument,
} from "../api";

const WS_LABEL: Record<string, string> = Object.fromEntries(
  WORKSTREAMS.map(w => [w.id, w.label])
);

// ── Metrik kartı ─────────────────────────────────────────────────────────────

function MetricBox({ label, value, color = "#60a5fa", sub }: {
  label: string; value: number | string; color?: string; sub?: string;
}) {
  return (
    <div style={{ background: "#0f1117", borderRadius: 8, padding: "12px 16px", minWidth: 100 }}>
      <p style={{ fontSize: 22, fontWeight: 800, color, margin: "0 0 2px 0" }}>{value}</p>
      <p style={{ fontSize: 11, color: "#64748b", margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</p>
      {sub && <p style={{ fontSize: 10, color: "#475569", margin: "2px 0 0 0" }}>{sub}</p>}
    </div>
  );
}

function ApprovalBar({ approved, rejected, pending }: { approved: number; rejected: number; pending: number }) {
  const total = approved + rejected + pending;
  if (total === 0) return <p style={{ fontSize: 12, color: "#475569" }}>Henüz öneri yok</p>;
  return (
    <div>
      <div style={{ display: "flex", height: 8, borderRadius: 4, overflow: "hidden", marginBottom: 6 }}>
        <div style={{ flex: approved, background: "#22c55e" }} title={`Onaylı: ${approved}`} />
        <div style={{ flex: rejected, background: "#ef4444" }} title={`Reddedildi: ${rejected}`} />
        <div style={{ flex: pending, background: "#475569" }} title={`Bekleyen: ${pending}`} />
      </div>
      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#64748b" }}>
        <span style={{ color: "#22c55e" }}>✓ {approved} onaylı</span>
        <span style={{ color: "#ef4444" }}>✗ {rejected} reddedildi</span>
        <span style={{ color: "#64748b" }}>⏳ {pending} bekleyen</span>
      </div>
    </div>
  );
}

// ── Döküman yükleme alanı ────────────────────────────────────────────────────

function DocumentUploader({ workstream, onUploaded }: {
  workstream: string;
  onUploaded: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [desc, setDesc] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    try {
      await uploadDocument(workstream, file, desc || undefined);
      setDesc("");
      onUploaded();
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
          transition: "all 0.15s",
        }}
      >
        {uploading ? "⏳ Yükleniyor…" : "📄 PDF veya metin dosyası yükle (sürükle bırak)"}
      </div>
    </div>
  );
}

// ── Döküman listesi ──────────────────────────────────────────────────────────

function DocumentList({ workstream, docs, onDelete }: {
  workstream: string;
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
          <span style={{ fontSize: 16, flexShrink: 0 }}>
            {d.file_type === "pdf" ? "📕" : "📄"}
          </span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 12, color: "#e2e8f0", margin: 0, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {d.filename}
            </p>
            <p style={{ fontSize: 10, color: "#64748b", margin: "2px 0 0 0" }}>
              {d.chunk_count} chunk • {new Date(d.created_at).toLocaleDateString("tr-TR")}
              {d.description && ` • ${d.description}`}
            </p>
          </div>
          <button
            onClick={() => onDelete(d.id)}
            style={{ padding: "3px 10px", borderRadius: 5, border: "1px solid #334155", background: "transparent", color: "#ef4444", cursor: "pointer", fontSize: 11, fontWeight: 600, flexShrink: 0 }}
          >
            Sil
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Ana sayfa ─────────────────────────────────────────────────────────────────

export default function AjanYonetimi() {
  const [selectedWs, setSelectedWs] = useState<string>(WORKSTREAMS[0].id);
  const [allMetrics, setAllMetrics] = useState<AgentMetrics[]>([]);
  const [wsMetrics, setWsMetrics] = useState<AgentMetrics | null>(null);
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [activeTab, setActiveTab] = useState<"metrics" | "docs">("metrics");

  // Tüm metrikleri yükle
  useEffect(() => {
    setLoadingMetrics(true);
    getAllAgentMetrics()
      .then(setAllMetrics)
      .catch(() => setAllMetrics([]))
      .finally(() => setLoadingMetrics(false));
  }, []);

  // Seçili workstream metrik + dökümanları
  useEffect(() => {
    setWsMetrics(null);
    setDocs([]);
    getWorkstreamMetrics(selectedWs).then(setWsMetrics).catch(() => {});
    loadDocs();
  }, [selectedWs]);

  const loadDocs = () => {
    listDocuments(selectedWs).then(setDocs).catch(() => setDocs([]));
  };

  const handleDeleteDoc = async (docId: string) => {
    await deleteDocument(selectedWs, docId);
    loadDocs();
  };

  const m = wsMetrics;
  const totalSuggestions = m ? m.suggestions_approved + m.suggestions_rejected + m.suggestions_pending : 0;
  const approvalRate = totalSuggestions > 0 && m ? Math.round((m.suggestions_approved / totalSuggestions) * 100) : null;

  return (
    <div style={{ display: "flex", height: "calc(100vh - 110px)", color: "#e2e8f0" }}>

      {/* ── Sol: Workstream listesi ───────────────────────────────────────── */}
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
                transition: "all 0.12s",
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

      {/* ── Sağ: Detay paneli ────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>

        {/* Başlık */}
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px 0" }}>
            {WORKSTREAMS.find(w => w.id === selectedWs)?.icon} {WS_LABEL[selectedWs] ?? selectedWs}
          </h1>
          <p style={{ fontSize: 12, color: "#64748b", margin: 0 }}>Ajan performansı ve bilgi yönetimi</p>
        </div>

        {/* Tab seçimi */}
        <div style={{ display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid #1e293b", paddingBottom: 12 }}>
          {(["metrics", "docs"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: "6px 16px", borderRadius: 6, border: "none",
                background: activeTab === tab ? "#3b82f6" : "transparent",
                color: activeTab === tab ? "#fff" : "#64748b",
                cursor: "pointer", fontSize: 13, fontWeight: activeTab === tab ? 700 : 400,
              }}
            >
              {tab === "metrics" ? "📊 Performans" : "📚 Bilgi Tabanı"}
            </button>
          ))}
        </div>

        {/* ── Performans Metrikleri ── */}
        {activeTab === "metrics" && (
          <>
            {!m ? (
              <p style={{ color: "#475569", textAlign: "center", padding: 40 }}>Yükleniyor…</p>
            ) : (
              <>
                {/* Ana metrikler */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: 12, marginBottom: 24 }}>
                  <MetricBox label="Interview" value={m.interviews_conducted} color="#60a5fa" />
                  <MetricBox label="Toplam Soru" value={m.questions_total} color="#a78bfa" />
                  <MetricBox label="Toplam Yanıt" value={m.answers_total} color="#34d399" />
                  <MetricBox label="Değerlendirilen" value={m.answers_evaluated} color="#fbbf24"
                    sub={m.answers_total > 0 ? `%${Math.round(m.answers_evaluated / m.answers_total * 100)}` : undefined} />
                  <MetricBox label="Yüklü Döküman" value={m.documents_loaded} color="#f472b6" />
                  {approvalRate !== null && (
                    <MetricBox label="Öneri Onay %" value={`%${approvalRate}`} color="#22c55e" />
                  )}
                </div>

                {/* Öneri performansı */}
                {m.questions_agent_suggested > 0 && (
                  <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16, marginBottom: 16 }}>
                    <h3 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 12px 0", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Agent Öneri Performansı
                    </h3>
                    <ApprovalBar
                      approved={m.suggestions_approved}
                      rejected={m.suggestions_rejected}
                      pending={m.suggestions_pending}
                    />
                    <p style={{ fontSize: 11, color: "#475569", marginTop: 8 }}>
                      Toplam {m.questions_agent_suggested} öneri yapıldı
                    </p>
                  </div>
                )}

                {/* Özet değerlendirme */}
                <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 10px 0", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Özet
                  </h3>
                  {m.answers_total === 0 ? (
                    <p style={{ fontSize: 12, color: "#475569" }}>Bu workstream için henüz interview yapılmamış.</p>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "#94a3b8" }}>
                      <span>✦ {m.interviews_conducted} interview yapıldı, {m.answers_total} yanıt alındı</span>
                      {m.answers_evaluated > 0 && <span>✦ {m.answers_evaluated} yanıt agent tarafından değerlendirildi</span>}
                      {m.questions_agent_suggested > 0 && (
                        <span>✦ Agent {m.questions_agent_suggested} soru önerdi, {m.suggestions_approved} onaylandı</span>
                      )}
                      {m.documents_loaded > 0 && (
                        <span>✦ {m.documents_loaded} bilgi dökümanı yüklü — agent bu kaynakları kullanıyor</span>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </>
        )}

        {/* ── Bilgi Tabanı (RAG) ── */}
        {activeTab === "docs" && (
          <>
            <div style={{ background: "#0a1a2f", border: "1px solid #1e3a5f", borderRadius: 10, padding: 16, marginBottom: 16 }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 8px 0", color: "#60a5fa" }}>
                Nasıl çalışır?
              </h3>
              <p style={{ fontSize: 12, color: "#64748b", margin: 0, lineHeight: 1.7 }}>
                Yüklediğiniz dökümanlar (PDF, metin) parçalara bölünerek vektör veritabanına eklenir.
                Agent, follow-up soru önerirken ve yanıt değerlendirirken bu dökümanları referans alır.
                Şirket mimarisi, politika dökümanları, best-practice rehberleri yükleyebilirsiniz.
              </p>
            </div>

            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16, marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 12px 0" }}>Döküman Yükle</h3>
              <DocumentUploader workstream={selectedWs} onUploaded={loadDocs} />
            </div>

            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 12px 0" }}>
                Yüklü Dökümanlar
                <span style={{ fontSize: 12, fontWeight: 400, color: "#64748b", marginLeft: 8 }}>
                  ({docs.length} adet)
                </span>
              </h3>
              <DocumentList workstream={selectedWs} docs={docs} onDelete={handleDeleteDoc} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
