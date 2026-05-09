/* global React */
const { useState: useStateMF } = React;

// === Sketchy icons reused, plus a few more ===
const MFIco = {
  spark: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 2l1.5 4.5L14 8l-4.5 1.5L8 14l-1.5-4.5L2 8l4.5-1.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>,
  image: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="10" stroke="currentColor" strokeWidth="1.5"/><circle cx="6" cy="7" r="1.2" stroke="currentColor" strokeWidth="1.2"/><path d="M3 12l3-3 3 2 4-4" stroke="currentColor" strokeWidth="1.5"/></svg>,
  brush: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 13c1-3 3-5 6-6l3-3-3 3c-1 3-3 5-6 6z" stroke="currentColor" strokeWidth="1.5"/></svg>,
  download: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 3v8M5 8l3 3 3-3M3 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  copy: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="5" y="5" width="9" height="9" stroke="currentColor" strokeWidth="1.5" rx="1"/><path d="M11 5V3a1 1 0 00-1-1H3a1 1 0 00-1 1v7a1 1 0 001 1h2" stroke="currentColor" strokeWidth="1.5"/></svg>,
  edit: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M11 2l3 3-8 8H3v-3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>,
  more: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="3" cy="8" r="1.2" fill="currentColor"/><circle cx="8" cy="8" r="1.2" fill="currentColor"/><circle cx="13" cy="8" r="1.2" fill="currentColor"/></svg>,
  heart: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 13s-5-3-5-7a3 3 0 015-2 3 3 0 015 2c0 4-5 7-5 7z" stroke="currentColor" strokeWidth="1.5"/></svg>,
  refresh: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8a5 5 0 019-3l1 1M13 8a5 5 0 01-9 3l-1-1M11 6h2.5V3.5M5 10H2.5V12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  check: () => <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
};

// Annotation arrow: callout text + dashed line to the target
const Annot = ({ x, y, text, lineW = 60, lineDir = 'left' }) => (
  <>
    <div className="mf-annot" style={{left: x, top: y}}>{text}</div>
    <div className="mf-annot-line" style={{
      left: lineDir === 'left' ? x - lineW - 4 : x + 60,
      top: y + 8,
      width: lineW
    }}></div>
  </>
);

// State spec marker (compact) — shows the state + its source button
const StateSpec = ({ children }) => (
  <span className="mf-state-dot">{children}</span>
);

// Top-bar (shared)
const TopBar = () => (
  <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
      <div className="mf-h1">⌬ Image Studio</div>
      <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>gpt-image-2</span>
    </div>
    <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
      <button className="mf-btn mf-btn--ghost">履歴</button>
      <button className="mf-btn mf-btn--ghost">ギャラリー</button>
      <button className="mf-btn">設定</button>
    </div>
  </div>
);

