import { useEffect, useMemo, useState } from "react";
import { ExpertiseCatalog, getExpertiseCatalog } from "../api";

interface Props {
  value: string[];
  onChange: (tags: string[]) => void;
}

export default function ExpertiseMultiSelect({ value, onChange }: Props) {
  const [catalog, setCatalog] = useState<ExpertiseCatalog | null>(null);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getExpertiseCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  const filtered = useMemo(() => {
    if (!catalog) return [];
    const q = search.trim().toLowerCase();
    return catalog.groups
      .map((g) => ({
        ...g,
        tags: g.tags.filter((t) => !q || t.toLowerCase().includes(q) || g.name.toLowerCase().includes(q)),
      }))
      .filter((g) => g.tags.length > 0);
  }, [catalog, search]);

  const toggle = (tag: string) => {
    if (value.includes(tag)) onChange(value.filter((t) => t !== tag));
    else onChange([...value, tag]);
  };

  return (
    <div data-testid="expertise-multi-select" style={{ gridColumn: "1 / -1" }}>
      <p style={{ fontSize: 12, color: "#94a3b8", margin: "0 0 6px" }}>Uzmanlık alanları</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
        {value.map((tag) => (
          <span
            key={tag}
            data-testid={`expertise-chip-${tag.replace(/\s+/g, "-").toLowerCase()}`}
            style={{
              background: "#1e3a5f",
              color: "#93c5fd",
              border: "1px solid #3b82f644",
              borderRadius: 12,
              padding: "2px 10px",
              fontSize: 11,
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            {tag}
            <button
              type="button"
              onClick={() => toggle(tag)}
              style={{ background: "none", border: "none", color: "#93c5fd", cursor: "pointer", padding: 0, fontSize: 12 }}
            >
              ×
            </button>
          </span>
        ))}
        {value.length === 0 && (
          <span style={{ fontSize: 11, color: "#64748b" }}>Henüz uzmanlık seçilmedi</span>
        )}
      </div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{
          background: "#0f1117",
          border: "1px solid #334155",
          borderRadius: 6,
          padding: "6px 10px",
          color: "#e2e8f0",
          fontSize: 12,
          cursor: "pointer",
          marginBottom: open ? 8 : 0,
        }}
      >
        {open ? "Listeyi gizle" : "Uzmanlık seç…"}
      </button>
      {open && (
        <div
          style={{
            background: "#0f1117",
            border: "1px solid #334155",
            borderRadius: 8,
            padding: 10,
            maxHeight: 220,
            overflowY: "auto",
          }}
        >
          <input
            placeholder="Ara…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "6px 8px",
              color: "#e2e8f0",
              fontSize: 12,
              marginBottom: 8,
            }}
          />
          {filtered.map((g) => (
            <div key={g.id} style={{ marginBottom: 10 }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: "#64748b", margin: "0 0 4px", textTransform: "uppercase" }}>
                {g.name}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {g.tags.map((tag) => (
                  <label
                    key={tag}
                    style={{
                      fontSize: 11,
                      color: "#cbd5e1",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={value.includes(tag)}
                      onChange={() => toggle(tag)}
                    />
                    {tag}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
