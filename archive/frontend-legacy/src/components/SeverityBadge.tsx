import type { FindingSeverity } from "../api/types";

const COLOR: Record<FindingSeverity, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-blue-100 text-blue-800",
  info: "bg-gray-100 text-gray-700",
};

export function SeverityBadge({ severity }: { severity: FindingSeverity }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold uppercase ${COLOR[severity]}`}>
      {severity}
    </span>
  );
}
