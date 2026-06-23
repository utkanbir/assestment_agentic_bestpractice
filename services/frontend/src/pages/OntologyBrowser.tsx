import { useEffect, useMemo, useState, lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { OntologyClass, OntologyProperty, getOntologySchema } from "../api";
import { useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";
import type { GraphCanvasEdge, GraphCanvasNode } from "../components/GraphCanvas";

const GraphCanvas = lazy(() => import("../components/GraphCanvas"));

function short(uri: string): string {
  if (uri.includes("#")) return uri.split("#").pop() || uri;
  return uri.split("/").pop() || uri;
}

function buildOntologyGraph(classes: OntologyClass[], properties: OntologyProperty[]) {
  const nodes: GraphCanvasNode[] = classes.map((cls) => ({
    id: cls.id,
    label: cls.label || short(cls.id),
    type: "class",
  }));
  const nodeIds = new Set(nodes.map((n) => n.id));
  const edges: GraphCanvasEdge[] = [];

  for (const cls of classes) {
    for (const parent of cls.parents) {
      if (nodeIds.has(parent)) {
        edges.push({ source: cls.id, target: parent, label: "subClassOf" });
      }
    }
  }

  for (const prop of properties) {
    const propId = `prop:${prop.id}`;
    nodes.push({
      id: propId,
      label: prop.label || short(prop.id),
      type: "property",
    });
    for (const domain of prop.domain) {
      if (nodeIds.has(domain)) {
        edges.push({ source: propId, target: domain, label: prop.kind });
      }
    }
  }

  return { nodes, edges };
}

type ViewMode = "list" | "graph";

export default function OntologyBrowser() {
  const withAssessment = useAssessmentNavLink();
  const [classes, setClasses] = useState<OntologyClass[]>([]);
  const [properties, setProperties] = useState<OntologyProperty[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<ViewMode>("list");

  useEffect(() => {
    getOntologySchema()
      .then((res) => {
        setClasses(res.classes);
        setProperties(res.properties);
        setSources(res.sources);
        if (res.classes.length > 0) setSelectedClass(res.classes[0].id);
      })
      .catch(() => {
        setClasses([]);
        setProperties([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const activeClass = useMemo(
    () => classes.find((cls) => cls.id === selectedClass) ?? null,
    [classes, selectedClass],
  );
  const classProperties = useMemo(
    () => properties.filter((p) => p.domain.includes(selectedClass)),
    [properties, selectedClass],
  );
  const graph = useMemo(
    () => buildOntologyGraph(classes, properties),
    [classes, properties],
  );

  if (loading) return <p style={{ color: "#64748b" }}>Ontoloji yukleniyor...</p>;

  return (
    <div style={{ maxWidth: 1180, margin: "0 auto" }}>
      <AssessmentPageHeader
        title="Ontoloji"
        subtitle="TBox şeması — sınıflar ve özellikler (global)"
        actions={
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div style={{ display: "flex", gap: 4 }}>
              {(["list", "graph"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  data-testid={`ontology-view-${mode}`}
                  onClick={() => setView(mode)}
                  style={{
                    background: view === mode ? "#3b82f6" : "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 6,
                    padding: "5px 12px",
                    color: view === mode ? "#fff" : "#94a3b8",
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  {mode === "list" ? "Liste" : "Graf"}
                </button>
              ))}
            </div>
            <Link to={withAssessment("/knowledge-graph")} style={{ color: "#60a5fa", fontSize: 13 }}>
              Bu assessment&apos;ın KG&apos;sine git →
            </Link>
          </div>
        }
      />
      <p style={{ color: "#64748b", fontSize: 12, marginTop: -8, marginBottom: 16 }}>Kaynaklar: {sources.join(", ")}</p>

      {view === "graph" ? (
        <Suspense fallback={<p style={{ color: "#64748b" }}>Graf yükleniyor…</p>}>
          <GraphCanvas nodes={graph.nodes} edges={graph.edges} height={560} />
        </Suspense>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 14, marginTop: 16 }}>
          <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, maxHeight: "70vh", overflow: "auto" }}>
            {classes.map((cls) => {
              const active = cls.id === selectedClass;
              return (
                <button
                  key={cls.id}
                  onClick={() => setSelectedClass(cls.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    border: "none",
                    borderBottom: "1px solid #334155",
                    background: active ? "#0f172a" : "transparent",
                    color: active ? "#e2e8f0" : "#94a3b8",
                    padding: "10px 12px",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 13 }}>{cls.label}</div>
                  <div style={{ fontSize: 11, color: "#64748b" }}>{short(cls.id)}</div>
                </button>
              );
            })}
          </div>

          <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: 16 }}>
            {!activeClass ? (
              <p style={{ color: "#64748b" }}>Sinif secin.</p>
            ) : (
              <>
                <h2 style={{ marginTop: 0 }}>{activeClass.label}</h2>
                <p style={{ color: "#94a3b8", fontSize: 13 }}>{activeClass.comment || "Aciklama yok."}</p>
                <p style={{ fontSize: 12, color: "#64748b" }}>
                  URI: <code>{activeClass.id}</code>
                </p>
                <h3 style={{ fontSize: 14, marginTop: 16 }}>Ust siniflar</h3>
                {activeClass.parents.length === 0 ? (
                  <p style={{ color: "#64748b", fontSize: 12 }}>Yok</p>
                ) : (
                  activeClass.parents.map((p) => (
                    <p key={p} style={{ margin: "2px 0", fontSize: 12, color: "#94a3b8" }}>{short(p)}</p>
                  ))
                )}

                <h3 style={{ fontSize: 14, marginTop: 18 }}>Ozellikler ({classProperties.length})</h3>
                {classProperties.length === 0 ? (
                  <p style={{ color: "#64748b", fontSize: 12 }}>Bu sinif icin domain ozelligi yok.</p>
                ) : (
                  classProperties.map((prop) => (
                    <div key={prop.id} style={{ border: "1px solid #334155", borderRadius: 8, padding: 10, marginBottom: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <strong style={{ fontSize: 13 }}>{prop.label}</strong>
                        <span style={{ fontSize: 11, color: "#64748b" }}>{prop.kind}</span>
                      </div>
                      <p style={{ margin: "6px 0", fontSize: 12, color: "#94a3b8" }}>{prop.comment || "Aciklama yok."}</p>
                      <p style={{ margin: "0", fontSize: 11, color: "#64748b" }}>
                        Range: {prop.range.length ? prop.range.map(short).join(", ") : "-"}
                      </p>
                    </div>
                  ))
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
