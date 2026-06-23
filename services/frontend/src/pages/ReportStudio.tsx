// S18/S20: Report Studio — hybrid block editor + per-section AI
import { useCallback, useEffect, useState } from "react";
import AssessmentPageHeader from "../components/AssessmentPageHeader";
import { useAssessment } from "../context/AssessmentContext";
import {
  ReportRecord,
  ReportContent,
  ReportSection,
  Consultant,
  composeReport,
  listReports,
  patchReport,
  aiGenerateReport,
  consultantReviewSection,
  downloadReportBlob,
  listAllConsultants,
} from "../api";

const AI_TYPES = new Set(["text", "table", "kpi_grid", "chart_radar", "chart_heatmap", "cover"]);

function migrateSectionOpinions(section: ReportSection): ReportSection {
  if (section.consultant_opinions?.length) return section;
  if (section.consultant_comment?.trim()) {
    return {
      ...section,
      consultant_opinions: [{ consultant_id: "", comment: section.consultant_comment }],
    };
  }
  return { ...section, consultant_opinions: section.consultant_opinions ?? [] };
}

function opinionsToLegacyComment(opinions: { consultant_id: string; comment: string }[]): string {
  return opinions.map((o) => o.comment.trim()).filter(Boolean).join("\n\n");
}

function RadarPreview({ data }: { data: { labels?: string[]; values?: number[] } }) {
  const labels = data.labels ?? [];
  const values = data.values ?? [];
  const scores = labels.map((label, i) => ({ label, value: values[i] ?? 0 }));
  const size = 200;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 80;
  const n = scores.length || 1;
  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const point = (i: number, v: number) => {
    const r = (v / 5) * maxR;
    return { x: cx + r * Math.cos(angle(i)), y: cy + r * Math.sin(angle(i)) };
  };
  const poly = scores.map((s, i) => point(i, s.value)).map((p) => `${p.x},${p.y}`).join(" ");
  return (
    <svg width={size} height={size}>
      <polygon points={poly} fill="#3b82f633" stroke="#3b82f6" strokeWidth={2} />
    </svg>
  );
}

function CommentaryEditor({
  section,
  onChange,
}: {
  section: ReportSection;
  onChange: (updated: ReportSection) => void;
}) {
  return (
    <div style={{ marginTop: 16 }}>
      <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>AI Yorumu</label>
      <textarea
        data-testid={`section-commentary-${section.id}`}
        value={section.commentary ?? ""}
        onChange={(e) => onChange({ ...section, commentary: e.target.value })}
        rows={4}
        placeholder="Grafik için kısa yorum…"
        style={{ width: "100%", background: "#0f1117", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 8, padding: 12, fontSize: 13 }}
      />
    </div>
  );
}

