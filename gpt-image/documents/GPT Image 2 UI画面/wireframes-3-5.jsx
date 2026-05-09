/* global React, Ico, PromptBox, Placeholder, Section, Row, ParamGroup, CostEstimate */

// ============ WIREFRAME 3: Mode-First Hub (choose your starting point) ============
const Wireframe3 = () => (
  <div className="wf" style={{width: 1280, height: 800, padding: 0, display: 'flex', flexDirection: 'column'}}>
    <div style={{padding: '12px 20px', borderBottom: '1.5px solid var(--line)', display: 'flex', justifyContent: 'space-between'}}>
      <Row gap={10}>
        <div className="wf-h1">⌬ Image Studio</div>
        <span className="wf-mono" style={{color: 'var(--ink-faint)', alignSelf: 'center'}}>gpt-image-2</span>
      </Row>
      <Row gap={8}>
        <span className="wf-chip"><Ico.history/> 履歴 (12)</span>
        <span className="wf-chip"><Ico.grid/> ギャラリー</span>
        <span className="wf-chip"><Ico.cog/></span>
      </Row>
    </div>

    <div style={{flex: 1, padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--paper)'}}>
      <div style={{textAlign: 'center', marginBottom: 32}}>
        <div className="wf-h1" style={{fontSize: 32, marginBottom: 8}}>はじめましょう</div>
        <div className="wf-text" style={{color: 'var(--ink-soft)'}}>どこから画像を作りますか？目的に合うモードを選んでください。</div>
      </div>

      <Row gap={20} style={{marginBottom: 32}}>
        {/* Mode 1: Generate */}
        <div className="wf-box-rough" style={{width: 280, padding: 24, cursor: 'pointer', position: 'relative'}}>
          <div style={{marginBottom: 12, fontSize: 36}}>
            <svg width="48" height="48" viewBox="0 0 48 48"><path d="M24 6l3 12 12 3-12 3-3 12-3-12-12-3 12-3z" stroke="#1a1a1a" strokeWidth="2" fill="none"/></svg>
          </div>
          <div className="wf-h2" style={{marginBottom: 6}}>テキストから生成</div>
          <div className="wf-small" style={{marginBottom: 16}}>プロンプトだけで新しい画像を作ります。ブログカバー・バナー向け。</div>
          <div className="wf-mono" style={{fontSize: 10, color: 'var(--ink-faint)'}}>POST /v1/images/generations</div>
          <span className="wf-stamp" style={{position: 'absolute', top: 12, right: 12}}>標準</span>
        </div>

        {/* Mode 2: Reference */}
        <div className="wf-box-rough" style={{width: 280, padding: 24, cursor: 'pointer', borderColor: 'var(--accent)'}}>
          <div style={{marginBottom: 12}}>
            <svg width="48" height="48" viewBox="0 0 48 48">
              <rect x="6" y="10" width="20" height="14" stroke="#1a1a1a" strokeWidth="2" fill="none"/>
              <rect x="22" y="22" width="20" height="14" stroke="#1a1a1a" strokeWidth="2" fill="none"/>
            </svg>
          </div>
          <div className="wf-h2" style={{marginBottom: 6}}>参照画像から生成</div>
          <div className="wf-small" style={{marginBottom: 16}}>キャラクター・ロゴ・背景素材を最大10枚まで指定。一貫性のある画像。</div>
          <div className="wf-mono" style={{fontSize: 10, color: 'var(--ink-faint)'}}>POST /v1/images/edits (image[])</div>
          <span className="wf-annotation" style={{position: 'absolute', top: -10, right: 16, background: 'var(--paper)', padding: '0 6px'}}>★ 推し</span>
        </div>

        {/* Mode 3: Edit with mask */}
        <div className="wf-box-rough" style={{width: 280, padding: 24, cursor: 'pointer'}}>
          <div style={{marginBottom: 12}}>
            <svg width="48" height="48" viewBox="0 0 48 48">
              <rect x="6" y="6" width="36" height="36" stroke="#1a1a1a" strokeWidth="2" fill="none"/>
              <circle cx="30" cy="20" r="8" stroke="#1a1a1a" strokeWidth="2" fill="none" strokeDasharray="3 2"/>
            </svg>
          </div>
          <div className="wf-h2" style={{marginBottom: 6}}>マスクで部分編集</div>
          <div className="wf-small" style={{marginBottom: 16}}>既存画像の一部だけを書き換え。透明領域=編集領域として描画。</div>
          <div className="wf-mono" style={{fontSize: 10, color: 'var(--ink-faint)'}}>POST /v1/images/edits (mask)</div>
        </div>
      </Row>

      <hr className="wf-divider-solid" style={{width: 600}}/>

      <div style={{textAlign: 'center'}}>
        <div className="wf-label" style={{marginBottom: 12}}>または、対話で磨き込む</div>
        <button className="wf-btn"><Ico.chat/> マルチターン会話モードを開く <span className="wf-mono" style={{fontSize: 10, marginLeft: 6}}>responses API</span></button>
      </div>

      <div style={{marginTop: 32, display: 'flex', gap: 12}}>
        <span className="wf-annotation">↑ 各カードをクリックすると、それぞれ専用のフォームに進む</span>
      </div>
    </div>
  </div>
);

// ============ WIREFRAME 4: Conversational (chat-driven multi-turn) ============
const Wireframe4 = () => (
  <div className="wf" style={{width: 1280, height: 800, display: 'flex'}}>
    {/* left: conversation list */}
    <div style={{width: 220, borderRight: '1.5px solid var(--line)', padding: 12, background: 'var(--paper-warm)'}}>
      <div className="wf-h2" style={{marginBottom: 12}}>会話</div>
      <button className="wf-btn" style={{width: '100%', marginBottom: 12, justifyContent: 'center'}}><Ico.plus/> 新規</button>
      <div className="wf-label" style={{marginBottom: 6}}>過去のセッション</div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
        <div className="wf-box" style={{padding: '6px 8px', fontSize: 12}}>Elenaカフェシーン<div className="wf-small">3 turns · 昨日</div></div>
        <div className="wf-box" style={{padding: '6px 8px', fontSize: 12, opacity: 0.6}}>商品モック作成<div className="wf-small">5 turns · 2日前</div></div>
        <div className="wf-box" style={{padding: '6px 8px', fontSize: 12, opacity: 0.6}}>SNSアイコン<div className="wf-small">2 turns · 先週</div></div>
      </div>
    </div>

    {/* center: chat */}
    <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
      <div style={{padding: '10px 16px', borderBottom: '1.5px solid var(--line)', display: 'flex', justifyContent: 'space-between'}}>
        <Row gap={8}>
          <div className="wf-h2">新しい会話</div>
          <span className="wf-chip"><Ico.spark/> マルチターン編集</span>
        </Row>
        <Row gap={6}>
          <span className="wf-mono" style={{color: 'var(--ink-faint)'}}>previous_response_id 自動継承</span>
        </Row>
      </div>

      {/* messages area — empty state */}
      <div style={{flex: 1, padding: 32, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <div style={{textAlign: 'center', maxWidth: 480}}>
          <svg width="80" height="80" viewBox="0 0 80 80" style={{margin: '0 auto 16px', display: 'block'}}>
            <path d="M14 22h52v36H30l-12 8v-8h0z" stroke="#1a1a1a" strokeWidth="2" fill="none" strokeLinejoin="round"/>
            <circle cx="32" cy="40" r="2.5" fill="#1a1a1a"/>
            <circle cx="42" cy="40" r="2.5" fill="#1a1a1a"/>
            <circle cx="52" cy="40" r="2.5" fill="#1a1a1a"/>
          </svg>
          <div className="wf-h1" style={{marginBottom: 8}}>会話しながら画像を磨きこむ</div>
          <div className="wf-text" style={{color: 'var(--ink-soft)', marginBottom: 20}}>
            最初の指示を送ると、ここに画像とAIの返事が表示されます。<br/>
            「もう少し明るく」「背景を変えて」と続けるだけでOK。
          </div>
          <Row gap={6} style={{justifyContent: 'center', flexWrap: 'wrap', marginBottom: 20}}>
            <span className="wf-chip">📝 「カフェで作業中の人物」</span>
            <span className="wf-chip">📝 「商品の俯瞰モック」</span>
            <span className="wf-chip">📝 「ヒーロー画像」</span>
          </Row>
          <span className="wf-annotation">↓ プロンプトを送ってスタート</span>
        </div>
      </div>

      {/* composer */}
      <div style={{padding: 16, borderTop: '1.5px solid var(--line)'}}>
        <div className="wf-box-rough" style={{padding: 10}}>
          <PromptBox placeholder="メッセージを送る…   (参照画像をドラッグ&ドロップでもOK)" lines={2} withHint={false}/>
          <Row style={{justifyContent: 'space-between', marginTop: 8}}>
            <Row gap={4}>
              <span className="wf-chip" style={{fontSize: 10}}><Ico.upload/> 画像</span>
              <span className="wf-chip" style={{fontSize: 10}}><Ico.brush/> マスク</span>
              <span className="wf-chip" style={{fontSize: 10}}>auto</span>
              <span className="wf-chip" style={{fontSize: 10}}>high</span>
              <span className="wf-chip" style={{fontSize: 10}}>n=1</span>
            </Row>
            <button className="wf-btn wf-btn-accent"><Ico.send/> 送信</button>
          </Row>
        </div>
      </div>
    </div>

    {/* right: params drawer (collapsed feel) */}
    <div style={{width: 240, borderLeft: '1.5px solid var(--line)', padding: 14, background: 'var(--paper)', overflow: 'auto'}}>
      <div className="wf-label" style={{marginBottom: 10}}>このセッションの設定</div>
      <ParamGroup compact/>
      <hr className="wf-divider"/>
      <CostEstimate compact/>
    </div>
  </div>
);

// ============ WIREFRAME 5: Compact Studio (power-user dense) ============
const Wireframe5 = () => (
  <div className="wf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    {/* dense top bar with everything */}
    <div style={{display: 'flex', alignItems: 'center', padding: '6px 12px', borderBottom: '1.5px solid var(--line)', gap: 8, background: 'var(--paper-warm)', flexWrap: 'wrap'}}>
      <div className="wf-h2" style={{marginRight: 8}}>⌬</div>
      <span className="wf-chip wf-chip-active">generate</span>
      <span className="wf-chip">edit</span>
      <span className="wf-chip">multi-turn</span>
      <div style={{width: 1, height: 20, background: 'var(--line)', margin: '0 4px'}}></div>
      <span className="wf-chip">1024×1024 ▾</span>
      <span className="wf-chip">high ▾</span>
      <span className="wf-chip">n=1 ▾</span>
      <span className="wf-chip">PNG ▾</span>
      <span className="wf-chip">auto bg ▾</span>
      <span className="wf-chip">thinking off ▾</span>
      <div style={{flex: 1}}></div>
      <span className="wf-mono" style={{color: 'var(--ink-faint)'}}>≈ $0.211 / call</span>
      <span className="wf-chip"><Ico.cog/></span>
    </div>

    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      {/* left rail: nav */}
      <div style={{width: 56, borderRight: '1.5px solid var(--line)', padding: '12px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14}}>
        <div className="wf-chip wf-chip-active" style={{padding: '6px 8px'}}><Ico.spark/></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.image/></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.brush/></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.chat/></div>
        <div style={{width: 24, height: 1, background: 'var(--line)'}}></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.history/></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.grid/></div>
        <div className="wf-chip" style={{padding: '6px 8px'}}><Ico.layers/></div>
      </div>

      {/* main: canvas + thumbnails */}
      <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
        {/* canvas */}
        <div style={{flex: 1, padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <div className="wf-box-dashed" style={{width: 560, height: 560, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <div style={{textAlign: 'center'}}>
              <div className="wf-mono" style={{color: 'var(--ink-faint)', marginBottom: 8}}>1024 × 1024</div>
              <div className="wf-h2">empty canvas</div>
              <div className="wf-small" style={{marginTop: 4}}>⌘+Enter で生成</div>
            </div>
          </div>
        </div>

        {/* thumbnail rail */}
        <div style={{padding: 12, borderTop: '1.5px solid var(--line)'}}>
          <Row gap={6} style={{marginBottom: 8}}>
            <span className="wf-label">最近の出力</span>
            <span className="wf-small">空 — まだ何も生成していません</span>
          </Row>
          <Row gap={6}>
            {[1,2,3,4,5,6,7,8].map(i => (
              <Placeholder key={i} height={64} style={{width: 64, opacity: 0.3}}>—</Placeholder>
            ))}
          </Row>
        </div>

        {/* prompt bar */}
        <div style={{padding: 12, borderTop: '1.5px solid var(--line)', background: 'var(--paper-warm)'}}>
          <Row gap={8}>
            <button className="wf-chip"><Ico.upload/> ref(0)</button>
            <button className="wf-chip"><Ico.brush/> mask</button>
            <input className="wf-input" placeholder="prompt: ここに入力…" style={{flex: 1}}/>
            <button className="wf-btn wf-btn-accent"><Ico.spark/> Run ⌘↵</button>
          </Row>
        </div>
      </div>

      {/* right inspector */}
      <div style={{width: 260, borderLeft: '1.5px solid var(--line)', padding: 12, overflow: 'auto'}}>
        <Row style={{justifyContent: 'space-between', marginBottom: 10}}>
          <span className="wf-label">Inspector</span>
          <span className="wf-chip" style={{fontSize: 10}}>JSON</span>
        </Row>
        <div className="wf-box" style={{padding: 8, marginBottom: 12}}>
          <pre className="wf-mono" style={{fontSize: 10, margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.5}}>{`{
  "model": "gpt-image-2",
  "prompt": "",
  "size": "1024x1024",
  "quality": "high",
  "n": 1,
  "format": "png",
  "background": "auto"
}`}</pre>
        </div>
        <div className="wf-label" style={{marginBottom: 6}}>テンプレ / プリセット</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12}}>
          <div className="wf-box" style={{padding: 6, fontSize: 12}}>📝 ブログカバー (1536×1024 high)</div>
          <div className="wf-box" style={{padding: 6, fontSize: 12}}>📝 SNSアイコン (1024 sq high)</div>
          <div className="wf-box" style={{padding: 6, fontSize: 12}}>📝 商品モック (low draft)</div>
          <div className="wf-box" style={{padding: 6, fontSize: 12, opacity: 0.6}}>+ 新規プリセット保存</div>
        </div>
        <hr className="wf-divider"/>
        <div className="wf-label" style={{marginBottom: 6}}>比較ビュー</div>
        <Row><span className="wf-chip">A/B</span><span className="wf-chip">Before/After</span></Row>
      </div>
    </div>
  </div>
);

window.Wireframe3 = Wireframe3;
window.Wireframe4 = Wireframe4;
window.Wireframe5 = Wireframe5;
