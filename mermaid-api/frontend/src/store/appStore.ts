import { create } from "zustand";
import type { Project, DiagramSummary, DiagramDetail, MessageItem } from "../api/client";

export interface SelectedNode {
  nodeId: string;
  nodeLabel: string;
  type: "participant" | "message" | "block";
}

interface AppState {
  projects: Project[];
  selectedProjectId: number | null;
  diagrams: DiagramSummary[];
  selectedDiagramId: number | null;
  diagram: DiagramDetail | null;
  isStreaming: boolean;
  streamingText: string;
  selectedNode: SelectedNode | null;

  setProjects: (projects: Project[]) => void;
  selectProject: (id: number | null) => void;
  setDiagrams: (diagrams: DiagramSummary[]) => void;
  selectDiagram: (id: number | null) => void;
  setDiagram: (diagram: DiagramDetail | null) => void;
  updateMermaidCode: (code: string) => void;
  appendMessage: (msg: MessageItem) => void;
  setStreaming: (v: boolean) => void;
  appendStreamingText: (text: string) => void;
  flushStreamingText: () => void;
  setSelectedNode: (node: SelectedNode | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  projects: [],
  selectedProjectId: null,
  diagrams: [],
  selectedDiagramId: null,
  diagram: null,
  isStreaming: false,
  streamingText: "",
  selectedNode: null,

  setProjects: (projects) => set({ projects }),
  selectProject: (id) => set({ selectedProjectId: id, diagrams: [], selectedDiagramId: null, diagram: null, selectedNode: null }),
  setDiagrams: (diagrams) => set({ diagrams }),
  selectDiagram: (id) => set({ selectedDiagramId: id }),
  setDiagram: (diagram) => set({ diagram }),
  updateMermaidCode: (code) =>
    set((s) => s.diagram ? { diagram: { ...s.diagram, mermaid_code: code } } : {}),
  appendMessage: (msg) =>
    set((s) =>
      s.diagram
        ? { diagram: { ...s.diagram, messages: [...s.diagram.messages, msg] } }
        : {},
    ),
  setStreaming: (isStreaming) => set({ isStreaming }),
  appendStreamingText: (text) =>
    set((s) => ({ streamingText: s.streamingText + text })),
  flushStreamingText: () => set({ streamingText: "" }),
  setSelectedNode: (node) => set({ selectedNode: node }),
}));
