import { Component, StrictMode } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("App error:", error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen items-center justify-center bg-gray-900 text-white p-8">
          <div className="max-w-md">
            <h1 className="text-xl font-bold mb-2 text-red-400">エラーが発生しました</h1>
            <pre className="text-sm bg-gray-800 rounded p-4 overflow-auto">
              {this.state.error.message}
            </pre>
            <button
              className="mt-4 px-4 py-2 bg-indigo-600 rounded hover:bg-indigo-500"
              onClick={() => this.setState({ error: null })}
            >
              再試行
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const basename = import.meta.env.PROD ? "/mermaid" : "/";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter basename={basename}>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
);
