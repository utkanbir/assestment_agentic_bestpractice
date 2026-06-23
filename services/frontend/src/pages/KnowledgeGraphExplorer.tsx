import { useEffect, useMemo, useState, useCallback, lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { KnowledgeGraphEdge, KnowledgeGraphNode, getAssessmentKnowledgeGraph, listAssessments } from "../api";
import { RequireAssessment, useAssessment } from "../context/AssessmentContext";
import type { GraphCanvasEdge, GraphCanvasNode } from "../components/GraphCanvas";

const GraphCanvas = lazy(() => import("../components/GraphCanvas"));

function short(uri: string): string {
  if (uri.includes("#")) return uri.split("#").pop() || uri;
  return uri.split("/").pop() || uri;
}

function toCanvasGraph(nodes: KnowledgeGraphNode[]): GraphCanvasNode[] {
  return nodes.map((n) => ({
    id: n.id,
    label: n.label || short(n.id),
    type: n.type,
    color: n.type.toLowerCase().includes("assessment") ? "simulated" : undefined,
  }));
}

function toCanvasEdges(edges: KnowledgeGraphEdge[]): GraphCanvasEdge[] {
  return edges.map((e, i) => ({
    id: `kg-${i}`,
    source: e.from,
    target: e.to,
    label: e.predicate,
  }));
}

type ViewMode = "graph" | "table";

function ExplorerContent() {
  const { assessmentId } = useAssessment();
  const [nodes, setNodes] = useState<KnowledgeGraphNode[]>([]);
  const [edges, setEdges] = useState<KnowledgeGraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSimulated, setIsSimulated] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);
  const [view, setView] = useState<ViewMode>("graph");

  const loadGraph = useCallback(() => {
    if (!assessmentId) return;
    setLoading(true);
    getAssessmentKnowledgeGraph(assessmentId)
      .then((res) => {
        setNodes(res.nodes);
        setEdges(res.edges);
      })
      .catch(() => {
        setNodes([]);
        setEdges([]);
      })
      .finally(() => setLoading(false));
  }, [assessmentId]);

  useEffect(() => {
    listAssessments()
      .then((list) => {
        const a = list.find((x) => x.id === assessmentId);
        setIsSimulated(a?.assessment_mode === "simulated");
      })
      .catch(() => setIsSimulated(false));
  }, [assessmentId]);

  useEffect(() => { loadGraph(); }, [loadGraph, refreshTick]);

  useEffect(() => {
    if (!isSimulated || !assessmentId) return;
    const id = setInterval(() => setRefreshTick((t) => t + 1), 4000);
    return () => clearInterval(id);
  }, [isSimulated, assessmentId]);

  const edgeRows = useMemo(
    () =>
      edges.map((e) => ({
        ...e,
        fromLabel: nodes.find((n) => n.id === e.from)?.label ?? short(e.from),
        toLabel: nodes.find((n) => n.id === e.to)?.label ?? short(e.to),
      })),
    [edges, nodes],
  );

  const canvasNodes = useMemo(() => toCanvasGraph(nodes), [nodes]);
  const canvasEdges = useMemo(() => toCanvasEdges(edges), [edges]);

  if (loading) return <p style={{ color: "#64748b" }}>Knowledge Graph yukleniyor...</p>;
  if (nodes.length === 0) {
    return (
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 24 }}>
        <p style={{ marginTop: 0, color: "#94a3b8" }}>
          Henuz KG verisi yok. Interview olusturup cevap kaydetmeyi deneyin.
        </p>
        <Link to={`/interview?assessment_id=${assessmentId}`} style={{ color: "#60a5fa" }}>
          Interview ekranina git
        </Link>
      </div>
    );
  }

  return (
    <>
      <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
        {(["graph", "table"] as const).map((mode) => (
          <button
            key={mode}
            type="button"
            data-testid={`kg-view-${mode}`}
            onClick={() => setView(mode)}
            style={{
              background: view === mode ? "#3b82f6" : "#1e293b",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "6px 14px",
              color: view === mode ? "#fff" : "#94a3b8",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            {mode === "graph" ? "Graf" : "Tablo"}
          </button>
        ))}
      </div>

      {isSimulated && (
        <div data-testid="kg-simulated-banner" style={{ marginBottom: 12, padding: "8px 12px", background: "#2e1065", border: "1px solid #7e22ce", borderRadius: 8, fontSize: 12, color: "#e9d5ff" }}>
          AI Simulated assessment — grafik otomatik yenileniyor (kg.updated)
        </div>
      )}

      {view === "graph" ? (
        <Suspense fallback={<p style={{ color: "#64748b" }}>Graf yükleniyor…</p>}>
          <GraphCanvas
            nodes={canvasNodes}
            edges={canvasEdges}
            height={520}
            simulatedHighlight={isSimulated}
          />
        </Suspense>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 12 }}>
              <strong>Dugum sayisi</strong>
              <p style={{ marginBottom: 0, color: "#94a3b8" }}>{nodes.length}</p>
            </div>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: 12 }}>
              <strong>Kenar sayisi</strong>
              <p style={{ marginBottom: 0, color: "#94a3b8" }}>{edges.length}</p>
            </div>
          </div>

          <h3 style={{ marginBottom: 8 }}>Node listesi</h3>
          <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, maxHeight: 250, overflow: "auto", marginBottom: 14 }}>
            {nodes.map((node) => (
              <div key={node.id} style={{ padding: "8px 12px", borderBottom: "1px solid #334155" }}>
                <strong style={{ fontSize: 13 }}>
                  {node.label}
                  {isSimulated && node.type.toLowerCase().includes("assessment") && (
                    <span style={{ marginLeft: 6, fontSize: 9, color: "#c084fc", border: "1px solid #7e22ce", borderRadius: 4, padding: "1px 5px" }}>AI</span>
                  )}
                </strong>
                <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 11 }}>{node.type}</p>
              </div>
            ))}
          </div>

          <h3 style={{ marginBottom: 8 }}>Iliski tablosu</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", background: "#1e293b", border: "1px solid #334155", borderRadius: 8, overflow: "hidden" }}>
            <thead>
              <tr style={{ background: "#0f1117", color: "#94a3b8", fontSize: 12 }}>
                <th style={{ textAlign: "left", padding: "8px 10px" }}>From</th>
                <th style={{ textAlign: "left", padding: "8px 10px" }}>Predicate</th>
                <th style={{ textAlign: "left", padding: "8px 10px" }}>To</th>
              </tr>
            </thead>
            <tbody>
              {edgeRows.map((e, idx) => (
                <tr key={`${e.from}-${e.predicate}-${idx}`} style={{ borderTop: "1px solid #334155", fontSize: 12 }}>
                  <td style={{ padding: "8px 10px" }}>{e.fromLabel}</td>
                  <td style={{ padding: "8px 10px", color: "#60a5fa" }}>{e.predicate}</td>
                  <td style={{ padding: "8px 10px" }}>{e.toLabel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}

export default function KnowledgeGraphExplorer() {
  return (
    <RequireAssessment>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h1 style={{ marginTop: 0 }}>Knowledge Graph</h1>
        <p style={{ color: "#94a3b8", fontSize: 13 }}>
          Assessment bazli instance graph gorunumu (ABox).
        </p>
        <ExplorerContent />
      </div>
    </RequireAssessment>
  );
}
