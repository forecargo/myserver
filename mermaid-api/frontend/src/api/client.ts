export interface Project {
  id: number;
  name: string;
  created_at: string;
}

export interface DiagramSummary {
  id: number;
  project_id: number;
  name: string;
  created_at: string;
}

export interface MessageItem {
  id: number;
  diagram_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface DiagramDetail extends DiagramSummary {
  mermaid_code: string;
  messages: MessageItem[];
}

export type SSEEvent =
  | { type: "token"; content: string }
  | { type: "mermaid"; code: string }
  | { type: "done" }
  | { type: "error"; message: string };

// 本番: BASE_URL = "/mermaid/" → "/mermaid/api" (Caddyが/mermaidをstripしてFastAPIへ)
// 開発: BASE_URL = "/"       → "/api"         (Vite proxyが/apiをFastAPIへ転送)
const BASE = `${import.meta.env.BASE_URL}api`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),

  createProject: (name: string) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  deleteProject: (id: number) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  listDiagrams: (projectId: number) =>
    request<DiagramSummary[]>(`/projects/${projectId}/diagrams`),

  createDiagram: (projectId: number, name: string) =>
    request<DiagramSummary>(`/projects/${projectId}/diagrams`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  getDiagram: (id: number) => request<DiagramDetail>(`/diagrams/${id}`),

  patchDiagram: (id: number, patch: { name?: string; mermaid_code?: string }) =>
    request<DiagramDetail>(`/diagrams/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  deleteDiagram: (id: number) =>
    request<void>(`/diagrams/${id}`, { method: "DELETE" }),

  async *chatStream(
    diagramId: number,
    message: string,
  ): AsyncGenerator<SSEEvent> {
    const res = await fetch(`${BASE}/diagrams/${diagramId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      const lines = buf.split("\n");
      buf = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const payload = JSON.parse(line.slice(6)) as SSEEvent;
            yield payload;
          } catch {
            // malformed line — skip
          }
        }
      }
    }
  },
};
