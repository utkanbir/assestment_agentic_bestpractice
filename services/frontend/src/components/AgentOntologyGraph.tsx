import { useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { AgentGraph, AgentGraphNode } from "../api";

const TYPE_COLOR: Record<string, string> = {
  agent: "#3b82f6",
  document: "#f472b6",
  learning_event: "#34d399",
  learning_event_ai: "#a78bfa",
  ontology: "#c084fc",
};

function layoutNodes(graph: AgentGraph): Node[] {
  const byType: Record<string, number> = {};
  return graph.nodes.map((n) => {
    const colKey = n.type === "learning_event_ai" ? "learning_event" : n.type;
    const col = { agent: 0, ontology: 1, document: 2, learning_event: 3 }[colKey] ?? 2;
    const row = byType[n.type] ?? 0;
    byType[n.type] = row + 1;
    return {
      id: n.id,
      position: { x: col * 160 + 20, y: row * 70 + 20 },
      data: { label: n.label, node: n },
      style: {
        background: TYPE_COLOR[n.type] ?? "#334155",
        color: "#fff",
        border: "none",
        borderRadius: 8,
        fontSize: 10,
        padding: "6px 10px",
        maxWidth: 140,
        cursor: "pointer",
      },
    };
  });
}

export default function AgentOntologyGraph({
  graph,
  height = 480,
  onNodeSelect,
}: {
  graph: AgentGraph | null;
  height?: number;
  onNodeSelect?: (node: AgentGraphNode | null) => void;
}) {
  const initialNodes = useMemo(() => (graph ? layoutNodes(graph) : []), [graph]);
  const initialEdges: Edge[] = useMemo(
    () =>
      (graph?.edges ?? []).map((e, i) => ({
        id: `e${i}`,
        source: e.source,
        target: e.target,
        label: e.label,
        style: { stroke: "#475569" },
        labelStyle: { fill: "#94a3b8", fontSize: 8 },
      })),
    [graph],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  if (!graph) {
    return <p style={{ color: "#475569", textAlign: "center", padding: 40 }}>Graf yükleniyor…</p>;
  }
  if (graph.nodes.length === 0) {
    return <p style={{ color: "#475569", textAlign: "center", padding: 40 }}>Henüz veri yok.</p>;
  }

  return (
    <div style={{ height, background: "#0f1117", borderRadius: 10, border: "1px solid #334155" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeSelect?.((node.data as { node?: AgentGraphNode }).node ?? null)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1e293b" gap={16} />
        <Controls />
        <MiniMap nodeColor={(n) => TYPE_COLOR[(graph.nodes.find((g) => g.id === n.id)?.type) ?? ""] ?? "#334155"} />
      </ReactFlow>
    </div>
  );
}
