import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";

export default function ChatPanel() {
  const {
    diagram,
    isStreaming,
    streamingText,
    setStreaming,
    appendStreamingText,
    flushStreamingText,
    updateMermaidCode,
    setDiagram,
    selectedNode,
    setSelectedNode,
  } = useAppStore();

  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [diagram?.messages, streamingText]);

  async function send() {
    if (!diagram || isStreaming || !input.trim()) return;

    const baseMessage = input.trim();
    const message = selectedNode
      ? selectedNode.type === "message"
        ? `[対象処理: ${selectedNode.nodeLabel}]\n${baseMessage}`
        : selectedNode.type === "block"
        ? `[対象ブロック: ${selectedNode.nodeLabel}]\n${baseMessage}`
        : `[対象参加者: ${selectedNode.nodeLabel}]\n${baseMessage}`
      : baseMessage;

    setInput("");
    setSelectedNode(null);
    setStreaming(true);
    flushStreamingText();

    try {
      for await (const event of api.chatStream(diagram.id, message)) {
        if (event.type === "token") {
          appendStreamingText(event.content);
        } else if (event.type === "mermaid") {
          updateMermaidCode(event.code);
        } else if (event.type === "done") {
          const updated = await api.getDiagram(diagram.id);
          setDiagram(updated);
          flushStreamingText();
        } else if (event.type === "error") {
          console.error("Chat error:", event.message);
          flushStreamingText();
        }
      }
    } finally {
      setStreaming(false);
    }
  }

  if (!diagram) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        ダイアグラムを選択してください
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* メッセージ一覧 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {diagram.messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}

        {isStreaming && streamingText && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap bg-white border border-gray-200 text-gray-800">
              {streamingText}
              <span className="inline-block w-1.5 h-3 bg-gray-400 ml-0.5 animate-pulse" />
            </div>
          </div>
        )}

        {isStreaming && !streamingText && (
          <div className="flex justify-start">
            <div className="px-3 py-2 text-sm text-gray-400">考え中...</div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* 入力エリア */}
      <div className="p-3 border-t border-gray-200 flex flex-col gap-2">
        {/* 対象ノードチップ */}
        {selectedNode && (
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">
              {selectedNode.type === "message" ? "処理:" : selectedNode.type === "block" ? "制御:" : "対象:"}
            </span>
            <span className="inline-flex items-center gap-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full px-2 py-0.5">
              {selectedNode.type === "message" || selectedNode.type === "block"
                ? `「${selectedNode.nodeLabel}」`
                : `[${selectedNode.nodeLabel}]`}
              <button
                className="ml-0.5 leading-none hover:text-indigo-900"
                onClick={() => setSelectedNode(null)}
                aria-label="選択解除"
              >
                ×
              </button>
            </span>
          </div>
        )}

        <textarea
          ref={textareaRef}
          className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-400 min-h-[100px] max-h-[240px] overflow-y-auto"
          placeholder={
            selectedNode
              ? selectedNode.type === "participant"
                ? `[${selectedNode.nodeLabel}] への指示を入力...\n（Cmd+Enter で送信）`
                : `「${selectedNode.nodeLabel}」への指示を入力...\n（Cmd+Enter で送信）`
              : "参加者・処理・制御ブロックをクリックして対象を選択、または直接指示を入力\n（Cmd+Enter で送信）"
          }
          value={input}
          onChange={(e) => { setInput(e.target.value); autoResize(); }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              send();
            }
          }}
          disabled={isStreaming}
        />
        <button
          className="self-end bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          onClick={send}
          disabled={isStreaming || !input.trim()}
        >
          送信
        </button>
      </div>
    </div>
  );
}
