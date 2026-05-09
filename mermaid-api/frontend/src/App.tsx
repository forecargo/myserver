import { useCallback, useEffect, useState } from "react";
import { useAppStore } from "./store/appStore";
import { api } from "./api/client";
import Sidebar from "./components/Sidebar";
import PreviewPanel from "./components/PreviewPanel";
import ChatPanel from "./components/ChatPanel";
import CodeEditor from "./components/CodeEditor";
import ExportMenu from "./components/ExportMenu";

type EditorTab = "preview" | "code";

export default function App() {
  const { diagram, updateMermaidCode, selectedNode, setSelectedNode } = useAppStore();
  const [tab, setTab] = useState<EditorTab>("preview");
  const [saveTimer, setSaveTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handleCodeChange = useCallback(
    (code: string) => {
      updateMermaidCode(code);
      if (saveTimer) clearTimeout(saveTimer);
      const t = setTimeout(async () => {
        if (diagram) {
          await api.patchDiagram(diagram.id, { mermaid_code: code }).catch(console.error);
        }
      }, 1000);
      setSaveTimer(t);
    },
    [diagram, saveTimer, updateMermaidCode],
  );

  useEffect(() => {
    return () => { if (saveTimer) clearTimeout(saveTimer); };
  }, [saveTimer]);

  return (
    <div className="flex h-dvh w-screen overflow-hidden bg-gray-100">
      {/* サイドバー */}
      <Sidebar />

      {/* メインエリア */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* ヘッダー */}
        <header className="h-10 bg-gray-800 text-white flex items-center px-4 gap-4 text-sm shrink-0">
          <span className="font-medium truncate">{diagram?.name ?? "ダイアグラム未選択"}</span>
          <div className="flex gap-1 ml-auto">
            <button
              className={`px-3 py-1 rounded text-xs ${tab === "preview" ? "bg-indigo-600" : "hover:bg-gray-700"}`}
              onClick={() => setTab("preview")}
            >
              プレビュー
            </button>
            <button
              className={`px-3 py-1 rounded text-xs ${tab === "code" ? "bg-indigo-600" : "hover:bg-gray-700"}`}
              onClick={() => setTab("code")}
            >
              コード
            </button>
          </div>
          {diagram && (
            <ExportMenu mermaidCode={diagram.mermaid_code} diagramName={diagram.name} />
          )}
        </header>

        {/* エディタ + チャット */}
        <div className="flex flex-1 overflow-hidden">
          {/* 左ペイン: プレビュー or コードエディタ */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {diagram ? (
              tab === "preview" ? (
                <PreviewPanel
                  code={diagram.mermaid_code}
                  onNodeSelect={setSelectedNode}
                  selectedNode={selectedNode}
                />
              ) : (
                <CodeEditor value={diagram.mermaid_code} onChange={handleCodeChange} />
              )
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
                左のサイドバーでプロジェクトとダイアグラムを選択してください
              </div>
            )}
          </div>

          {/* 右ペイン: チャット */}
          <div className="w-1/3 min-w-72 border-l border-gray-300 flex flex-col overflow-hidden">
            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
