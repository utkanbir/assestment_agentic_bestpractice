import { useState, useRef, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Send } from "lucide-react";
import { api } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";
import type { WSMessage } from "../api/types";

interface ChatMessage {
  role: "agent" | "user";
  text: string;
}

export function InterviewRoom() {
  const { taskId } = useParams<{ taskId: string }>();
  const qc = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [activeInterviewId, setActiveInterviewId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: interviews = [] } = useQuery({
    queryKey: ["interviews", taskId],
    queryFn: () => api.interviews.list(taskId!),
    enabled: !!taskId,
  });

  // Use the most recent in-progress interview
  useEffect(() => {
    const active = interviews.find((i) => i.status === "in_progress") ?? interviews[0];
    if (active) setActiveInterviewId(active.id);
  }, [interviews]);

  const createInterview = useMutation({
    mutationFn: () => api.interviews.create({ task_id: taskId! }),
    onSuccess: (data) => {
      setActiveInterviewId(data.id);
      qc.invalidateQueries({ queryKey: ["interviews", taskId] });
    },
  });

  const handleWSMessage = (msg: WSMessage) => {
    if (msg.event === "question.suggested") {
      const text = (msg.payload.question as string) ?? JSON.stringify(msg.payload);
      setMessages((prev) => [...prev, { role: "agent", text }]);
    }
    if (msg.event === "finding.detected") {
      const desc = (msg.payload.description as string) ?? "Finding detected";
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: `Finding: ${desc}` },
      ]);
    }
  };

  const { send } = useWebSocket(activeInterviewId, handleWSMessage);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = () => {
    const text = input.trim();
    if (!text || !activeInterviewId) return;
    setMessages((prev) => [...prev, { role: "user", text }]);
    send({
      event: "answer.submitted",
      payload: { answer: text, interview_id: activeInterviewId },
    });
    setInput("");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="flex items-center gap-3 mb-4">
        <Link to={`/`} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft size={16} />
        </Link>
        <h1 className="font-semibold text-gray-900">Interview Room</h1>
        {activeInterviewId && (
          <span className="text-xs text-gray-400 font-mono">{activeInterviewId.slice(0, 8)}</span>
        )}
      </div>

      {!activeInterviewId ? (
        <div className="flex-1 flex items-center justify-center">
          <button
            onClick={() => createInterview.mutate()}
            disabled={createInterview.isPending}
            className="bg-brand-600 hover:bg-brand-700 text-white font-medium px-6 py-3 rounded-xl disabled:opacity-50"
          >
            {createInterview.isPending ? "Starting..." : "Start Interview"}
          </button>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
            {messages.length === 0 && (
              <p className="text-sm text-gray-400 text-center mt-8">
                Waiting for agent to start the interview...
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xl px-4 py-2.5 rounded-2xl text-sm ${
                    m.role === "user"
                      ? "bg-brand-600 text-white rounded-br-sm"
                      : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="flex gap-2">
            <input
              className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
              placeholder="Type your answer..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit()}
            />
            <button
              onClick={submit}
              disabled={!input.trim()}
              className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2.5 rounded-xl disabled:opacity-40"
            >
              <Send size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
