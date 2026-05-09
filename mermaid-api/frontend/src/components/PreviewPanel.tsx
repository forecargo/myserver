import { useEffect, useRef, useState } from "react";
import type mermaidType from "mermaid";
import type { SelectedNode } from "../store/appStore";

let idCounter = 0;
let mermaidInstance: typeof mermaidType | null = null;

async function getMermaid(): Promise<typeof mermaidType> {
  if (mermaidInstance) return mermaidInstance;
  const mod = await import("mermaid");
  const m = mod.default;
  m.initialize({ startOnLoad: false, theme: "default" });
  mermaidInstance = m;
  return m;
}

const BLOCK_CLASSES = ["labelText", "loopText", "labelBox", "loopLine"];

function buildBlockLabel(g: Element): string | null {
  const keyword = g.querySelector("text.labelText")?.textContent?.trim() || "";
  const condition = g.querySelector("text.loopText")?.textContent?.trim() || "";
  return keyword ? (condition ? `${keyword}: ${condition}` : keyword) : null;
}

function getSequenceBlock(target: Element): string | null {
  let el: Element | null = target;
  if (el.tagName.toLowerCase() === "tspan") el = el.parentElement;
  if (!el || !BLOCK_CLASSES.some((c) => el!.classList.contains(c))) return null;
  let ancestor: Element | null = el.parentElement;
  while (ancestor && ancestor.tagName.toLowerCase() !== "svg") {
    if (ancestor.tagName.toLowerCase() === "g" && ancestor.querySelector("text.labelText")) {
      return buildBlockLabel(ancestor);
    }
    ancestor = ancestor.parentElement;
  }
  return null;
}

function applyHighlight(container: HTMLElement, selected: SelectedNode | null) {
  container
    .querySelectorAll(".node-selected, .actor-selected, .message-selected, .block-selected")
    .forEach((el) => el.classList.remove("node-selected", "actor-selected", "message-selected", "block-selected"));

  if (!selected) return;
  const { nodeId, type } = selected;

  if (type === "message") {
    container.querySelectorAll("text.messageText").forEach((el) => {
      if (el.textContent?.trim() === nodeId) el.classList.add("message-selected");
    });
    return;
  }

  if (type === "block") {
    container.querySelectorAll("text.labelText").forEach((labelEl) => {
      let g: Element | null = labelEl.parentElement;
      while (g && g.tagName.toLowerCase() !== "svg") {
        if (g.tagName.toLowerCase() === "g") {
          if (buildBlockLabel(g) === nodeId) {
            labelEl.classList.add("block-selected");
            g.querySelector("rect.labelBox")?.classList.add("block-selected");
          }
          break;
        }
        g = g.parentElement;
      }
    });
    return;
  }

  const flowEl = container.querySelector(`[id^="flowchart-${nodeId}-"]`);
  if (flowEl) { flowEl.classList.add("node-selected"); return; }

  container.querySelectorAll("text.actor").forEach((textEl) => {
    if (textEl.textContent?.trim() === nodeId) {
      textEl.classList.add("actor-selected");
      textEl.parentElement?.querySelectorAll("rect.actor").forEach((r) => r.classList.add("actor-selected"));
    }
  });
}

function getSequenceParticipant(target: Element): string | null {
  let el: Element | null = target;
  if (el.tagName.toLowerCase() === "tspan") el = el.parentElement;
  if (!el || !el.classList.contains("actor")) return null;
  if (el.tagName.toLowerCase() === "text") return el.textContent?.trim() || null;
  if (el.tagName.toLowerCase() === "rect") {
    return el.parentElement?.querySelector("text.actor")?.textContent?.trim() || null;
  }
  return null;
}

function getSequenceMessage(target: Element): string | null {
  let el: Element | null = target;
  if (el.tagName.toLowerCase() === "tspan") el = el.parentElement;
  if (!el) return null;
  if (el.classList.contains("messageText")) return el.textContent?.trim() || null;
  return null;
}

// SVG は width だけ % 指定だと Safari で height: auto が効かないことがある。
// viewBox から縦横比を取り、幅も高さも px で明示する。
function applySvgWidth(
  container: HTMLElement,
  scrollEl: HTMLElement | null,
  scale: number,
) {
  const svgEl = container.querySelector("svg");
  if (!svgEl) return;

  // viewBox から自然なアスペクト比 (h/w) を取得
  const viewBox = svgEl.getAttribute("viewBox");
  let aspectRatio = 0;
  if (viewBox) {
    const parts = viewBox.split(/[\s,]+/);
    const w = parseFloat(parts[2]) || 0;
    const h = parseFloat(parts[3]) || 0;
    if (w > 0 && h > 0) aspectRatio = h / w;
  }

  svgEl.removeAttribute("width");
  svgEl.removeAttribute("height");
  svgEl.style.display = "block";
  // mermaid が style="max-width: <自然幅>" を埋め込むため打ち消す
  svgEl.style.maxWidth = "none";
  svgEl.style.maxHeight = "none";

  // スクロール領域の内幅（パディング除く）を基準とする
  const scrollW = scrollEl ? scrollEl.clientWidth : container.offsetWidth;
  if (scrollW <= 0) {
    svgEl.style.width = "100%";
    svgEl.style.height = "auto";
    container.style.width = "";
    return;
  }
  const cs = getComputedStyle(container);
  const padX = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
  const innerBaseW = Math.max(0, scrollW - padX);

  const targetW = Math.ceil(innerBaseW * scale);
  const targetH = aspectRatio > 0 ? Math.ceil(targetW * aspectRatio) : 0;

  svgEl.style.width = `${targetW}px`;
  svgEl.style.height = targetH > 0 ? `${targetH}px` : "auto";

  // scale > 1 ではコンテナも明示的に拡張してスクロール幅を広げる
  if (scale > 1) {
    container.style.width = `${targetW + padX}px`;
  } else {
    container.style.width = "";
  }
}

