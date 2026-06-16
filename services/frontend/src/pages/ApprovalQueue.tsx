// S7-FA-003: Human approval UI — finding/risk/recommendation onay akışı
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchJSON } from "../api";

const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444", high: "#f97316", medium: "#eab308", low: "#22c55e", info: "#60a5fa",
};

interface PendingItem {
  id: string;
  type: "finding" | "risk" | "recommendation";
  description: string;
  severity?: string;
  level?: string;
  confidence?: number;
  title?: string;
}

interface FindingItem { id: string; description: string; severity: string; confidence?: number; }
interface RiskItem { id: string; title?: string; description: string; level: string; }
interface RecItem { id: string; description: string; priority?: number; effort?: string; }

interface ApprovalQueueData {
  pending_findings: (string | FindingItem)[];
  pending_risks: (string | RiskItem)[];
  pending_recommendations: (string | RecItem)[];
  total: number;
}

async function applyDecision(type: string, id: string, decision: "approved" | "rejected", note?: string) {
  return fetchJSON(`/approvals/${type}s/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ decision, reviewer_note: note ?? "" }),
  });
}

function ItemCard({
  item,
  onDecision,
}: {
  item: PendingItem;
  onDecision: (id: string, type: string, decision: "approved" | "rejected") => void;
}) {
  const [note, setNote] = useState("");
  const [deciding, setDeciding] = useState(false);
  const sev = item.severity ?? item.level ?? "info";
  const color = SEV_COLOR[sev] ?? "#60a5fa";

  const decide = async (d: "approved" | "rejected") => {
    setDeciding(true);
    try {
      await applyDecision(item.type, item.id, d, note);
      onDecision(item.id, item.type, d);
    } catch { /* ignore */ } finally { setDeciding(false); }
  };

  return (
    <div style={{
      background: "#1e293b",
      border: `1px solid ${color}44`,
      borderLeft: `3px solid ${color}`,
      borderRadius: 8,
      padding: "14px 16px",
      marginBottom: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 6 }}>
            <span style={{
              background: "#334155",
              borderRadius: 4,
              padding: "1px 8px",
              fontSize: 10,
              fontWeight: 700,
              color: "#94a3b8",
              textTransform: "uppercase",
            }}>
              {item.type}
            </span>
            <span style={{ background: color + "22", color, borderRadius: 3, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>
              {sev.toUpperCase()}
            </span>
            {item.confidence !== undefined && (
              <span style={{ fontSize: 10, color: "#64748b" }}>
                güven: {(item.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.5, margin: 0 }}>
            {item.title ?? item.description}
          </p>
          {item.title && item.description && (
            <p style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>{item.description}</p>
          )}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Gözlemci notu (opsiyonel)…"
          style={{
            flex: 1, background: "#0f1117", border: "1px solid #334155",
            borderRadius: 6, padding: "5px 10px", color: "#e2e8f0", fontSize: 12, outline: "none",
          }}
        />
        <button
          onClick={() => decide("approved")}
          disabled={deciding}
          style={{
            background: "#16a34a22", border: "1px solid #16a34a88",
            borderRadius: 6, padding: "5px 14px", color: "#4ade80",
            cursor: "pointer", fontSize: 12, fontWeight: 700,
          }}
        >
          Onayla
        </button>
        <button
          onClick={() => decide("rejected")}
          disabled={deciding}
          style={{
            background: "#dc262622", border: "1px solid #dc262688",
            borderRadius: 6, padding: "5px 14px", color: "#f87171",
            cursor: "pointer", fontSize: 12, fontWeight: 700,
          }}
        >
          Reddet
        </button>
      </div>
    </div>
  );
}

export default function ApprovalQueue() {
  const [searchParams] = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? "";
  const [items, setItems] = useState<PendingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "finding" | "risk" | "recommendation">("all");

  const load = async () => {
    setLoading(true);
    try {
      const url = assessmentId
        ? `/approvals/pending?assessment_id=${assessmentId}`
        : "/approvals/pending";
      const data = await fetchJSON<ApprovalQueueData>(url);

      const collected: PendingItem[] = [];

      // S8-BA-002: API now returns enriched objects; fall back to ID lookup for legacy
      const toItem = (raw: string | FindingItem | RiskItem | RecItem, type: PendingItem["type"]): Partial<PendingItem> => {
        if (typeof raw === "string") return { id: raw };
        return raw as any;
      };

      for (const raw of data.pending_findings) {
        const item = toItem(raw, "finding") as any;
        collected.push({ id: item.id, type: "finding", description: item.description ?? "—", severity: item.severity ?? "info", confidence: item.confidence });
      }
      for (const raw of data.pending_risks) {
        const item = toItem(raw, "risk") as any;
        collected.push({ id: item.id, type: "risk", title: item.title, description: item.description ?? "—", level: item.level ?? "medium" });
      }
      for (const raw of data.pending_recommendations) {
        const item = toItem(raw, "recommendation") as any;
        collected.push({ id: item.id, type: "recommendation", description: item.description ?? "—", severity: "info" });
      }

      setItems(collected);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [assessmentId]);

  const onDecision = (id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  const visible = filter === "all" ? items : items.filter((i) => i.type === filter);

  return (
    <div style={{ maxWidth: 860, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Onay Kuyruğu</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            {items.length} öğe bekliyor
            {assessmentId && ` — ${assessmentId.slice(0, 8)}…`}
          </p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {(["all", "finding", "risk", "recommendation"] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              background: filter === f ? "#3b82f6" : "#1e293b",
              border: "1px solid #334155",
              borderRadius: 6, padding: "5px 12px",
              color: filter === f ? "#fff" : "#94a3b8",
              cursor: "pointer", fontSize: 12, fontWeight: filter === f ? 700 : 400,
            }}>
              {f === "all" ? "Tümü" : f === "finding" ? "Bulgular" : f === "risk" ? "Riskler" : "Öneriler"}
              {" "}
              <span style={{ color: "#60a5fa", fontWeight: 700 }}>
                {f === "all" ? items.length : items.filter((i) => i.type === f).length}
              </span>
            </button>
          ))}
          <button onClick={load} style={{
            background: "transparent", border: "1px solid #334155",
            borderRadius: 6, padding: "5px 12px",
            color: "#94a3b8", cursor: "pointer", fontSize: 12,
          }}>
            Yenile
          </button>
        </div>
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>Yükleniyor…</p>
      ) : visible.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
          <p style={{ fontSize: 36, marginBottom: 12 }}>✅</p>
          <p>Bekleyen onay yok.</p>
        </div>
      ) : (
        visible.map((item) => (
          <ItemCard key={item.id} item={item} onDecision={onDecision} />
        ))
      )}
    </div>
  );
}
