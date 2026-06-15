const COLOR: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  in_progress: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  archived: "bg-gray-200 text-gray-500",
  pending: "bg-yellow-100 text-yellow-800",
  skipped: "bg-gray-100 text-gray-400",
  scheduled: "bg-purple-100 text-purple-800",
  cancelled: "bg-red-100 text-red-700",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-700",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${COLOR[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status.replace("_", " ")}
    </span>
  );
}
