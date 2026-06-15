import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api } from "../api/client";

export function ReportViewer() {
  const { taskId } = useParams<{ taskId?: string }>();

  const { data: findings = [] } = useQuery({
    queryKey: ["findings", taskId],
    queryFn: () => api.findings.list(taskId),
  });

  // Build a simple report from approved findings if no stored report
  const approved = findings.filter((f) => f.approval_status === "approved");

  const markdown = `# Assessment Report

## Summary

${approved.length} approved findings across ${new Set(approved.map((f) => f.severity)).size} severity levels.

## Findings

${
  approved.length === 0
    ? "_No approved findings yet._"
    : approved
        .map(
          (f) =>
            `### ${f.severity.toUpperCase()}: ${f.description}\n\n- Confidence: ${Math.round(f.confidence * 100)}%\n- Status: ${f.approval_status}`,
        )
        .join("\n\n")
}
`;

  const download = () => {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aakp-report-${taskId ?? "all"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <Link to="/" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft size={14} /> Back
        </Link>
        <button
          onClick={download}
          className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg px-3 py-1.5"
        >
          <Download size={14} /> Export .md
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl px-8 py-6 prose prose-sm max-w-none">
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
