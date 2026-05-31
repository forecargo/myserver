"""抽出済み JSON の確認用ローカル UI。

起動: `.venv/bin/python viewer.py` → http://127.0.0.1:8765/
- 左ペイン: 元画像 (EXIF + --rotate 90 補正済み)
- 右ペイン: VocabularyItem ごとのカード表示
- サイドバー: バッチ選択・ファイル一覧・前後ナビ
- キーボード: ← / → でページ送り
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from PIL import Image, ImageOps

logger = logging.getLogger("viewer")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCANS_DIR = BASE_DIR / "scans"
# part1 は --rotate 90 で抽出済み。バッチ別に変えたくなったら辞書化する
DEFAULT_ROTATE_DEG = 90
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

app = FastAPI(title="Vocab Extractor Viewer")


def _find_image(batch: str, stem: str) -> Path | None:
    base = SCANS_DIR / batch
    if not base.is_dir():
        return None
    for ext in IMAGE_EXTENSIONS:
        cand = base / f"{stem}{ext}"
        if cand.exists():
            return cand
    return None


@app.get("/api/batches")
def list_batches() -> list[str]:
    if not DATA_DIR.is_dir():
        return []
    return sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir())


@app.get("/api/files/{batch}")
def list_files(batch: str) -> list[dict]:
    bd = DATA_DIR / batch
    if not bd.is_dir():
        raise HTTPException(status_code=404, detail="batch not found")
    items: list[dict] = []
    for p in sorted(bd.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            n = len(data.get("vocabulary_list", []))
        except Exception:
            n = -1
        items.append({"stem": p.stem, "count": n, "has_image": _find_image(batch, p.stem) is not None})
    return items


@app.get("/api/data/{batch}/{stem}")
def get_data(batch: str, stem: str) -> JSONResponse:
    p = DATA_DIR / batch / f"{stem}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="json not found")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@app.get("/image/{batch}/{stem}")
def get_image(batch: str, stem: str) -> StreamingResponse:
    src = _find_image(batch, stem)
    if src is None:
        raise HTTPException(status_code=404, detail="image not found")
    with Image.open(src) as img:
        img.load()
        img = ImageOps.exif_transpose(img)
        if DEFAULT_ROTATE_DEG:
            img = img.rotate(DEFAULT_ROTATE_DEG, expand=True)
        img.thumbnail((1600, 1600))
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88, optimize=True)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/jpeg")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Vocab Extractor Viewer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
         display: flex; height: 100vh; background: #f5f5f7; color: #1d1d1f; }
  #sidebar { width: 260px; background: #1d1d1f; color: #f5f5f7; display: flex; flex-direction: column; }
  #sidebar .header { padding: 1rem; border-bottom: 1px solid #2c2c2e; }
  #sidebar select { width: 100%; padding: 0.5rem; background: #2c2c2e; color: #f5f5f7;
                    border: 1px solid #444; border-radius: 6px; font-size: 0.9rem; }
  #sidebar .nav { display: flex; gap: 0.4rem; margin: 0.5rem 0; }
  #sidebar .nav button { flex: 1; padding: 0.4rem; background: #2c2c2e; color: #f5f5f7;
                         border: 1px solid #444; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
  #sidebar .nav button:hover:not(:disabled) { background: #3a3a3c; }
  #sidebar .nav button:disabled { opacity: 0.35; cursor: not-allowed; }
  #status { padding: 0 1rem 0.5rem; font-size: 0.78rem; color: #98989d; }
  #file-list { flex: 1; overflow-y: auto; padding: 0 0.4rem 1rem; }
  .file-item { display: flex; align-items: center; justify-content: space-between;
               padding: 0.5rem 0.7rem; cursor: pointer; border-radius: 6px;
               font-size: 0.82rem; color: #e5e5ea; }
  .file-item:hover { background: #2c2c2e; }
  .file-item.active { background: #0a84ff; color: white; }
  .file-item .count { font-size: 0.7rem; color: #98989d; background: #2c2c2e; padding: 0.1rem 0.4rem; border-radius: 10px; }
  .file-item.active .count { background: rgba(255,255,255,0.25); color: white; }

  #main { flex: 1; display: flex; min-width: 0; }
  #image-panel { flex: 1; background: #2c2c2e; overflow: auto; padding: 1rem;
                 display: flex; align-items: flex-start; justify-content: center; }
  #image-panel img { max-width: 100%; height: auto; box-shadow: 0 4px 16px rgba(0,0,0,0.35); border-radius: 4px; }
  #data-panel { width: 52%; min-width: 480px; overflow-y: auto; padding: 1rem 1.2rem; background: #f5f5f7; }

  .card { background: white; border-radius: 14px; padding: 1rem 1.2rem;
          margin-bottom: 0.9rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .card-header { display: flex; align-items: baseline; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
  .card-id { color: #86868b; font-size: 0.78rem; font-weight: 600; }
  .card-word { font-size: 1.45rem; font-weight: 700; }
  .card-phonetic { color: #6e6e73; font-style: italic; font-size: 0.95rem; }
  .level { background: #007aff; color: white; padding: 0.15rem 0.55rem;
           border-radius: 999px; font-size: 0.7rem; font-weight: 700; margin-left: auto; letter-spacing: 0.05em; }
  .level.empty { background: #c7c7cc; color: #6e6e73; }

  .section { margin-top: 0.7rem; }
  .section-title { font-size: 0.68rem; font-weight: 700; color: #86868b;
                   letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem; }
  .pos-block { margin-bottom: 0.5rem; }
  .pos-tag { display: inline-block; background: #f2f2f7; color: #1d1d1f;
             padding: 0.15rem 0.55rem; border-radius: 6px; font-size: 0.78rem;
             font-weight: 600; margin-right: 0.4rem; }
  .meanings { padding-left: 1.2rem; }
  .meanings li { margin: 0.2rem 0; font-size: 0.93rem; line-height: 1.45; }
  .usages { padding-left: 1.2rem; }
  .usages li { margin: 0.2rem 0; color: #3a3a3c; font-size: 0.86rem; line-height: 1.45; }
  .origin { background: #fff9e6; padding: 0.55rem 0.7rem; border-radius: 8px; font-size: 0.86rem; }
  .origin .formula { font-family: ui-monospace, "SF Mono", Menlo, monospace;
                     color: #5c5c5e; margin-bottom: 0.2rem; }
  .examples { list-style: none; padding-left: 0; }
  .examples li { margin: 0.45rem 0; padding-left: 0.5rem; border-left: 3px solid #e5e5ea; }
  .ex-en { color: #1d1d1f; font-weight: 500; line-height: 1.4; }
  .ex-ja { color: #6e6e73; font-size: 0.86rem; margin-top: 0.1rem; line-height: 1.4; }

  .empty-state { padding: 2rem; color: #86868b; text-align: center; }
</style>
</head>
<body>
  <aside id="sidebar">
    <div class="header">
      <select id="batch-select" aria-label="バッチ選択"></select>
      <div class="nav">
        <button id="prev" title="前 (←)">← 前</button>
        <button id="next" title="次 (→)">次 →</button>
      </div>
    </div>
    <div id="status"></div>
    <div id="file-list"></div>
  </aside>
  <div id="main">
    <div id="image-panel"><img id="page-image" alt="" /></div>
    <div id="data-panel"><div class="empty-state">ファイルを選択してください</div></div>
  </div>

<script>
let batches = [], currentBatch = null, files = [], currentIdx = -1;

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function loadBatches() {
  batches = await fetchJson('/api/batches');
  const sel = document.getElementById('batch-select');
  sel.innerHTML = batches.length
    ? batches.map(b => `<option value="${esc(b)}">${esc(b)}</option>`).join('')
    : '<option>(バッチなし)</option>';
  sel.onchange = () => selectBatch(sel.value);
  if (batches.length) selectBatch(batches[0]);
}

async function selectBatch(batch) {
  currentBatch = batch;
  files = await fetchJson(`/api/files/${encodeURIComponent(batch)}`);
  currentIdx = -1;
  renderFileList();
  if (files.length) selectFile(0);
}

function renderFileList() {
  const list = document.getElementById('file-list');
  list.innerHTML = files.map((f, i) => `
    <div class="file-item ${i === currentIdx ? 'active' : ''}" data-idx="${i}">
      <span>${esc(f.stem)}</span>
      <span class="count">${f.count >= 0 ? f.count : 'err'}</span>
    </div>`).join('');
  list.querySelectorAll('.file-item').forEach(el => {
    el.onclick = () => selectFile(parseInt(el.dataset.idx, 10));
  });
  // アクティブ項目を視界内へ
  const active = list.querySelector('.file-item.active');
  if (active) active.scrollIntoView({ block: 'nearest' });
}

async function selectFile(idx) {
  if (idx < 0 || idx >= files.length) return;
  currentIdx = idx;
  const f = files[idx];
  renderFileList();
  const imgEl = document.getElementById('page-image');
  imgEl.src = `/image/${encodeURIComponent(currentBatch)}/${encodeURIComponent(f.stem)}`;
  imgEl.alt = f.stem;
  try {
    const data = await fetchJson(`/api/data/${encodeURIComponent(currentBatch)}/${encodeURIComponent(f.stem)}`);
    renderData(data);
    document.getElementById('status').textContent =
      `${idx + 1} / ${files.length} — ${data.vocabulary_list.length} 語`;
  } catch (e) {
    document.getElementById('data-panel').innerHTML = `<div class="empty-state">読み込み失敗: ${esc(e.message)}</div>`;
  }
  document.getElementById('prev').disabled = idx === 0;
  document.getElementById('next').disabled = idx >= files.length - 1;
}

function renderData(data) {
  const panel = document.getElementById('data-panel');
  if (!data.vocabulary_list?.length) {
    panel.innerHTML = '<div class="empty-state">単語が抽出されていません</div>';
    return;
  }
  panel.innerHTML = data.vocabulary_list.map(renderCard).join('');
  panel.scrollTop = 0;
}

function renderCard(it) {
  const level = it.level_tag
    ? `<span class="level">${esc(it.level_tag)}</span>`
    : `<span class="level empty">—</span>`;
  const defs = (it.definitions || []).map(d => `
    <div class="pos-block">
      <span class="pos-tag">${esc(d.part_of_speech)}</span>
      <ol class="meanings">${(d.meanings || []).map(m => `<li>${esc(m)}</li>`).join('')}</ol>
    </div>`).join('');
  const usages = (it.usages_and_notes || []).length ? `
    <div class="section">
      <div class="section-title">語法・注意・派生</div>
      <ul class="usages">${it.usages_and_notes.map(u => `<li>${esc(u)}</li>`).join('')}</ul>
    </div>` : '';
  const origin = it.word_origin ? `
    <div class="section">
      <div class="section-title">語源</div>
      <div class="origin">
        ${it.word_origin.formula ? `<div class="formula">${esc(it.word_origin.formula)}</div>` : ''}
        ${it.word_origin.description ? `<div>${esc(it.word_origin.description)}</div>` : ''}
      </div>
    </div>` : '';
  const examples = (it.examples || []).length ? `
    <div class="section">
      <div class="section-title">例文</div>
      <ul class="examples">${it.examples.map(ex => `
        <li>
          <div class="ex-en">${esc(ex.en)}</div>
          <div class="ex-ja">${esc(ex.ja)}</div>
        </li>`).join('')}</ul>
    </div>` : '';
  return `
    <div class="card">
      <div class="card-header">
        <span class="card-id">#${esc(it.id || '?')}</span>
        <span class="card-word">${esc(it.word)}</span>
        <span class="card-phonetic">${esc(it.phonetic)}</span>
        ${level}
      </div>
      ${defs}
      ${usages}
      ${origin}
      ${examples}
    </div>`;
}

function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

document.getElementById('prev').onclick = () => selectFile(currentIdx - 1);
document.getElementById('next').onclick = () => selectFile(currentIdx + 1);
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft') { e.preventDefault(); selectFile(currentIdx - 1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); selectFile(currentIdx + 1); }
});

loadBatches();
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("viewer:app", host="127.0.0.1", port=8765, reload=False)
