// S7-FA-007: OpenMetadata catalog UI embed veya link
import { useEffect, useState } from "react";
import { fetchJSON } from "../api";

interface CatalogEntity {
  name: string;
  fullyQualifiedName: string;
  description?: string;
  entityType: string;
  href?: string;
}

const OM_BASE = "/openmetadata"; // reverse-proxied via Kong/nginx

export default function CatalogLink() {
  const [entities, setEntities] = useState<CatalogEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [useEmbed, setUseEmbed] = useState(false);

  useEffect(() => {
    // Try to load AAKP-related entities from OpenMetadata search API
    fetch(`${OM_BASE}/api/v1/search/query?q=aakp&index=all&from=0&size=20`)
      .then((r) => r.json())
      .then((data) => {
        const hits = data?.hits?.hits ?? [];
        setEntities(hits.map((h: any) => ({
          name: h._source?.name ?? h._id,
          fullyQualifiedName: h._source?.fullyQualifiedName ?? "",
          description: h._source?.description,
          entityType: h._source?.entityType ?? "unknown",
          href: `${OM_BASE}/${h._source?.entityType?.toLowerCase()}/${encodeURIComponent(h._source?.fullyQualifiedName ?? "")}`,
        })));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = entities.filter(
    (e) =>
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      (e.description ?? "").toLowerCase().includes(search.toLowerCase())
  );

  const entityTypeIcon: Record<string, string> = {
    table: "🗄️", pipeline: "🔄", dashboard: "📊", topic: "📨",
    "assessment-finding": "🔍", unknown: "📄",
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Veri Kataloğu</h1>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>OpenMetadata — AAKP varlık kataloğu</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            onClick={() => setUseEmbed((v) => !v)}
            style={{
              background: useEmbed ? "#3b82f6" : "#1e293b",
              border: "1px solid #334155", borderRadius: 6,
              padding: "6px 12px", color: useEmbed ? "#fff" : "#94a3b8",
              cursor: "pointer", fontSize: 12,
            }}
          >
            {useEmbed ? "Liste Görünümü" : "Tam Ekran Embed"}
          </button>
          <a
            href={OM_BASE}
            target="_blank"
            rel="noreferrer"
            style={{
              background: "#1e293b", border: "1px solid #334155",
              borderRadius: 6, padding: "6px 12px",
              color: "#94a3b8", fontSize: 12, textDecoration: "none",
            }}
          >
            Kataloğu Aç ↗
          </a>
        </div>
      </div>

      {useEmbed ? (
        <iframe
          src={OM_BASE}
          style={{
            width: "100%", height: "calc(100vh - 160px)",
            border: "1px solid #334155", borderRadius: 8,
            background: "#fff",
          }}
          title="OpenMetadata Catalog"
        />
      ) : (
        <>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Varlık adı veya açıklama ara…"
            style={{
              width: "100%", background: "#1e293b", border: "1px solid #334155",
              borderRadius: 8, padding: "10px 14px", color: "#e2e8f0",
              fontSize: 14, outline: "none", marginBottom: 16, boxSizing: "border-box",
            }}
          />

          {loading ? (
            <p style={{ textAlign: "center", color: "#64748b", padding: 40 }}>
              OpenMetadata bağlantısı kuruluyor…
            </p>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>
              <p style={{ fontSize: 36, marginBottom: 12 }}>🗄️</p>
              <p>Katalog varlığı bulunamadı veya OpenMetadata erişilemiyor.</p>
              <a href={OM_BASE} target="_blank" rel="noreferrer"
                style={{ color: "#3b82f6", fontSize: 14 }}>
                OpenMetadata'yı doğrudan aç ↗
              </a>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
              {filtered.map((e) => (
                <a
                  key={e.fullyQualifiedName}
                  href={e.href}
                  target="_blank"
                  rel="noreferrer"
                  style={{ textDecoration: "none" }}
                >
                  <div style={{
                    background: "#1e293b", border: "1px solid #334155",
                    borderRadius: 8, padding: "14px 16px",
                    transition: "border-color 0.15s",
                  }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                      <span style={{ fontSize: 18 }}>{entityTypeIcon[e.entityType] ?? "📄"}</span>
                      <span style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0" }}>{e.name}</span>
                    </div>
                    <div style={{ fontSize: 10, color: "#475569", marginBottom: 6, textTransform: "uppercase" }}>
                      {e.entityType}
                    </div>
                    {e.description && (
                      <p style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.4, margin: 0 }}>
                        {e.description.slice(0, 100)}{e.description.length > 100 ? "…" : ""}
                      </p>
                    )}
                  </div>
                </a>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