// Left sidebar (shared, with parameters in their post-generation state)
const LeftSidebar = () => (
  <div style={{width: 300, padding: 16, borderRight: '1px solid var(--mf-line)', background: 'var(--mf-bg)', overflow: 'auto', flexShrink: 0}}>
    <div style={{marginBottom: 16}}>
      <div className="mf-label" style={{marginBottom: 6}}>モード</div>
      <div className="mf-segmented" style={{width: '100%', display: 'flex'}}>
        <button className="mf-seg-active" style={{flex: 1}}>生成</button>
        <button style={{flex: 1}}>参照</button>
        <button style={{flex: 1}}>編集</button>
      </div>
    </div>

    <div style={{marginBottom: 16}}>
      <div className="mf-label" style={{marginBottom: 6}}>サイズ</div>
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6}}>
        <button className="mf-chip mf-chip--active" style={{justifyContent: 'center'}}>1:1 · 1024</button>
        <button className="mf-chip" style={{justifyContent: 'center'}}>3:2 · 1536</button>
        <button className="mf-chip" style={{justifyContent: 'center'}}>2:3 · 1024</button>
        <button className="mf-chip" style={{justifyContent: 'center'}}>16:9 · HD</button>
      </div>
      <button className="mf-btn mf-btn--ghost" style={{marginTop: 6, fontSize: 11, padding: '4px 8px'}}>+ カスタムサイズ</button>
    </div>

    <div style={{marginBottom: 16}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6}}>
        <div className="mf-label">品質</div>
        <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>$0.211</span>
      </div>
      <div className="mf-segmented" style={{width: '100%', display: 'flex'}}>
        <button style={{flex: 1}}>low</button>
        <button style={{flex: 1}}>med</button>
        <button className="mf-seg-active" style={{flex: 1}}>high</button>
        <button style={{flex: 1}}>auto</button>
      </div>
    </div>

    <div style={{marginBottom: 16}}>
      <div className="mf-label" style={{marginBottom: 6}}>同時生成 (n)</div>
      <div className="mf-segmented" style={{width: '100%', display: 'flex'}}>
        <button style={{flex: 1}}>1</button>
        <button style={{flex: 1}}>2</button>
        <button className="mf-seg-active" style={{flex: 1}}>4</button>
        <button style={{flex: 1}}>8</button>
      </div>
    </div>

    <hr className="mf-divider"/>

    <div style={{marginBottom: 16}}>
      <div className="mf-label" style={{marginBottom: 6}}>出力フォーマット</div>
      <div className="mf-segmented" style={{width: '100%', display: 'flex'}}>
        <button className="mf-seg-active" style={{flex: 1}}>PNG</button>
        <button style={{flex: 1}}>JPEG</button>
        <button style={{flex: 1}}>WebP</button>
      </div>
    </div>

    <div style={{marginBottom: 16}}>
      <div className="mf-label" style={{marginBottom: 6}}>背景</div>
      <div className="mf-segmented" style={{width: '100%', display: 'flex'}}>
        <button className="mf-seg-active" style={{flex: 1}}>auto</button>
        <button style={{flex: 1}}>opaque</button>
        <button style={{flex: 1, opacity: 0.35, textDecoration: 'line-through'}}>透過</button>
      </div>
    </div>

    <div style={{marginBottom: 16}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div className="mf-label">Thinking mode</div>
        <span className="mf-chip" style={{fontSize: 10}}>off</span>
      </div>
      <div className="mf-small" style={{marginTop: 4}}>複雑なプロンプトで内部推論を有効化</div>
    </div>
  </div>
);

// Prompt bar (shared)
const PromptBar = ({ prompt = "Elena Bloom sitting at a late-night café, coding on a laptop, warm amber lighting, cinematic composition." }) => (
  <div style={{padding: 12, borderTop: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
    <div style={{display: 'flex', gap: 8, alignItems: 'flex-start'}}>
      <div style={{display: 'flex', gap: 4}}>
        <button className="mf-btn"><MFIco.image/> 0</button>
        <button className="mf-btn"><MFIco.brush/></button>
      </div>
      <textarea className="mf-textarea" rows={2} defaultValue={prompt} style={{flex: 1}}></textarea>
      <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
        <button className="mf-btn mf-btn--accent mf-btn--lg"><MFIco.spark/> 再生成</button>
        <span className="mf-small" style={{textAlign: 'center'}}>⌘↵</span>
      </div>
    </div>
  </div>
);

// Result tile (shared)
const ResultTile = ({ variant = 1, selected = false, size = 'square', meta }) => {
  const cls = {1: '', 2: 'mf-img-gen-2', 3: 'mf-img-gen-3', 4: 'mf-img-gen-4'}[variant] || '';
  return (
    <div className="mf-img-gen-wrap" style={{position: 'relative', borderRadius: 8, outline: selected ? '2px solid var(--mf-accent)' : 'none', outlineOffset: 2}}>
      <div className={`mf-img-gen ${cls}`} style={{width: '100%', aspectRatio: size === 'square' ? '1/1' : size, height: size !== 'square' ? 'auto' : undefined}}></div>
      {meta && (
        <div style={{position: 'absolute', top: 8, left: 8, background: 'rgba(255,255,255,0.95)', padding: '2px 6px', borderRadius: 4, fontSize: 10, fontFamily: 'JetBrains Mono, monospace'}}>{meta}</div>
      )}
      <div className="mf-overlay-actions">
        <button className="mf-icon-btn"><MFIco.download/></button>
        <button className="mf-icon-btn"><MFIco.copy/></button>
        <button className="mf-icon-btn"><MFIco.edit/></button>
        <button className="mf-icon-btn"><MFIco.heart/></button>
      </div>
    </div>
  );
};

window.MFIco = MFIco;
window.Annot = Annot;
window.StateSpec = StateSpec;
window.MFTopBar = TopBar;
window.MFLeftSidebar = LeftSidebar;
window.MFPromptBar = PromptBar;
window.MFResultTile = ResultTile;