const ZOOM_STEP = 0.25;
const ZOOM_MIN = 0.25;
const ZOOM_MAX = 4;

interface Props {
  code: string;
  onNodeSelect: (node: SelectedNode | null) => void;
  selectedNode: SelectedNode | null;
}

export default function PreviewPanel({ code, onNodeSelect, selectedNode }: Props) {
  // containerRef: SVG を保持する div（scrollRef の直接の子）
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollRef    = useRef<HTMLDivElement>(null);
  const selectedNodeRef = useRef(selectedNode);
  selectedNodeRef.current = selectedNode;

  const [scale, setScale] = useState(1);
  const scaleRef = useRef(scale);
  scaleRef.current = scale;

  const zoomIn    = () => setScale((s) => Math.min(ZOOM_MAX, Math.round((s + ZOOM_STEP) * 100) / 100));
  const zoomOut   = () => setScale((s) => Math.max(ZOOM_MIN, Math.round((s - ZOOM_STEP) * 100) / 100));
  const zoomReset = () => setScale(1);

  // document レベルで登録することで Safari の passive 制限を回避
  useEffect(() => {
    const scroll = scrollRef.current;
    if (!scroll) return;
    const onWheel = (e: WheelEvent) => {
      if (!scroll.contains(e.target as Node)) return;
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      setScale((s) => {
        const next = s - e.deltaY * 0.001;
        return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(next * 100) / 100));
      });
    };
    document.addEventListener("wheel", onWheel, { passive: false });
    return () => document.removeEventListener("wheel", onWheel);
  }, []);

  // SVG 描画
  useEffect(() => {
    if (!containerRef.current || !code.trim()) return;
    const container = containerRef.current;
    const id = `mermaid-${++idCounter}`;
    container.innerHTML = "";

    (async () => {
      try {
        const mermaid = await getMermaid();
        const { svg } = await mermaid.render(id, code);
        if (container.isConnected) {
          container.innerHTML = svg;
          applySvgWidth(container, scrollRef.current, scaleRef.current);
          applyHighlight(container, selectedNodeRef.current);
        }
      } catch {
        if (container.isConnected) {
          container.innerHTML =
            '<p class="text-red-400 p-4 text-sm">構文エラー: Mermaidコードを確認してください</p>';
        }
      }
    })();
  }, [code]);

  // ズーム変更時
  useEffect(() => {
    if (containerRef.current) applySvgWidth(containerRef.current, scrollRef.current, scale);
  }, [scale]);

  // ハイライト変更時
  useEffect(() => {
    if (containerRef.current) applyHighlight(containerRef.current, selectedNode);
  }, [selectedNode]);

  function handleSvgClick(e: React.MouseEvent<HTMLDivElement>) {
    const target = e.target as Element;

    const nodeEl = target.closest(".node");
    if (nodeEl) {
      const elId = nodeEl.id ?? "";
      const match = elId.match(/flowchart-(.+)-\d+$/);
      const nodeId = match ? match[1] : elId;
      const labelEl = nodeEl.querySelector("foreignObject span") ?? nodeEl.querySelector("text");
      const nodeLabel = labelEl?.textContent?.trim() ?? nodeId;
      if (selectedNode?.nodeId === nodeId && selectedNode?.type === "participant") onNodeSelect(null);
      else onNodeSelect({ nodeId, nodeLabel, type: "participant" });
      return;
    }

    const blockLabel = getSequenceBlock(target);
    if (blockLabel) {
      if (selectedNode?.nodeId === blockLabel && selectedNode?.type === "block") onNodeSelect(null);
      else onNodeSelect({ nodeId: blockLabel, nodeLabel: blockLabel, type: "block" });
      return;
    }

    const participantName = getSequenceParticipant(target);
    if (participantName) {
      if (selectedNode?.nodeId === participantName && selectedNode?.type === "participant") onNodeSelect(null);
      else onNodeSelect({ nodeId: participantName, nodeLabel: participantName, type: "participant" });
      return;
    }

    const messageName = getSequenceMessage(target);
    if (messageName) {
      if (selectedNode?.nodeId === messageName && selectedNode?.type === "message") onNodeSelect(null);
      else onNodeSelect({ nodeId: messageName, nodeLabel: messageName, type: "message" });
      return;
    }

    onNodeSelect(null);
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white">
      {/* ズームコントロール（スクロール領域の外に固定） */}
      <div className="flex justify-end items-center px-3 py-1 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-1 border border-gray-200 rounded-lg px-2 py-1 text-xs text-gray-700 select-none">
          <button
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 disabled:opacity-30 text-base leading-none"
            onClick={zoomOut}
            disabled={scale <= ZOOM_MIN}
            title="縮小"
          >
            −
          </button>
          <button
            className="w-12 text-center hover:bg-gray-100 rounded py-0.5 tabular-nums"
            onClick={zoomReset}
            title="100% に戻す"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 disabled:opacity-30 text-base leading-none"
            onClick={zoomIn}
            disabled={scale >= ZOOM_MAX}
            title="拡大"
          >
            ＋
          </button>
        </div>
      </div>

      {/* スクロール領域: containerRef が直接の子になることでスクロール幅が正確に計算される */}
      <div ref={scrollRef} className="flex-1 overflow-auto">
        <div
          ref={containerRef}
          className="p-4 w-full"
          onClick={handleSvgClick}
        />
      </div>
    </div>
  );
}
