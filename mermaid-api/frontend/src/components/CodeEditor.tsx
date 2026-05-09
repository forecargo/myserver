import { lazy, Suspense } from "react";
import type { OnChange } from "@monaco-editor/react";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function CodeEditor({ value, onChange }: Props) {
  const handleChange: OnChange = (v) => {
    if (v !== undefined) onChange(v);
  };

  return (
    <Suspense fallback={<div className="p-2 text-gray-400 text-sm">Loading editor...</div>}>
      <MonacoEditor
        height="100%"
        defaultLanguage="markdown"
        theme="vs-dark"
        value={value}
        onChange={handleChange}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          wordWrap: "on",
          lineNumbers: "on",
          scrollBeyondLastLine: false,
        }}
      />
    </Suspense>
  );
}
