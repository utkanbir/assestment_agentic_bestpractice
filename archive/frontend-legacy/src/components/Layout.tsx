import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, ClipboardList, Search, CheckSquare } from "lucide-react";

const NAV = [
  { to: "/", label: "Assessments", icon: LayoutDashboard },
  { to: "/findings", label: "Findings", icon: Search },
  { to: "/approvals", label: "Onay Kuyruğu", icon: CheckSquare },
  { to: "/reports", label: "Reports", icon: ClipboardList },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-brand-600 text-lg tracking-tight">AAKP</span>
        <nav className="flex gap-4">
          {NAV.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
                (to === "/" ? pathname === "/" : pathname.startsWith(to))
                  ? "bg-brand-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full">{children}</main>
    </div>
  );
}
