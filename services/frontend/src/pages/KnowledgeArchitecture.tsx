// S15-FA-001/002: Knowledge Architecture — 4-layer stack + live touch timeline
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArchitectureLayer,
  LayerTouch,
  LayerTouchSummary,
  getArchitectureLayers,
  getLayerTouchSummary,
  listLayerTouches,
} from "../api";
import { useAssessment, useAssessmentNavLink } from "../context/AssessmentContext";

const SYSTEM_PATH_PREFIXES = ["/health", "/api/", "/openmetadata"];

function resolveLink(url: string | null | undefined, navLink: (path: string) => string): string {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  if (SYSTEM_PATH_PREFIXES.some((p) => url.startsWith(p))) return url;
  if (url.startsWith("/")) return navLink(url);
  return url;
}

const LAYER_COLORS: Record<string, { bg: string; border: string; accent: string }> = {
  data:        { bg: "#1a1208", border: "#92400e", accent: "#f59e0b" },
  information: { bg: "#0a1628", border: "#1e40af", accent: "#3b82f6" },
  knowledge:   { bg: "#0a1a14", border: "#065f46", accent: "#10b981" },
  agent:       { bg: "#1a0a28", border: "#6b21a8", accent: "#a855f7" },
};

const LAYER_ORDER = ["agent", "knowledge", "information", "data"];

