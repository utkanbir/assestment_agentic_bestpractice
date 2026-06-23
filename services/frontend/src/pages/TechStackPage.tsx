import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArchitectureLayer, getArchitectureLayers } from "../api";
import { useAssessmentNavLink } from "../context/AssessmentContext";
import AssessmentPageHeader from "../components/AssessmentPageHeader";

const SYSTEM_PATH_PREFIXES = ["/health", "/api/"];

function resolveLink(url: string | null | undefined, navLink: (path: string) => string): string {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  if (SYSTEM_PATH_PREFIXES.some((p) => url.startsWith(p))) return url;
  if (url.startsWith("/")) return navLink(url);
  return url;
}

export default function TechStackPage() {
  const withAssessment = useAssessmentNavLink();
  const [layers, setLayers] = useState<ArchitectureLayer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getArchitectureLayers()
      .then((res) => setLayers(res.layers))
      .catch(() => setLayers([]))
      .finally(() => setLoading(false));
  }, []);

  const rows = useMemo(
    () =>
      layers.flatMap((layer) =>
        layer.technologies.map((tech) => ({
          layerId: layer.id,
          layerName: layer.name,
          tech,
        })),
      ),
    [layers],
  );

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }} data-testid="tech-stack-page">
      <AssessmentPageHeader
        title="Teknoloji Stack"
        subtitle="4 katman mimarisindeki teknolojiler — durum ve konsol linkleri"
        actions={
          <Link to={withAssessment("/mimari")} style={{ color: "#60a5fa", fontSize: 13 }}>
            Mimari görünümü →
          </Link>
        }
      />

      {loading ? (
        <p style={{ color: "#64748b" }}>Yükleniyor…</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 10,
              overflow: "hidden",
              fontSize: 13,
            }}
          >
            <thead>
              <tr style={{ background: "#0f1117", color: "#94a3b8", textAlign: "left" }}>
                <th style={{ padding: "10px 12px" }}>Katman</th>
                <th style={{ padding: "10px 12px" }}>Teknoloji</th>
                <th style={{ padding: "10px 12px" }}>Durum</th>
                <th style={{ padding: "10px 12px" }}>Link</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ layerId, layerName, tech }) => {
                const href = resolveLink(tech.console_url, withAssessment);
                const isInternal = tech.link_mode === "internal" || (!href && tech.notes);
                const status = tech.active_in_api
                  ? "Aktif"
                  : tech.configured
                    ? "Yapılandırıldı"
                    : "Planlı";
                return (
                  <tr key={`${layerId}-${tech.id}`} style={{ borderTop: "1px solid #334155" }}>
                    <td style={{ padding: "10px 12px", color: "#e2e8f0" }}>{layerName}</td>
                    <td style={{ padding: "10px 12px" }}>
                      <div style={{ fontWeight: 600, color: "#e2e8f0" }}>{tech.name}</div>
                      <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{tech.role}</div>
                      {tech.notes && (
                        <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>{tech.notes}</div>
                      )}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: 4,
                          background: tech.active_in_api ? "#16a34a22" : "#334155",
                          color: tech.active_in_api ? "#4ade80" : "#94a3b8",
                        }}
                      >
                        {status}
                      </span>
                      {isInternal && (
                        <span
                          style={{
                            marginLeft: 6,
                            fontSize: 10,
                            fontWeight: 700,
                            padding: "2px 6px",
                            borderRadius: 4,
                            background: "#581c8722",
                            color: "#c084fc",
                          }}
                        >
                          Internal
                        </span>
                      )}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {href ? (
                        <a
                          href={href}
                          target={href.startsWith("http") ? "_blank" : "_self"}
                          rel="noreferrer"
                          style={{ color: "#60a5fa", textDecoration: "none" }}
                        >
                          Aç →
                        </a>
                      ) : (
                        <span style={{ color: "#475569" }}>—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
