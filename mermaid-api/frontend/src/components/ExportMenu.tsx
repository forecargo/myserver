interface Props {
  mermaidCode: string;
  diagramName: string;
}

export default function ExportMenu({ mermaidCode, diagramName }: Props) {
  function exportMarkdown() {
    const content = `# ${diagramName}\n\n\`\`\`mermaid\n${mermaidCode}\n\`\`\`\n`;
    const blob = new Blob([content], { type: "text/markdown" });
    download(blob, `${diagramName}.md`);
  }

  function exportSvg() {
    const svgEl = document.querySelector(".mermaid svg") ?? document.querySelector("svg");
    if (!svgEl) return;
    const blob = new Blob([svgEl.outerHTML], { type: "image/svg+xml" });
    download(blob, `${diagramName}.svg`);
  }

  function exportPng() {
    const svgEl = document.querySelector(".mermaid svg") ?? document.querySelector("svg");
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const img = new Image();
    const blob = new Blob([svgData], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.width || 800;
      canvas.height = img.height || 600;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((b) => { if (b) download(b, `${diagramName}.png`); });
    };
    img.src = url;
  }

  function download(blob: Blob, filename: string) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="flex gap-1">
      <button
        className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded"
        onClick={exportMarkdown}
        title="Markdown としてエクスポート"
      >
        .md
      </button>
      <button
        className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded"
        onClick={exportSvg}
        title="SVG としてエクスポート"
      >
        SVG
      </button>
      <button
        className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded"
        onClick={exportPng}
        title="PNG としてエクスポート"
      >
        PNG
      </button>
    </div>
  );
}
