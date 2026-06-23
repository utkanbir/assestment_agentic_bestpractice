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

export interface GraphCanvasNode {
  id: string;
  label: string;
  type?: string;
  color?: string;
}

export interface GraphCanvasEdge {
  id?: string;
  source: string;
  target: string;
  label?: string;
}

const DEFAULT_COLORS: Record<string, string> = {
  class: "#3b82f6",
  property: "#a78bfa",
  assessment: "#a855f7",
  finding: "#f97316",
  default: "#334155",
};

function layoutNodes(
  graphNodes: GraphCanvasNode[],
  simulatedHighlight?: boolean,
): Node[] {
  const byCol: Record<string, number> = {};
  return graphNodes.map((n) => {
    const colKey = n.type ?? "default";
    const row = byCol[colKey] ?? 0;
    byCol[colKey] = row + 1;
    const col = { class: 0, property: 1, assessment: 2, finding: 3, default: 2 }[colKey] ?? 2;
    const isSimAssessment =
      simulatedHighlight &&
      (n.type?.toLowerCase().includes("assessment") || n.color === "simulated");
    const bg = isSimAssessment ? "#7e22ce" : n.color ?? DEFAULT_COLORS[colKey] ?? DEFAULT_COLORS.default;
    return {
      id: n.id,
      position: { x: col * 220 + 40, y: row * 88 + 40 },
      data: { label: n.label },
      style: {
        background: bg,
        color: "#fff",
        border: isSimAssessment ? "2px solid #c084fc" : "none",
        borderRadius: 8,
        fontSize: 11,
        padding: "8px 12px",
        maxWidth: 200,
      },
    };
  });
}

export default function GraphCanvas({
  nodes: graphNodes,
  edges: graphEdges,
  height = 480,
  simulatedHighlight = false,
}: {
  nodes: GraphCanvasNode[];
  edges: GraphCanvasEdge[];
  height?: number;
  simulatedHighlight?: boolean;
}) {
  const initialNodes = useMemo(
    () => layoutNodes(graphNodes, simulatedHighlight),
    [graphNodes, simulatedHighlight],
  );
  const initialEdges: Edge[] = useMemo(
    () =>
      graphEdges.map((e, i) => ({
        id: e.id ?? `e${i}`,
        source: e.source,
        target: e.target,
        label: e.label,
        style: { stroke: "#475569" },
        labelStyle: { fill: "#94a3b8", fontSize: 9 },
      })),
    [graphEdges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  if (graphNodes.length === 0) {
    return (
      <p style={{ color: "#475569", textAlign: "center", padding: 40 }}>
        Graf verisi yok.
      </p>
    );
  }

  return (
    <div
      data-testid="graph-canvas"
      style={{ height, background: "#0f1117", borderRadius: 10, border: "1px solid #334155" }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background color="#1e293b" gap={16} />
        <Controls />
        <MiniMap nodeColor="#334155" maskColor="#0f111744" />
      </ReactFlow>
    </div>
  );
}