function ConsultantOpinionsEditor({
  section,
  reportId,
  consultants,
  onChange,
  onFeedback,
}: {
  section: ReportSection;
  reportId: string;
  consultants: Consultant[];
  onChange: (updated: ReportSection) => void;
  onFeedback: (msg: string) => void;
}) {
  const [checking, setChecking] = useState(false);
  const opinions = migrateSectionOpinions(section).consultant_opinions ?? [];

  const updateOpinions = (next: { consultant_id: string; comment: string }[]) => {
    onChange({
      ...section,
      consultant_opinions: next,
      consultant_comment: opinionsToLegacyComment(next),
      consultant_approved: false,
    });
  };

  const handleAiCheck = async () => {
    setChecking(true);
    try {
      const combined = opinionsToLegacyComment(opinions);
      const res = await consultantReviewSection(reportId, {
        section_id: section.id,
        consultant_comment: combined,
      });
      const parsed = JSON.parse(res.content_json) as ReportContent;
      const updated = parsed.sections.find((s) => s.id === section.id);
      if (updated) onChange(migrateSectionOpinions(updated));
      onFeedback(res.consistent ? `✓ ${res.feedback}` : `⚠ ${res.feedback}`);
    } catch {
      onFeedback("Danışman kontrolü başarısız.");
    } finally {
      setChecking(false);
    }
  };

  return (
    <div style={{ marginTop: 20, padding: 14, border: "1px solid #334155", borderRadius: 8, background: "#0f1117" }}>
      <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 8 }}>Danışman Görüşleri</label>
      {opinions.map((row, idx) => (
        <div key={idx} style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
          <select
            value={row.consultant_id}
            onChange={(e) => {
              const next = [...opinions];
              next[idx] = { ...next[idx], consultant_id: e.target.value };
              updateOpinions(next);
            }}
            style={{ minWidth: 160, background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 6, padding: 6 }}
          >
            <option value="">Danışman seç…</option>
            {consultants.map((c) => (
              <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
            ))}
          </select>
          <textarea
            data-testid={`section-consultant-opinion-${section.id}-${idx}`}
            value={row.comment}
            onChange={(e) => {
              const next = [...opinions];
              next[idx] = { ...next[idx], comment: e.target.value };
              updateOpinions(next);
            }}
            rows={2}
            placeholder="Görüş…"
            style={{ flex: 1, minWidth: 200, background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 8, padding: 8, fontSize: 13 }}
          />
          <button
            type="button"
            onClick={() => updateOpinions(opinions.filter((_, i) => i !== idx))}
            style={{ background: "transparent", border: "1px solid #475569", color: "#94a3b8", borderRadius: 6, padding: "4px 8px", cursor: "pointer" }}
          >
            Sil
          </button>
        </div>
      ))}
      <button
        type="button"
        data-testid={`section-add-opinion-${section.id}`}
        onClick={() => updateOpinions([...opinions, { consultant_id: "", comment: "" }])}
        style={{ fontSize: 12, padding: "6px 10px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 6, cursor: "pointer", marginBottom: 10 }}
      >
        + Görüş ekle
      </button>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button type="button" onClick={handleAiCheck} disabled={checking} style={btnStyle}>
          {checking ? "Kontrol ediliyor…" : "AI ile kontrol et"}
        </button>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94a3b8", cursor: "pointer" }}>
          <input
            type="checkbox"
            data-testid={`section-consultant-approved-${section.id}`}
            checked={section.consultant_approved ?? false}
            onChange={(e) => onChange({ ...section, consultant_approved: e.target.checked })}
          />
          Onaylandı
        </label>
      </div>
    </div>
  );
}

function SectionPreview({
  section,
  selected,
  onSelect,
  onAi,
  aiBusy,
}: {
  section: ReportSection;
  selected: boolean;
  onSelect: () => void;
  onAi: (e: React.MouseEvent) => void;
  aiBusy: boolean;
}) {
  const canAi = AI_TYPES.has(section.type) && section.type !== "divider";
  return (
    <div style={{ display: "flex", gap: 4, marginBottom: 4, alignItems: "stretch" }}>
      <button
        type="button"
        onClick={onSelect}
        style={{
          flex: 1,
          textAlign: "left",
          padding: "8px 10px",
          borderRadius: 6,
          border: selected ? "1px solid #3b82f6" : "1px solid #334155",
          background: selected ? "#1e3a5f" : "#1e293b",
          color: "#e2e8f0",
          cursor: "pointer",
          fontSize: 12,
        }}
      >
        <span style={{ color: "#64748b", fontSize: 10 }}>{section.type}</span>
        <div style={{ fontWeight: 600 }}>{section.title || section.id}</div>
      </button>
      {canAi && (
        <button
          type="button"
          data-testid={`section-ai-${section.id}`}
          onClick={onAi}
          disabled={aiBusy}
          title="AI Yaz"
          style={{
            ...smallBtn,
            padding: "6px 8px",
            minWidth: 32,
            background: "#1d4ed8",
          }}
        >
          {aiBusy ? "…" : "✨"}
        </button>
      )}
    </div>
  );
}

