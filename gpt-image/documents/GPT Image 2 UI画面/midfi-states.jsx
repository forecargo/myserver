/* global React, MFIco, MFTopBar, MFLeftSidebar, MFPromptBar, MFResultTile */

// =========================================================
// B-1. 生成中 · ストリーミング (partial_images)
// =========================================================
const StreamingState = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      <MFLeftSidebar/>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)'}}>
        <div style={{padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span className="mf-chip" style={{background: 'var(--mf-warn)', color: 'white', borderColor: 'var(--mf-warn)'}}>● 生成中…</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>4枚 · 1024×1024 · high · partial_images=2</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>· 経過 12.3s / ~18s予測</span>
          </div>
          <button className="mf-btn">中止</button>
        </div>

        <div style={{flex: 1, display: 'flex', minHeight: 0}}>
          <div style={{flex: 1, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <div style={{width: 540, position: 'relative'}}>
              <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 8, position: 'relative', filter: 'blur(2px) brightness(0.85)'}}></div>
              {/* Progress overlay */}
              <div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'white'}}>
                <div className="mf-mono" style={{fontSize: 13, marginBottom: 12, background: 'rgba(0,0,0,0.55)', padding: '6px 12px', borderRadius: 6}}>preview 2/2 · 約76%</div>
                <div style={{width: 320, height: 4, background: 'rgba(255,255,255,0.25)', borderRadius: 2, overflow: 'hidden'}}>
                  <div style={{width: '76%', height: '100%', background: 'white', transition: 'width 0.3s'}}></div>
                </div>
              </div>
            </div>
          </div>

          <div style={{width: 200, padding: '24px 16px 24px 0', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto'}}>
            <div className="mf-label">このrunの進捗</div>
            {/* tile 1: done */}
            <div style={{position: 'relative'}}>
              <div className="mf-img-gen" style={{aspectRatio: '1/1', borderRadius: 6}}></div>
              <div style={{position: 'absolute', top: 6, right: 6, background: 'var(--mf-success)', color: 'white', borderRadius: 4, padding: '2px 6px', fontSize: 10, fontFamily: 'JetBrains Mono'}}>✓</div>
            </div>
            {/* tile 2: streaming current */}
            <div style={{position: 'relative', outline: '2px solid var(--mf-accent)', outlineOffset: 2, borderRadius: 6}}>
              <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 6, filter: 'blur(2px)'}}></div>
              <div style={{position: 'absolute', bottom: 4, left: 4, right: 4, fontSize: 10, fontFamily: 'JetBrains Mono', color: 'white', background: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: 3, textAlign: 'center'}}>76%</div>
            </div>
            {/* tile 3: queued */}
            <div className="mf-img-ph" style={{aspectRatio: '1/1', borderRadius: 6, background: '#f3f1ea'}}>
              <span className="mf-mono" style={{fontSize: 10, color: 'var(--mf-ink-faint)'}}>待機中</span>
            </div>
            <div className="mf-img-ph" style={{aspectRatio: '1/1', borderRadius: 6, background: '#f3f1ea'}}>
              <span className="mf-mono" style={{fontSize: 10, color: 'var(--mf-ink-faint)'}}>待機中</span>
            </div>

            <div className="mf-small" style={{marginTop: 4, fontSize: 10}}>※ 各partial_imageは100出力トークン課金</div>
          </div>
        </div>

        <div style={{padding: 12, borderTop: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
            <textarea className="mf-textarea" rows={2} disabled defaultValue="Elena Bloom sitting at a late-night café, coding on a laptop, warm amber lighting, cinematic composition." style={{flex: 1, background: 'var(--mf-bg-alt)'}}></textarea>
            <button className="mf-btn mf-btn--lg mf-state-disabled">⏳ 生成中…</button>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// =========================================================
// B-2. 参照画像アップロード済み (最大10枚、役割ラベル付き)
// =========================================================
const RefUploadedState = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      <MFLeftSidebar/>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)'}}>
        <div style={{padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span className="mf-chip mf-chip--active"><MFIco.image/> 参照モード</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>3枚アップロード済み · /v1/images/edits</span>
          </div>
          <span className="mf-small">最大10枚まで</span>
        </div>

        {/* reference panel */}
        <div style={{padding: 20, background: 'var(--mf-bg)', borderBottom: '1px solid var(--mf-line)'}}>
          <div className="mf-label" style={{marginBottom: 10}}>参照画像 (順序が役割を決めます)</div>
          <div style={{display: 'flex', gap: 12, alignItems: 'flex-start'}}>
            {/* ref 1: character */}
            <div style={{width: 140, position: 'relative'}}>
              <div className="mf-img-gen mf-img-gen-3" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
              <div style={{position: 'absolute', top: 6, left: 6, background: 'var(--mf-ink)', color: 'white', borderRadius: 4, padding: '2px 6px', fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 600}}>① キャラクター</div>
              <button style={{position: 'absolute', top: 4, right: 4, width: 22, height: 22, border: 'none', borderRadius: 4, background: 'rgba(0,0,0,0.65)', color: 'white', cursor: 'pointer', fontSize: 12}}>×</button>
              <div className="mf-small" style={{marginTop: 6, fontSize: 11}}>elena_ref.png<br/><span style={{color: 'var(--mf-ink-faint)'}}>1024×1024 · 248KB</span></div>
            </div>
            {/* ref 2: logo */}
            <div style={{width: 140, position: 'relative'}}>
              <div className="mf-img-gen" style={{aspectRatio: '1/1', borderRadius: 8, background: '#fafaf7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif', fontSize: 64, fontWeight: 900, color: 'var(--mf-ink)'}}>A</div>
              <div style={{position: 'absolute', top: 6, left: 6, background: 'var(--mf-ink)', color: 'white', borderRadius: 4, padding: '2px 6px', fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 600}}>② ロゴ</div>
              <button style={{position: 'absolute', top: 4, right: 4, width: 22, height: 22, border: 'none', borderRadius: 4, background: 'rgba(0,0,0,0.65)', color: 'white', cursor: 'pointer', fontSize: 12}}>×</button>
              <div className="mf-small" style={{marginTop: 6, fontSize: 11}}>AICU-Japan-A.png<br/><span style={{color: 'var(--mf-ink-faint)'}}>512×512 · 24KB</span></div>
            </div>
            {/* ref 3: bg */}
            <div style={{width: 140, position: 'relative'}}>
              <div className="mf-img-gen mf-img-gen-4" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
              <div style={{position: 'absolute', top: 6, left: 6, background: 'var(--mf-ink)', color: 'white', borderRadius: 4, padding: '2px 6px', fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 600}}>③ 背景</div>
              <button style={{position: 'absolute', top: 4, right: 4, width: 22, height: 22, border: 'none', borderRadius: 4, background: 'rgba(0,0,0,0.65)', color: 'white', cursor: 'pointer', fontSize: 12}}>×</button>
              <div className="mf-small" style={{marginTop: 6, fontSize: 11}}>cafe_bg.jpg<br/><span style={{color: 'var(--mf-ink-faint)'}}>1920×1080 · 580KB</span></div>
            </div>
            {/* upload more */}
            <div style={{width: 140}}>
              <div style={{aspectRatio: '1/1', border: '1.5px dashed var(--mf-line)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 6, color: 'var(--mf-ink-soft)', cursor: 'pointer'}}>
                <span style={{fontSize: 24}}>+</span>
                <span style={{fontSize: 11}}>追加 (3/10)</span>
              </div>
              <div className="mf-small" style={{marginTop: 6, fontSize: 11, color: 'var(--mf-ink-faint)'}}>ドラッグ&ドロップ可</div>
            </div>
          </div>
          <div style={{marginTop: 10, padding: '8px 12px', background: 'var(--mf-accent-soft)', borderRadius: 6, fontSize: 12, color: 'var(--mf-ink)', display: 'flex', alignItems: 'center', gap: 8}}>
            <span style={{color: 'var(--mf-accent)', fontWeight: 600}}>💡</span>
            プロンプトで「1枚目はキャラクター、2枚目のロゴを胸に持っている構図」のように役割を明示するとうまくいきます
          </div>
        </div>

        {/* preview area */}
        <div style={{flex: 1, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <div style={{textAlign: 'center', maxWidth: 360}}>
            <div className="mf-h2" style={{marginBottom: 8}}>プロンプトを書いて生成</div>
            <div className="mf-small">3枚の参照画像を組み合わせて、新しい画像を作ります</div>
          </div>
        </div>

        <MFPromptBar prompt="1枚目のキャラクターが、2枚目のAロゴを胸の前で持ち、3枚目のカフェ背景の中に立っている構図。X/Twitterアイコンに適した正方形構図。" />
      </div>
    </div>
  </div>
);

// =========================================================
// B-3. マスク編集モード (部分編集)
// =========================================================
const MaskEditMode = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      {/* mask-specific tools sidebar */}
      <div style={{width: 240, padding: 16, borderRight: '1px solid var(--mf-line)', background: 'var(--mf-bg)', overflow: 'auto'}}>
        <div className="mf-label" style={{marginBottom: 10}}>マスクツール</div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 16}}>
          <button className="mf-btn" style={{justifyContent: 'center', background: 'var(--mf-ink)', color: 'white', borderColor: 'var(--mf-ink)'}}><MFIco.brush/> 描画</button>
          <button className="mf-btn" style={{justifyContent: 'center'}}>消去</button>
          <button className="mf-btn" style={{justifyContent: 'center'}}>選択</button>
          <button className="mf-btn" style={{justifyContent: 'center'}}>反転</button>
        </div>
        <div style={{marginBottom: 16}}>
          <div className="mf-label" style={{marginBottom: 6}}>ブラシサイズ</div>
          <input type="range" min="1" max="100" defaultValue="40" style={{width: '100%'}}/>
          <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'JetBrains Mono', fontSize: 10, color: 'var(--mf-ink-faint)'}}>
            <span>1</span><span>40px</span><span>100</span>
          </div>
        </div>
        <div style={{marginBottom: 16}}>
          <div className="mf-label" style={{marginBottom: 6}}>不透明度 (羽根ぼかし)</div>
          <input type="range" min="0" max="100" defaultValue="100" style={{width: '100%'}}/>
        </div>
        <hr className="mf-divider"/>
        <button className="mf-btn" style={{width: '100%', justifyContent: 'center', marginBottom: 8}}>マスクを画像から読み込み</button>
        <button className="mf-btn" style={{width: '100%', justifyContent: 'center', marginBottom: 8}}>マスクをDL</button>
        <button className="mf-btn" style={{width: '100%', justifyContent: 'center'}}>クリア</button>
        <hr className="mf-divider"/>
        <div className="mf-label" style={{marginBottom: 6}}>履歴</div>
        <div style={{fontFamily: 'JetBrains Mono', fontSize: 11, color: 'var(--mf-ink-soft)', display: 'flex', flexDirection: 'column', gap: 4}}>
          <div>↶ 元に戻す  ⌘Z</div>
          <div>↷ やり直し  ⌘⇧Z</div>
        </div>
        <hr className="mf-divider"/>
        <div style={{padding: '8px 10px', background: 'var(--mf-accent-soft)', borderRadius: 6, fontSize: 11, lineHeight: 1.4}}>
          <strong>マスクの仕様</strong><br/>
          透明=編集する領域<br/>
          不透明=保持する領域<br/>
          形状はガイド扱い
        </div>
      </div>

      {/* canvas */}
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)'}}>
        <div style={{padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span className="mf-h2">マスクで部分編集</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>· 元画像: run_4f7a · 変種02</span>
          </div>
          <div style={{display: 'flex', gap: 6}}>
            <span className="mf-segmented" style={{display: 'inline-flex'}}>
              <button className="mf-seg-active">マスク</button>
              <button>元画像</button>
              <button>結果</button>
            </span>
            <button className="mf-btn">⌘ + Z</button>
          </div>
        </div>

        <div style={{flex: 1, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'}}>
          <div style={{width: 540, position: 'relative', cursor: 'crosshair'}}>
            <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
            {/* fake mask overlay (a shape representing painted area) */}
            <svg style={{position: 'absolute', inset: 0, width: '100%', height: '100%', borderRadius: 8, pointerEvents: 'none'}} viewBox="0 0 540 540" preserveAspectRatio="none">
              <defs>
                <pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
                  <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(255,107,53,0.7)" strokeWidth="3"/>
                </pattern>
              </defs>
              <ellipse cx="280" cy="180" rx="120" ry="100" fill="url(#hatch)" stroke="var(--mf-accent)" strokeWidth="2" strokeDasharray="6 3"/>
            </svg>
            {/* brush cursor preview */}
            <div style={{position: 'absolute', top: '40%', left: '55%', width: 40, height: 40, border: '2px solid var(--mf-accent)', borderRadius: '50%', pointerEvents: 'none', background: 'rgba(255,107,53,0.15)'}}></div>
            {/* zoom badge */}
            <div style={{position: 'absolute', bottom: 12, right: 12, background: 'rgba(0,0,0,0.7)', color: 'white', padding: '4px 8px', borderRadius: 4, fontSize: 11, fontFamily: 'JetBrains Mono'}}>100% · 1024×1024</div>
          </div>
        </div>

        <div style={{padding: 12, borderTop: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
            <textarea className="mf-textarea" rows={2} placeholder="マスク領域に何を入れますか? 例: 「背景を雨の窓に変更」" style={{flex: 1}}></textarea>
            <button className="mf-btn mf-btn--accent mf-btn--lg"><MFIco.brush/> 編集を実行</button>
          </div>
          <div className="mf-small" style={{marginTop: 4, color: 'var(--mf-ink-faint)'}}>マスク領域 ≈ 12% · 推定コスト $0.21</div>
        </div>
      </div>
    </div>
  </div>
);

// =========================================================
// B-4. 1枚フルスクリーン詳細 (lightbox)
// =========================================================
const LightboxView = () => (
  <div className="mf" style={{width: 1280, height: 800, position: 'relative', background: '#1a1a1a', display: 'flex', flexDirection: 'column'}}>
    {/* top bar */}
    <div style={{padding: '12px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'white', borderBottom: '1px solid rgba(255,255,255,0.1)'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
        <button className="mf-btn" style={{background: 'transparent', borderColor: 'rgba(255,255,255,0.25)', color: 'white'}}>✕ 閉じる (Esc)</button>
        <span className="mf-h2" style={{color: 'white'}}>変種 02 / 04</span>
        <span className="mf-mono" style={{color: 'rgba(255,255,255,0.5)'}}>elena_cafe_02.png</span>
      </div>
      <div style={{display: 'flex', gap: 6}}>
        <button className="mf-btn" style={{background: 'transparent', borderColor: 'rgba(255,255,255,0.25)', color: 'white'}}><MFIco.heart/> お気に入り</button>
        <button className="mf-btn" style={{background: 'transparent', borderColor: 'rgba(255,255,255,0.25)', color: 'white'}}><MFIco.copy/> URLコピー</button>
        <button className="mf-btn" style={{background: 'white', borderColor: 'white', color: 'var(--mf-ink)'}}><MFIco.download/> ダウンロード</button>
      </div>
    </div>

    <div style={{flex: 1, display: 'flex', minHeight: 0}}>
      {/* prev arrow */}
      <div style={{width: 60, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <button style={{width: 44, height: 44, border: '1px solid rgba(255,255,255,0.25)', borderRadius: '50%', background: 'transparent', color: 'white', cursor: 'pointer', fontSize: 18}}>←</button>
      </div>

      {/* image */}
      <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24}}>
        <div className="mf-img-gen mf-img-gen-2" style={{maxWidth: '100%', maxHeight: '100%', width: 600, aspectRatio: '1/1', borderRadius: 8, boxShadow: '0 20px 60px rgba(0,0,0,0.5)'}}></div>
      </div>

      {/* next arrow */}
      <div style={{width: 60, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <button style={{width: 44, height: 44, border: '1px solid rgba(255,255,255,0.25)', borderRadius: '50%', background: 'transparent', color: 'white', cursor: 'pointer', fontSize: 18}}>→</button>
      </div>

      {/* metadata panel */}
      <div style={{width: 320, background: '#262626', color: 'white', padding: 20, overflow: 'auto'}}>
        <div style={{fontSize: 10, fontFamily: 'JetBrains Mono', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'rgba(255,255,255,0.5)', marginBottom: 8}}>プロンプト</div>
        <div style={{fontSize: 13, lineHeight: 1.5, marginBottom: 16}}>
          Elena Bloom sitting at a late-night café, coding on a laptop, warm amber lighting, cinematic composition. No text or letters in the image.
        </div>

        <div style={{fontSize: 10, fontFamily: 'JetBrains Mono', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'rgba(255,255,255,0.5)', marginBottom: 8}}>パラメータ</div>
        <div style={{fontFamily: 'JetBrains Mono', fontSize: 11, lineHeight: 1.7, color: 'rgba(255,255,255,0.85)', marginBottom: 16}}>
          <div>model: gpt-image-2</div>
          <div>size: 1024×1024</div>
          <div>quality: high</div>
          <div>format: PNG</div>
          <div>n: 4 (this is #2)</div>
          <div>background: auto</div>
          <div>thinking: off</div>
        </div>

        <div style={{fontSize: 10, fontFamily: 'JetBrains Mono', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'rgba(255,255,255,0.5)', marginBottom: 8}}>参照画像</div>
        <div style={{display: 'flex', gap: 6, marginBottom: 16}}>
          <div className="mf-img-gen mf-img-gen-3" style={{width: 50, height: 50, borderRadius: 4}}></div>
        </div>

        <div style={{fontSize: 10, fontFamily: 'JetBrains Mono', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'rgba(255,255,255,0.5)', marginBottom: 8}}>メトリクス</div>
        <div style={{fontFamily: 'JetBrains Mono', fontSize: 11, lineHeight: 1.7, color: 'rgba(255,255,255,0.85)', marginBottom: 16}}>
          <div>生成時間: 18.4s</div>
          <div>コスト: $0.211</div>
          <div>response_id: rsp_3a8f2k9d</div>
        </div>

        <hr style={{border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '16px 0'}}/>

        <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
          <button className="mf-btn" style={{background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)', color: 'white', justifyContent: 'flex-start'}}><MFIco.brush/> マスクで編集</button>
          <button className="mf-btn" style={{background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)', color: 'white', justifyContent: 'flex-start'}}><MFIco.image/> これを参照に</button>
          <button className="mf-btn" style={{background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)', color: 'white', justifyContent: 'flex-start'}}><MFIco.refresh/> 同パラメータで再生成</button>
          <button className="mf-btn" style={{background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)', color: 'white', justifyContent: 'flex-start'}}><MFIco.copy/> プロンプトをコピー</button>
        </div>
      </div>
    </div>

    {/* dot indicator */}
    <div style={{padding: 12, display: 'flex', justifyContent: 'center', gap: 6}}>
      {[1,2,3,4].map(i => (
        <div key={i} style={{width: i === 2 ? 24 : 8, height: 8, borderRadius: 4, background: i === 2 ? 'white' : 'rgba(255,255,255,0.3)', transition: 'all 0.2s'}}></div>
      ))}
    </div>
  </div>
);

// =========================================================
// B-5. エラー状態 (toast / inline / blocking)
// =========================================================
const ErrorStates = () => (
  <div className="mf" style={{width: 1280, height: 800, padding: 32, overflow: 'auto', background: 'var(--mf-bg-canvas)'}}>
    <div style={{maxWidth: 1100, margin: '0 auto'}}>
      <div className="mf-h1" style={{fontSize: 22, marginBottom: 4}}>エラー・警告状態</div>
      <div className="mf-small" style={{marginBottom: 28}}>API側の制約・コンテンツモデレーション・組織認証など各種エラーの表示パターン</div>

      {/* RGBA warning — inline */}
      <div className="mf-card" style={{padding: 20, marginBottom: 16, borderColor: 'var(--mf-warn)'}}>
        <div className="mf-label" style={{color: 'var(--mf-warn)', marginBottom: 8}}>📁 ① 軽度警告 — 自動修正可能</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
          <div className="mf-img-gen mf-img-gen-3" style={{width: 80, height: 80, borderRadius: 6, flexShrink: 0}}></div>
          <div style={{flex: 1}}>
            <div className="mf-h3" style={{marginBottom: 4}}>透過PNG (RGBA) を検出しました</div>
            <div className="mf-small" style={{marginBottom: 8}}>elena_ref.png は透過チャンネル付きです。APIエラーを回避するため、白背景でRGB変換します。</div>
            <div style={{display: 'flex', gap: 6}}>
              <button className="mf-btn mf-btn--primary" style={{fontSize: 12, padding: '4px 10px'}}>自動変換する</button>
              <button className="mf-btn" style={{fontSize: 12, padding: '4px 10px'}}>このまま使う</button>
              <button className="mf-btn mf-btn--ghost" style={{fontSize: 12, padding: '4px 10px'}}>削除</button>
            </div>
          </div>
        </div>
      </div>

      {/* Prompt too long — inline */}
      <div className="mf-card" style={{padding: 20, marginBottom: 16, borderColor: '#dc2626'}}>
        <div className="mf-label" style={{color: '#dc2626', marginBottom: 8}}>⚠ ② 入力エラー — 修正が必要</div>
        <div className="mf-h3" style={{marginBottom: 8}}>プロンプトが長すぎます</div>
        <textarea className="mf-textarea" rows={3} defaultValue="（URL本文1042字…）The OpenAI API lets you generate and edit images from text prompts using GPT Image models, including our latest, gpt-image-2. You can access image generation capabilities through two APIs..." style={{borderColor: '#dc2626', boxShadow: '0 0 0 3px rgba(220,38,38,0.08)', marginBottom: 8}}></textarea>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{color: '#dc2626', fontSize: 12}}>1042 / 4000字 (制限超過まで残り少なめ)</div>
          <div style={{display: 'flex', gap: 6}}>
            <button className="mf-btn" style={{fontSize: 12, padding: '4px 10px'}}><MFIco.spark/> AIで要約</button>
            <button className="mf-btn" style={{fontSize: 12, padding: '4px 10px'}}>クリア</button>
          </div>
        </div>
      </div>

      {/* Content moderation — blocking */}
      <div className="mf-card" style={{padding: 20, marginBottom: 16, background: '#fef2f2', borderColor: '#dc2626'}}>
        <div className="mf-label" style={{color: '#dc2626', marginBottom: 8}}>🚫 ③ コンテンツモデレーション — 生成不可</div>
        <div className="mf-h3" style={{marginBottom: 8}}>このプロンプトは生成できません</div>
        <div className="mf-text" style={{marginBottom: 12}}>
          ポリシーに違反する可能性のある表現が含まれています。プロンプトを書き換えてもう一度お試しください。
        </div>
        <div style={{padding: 10, background: 'white', borderRadius: 6, fontFamily: 'JetBrains Mono', fontSize: 11, color: 'var(--mf-ink-soft)', marginBottom: 12}}>
          error: content_policy_violation<br/>
          message: "Your request was rejected as a result of our safety system."
        </div>
        <div style={{display: 'flex', gap: 6}}>
          <button className="mf-btn mf-btn--primary">プロンプトを編集</button>
          <button className="mf-btn">ヘルプを見る</button>
          <button className="mf-btn mf-btn--ghost"><span style={{fontSize: 12}}>moderation = "low" に切替</span></button>
        </div>
      </div>

      {/* Organization not verified — blocking modal style */}
      <div className="mf-card" style={{padding: 20, marginBottom: 16, background: 'var(--mf-accent-soft)', borderColor: 'var(--mf-accent)'}}>
        <div className="mf-label" style={{color: 'var(--mf-accent)', marginBottom: 8}}>🔐 ④ 組織認証が未完了</div>
        <div className="mf-h3" style={{marginBottom: 8}}>GPT Imageモデルの利用には組織認証が必要です</div>
        <div className="mf-text" style={{marginBottom: 12}}>
          OpenAIデベロッパーコンソールで「API Organization Verification」を完了してください。
          認証完了後、自動で利用可能になります。
        </div>
        <div style={{display: 'flex', gap: 6}}>
          <button className="mf-btn mf-btn--primary">コンソールを開く ↗</button>
          <button className="mf-btn">ステータスを再確認</button>
        </div>
      </div>

      {/* API failure — toast example */}
      <div className="mf-card" style={{padding: 20, marginBottom: 16}}>
        <div className="mf-label" style={{marginBottom: 8}}>🔔 ⑤ トースト通知 (右上にフェードイン)</div>
        <div style={{display: 'flex', justifyContent: 'flex-end'}}>
          <div style={{width: 360, background: 'var(--mf-ink)', color: 'white', padding: 14, borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 10, boxShadow: '0 8px 24px rgba(0,0,0,0.15)'}}>
            <span style={{fontSize: 16}}>⚠</span>
            <div style={{flex: 1}}>
              <div style={{fontWeight: 600, fontSize: 13, marginBottom: 2}}>生成に失敗しました</div>
              <div style={{fontSize: 12, color: 'rgba(255,255,255,0.7)', marginBottom: 8}}>レート制限に達しました。30秒後に自動リトライします。</div>
              <div style={{display: 'flex', gap: 6}}>
                <button style={{background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', padding: '4px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer'}}>今すぐリトライ</button>
                <button style={{background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.6)', padding: '4px 10px', fontSize: 11, cursor: 'pointer'}}>閉じる</button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
);

window.StreamingState = StreamingState;
window.RefUploadedState = RefUploadedState;
window.MaskEditMode = MaskEditMode;
window.LightboxView = LightboxView;
window.ErrorStates = ErrorStates;
