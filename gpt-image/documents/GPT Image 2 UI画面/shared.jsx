/* global React */
const { useState } = React;

// ============ Shared mini-icons (sketchy SVG primitives) ============
const Ico = {
  plus: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>,
  upload: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M8 11V3M5 6l3-3 3 3M3 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>,
  download: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M8 3v8M5 8l3 3 3-3M3 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>,
  spark: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M8 2l1.5 4.5L14 8l-4.5 1.5L8 14l-1.5-4.5L2 8l4.5-1.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none"/></svg>,
  brush: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M3 13c1-3 3-5 6-6l3-3-3 3c-1 3-3 5-6 6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none"/></svg>,
  send: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M2 14l12-6L2 2v5l8 1-8 1z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none"/></svg>,
  history: () => <svg className="wf-icon" viewBox="0 0 16 16"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.5" fill="none"/><path d="M8 5v3l2 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>,
  grid: () => <svg className="wf-icon" viewBox="0 0 16 16"><rect x="2.5" y="2.5" width="4" height="4" stroke="currentColor" strokeWidth="1.5" fill="none"/><rect x="9.5" y="2.5" width="4" height="4" stroke="currentColor" strokeWidth="1.5" fill="none"/><rect x="2.5" y="9.5" width="4" height="4" stroke="currentColor" strokeWidth="1.5" fill="none"/><rect x="9.5" y="9.5" width="4" height="4" stroke="currentColor" strokeWidth="1.5" fill="none"/></svg>,
  image: () => <svg className="wf-icon" viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" stroke="currentColor" strokeWidth="1.5" fill="none"/><circle cx="6" cy="7" r="1.2" stroke="currentColor" strokeWidth="1.2" fill="none"/><path d="M3 12l3-3 3 2 4-4" stroke="currentColor" strokeWidth="1.5" fill="none"/></svg>,
  cog: () => <svg className="wf-icon" viewBox="0 0 16 16"><circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.5" fill="none"/><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeDasharray="2 2"/></svg>,
  chat: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M2 4h12v8H6l-3 2v-2H2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none"/></svg>,
  layers: () => <svg className="wf-icon" viewBox="0 0 16 16"><path d="M2 5l6-3 6 3-6 3zM2 8l6 3 6-3M2 11l6 3 6-3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none"/></svg>,
};

// ============ Reusable bits ============
const PromptBox = ({ placeholder = "プロンプトを入力…", lines = 3, withHint = true }) => (
  <div className="wf-box" style={{padding: '10px 12px', minHeight: lines * 22 + 16}}>
    <div className="wf-text" style={{color: 'var(--ink-faint)'}}>{placeholder}</div>
    {withHint && (
      <div style={{position: 'absolute', bottom: 6, right: 8, display: 'flex', gap: 6}}>
        <span className="wf-mono" style={{color: 'var(--ink-faint)'}}>0/4000</span>
      </div>
    )}
  </div>
);

const Placeholder = ({ children, height = 200, style = {} }) => (
  <div className="wf-placeholder" style={{height, ...style}}>
    <div>
      <div>{children}</div>
    </div>
  </div>
);

const Section = ({ title, children, hint }) => (
  <div style={{marginBottom: 18}}>
    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6}}>
      <div className="wf-label">{title}</div>
      {hint && <span className="wf-small" style={{fontSize: 10}}>{hint}</span>}
    </div>
    {children}
  </div>
);

const Row = ({ children, gap = 8, style = {} }) => (
  <div style={{display: 'flex', gap, alignItems: 'center', ...style}}>{children}</div>
);

// ============ Shared param controls (used by multiple wireframes) ============
const ParamGroup = ({ density = 'normal' }) => {
  const compact = density === 'compact';
  return (
    <>
      <Section title="SIZE / アスペクト比">
        <Row gap={4} style={{flexWrap: 'wrap'}}>
          <span className="wf-chip">auto</span>
          <span className="wf-chip wf-chip-active">1:1 · 1024</span>
          <span className="wf-chip">3:2 · 1536×1024</span>
          <span className="wf-chip">2:3 · 1024×1536</span>
          <span className="wf-chip">16:9 · 1920×1080</span>
          {!compact && <span className="wf-chip">+ カスタム</span>}
        </Row>
      </Section>

      <Section title="QUALITY" hint="$0.005 〜 $0.211">
        <Row>
          <span className="wf-chip">low</span>
          <span className="wf-chip">medium</span>
          <span className="wf-chip wf-chip-active">high</span>
          <span className="wf-chip">auto</span>
        </Row>
      </Section>

      <Section title="N · 生成枚数">
        <Row>
          <span className="wf-chip wf-chip-active">1</span>
          <span className="wf-chip">2</span>
          <span className="wf-chip">4</span>
          <span className="wf-chip">8</span>
          <span className="wf-small">枚同時生成</span>
        </Row>
      </Section>

      <Section title="FORMAT">
        <Row>
          <span className="wf-chip wf-chip-active">PNG</span>
          <span className="wf-chip">JPEG</span>
          <span className="wf-chip">WebP</span>
        </Row>
        {!compact && (
          <div style={{marginTop: 8}}>
            <span className="wf-small">圧縮率 (JPEG/WebP)</span>
            <div className="wf-slider"><div className="wf-slider-thumb" style={{left: '70%'}}></div></div>
          </div>
        )}
      </Section>

      <Section title="BACKGROUND">
        <Row>
          <span className="wf-chip wf-chip-active">auto</span>
          <span className="wf-chip">opaque</span>
          <span className="wf-chip" style={{textDecoration: 'line-through', opacity: 0.4}}>transparent</span>
          <span className="wf-small">※非対応</span>
        </Row>
      </Section>

      <Section title="THINKING MODE">
        <Row>
          <span className="wf-chip wf-chip-active">○ off</span>
          <span className="wf-chip">● on</span>
          <span className="wf-small">複雑なプロンプト向け</span>
        </Row>
      </Section>
    </>
  );
};

// ============ Cost Estimator ============
const CostEstimate = ({ compact }) => (
  <div className="wf-box" style={{padding: '8px 10px', background: 'var(--paper-warm)'}}>
    <Row style={{justifyContent: 'space-between'}}>
      <span className="wf-label">推定コスト</span>
      <span className="wf-mono" style={{fontWeight: 700}}>≈ $0.211</span>
    </Row>
    {!compact && <div className="wf-small" style={{marginTop: 2}}>1024×1024 · high · n=1</div>}
  </div>
);

// Export
window.Ico = Ico;
window.PromptBox = PromptBox;
window.Placeholder = Placeholder;
window.Section = Section;
window.Row = Row;
window.ParamGroup = ParamGroup;
window.CostEstimate = CostEstimate;