function SectionEditor({
  section,
  onChange,
  reportId,
  consultants,
  onFeedback,
}: {
  section: ReportSection;
  onChange: (updated: ReportSection) => void;
  reportId?: string;
  consultants: Consultant[];
  onFeedback?: (msg: string) => void;
}) {
  if (section.type === "text") {
    return (
      <>
        <textarea
          data-testid={`section-body-${section.id}`}
          value={section.body ?? ""}
          onChange={(e) => onChange({ ...section, body: e.target.value })}
          rows={12}
          style={{ width: "100%", background: "#0f1117", color: "#e2e8f0", border: "1px solid #334155", borderRadius: 8, padding: 12, fontSize: 13 }}
        />
        {reportId && onFeedback && (
          <ConsultantOpinionsEditor section={section} reportId={reportId} consultants={consultants} onChange={onChange} onFeedback={onFeedback} />
        )}
      </>
    );
  }
  if (section.type === "table") {
    const rows = section.rows ?? [];
    const cols = section.columns ?? [];
    return (
      <div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr>{cols.map((c, i) => <th key={i} style={{ border: "1px solid #334155", padding: 6 }}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci} style={{ border: "1px solid #334155", padding: 0 }}>
                    <input
                      value={cell}
                      onChange={(e) => {
                        const newRows = rows.map((r, ridx) =>
                          ridx === ri ? r.map((c, cidx) => (cidx === ci ? e.target.value : c)) : r
                        );
                        onChange({ ...section, rows: newRows });
                      }}
                      style={{ width: "100%", background: "transparent", color: "#e2e8f0", border: "none", padding: 6 }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <button
          type="button"
          onClick={() => onChange({ ...section, rows: [...rows, cols.map(() => "")] })}
          style={{ marginTop: 8, fontSize: 12, padding: "6px 10px", background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 6, cursor: "pointer" }}
        >
          + Satır
        </button>
      </div>
    );
  }
  if (section.type === "kpi_grid") {
    return (
      <>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {(section.items ?? []).map((item, i) => (
            <div key={i} style={{ border: "1px solid #334155", borderRadius: 8, padding: 12, minWidth: 100 }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#60a5fa" }}>{item.value}</div>
              <div style={{ fontSize: 11, color: "#94a3b8" }}>{item.label}</div>
            </div>
          ))}
        </div>
        <CommentaryEditor section={section} onChange={onChange} />
      </>
    );
  }
  if (section.type === "chart_radar") {
    return (
      <>
        <RadarPreview data={section.data ?? {}} />
        <CommentaryEditor section={section} onChange={onChange} />
      </>
    );
  }
  if (section.type === "chart_heatmap") {
    const cells = section.data?.cells ?? [];
    return (
      <>
        <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
          <thead><tr><th style={{ border: "1px solid #334155", padding: 6 }}>Alan</th><th style={{ border: "1px solid #334155", padding: 6 }}>Severity</th><th style={{ border: "1px solid #334155", padding: 6 }}>Sayı</th></tr></thead>
          <tbody>
            {cells.map((c, i) => (
              <tr key={i}>
                <td style={{ border: "1px solid #334155", padding: 6 }}>{c.capability_area}</td>
                <td style={{ border: "1px solid #334155", padding: 6 }}>{c.severity}</td>
                <td style={{ border: "1px solid #334155", padding: 6 }}>{c.risk_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <CommentaryEditor section={section} onChange={onChange} />
      </>
    );
  }
  if (section.type === "cover") {
    return (
      <div style={{ padding: 20, border: "1px solid #334155", borderRadius: 8 }}>
        <h2 style={{ margin: 0 }}>{section.title}</h2>
        <input
          value={section.subtitle ?? ""}
          onChange={(e) => onChange({ ...section, subtitle: e.target.value })}
          placeholder="Alt başlık / özet"
          style={{ ...selectStyle, width: "100%", marginTop: 12 }}
        />
        <p style={{ color: "#94a3b8", fontSize: 13, marginTop: 12 }}>Müşteri: {section.client} · {section.date}</p>
      </div>
    );
  }
  return <p style={{ color: "#64748b" }}>Bu bölüm tipi salt okunurdur.</p>;
}

function firstTextSectionId(sections: ReportSection[]): string | null {
  const text = sections.find((s) => s.type === "text");
  return text?.id ?? sections[0]?.id ?? null;
}

function seedConsultantOpinions(content: ReportContent, consultants: Consultant[]): ReportContent {
  if (!consultants.length) return content;
  const sections = content.sections.map((s) => {
    if (s.type !== "text" || s.consultant_opinions?.length) return s;
    return {
      ...s,
      consultant_opinions: consultants.map((c) => ({ consultant_id: c.id, comment: "" })),
    };
  });
  return { ...content, sections };
}

export default function ReportStudio() {
  const { assessmentId } = useAssessment();
  const [report, setReport] = useState<ReportRecord | null>(null);
  const [content, setContent] = useState<ReportContent>({ version: 1, sections: [] });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [composing, setComposing] = useState(false);
  const [aiMode, setAiMode] = useState<"generate" | "rewrite" | "expand" | "shorten" | "tone_executive">("generate");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiSectionId, setAiSectionId] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState("");
  const [status, setStatus] = useState("");
  const [consultants, setConsultants] = useState<Consultant[]>([]);

  useEffect(() => {
    if (!assessmentId) {
      setConsultants([]);
      return;
    }
    listAllConsultants().then(setConsultants).catch(() => setConsultants([]));
  }, [assessmentId]);

  const load = useCallback(async () => {
    if (!assessmentId) { setLoading(false); return; }
    setLoading(true);
    try {
      const reports = await listReports(assessmentId);
      const r = reports[0] ?? null;
      setReport(r);
      if (r?.content_json) {
        const parsed = JSON.parse(r.content_json) as ReportContent;
        parsed.sections = parsed.sections.map(migrateSectionOpinions);
        setContent(parsed);
        setSelectedId(firstTextSectionId(parsed.sections));
      }
    } catch {
      setReport(null);
      setStatus("Rapor yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => { load(); }, [load]);

  const selected = content.sections.find((s) => s.id === selectedId) ?? null;

  const saveContent = async (parsed: ReportContent, reportId: string) => {
    const updated = await patchReport(reportId, {
      title: report?.title,
      content_json: JSON.stringify(parsed),
    });
    setReport(updated);
    return updated;
  };

  const applyAiResult = async (res: { content_json: string; updated_sections: string[]; total_sections?: number }) => {
    const parsed = JSON.parse(res.content_json) as ReportContent;
    setContent(parsed);
    if (report) {
      await saveContent(parsed, report.id);
    }
    const count = res.total_sections ?? res.updated_sections.length;
    setStatus(`AI tamamlandı (${count} bölüm) — kaydedildi.`);
  };

  const handleCompose = async () => {
    if (!assessmentId) return;
    setComposing(true);
    setStatus("");
    try {
      const r = await composeReport(assessmentId);
      setReport(r);
      let parsed = JSON.parse(r.content_json ?? '{"version":1,"sections":[]}') as ReportContent;
      parsed = seedConsultantOpinions(parsed, consultants);
      if (consultants.length) {
        const updated = await patchReport(r.id, {
          title: r.title,
          content_json: JSON.stringify(parsed),
        });
        setReport(updated);
      }
      setContent(parsed);
      setSelectedId(firstTextSectionId(parsed.sections));
      setStatus("Rapor oluşturuldu.");
    } catch {
      setStatus("Compose başarısız.");
    } finally {
      setComposing(false);
    }
  };

  const handleSave = async () => {
    if (!report) return;
    setSaving(true);
    setStatus("");
    try {
      await saveContent(content, report.id);
      setStatus("Kaydedildi.");
    } catch {
      setStatus("Kaydetme hatası.");
    } finally {
      setSaving(false);
    }
  };

  const runAiGenerate = async (sectionId?: string | null) => {
    if (!report) return;
    setAiBusy(true);
    setAiSectionId(sectionId ?? null);
    setStatus("");
    setBatchProgress(sectionId ? "" : "AI yazımı başlıyor…");
    try {
      const res = await aiGenerateReport(report.id, {
        section_id: sectionId ?? null,
        instruction: "Bu bölüm için profesyonel rapor metni yaz",
        mode: aiMode,
      });
      await applyAiResult(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "AI yazım hatası";
      setStatus(`AI hatası: ${msg}`);
    } finally {
      setAiBusy(false);
      setAiSectionId(null);
      setBatchProgress("");
    }
  };

  const handleBatchAi = async () => {
    if (!report) return;
    const count = content.sections.filter((s) => AI_TYPES.has(s.type) && s.type !== "divider").length;
    if (!window.confirm(`${count} bölüm AI ile yazılacak. Devam?`)) return;
    setBatchProgress(`0/${count} bölüm…`);
    await runAiGenerate(null);
  };

  const addSection = () => {
    const id = `custom-${Date.now()}`;
    const section: ReportSection = { id, type: "text", title: "Yeni Bölüm", body: "" };
    setContent((c) => ({ ...c, sections: [...c.sections, section] }));
    setSelectedId(id);
  };

  const removeSection = () => {
    if (!selectedId) return;
    setContent((c) => ({ ...c, sections: c.sections.filter((s) => s.id !== selectedId) }));
    setSelectedId(null);
  };

  const moveSection = (dir: -1 | 1) => {
    if (!selectedId) return;
    const idx = content.sections.findIndex((s) => s.id === selectedId);
    if (idx < 0) return;
    const next = idx + dir;
    if (next < 0 || next >= content.sections.length) return;
    const sections = [...content.sections];
    [sections[idx], sections[next]] = [sections[next], sections[idx]];
    setContent({ ...content, sections });
  };

  return (
    <div data-testid="report-studio">
      <AssessmentPageHeader
        title="Rapor Stüdyosu"
        subtitle="Assessment verilerinden rapor oluşturun, düzenleyin ve dışa aktarın."
        actions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <button type="button" onClick={handleCompose} disabled={!assessmentId || composing} style={btnStyle}>
              {composing ? "Oluşturuluyor…" : "Rapor Oluştur / Yenile"}
            </button>
            <button type="button" onClick={handleSave} disabled={!report || saving} style={btnStyle}>
              {saving ? "Kaydediliyor…" : "Kaydet"}
            </button>
            {report && (
              <>
                <select value={aiMode} onChange={(e) => setAiMode(e.target.value as typeof aiMode)} style={selectStyle}>
                  <option value="generate">Üret</option>
                  <option value="rewrite">Yeniden yaz</option>
                  <option value="expand">Genişlet</option>
                  <option value="shorten">Kısalt</option>
                  <option value="tone_executive">Yönetici tonu</option>
                </select>
                <button type="button" onClick={() => downloadReportBlob(report.id, "pdf")} style={btnStyle}>PDF</button>
                <button type="button" onClick={() => downloadReportBlob(report.id, "docx")} style={btnStyle}>Word</button>
              </>
            )}
          </div>
        }
      />

      {(status || batchProgress) && (
        <p style={{ color: status.startsWith("AI hatası") ? "#f87171" : "#60a5fa", fontSize: 13, marginBottom: 12 }}>
          {batchProgress || status}
        </p>
      )}

      {report && (
        <div style={{ marginBottom: 16 }}>
          <button
            type="button"
            data-testid="report-ai-generate-all-top"
            onClick={handleBatchAi}
            disabled={aiBusy}
            style={{
              width: "100%",
              padding: "14px 20px",
              borderRadius: 10,
              border: "none",
              background: aiBusy ? "#4c1d95" : "linear-gradient(135deg, #7e22ce, #6d28d9)",
              color: "#fff",
              fontWeight: 800,
              fontSize: 15,
              cursor: aiBusy ? "not-allowed" : "pointer",
              boxShadow: "0 4px 20px rgba(126,34,206,0.45)",
            }}
          >
            {aiBusy && !aiSectionId ? "AI yazıyor…" : "✨ Tüm Raporu AI ile Yaz"}
          </button>
        </div>
      )}

      {loading ? (
        <p style={{ color: "#64748b" }}>Yükleniyor…</p>
      ) : !report ? (
        <div
          data-testid="report-empty-state"
          style={{
            textAlign: "center",
            padding: 56,
            color: "#64748b",
            border: "1px dashed #334155",
            borderRadius: 12,
            background: "#0f1117",
          }}
        >
          <p style={{ fontSize: 16, marginBottom: 16, color: "#94a3b8" }}>
            Bu assessment için henüz rapor oluşturulmadı.
          </p>
          <button
            type="button"
            data-testid="report-compose-cta"
            onClick={handleCompose}
            disabled={!assessmentId || composing}
            style={{
              ...btnStyle,
              fontSize: 15,
              padding: "12px 24px",
              boxShadow: "0 4px 14px rgba(37,99,235,0.35)",
            }}
          >
            {composing ? "Oluşturuluyor…" : "Rapor Oluştur / Yenile"}
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 16, minHeight: 480 }}>
          <aside style={{ borderRight: "1px solid #1e293b", paddingRight: 12 }}>
            <div style={{ display: "flex", gap: 4, marginBottom: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={addSection} style={smallBtn}>+ Bölüm</button>
              <button type="button" onClick={removeSection} disabled={!selectedId} style={smallBtn}>Sil</button>
              <button type="button" onClick={() => moveSection(-1)} style={smallBtn}>↑</button>
              <button type="button" onClick={() => moveSection(1)} style={smallBtn}>↓</button>
            </div>
            {content.sections.map((s) => (
              <SectionPreview
                key={s.id}
                section={s}
                selected={s.id === selectedId}
                onSelect={() => setSelectedId(s.id)}
                onAi={(e) => {
                  e.stopPropagation();
                  runAiGenerate(s.id);
                }}
                aiBusy={aiBusy && aiSectionId === s.id}
              />
            ))}
          </aside>
          <section>
            {selected ? (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <h2 style={{ margin: 0, fontSize: 18 }}>{selected.title || selected.id}</h2>
                  {AI_TYPES.has(selected.type) && (
                    <button
                      type="button"
                      data-testid={`section-ai-toolbar-${selected.id}`}
                      onClick={() => runAiGenerate(selected.id)}
                      disabled={aiBusy}
                      style={btnStyle}
                    >
                      {aiBusy && aiSectionId === selected.id ? "AI yazıyor…" : "✨ AI Yaz"}
                    </button>
                  )}
                </div>
                {selected.type === "text" && (
                  <input
                    value={selected.title ?? ""}
                    onChange={(e) => {
                      const sections = content.sections.map((s) =>
                        s.id === selectedId ? { ...s, title: e.target.value } : s
                      );
                      setContent({ ...content, sections });
                    }}
                    style={{ ...selectStyle, width: "100%", marginBottom: 12 }}
                    placeholder="Bölüm başlığı"
                  />
                )}
                <SectionEditor
                  section={selected}
                  reportId={report.id}
                  consultants={consultants}
                  onFeedback={setStatus}
                  onChange={(updated) => {
                    setContent({
                      ...content,
                      sections: content.sections.map((s) => (s.id === updated.id ? updated : s)),
                    });
                  }}
                />
              </>
            ) : (
              <p style={{ color: "#64748b" }}>Düzenlemek için sol panelden bir bölüm seçin.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  background: "#2563eb",
  border: "none",
  borderRadius: 6,
  padding: "8px 14px",
  color: "#fff",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
};

const smallBtn: React.CSSProperties = {
  ...btnStyle,
  padding: "4px 8px",
  fontSize: 11,
  background: "#334155",
};

const selectStyle: React.CSSProperties = {
  background: "#1e293b",
  color: "#e2e8f0",
  border: "1px solid #334155",
  borderRadius: 6,
  padding: "6px 8px",
  fontSize: 12,
};
