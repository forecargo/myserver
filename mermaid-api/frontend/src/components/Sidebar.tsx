import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/appStore";

const COLLAPSED_KEY = "mermaid-sidebar-collapsed";

export default function Sidebar() {
  const {
    projects, selectedProjectId, diagrams, selectedDiagramId,
    setProjects, selectProject, setDiagrams, selectDiagram, setDiagram,
  } = useAppStore();

  const [newProjectName, setNewProjectName] = useState("");
  const [newDiagramName, setNewDiagramName] = useState("");
  const [projectInputError, setProjectInputError] = useState(false);
  const [diagramInputError, setDiagramInputError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(COLLAPSED_KEY) === "1",
  );

  const projectInputRef = useRef<HTMLInputElement>(null);
  const diagramInputRef = useRef<HTMLInputElement>(null);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(COLLAPSED_KEY, next ? "1" : "0");
      return next;
    });
  }

  useEffect(() => {
    api.listProjects().then(setProjects).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (selectedProjectId == null) return;
    api.listDiagrams(selectedProjectId).then(setDiagrams).catch((e) => setError(String(e)));
  }, [selectedProjectId]);

  async function handleSelectDiagram(id: number) {
    selectDiagram(id);
    try {
      const detail = await api.getDiagram(id);
      setDiagram(detail);
    } catch (e) {
      setError(String(e));
    }
  }

  async function addProject() {
    const name = newProjectName.trim();
    if (!name) {
      setProjectInputError(true);
      projectInputRef.current?.focus();
      setTimeout(() => setProjectInputError(false), 1500);
      return;
    }
    try {
      const p = await api.createProject(name);
      setProjects([p, ...projects]);
      setNewProjectName("");
    } catch (e) {
      setError(String(e));
    }
  }

  async function deleteProject(id: number) {
    try {
      await api.deleteProject(id);
      setProjects(projects.filter((p) => p.id !== id));
      if (selectedProjectId === id) selectProject(null);
    } catch (e) {
      setError(String(e));
    }
  }

  async function addDiagram() {
    if (selectedProjectId == null) return;
    const name = newDiagramName.trim();
    if (!name) {
      setDiagramInputError(true);
      diagramInputRef.current?.focus();
      setTimeout(() => setDiagramInputError(false), 1500);
      return;
    }
    try {
      const d = await api.createDiagram(selectedProjectId, name);
      setDiagrams([d, ...diagrams]);
      setNewDiagramName("");
    } catch (e) {
      setError(String(e));
    }
  }

  async function deleteDiagram(id: number) {
    try {
      await api.deleteDiagram(id);
      setDiagrams(diagrams.filter((d) => d.id !== id));
      if (selectedDiagramId === id) {
        selectDiagram(null);
        setDiagram(null);
      }
    } catch (e) {
      setError(String(e));
    }
  }

  if (collapsed) {
    return (
      <aside className="w-10 bg-gray-900 text-gray-100 flex flex-col h-full shrink-0">
        <button
          className="h-10 flex items-center justify-center hover:bg-gray-800 border-b border-gray-700"
          onClick={toggleCollapsed}
          title="サイドバーを開く"
          aria-label="サイドバーを開く"
        >
          ▶
        </button>
      </aside>
    );
  }

  return (
    <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col h-full text-sm shrink-0">
      <div className="px-3 h-10 border-b border-gray-700 flex items-center justify-between">
        <span className="font-bold text-base truncate">Mermaid Editor</span>
        <button
          className="text-gray-400 hover:text-gray-100 shrink-0 ml-2"
          onClick={toggleCollapsed}
          title="サイドバーを閉じる"
          aria-label="サイドバーを閉じる"
        >
          ◀
        </button>
      </div>

      {error && (
        <div
          className="mx-2 mt-2 px-2 py-1 bg-red-800 text-red-100 rounded text-xs cursor-pointer"
          onClick={() => setError(null)}
        >
          {error}
        </div>
      )}

      {/* プロジェクト一覧 */}
      <div className="p-2 border-b border-gray-700">
        <div className="text-xs text-gray-400 mb-1 uppercase tracking-wide">Projects</div>
        <ul className="space-y-0.5 max-h-40 overflow-y-auto">
          {projects.map((p) => (
            <li
              key={p.id}
              className={`flex items-center justify-between rounded px-2 py-1 cursor-pointer ${
                selectedProjectId === p.id ? "bg-indigo-600" : "hover:bg-gray-700"
              }`}
              onClick={() => selectProject(p.id)}
            >
              <span className="truncate">{p.name}</span>
              <button
                className="ml-1 text-gray-400 hover:text-red-400 shrink-0"
                onClick={(e) => { e.stopPropagation(); deleteProject(p.id); }}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        <div className="flex mt-1 gap-1">
          <input
            ref={projectInputRef}
            className={`flex-1 bg-gray-800 rounded px-2 py-0.5 text-xs placeholder-gray-500 outline-none transition-colors ${
              projectInputError ? "ring-1 ring-red-500 bg-red-900/30" : "focus:ring-1 focus:ring-indigo-500"
            }`}
            placeholder={projectInputError ? "名前を入力してください" : "プロジェクト名"}
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
          />
          <button
            className="bg-indigo-600 hover:bg-indigo-500 rounded px-2 py-0.5 text-xs font-bold"
            onClick={addProject}
            title="プロジェクトを追加"
          >
            +
          </button>
        </div>
      </div>

      {/* ダイアグラム一覧 */}
      {selectedProjectId != null && (
        <div className="p-2 flex-1 overflow-hidden flex flex-col">
          <div className="text-xs text-gray-400 mb-1 uppercase tracking-wide">Diagrams</div>
          <ul className="space-y-0.5 flex-1 overflow-y-auto">
            {diagrams.map((d) => (
              <li
                key={d.id}
                className={`flex items-center justify-between rounded px-2 py-1 cursor-pointer ${
                  selectedDiagramId === d.id ? "bg-indigo-600" : "hover:bg-gray-700"
                }`}
                onClick={() => handleSelectDiagram(d.id)}
              >
                <span className="truncate">{d.name}</span>
                <button
                  className="ml-1 text-gray-400 hover:text-red-400 shrink-0"
                  onClick={(e) => { e.stopPropagation(); deleteDiagram(d.id); }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
          <div className="flex mt-1 gap-1">
            <input
              ref={diagramInputRef}
              className={`flex-1 bg-gray-800 rounded px-2 py-0.5 text-xs placeholder-gray-500 outline-none transition-colors ${
                diagramInputError ? "ring-1 ring-red-500 bg-red-900/30" : "focus:ring-1 focus:ring-indigo-500"
              }`}
              placeholder={diagramInputError ? "名前を入力してください" : "ダイアグラム名"}
              value={newDiagramName}
              onChange={(e) => setNewDiagramName(e.target.value)}
            />
            <button
              className="bg-indigo-600 hover:bg-indigo-500 rounded px-2 py-0.5 text-xs font-bold"
              onClick={addDiagram}
              title="ダイアグラムを追加"
            >
              +
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
