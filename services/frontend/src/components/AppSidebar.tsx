import { NavLink } from "react-router-dom";
import { NAV_ICONS, type NavIconName } from "./navIcons";

export interface NavItem {
  to: string;
  label: string;
  icon: NavIconName;
  group?: string;
  badge?: boolean;
  end?: boolean;
  indent?: boolean;
}

interface AppSidebarProps {
  items: NavItem[];
  pendingBadge: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const linkStyle = (active: boolean, collapsed: boolean, indent?: boolean): React.CSSProperties => ({
  display: "flex",
  alignItems: "center",
  gap: collapsed ? 0 : 10,
  justifyContent: collapsed ? "center" : "flex-start",
  padding: collapsed ? "10px 8px" : indent ? "8px 12px 8px 22px" : "8px 12px",
  borderRadius: 8,
  textDecoration: "none",
  color: active ? "#fff" : "#94a3b8",
  background: active ? "#2563eb" : "transparent",
  fontWeight: active ? 600 : 400,
  fontSize: 13,
  transition: "all 0.15s",
  width: "100%",
  boxSizing: "border-box",
});

export default function AppSidebar({ items, pendingBadge, collapsed, onToggleCollapse }: AppSidebarProps) {
  const groups = ["Genel", "Knowledge", "Analiz", "Operasyon"];
  const grouped = groups.map((g) => ({
    name: g,
    items: items.filter((i) => (i.group ?? "Genel") === g),
  }));

  return (
    <aside
      data-testid="app-sidebar"
      style={{
        width: collapsed ? 56 : 220,
        minWidth: collapsed ? 56 : 220,
        height: "100vh",
        position: "sticky",
        top: 0,
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid #1e293b",
        background: "#0f1117",
        transition: "width 0.2s",
        overflow: "hidden",
      }}
    >
      <div style={{ padding: collapsed ? "14px 8px" : "14px 16px", borderBottom: "1px solid #1e293b" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "space-between" }}>
          {!collapsed && (
            <span style={{ fontWeight: 800, fontSize: 17, color: "#60a5fa" }}>AAKP</span>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Toggle sidebar"
            style={{
              background: "transparent",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "4px 8px",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>
      </div>

      <nav style={{ flex: 1, overflowY: "auto", padding: "8px 6px" }}>
        {grouped.map(({ name, items: groupItems }) =>
          groupItems.length === 0 ? null : (
            <div key={name} style={{ marginBottom: 12 }}>
              {!collapsed && (
                <div style={{ fontSize: 10, color: "#475569", padding: "4px 12px 6px", textTransform: "uppercase", letterSpacing: 0.5 }}>
                  {name}
                </div>
              )}
              {groupItems.map((item) => {
                const Icon = NAV_ICONS[item.icon];
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    title={collapsed ? item.label : undefined}
                    style={({ isActive }) => linkStyle(isActive, collapsed, item.indent)}
                  >
                    <Icon style={{ flexShrink: 0 }} />
                    {!collapsed && (
                      <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {item.label}
                      </span>
                    )}
                    {!collapsed && item.badge && pendingBadge > 0 && (
                      <span style={{
                        background: "#ef4444",
                        color: "#fff",
                        borderRadius: 999,
                        padding: "1px 6px",
                        fontSize: 10,
                        fontWeight: 700,
                      }}>
                        {pendingBadge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          ),
        )}
      </nav>

      <div style={{ padding: collapsed ? "8px 4px" : "8px 12px", borderTop: "1px solid #1e293b", fontSize: 10, color: "#475569", textAlign: collapsed ? "center" : "left" }}>
        {collapsed ? "©" : "Migros © 2026"}
      </div>
    </aside>
  );
}
