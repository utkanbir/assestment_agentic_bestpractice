import { useParams, useSearchParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Printer, FileText, Calendar, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api } from "../api/client";

export function ReportViewer() {
  const { taskId } = useParams<{ taskId?: string }>();
  const [searchParams] = useSearchParams();

  // assessment_id: from query param, or from route /assessments/:id
  // (taskId here is reused from legacy route /tasks/:taskId/report)
  const assessmentId = searchParams.get("assessment_id") ?? taskId ?? undefined;

  const { data: assessment } = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => api.assessments.get(assessmentId!),
    enabled: !!assessmentId,
  });

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports", assessmentId],
    queryFn: () => api.reports.list(assessmentId),
    enabled: true,
  });

  // Use the most recent report (last in list)
  const report = reports.length > 0 ? reports[reports.length - 1] : null;

  const printPage = () => window.print();

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });

  return (
    <div>
      {/* Top bar — hidden when printing */}
      <div className="flex items-center justify-between mb-6 print:hidden">
        <Link
          to={assessmentId ? `/assessments/${assessmentId}` : "/"}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft size={14} /> Geri
        </Link>
        {report && (
          <button
            onClick={printPage}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg px-3 py-1.5 transition-colors"
          >
            <Printer size={14} /> PDF İndir
          </button>
        )}
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Yükleniyor...</p>
      ) : !report ? (
        /* No report yet */
        <div className="text-center py-20">
          <FileText size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500 font-medium">Henüz rapor üretilmedi.</p>
          <p className="text-sm text-gray-400 mt-1">
            Önce Executive Summary oluşturun.
          </p>
          {assessmentId && (
            <Link
              to={`/assessments/${assessmentId}`}
              className="inline-flex items-center gap-1.5 mt-4 text-sm text-brand-600 hover:text-brand-800 font-medium"
            >
              <ArrowLeft size={14} /> Assessment'a Dön
            </Link>
          )}
        </div>
      ) : (
        /* Report found */
        <div className="space-y-4">
          {/* Assessment info card */}
          {assessment && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl px-6 py-4 print:border-0 print:px-0">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <User size={13} />
                <span className="font-medium text-gray-700">{assessment.client_name}</span>
                <span>—</span>
                <span>{assessment.project_name}</span>
              </div>
            </div>
          )}

          {/* Report card */}
          <div className="bg-white border border-gray-200 rounded-xl px-8 py-6 print:border-0 print:px-0">
            {/* Report header */}
            <div className="border-b border-gray-100 pb-5 mb-6">
              <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-2">
                <Calendar size={11} />
                <span>Oluşturuldu: {formatDate(report.created_at)}</span>
                {report.updated_at !== report.created_at && (
                  <>
                    <span>·</span>
                    <span>Güncellendi: {formatDate(report.updated_at)}</span>
                  </>
                )}
              </div>
            </div>

            {/* Executive Summary */}
            {report.executive_summary && (
              <div className="mb-6">
                <h2 className="text-base font-semibold text-gray-800 mb-3">
                  Executive Summary
                </h2>
                <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-sm text-gray-700 leading-relaxed">
                  {report.executive_summary}
                </div>
              </div>
            )}

            {/* Full content (if content_json has markdown/text) */}
            {report.content_json && (
              <div className="prose prose-sm max-w-none">
                {(() => {
                  try {
                    const parsed = JSON.parse(report.content_json);
                    // If it's a string, render as markdown
                    if (typeof parsed === "string") {
                      return <ReactMarkdown>{parsed}</ReactMarkdown>;
                    }
                    // If it's an object, render key sections
                    return (
                      <pre className="text-xs bg-gray-50 rounded-lg p-4 overflow-auto">
                        {JSON.stringify(parsed, null, 2)}
                      </pre>
                    );
                  } catch {
                    // Not JSON — treat as plain text/markdown
                    return <ReactMarkdown>{report.content_json}</ReactMarkdown>;
                  }
                })()}
              </div>
            )}

            {/* Report metadata footer */}
            <div className="mt-8 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400 print:hidden">
              <span>Rapor ID: {report.id}</span>
              <span>Assessment ID: {report.assessment_id}</span>
            </div>
          </div>

          {/* Multiple reports indicator */}
          {reports.length > 1 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 print:hidden">
              <p className="text-xs text-amber-700">
                Bu assessment için {reports.length} rapor mevcut. En güncel rapor gösteriliyor.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