function LayerCard({
  layer,
  touchCount,
  dimmed,
  selected,
  onSelect,
}: {
  layer: ArchitectureLayer;
  touchCount: number;
  dimmed: boolean;
  selected: boolean;
  onSelect: () => void;
}) {
  const colors = LAYER_COLORS[layer.id] ?? LAYER_COLORS.information;
  const maxHeat = 20;
  const heatPct = Math.min(100, (touchCount / maxHeat) * 100);

  return (
    <div
      data-testid={`layer-card-${layer.id}`}
      onClick={onSelect}
      style={{
        background: colors.bg,
        border: `1px solid ${selected ? colors.accent : dimmed ? "#334155" : colors.border}`,
        borderRadius: 10,
        padding: "16px 18px",
        opacity: dimmed ? 0.55 : 1,
        transition: "opacity 0.2s",
        cursor: "pointer",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: dimmed ? "#64748b" : "#e2e8f0" }}>
            {layer.name}
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "#64748b" }}>{layer.namespace}</p>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 4,
          background: touchCount > 0 ? `${colors.accent}22` : "#1e293b",
          color: touchCount > 0 ? colors.accent : "#475569",
        }}>
          {touchCount} touch
        </span>
      </div>
      <p style={{ fontSize: 12, color: "#94a3b8", margin: "0 0 10px", lineHeight: 1.5 }}>{layer.description}</p>
      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, marginBottom: 12, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${heatPct}%`, background: colors.accent, borderRadius: 2, transition: "width 0.3s" }} />
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {layer.technologies.map(tech => (
          <span
            key={tech.id}
            title={tech.role}
            style={{
              fontSize: 10, padding: "3px 8px", borderRadius: 4,
              background: tech.active_in_api ? `${colors.accent}18` : "#1e293b",
              border: `1px solid ${tech.configured ? colors.border + "66" : "#334155"}`,
              color: tech.active_in_api ? colors.accent : "#64748b",
            }}
          >
            {tech.name}
            {!tech.active_in_api && tech.configured ? " (idle)" : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function TouchRow({ touch, expanded, onToggle }: { touch: LayerTouch; expanded: boolean; onToggle: () => void }) {
  const colors = LAYER_COLORS[touch.layer] ?? LAYER_COLORS.information;
  return (
    <div
      data-testid={`touch-row-${touch.id}`}
      style={{ border: "1px solid #334155", borderRadius: 8, marginBottom: 8, overflow: "hidden" }}
    >
      <button
        onClick={onToggle}
        style={{
          width: "100%", textAlign: "left", padding: "10px 14px",
          background: "#1e293b", border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", gap: 10,
        }}
      >
        <span style={{
          fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 4,
          background: `${colors.accent}22`, color: colors.accent, textTransform: "uppercase",
        }}>
          {touch.layer}
        </span>
        <span style={{ fontSize: 13, color: "#e2e8f0", flex: 1 }}>{touch.operation}</span>
        <span style={{ fontSize: 11, color: "#64748b" }}>{touch.technology} · {touch.action}</span>
        <span style={{ fontSize: 10, color: "#475569" }}>{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && (
        <div style={{ padding: "10px 14px", background: "#0f1117", fontSize: 11, color: "#94a3b8" }}>
          {touch.detail ? (
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 11 }}>
              {JSON.stringify(touch.detail, null, 2)}
            </pre>
          ) : (
            <span>Detay yok</span>
          )}
          {touch.duration_ms != null && (
            <p style={{ margin: "8px 0 0", color: "#64748b" }}>{touch.duration_ms} ms</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function KnowledgeArchitecture() {
  const [searchParams] = useSearchParams();
  const navLink = useAssessmentNavLink();
  const { selectedAssessment } = useAssessment();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const interviewId = searchParams.get("interview_id") ?? "";
  const [selectedLayer, setSelectedLayer] = useState<string>("");

  const [layers, setLayers] = useState<ArchitectureLayer[]>([]);
  const [touches, setTouches] = useState<LayerTouch[]>([]);
  const [summary, setSummary] = useState<LayerTouchSummary[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const touchCountByLayer = useMemo(() => {
    const map: Record<string, number> = {};
    for (const s of summary) map[s.layer] = s.touch_count;
    return map;
  }, [summary]);

  const refresh = useCallback(async () => {
    try {
      const [layersRes, touchesRes, summaryRes] = await Promise.all([
        getArchitectureLayers(),
        listLayerTouches(assessmentId || undefined, interviewId || undefined, selectedLayer || undefined),
        getLayerTouchSummary(assessmentId || undefined, interviewId || undefined),
      ]);
      setLayers(layersRes.layers);
      setTouches(touchesRes);
      setSummary(summaryRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [assessmentId, interviewId, selectedLayer]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  // WebSocket live updates when interview_id is set
  useEffect(() => {
    if (!interviewId) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/interviews/${interviewId}`);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.event === "layer.touch" && msg.payload?.touch) {
          setTouches(prev => [msg.payload.touch as LayerTouch, ...prev].slice(0, 100));
          setSummary(prev => {
            const layer = msg.payload.touch.layer as string;
            const existing = prev.find(s => s.layer === layer);
            if (existing) {
              return prev.map(s =>
                s.layer === layer
                  ? { ...s, touch_count: s.touch_count + 1, last_operation: msg.payload.touch.operation }
                  : s,
              );
            }
            return [...prev, { layer, touch_count: 1, last_operation: msg.payload.touch.operation, last_at: msg.payload.touch.created_at }];
          });
        }
      } catch { /* ignore */ }
    };
    return () => ws.close();
  }, [interviewId]);

  const orderedLayers = LAYER_ORDER
    .map(id => layers.find(l => l.id === id))
    .filter((l): l is ArchitectureLayer => !!l);

  return (
    <div style={{ padding: "20px 24px", maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 6px" }}>Knowledge Architecture</h1>
        <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>
          4 katmanlı mimari — her işlemde hangi teknolojiye dokunulduğu
        </p>
        {selectedAssessment && (
          <div
            data-testid="architecture-assessment-banner"
            style={{
              marginTop: 12,
              padding: "8px 12px",
              background: "#1e3a5f",
              border: "1px solid #1d4ed8",
              borderRadius: 8,
              fontSize: 12,
              color: "#bfdbfe",
            }}
          >
            Bu görünüm seçili assessment için:{" "}
            <strong>{selectedAssessment.client_name} — {selectedAssessment.project_name}</strong>
          </div>
        )}
        {(assessmentId || interviewId) && (
          <p style={{ fontSize: 11, color: "#64748b", marginTop: 8 }}>
            Filtre: {assessmentId && `assessment ${assessmentId.slice(0, 8)}…`}
            {assessmentId && interviewId && " · "}
            {interviewId && `interview ${interviewId.slice(0, 8)}…`}
          </p>
        )}
      </div>

      {loading ? (
        <p style={{ color: "#64748b" }}>Yükleniyor…</p>
      ) : (
        <>
          <div
            data-testid="layer-stack"
            style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 32 }}
          >
            {orderedLayers.map(layer => (
              <LayerCard
                key={layer.id}
                layer={layer}
                touchCount={touchCountByLayer[layer.id] ?? 0}
                dimmed={(touchCountByLayer[layer.id] ?? 0) === 0 && !!(assessmentId || interviewId)}
                selected={selectedLayer === layer.id}
                onSelect={() => setSelectedLayer((prev) => (prev === layer.id ? "" : layer.id))}
              />
            ))}
          </div>

          {selectedLayer && (
            <div style={{ marginBottom: 18, background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 14 }}>
              <h3 style={{ marginTop: 0, fontSize: 14 }}>Teknoloji Linkleri ({selectedLayer})</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {(layers.find((l) => l.id === selectedLayer)?.technologies ?? []).map((tech) => {
                  const href = resolveLink(tech.console_url, navLink);
                  const isInternal = tech.link_mode === "internal" || (!href && tech.notes);
                  if (isInternal) {
                    return (
                      <span
                        key={tech.id}
                        title={tech.notes ?? "Cluster-internal"}
                        style={{
                          fontSize: 12,
                          border: "1px solid #334155",
                          borderRadius: 6,
                          padding: "5px 8px",
                          color: "#64748b",
                        }}
                      >
                        {tech.name}
                      </span>
                    );
                  }
                  return (
                  <a
                    key={tech.id}
                    href={href || "#"}
                    target={tech.console_url?.startsWith("http") ? "_blank" : "_self"}
                    rel="noreferrer"
                    style={{
                      fontSize: 12,
                      border: "1px solid #334155",
                      borderRadius: 6,
                      padding: "5px 8px",
                      color: href ? "#60a5fa" : "#64748b",
                      textDecoration: "none",
                      pointerEvents: href ? "auto" : "none",
                    }}
                  >
                    {tech.name}
                  </a>
                  );
                })}
              </div>
            </div>
          )}

          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>
            Katman Dokunuşları {touches.length > 0 ? `(${touches.length})` : ""}{selectedLayer ? ` - ${selectedLayer}` : ""}
          </h2>
          {touches.length === 0 ? (
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 24, textAlign: "center" }}>
              <p style={{ color: "#64748b", fontSize: 13, margin: 0 }}>
                Henüz kayıt yok. Interview'da cevap kaydedin veya değerlendirin.
              </p>
              {assessmentId && (
                <Link to={`/interview?assessment_id=${assessmentId}`} style={{ color: "#3b82f6", fontSize: 12, marginTop: 8, display: "inline-block" }}>
                  Interview'a git →
                </Link>
              )}
            </div>
          ) : (
            touches.map(t => (
              <TouchRow
                key={t.id}
                touch={t}
                expanded={expandedId === t.id}
                onToggle={() => setExpandedId(expandedId === t.id ? null : t.id)}
              />
            ))
          )}
        </>
      )}
    </div>
  );
}
