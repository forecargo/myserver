/* global React, MFIco, Annot, StateSpec, MFTopBar, MFLeftSidebar, MFPromptBar, MFResultTile */

// ============================================================
// Pattern 1: Equal Grid — シンプルに横並び (n枚を等寸で見せる)
// ============================================================
const PatternA1 = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      <MFLeftSidebar/>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)'}}>
        {/* run header */}
        <div style={{padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span className="mf-chip mf-chip--active" style={{background: 'var(--mf-success)', borderColor: 'var(--mf-success)'}}><MFIco.check/> 完了</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>4枚 · 1024×1024 · high · 18.4s · ~$0.84</span>
          </div>
          <div style={{display: 'flex', gap: 6}}>
            <button className="mf-btn"><MFIco.download/> すべてDL</button>
            <button className="mf-btn"><MFIco.copy/> プロンプトコピー</button>
            <button className="mf-btn"><MFIco.refresh/> 再生成</button>
          </div>
        </div>

        {/* equal 2x2 grid */}
        <div style={{flex: 1, padding: 24, display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: 16, minHeight: 0}}>
          <MFResultTile variant={1} meta="01"/>
          <MFResultTile variant={2} selected meta="02"/>
          <MFResultTile variant={3} meta="03"/>
          <MFResultTile variant={4} meta="04"/>
        </div>

        <MFPromptBar/>
      </div>
    </div>

    {/* spec callouts */}
    <div style={{position: 'absolute', top: 165, right: 30, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, lineHeight: 1.2, fontWeight: 700, textAlign: 'right'}}>
      hover で<br/>アクションが浮き上がる
    </div>
    <div style={{position: 'absolute', top: 535, left: 575, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, fontWeight: 700}}>
      ← 選択中 (枠ハイライト)
    </div>
  </div>
);

// ============================================================
// Pattern 2: Hero + Thumbnails — 1枚拡大、他はサムネイル
// ============================================================
const PatternA2 = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      <MFLeftSidebar/>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)'}}>
        <div style={{padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--mf-line)', background: 'var(--mf-bg)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span className="mf-h2">変種 02 / 04</span>
            <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>· seed: 7f3a2 · 1024×1024 high</span>
          </div>
          <div style={{display: 'flex', gap: 6}}>
            <button className="mf-btn"><MFIco.brush/> マスクで編集</button>
            <button className="mf-btn"><MFIco.image/> これを参照に</button>
            <button className="mf-btn"><MFIco.download/> DL</button>
            <button className="mf-btn">⋯</button>
          </div>
        </div>

        <div style={{flex: 1, display: 'flex', minHeight: 0}}>
          {/* hero */}
          <div style={{flex: 1, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <div style={{width: 540, position: 'relative'}}>
              <MFResultTile variant={2} selected/>
            </div>
          </div>

          {/* thumbnails column */}
          <div style={{width: 200, padding: '24px 16px 24px 0', display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto'}}>
            <div className="mf-label">同じrun (4枚)</div>
            <div style={{cursor: 'pointer'}}><MFResultTile variant={1} meta="01"/></div>
            <div style={{cursor: 'pointer'}}><MFResultTile variant={2} selected meta="02"/></div>
            <div style={{cursor: 'pointer'}}><MFResultTile variant={3} meta="03"/></div>
            <div style={{cursor: 'pointer'}}><MFResultTile variant={4} meta="04"/></div>

            <hr className="mf-divider"/>
            <div className="mf-label">前のrun</div>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6}}>
              <div className="mf-img-gen mf-img-gen-3" style={{aspectRatio: '1/1', borderRadius: 4, opacity: 0.7}}></div>
              <div className="mf-img-gen mf-img-gen-4" style={{aspectRatio: '1/1', borderRadius: 4, opacity: 0.7}}></div>
              <div className="mf-img-gen" style={{aspectRatio: '1/1', borderRadius: 4, opacity: 0.7}}></div>
              <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 4, opacity: 0.7}}></div>
            </div>
          </div>
        </div>

        <MFPromptBar/>
      </div>
    </div>

    {/* annotations */}
    <div style={{position: 'absolute', top: 130, left: 730, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, fontWeight: 700}}>
      ↑ 選んだ1枚を大きく見る
    </div>
    <div style={{position: 'absolute', top: 280, right: 24, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, fontWeight: 700, textAlign: 'right'}}>
      他のrunにも<br/>すぐアクセス
    </div>
  </div>
);

// ============================================================
// Pattern 3: Run Stage — ラン全体をカードに、メタ情報リッチ
// ============================================================
const PatternA3 = () => (
  <div className="mf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <MFTopBar/>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      <MFLeftSidebar/>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--mf-bg-canvas)', overflow: 'auto'}}>
        {/* Runs stack — newest first */}
        <div style={{padding: 20, display: 'flex', flexDirection: 'column', gap: 16}}>

          {/* Run 1 — current */}
          <div className="mf-card" style={{padding: 16}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12}}>
              <div style={{flex: 1, paddingRight: 16}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6}}>
                  <span className="mf-state-dot" style={{color: 'var(--mf-success)'}}>完了 · たった今</span>
                  <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>run_4f7a · 18.4s · $0.84</span>
                </div>
                <div className="mf-text" style={{lineHeight: 1.5, color: 'var(--mf-ink)'}}>
                  Elena Bloom sitting at a late-night café, coding on a laptop, warm amber lighting, cinematic composition. No text or letters in the image.
                </div>
                <div style={{marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap'}}>
                  <span className="mf-chip">1024×1024</span>
                  <span className="mf-chip">high</span>
                  <span className="mf-chip">n=4</span>
                  <span className="mf-chip">PNG</span>
                  <span className="mf-chip">参照: 1枚</span>
                </div>
              </div>
              <div style={{display: 'flex', gap: 6}}>
                <button className="mf-btn"><MFIco.refresh/> 再生成</button>
                <button className="mf-btn"><MFIco.copy/></button>
                <button className="mf-btn">⋯</button>
              </div>
            </div>

            <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12}}>
              <MFResultTile variant={1} meta="01"/>
              <MFResultTile variant={2} selected meta="02 ★"/>
              <MFResultTile variant={3} meta="03"/>
              <MFResultTile variant={4} meta="04"/>
            </div>
          </div>

          {/* Run 2 — older */}
          <div className="mf-card" style={{padding: 16, opacity: 0.85}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12}}>
              <div style={{flex: 1, paddingRight: 16}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4}}>
                  <span className="mf-mono" style={{color: 'var(--mf-ink-faint)'}}>run_3e1b · 5分前 · low draft · $0.024</span>
                </div>
                <div className="mf-small" style={{color: 'var(--mf-ink-soft)'}}>
                  Elena Bloom at a café, draft sketch
                </div>
              </div>
              <div style={{display: 'flex', gap: 6}}>
                <button className="mf-btn">展開</button>
              </div>
            </div>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12}}>
              <div className="mf-img-gen" style={{aspectRatio: '1/1', borderRadius: 6, opacity: 0.6}}></div>
              <div className="mf-img-gen mf-img-gen-3" style={{aspectRatio: '1/1', borderRadius: 6, opacity: 0.6}}></div>
              <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 6, opacity: 0.6}}></div>
              <div className="mf-img-gen mf-img-gen-4" style={{aspectRatio: '1/1', borderRadius: 6, opacity: 0.6}}></div>
            </div>
          </div>
        </div>

        <MFPromptBar/>
      </div>
    </div>

    <div style={{position: 'absolute', top: 95, left: 720, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, fontWeight: 700}}>
      ↑ 各run = プロンプト + 設定 + 結果のセット
    </div>
    <div style={{position: 'absolute', top: 460, left: 530, fontFamily: "'Caveat', cursive", color: 'var(--mf-accent)', fontSize: 14, fontWeight: 700}}>
      過去のrunも同じ場所に積み重なる
    </div>
  </div>
);

// ============================================================
// Component states spec — 詳細に
// ============================================================
const ComponentStates = () => (
  <div className="mf" style={{width: 1280, height: 800, padding: 32, overflow: 'auto'}}>
    <div style={{maxWidth: 1100, margin: '0 auto'}}>
      <div className="mf-h1" style={{fontSize: 22, marginBottom: 4}}>UIコンポーネントの振る舞い</div>
      <div className="mf-small" style={{marginBottom: 32}}>各コントロールの状態 (default / hover / active / focused / disabled) を明示</div>

      {/* Buttons */}
      <div style={{marginBottom: 32}}>
        <div className="mf-label" style={{marginBottom: 12}}>ボタン</div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, alignItems: 'center'}}>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>default</div>
            <button className="mf-btn mf-btn--accent mf-btn--lg"><MFIco.spark/> 生成する</button>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>hover</div>
            <button className="mf-btn mf-btn--accent mf-btn--lg" style={{background: '#e85a25', borderColor: '#e85a25', boxShadow: '0 2px 8px rgba(255,107,53,0.35)'}}><MFIco.spark/> 生成する</button>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>active (押下)</div>
            <button className="mf-btn mf-btn--accent mf-btn--lg" style={{background: '#c64d1d', borderColor: '#c64d1d', transform: 'translateY(1px)'}}><MFIco.spark/> 生成する</button>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>focused (キーボード)</div>
            <button className="mf-btn mf-btn--accent mf-btn--lg" style={{outline: '3px solid #ffd9c8', outlineOffset: 2}}><MFIco.spark/> 生成する</button>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>disabled (空プロンプト)</div>
            <button className="mf-btn mf-btn--accent mf-btn--lg mf-state-disabled"><MFIco.spark/> 生成する</button>
          </div>
        </div>
      </div>

      {/* Secondary buttons */}
      <div style={{marginBottom: 32}}>
        <div className="mf-label" style={{marginBottom: 12}}>セカンダリ・アイコンボタン</div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16}}>
          <div><div className="mf-small" style={{marginBottom: 6}}>default</div><button className="mf-btn"><MFIco.download/> ダウンロード</button></div>
          <div><div className="mf-small" style={{marginBottom: 6}}>hover</div><button className="mf-btn" style={{background: 'var(--mf-bg-alt)', borderColor: 'var(--mf-ink-faint)'}}><MFIco.download/> ダウンロード</button></div>
          <div><div className="mf-small" style={{marginBottom: 6}}>active</div><button className="mf-btn" style={{background: '#e8e6df'}}><MFIco.download/> ダウンロード</button></div>
          <div><div className="mf-small" style={{marginBottom: 6}}>focused</div><button className="mf-btn" style={{outline: '2px solid var(--mf-accent)', outlineOffset: 2}}><MFIco.download/> ダウンロード</button></div>
          <div><div className="mf-small" style={{marginBottom: 6}}>disabled</div><button className="mf-btn mf-state-disabled"><MFIco.download/> ダウンロード</button></div>
        </div>
      </div>

      {/* Chips / segmented */}
      <div style={{marginBottom: 32}}>
        <div className="mf-label" style={{marginBottom: 12}}>セグメント・チップ</div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, alignItems: 'center'}}>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>default</div>
            <span className="mf-chip">high</span>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>hover</div>
            <span className="mf-chip" style={{borderColor: 'var(--mf-ink-faint)', color: 'var(--mf-ink)'}}>high</span>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>selected (active)</div>
            <span className="mf-chip mf-chip--active">high</span>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>focused</div>
            <span className="mf-chip" style={{outline: '2px solid var(--mf-accent)', outlineOffset: 2}}>high</span>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>disabled (※非対応)</div>
            <span className="mf-chip mf-state-disabled" style={{textDecoration: 'line-through'}}>透過</span>
          </div>
        </div>
      </div>

      {/* Textarea */}
      <div style={{marginBottom: 32}}>
        <div className="mf-label" style={{marginBottom: 12}}>プロンプト入力</div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16}}>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>default · 空</div>
            <textarea className="mf-textarea" rows={3} placeholder="プロンプトを入力…"></textarea>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>focused · 入力中</div>
            <textarea className="mf-textarea" rows={3} defaultValue="夜のカフェでノートPCを開いて…" style={{borderColor: 'var(--mf-ink)', boxShadow: '0 0 0 3px rgba(0,0,0,0.06)'}}></textarea>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>error · 1000字超</div>
            <textarea className="mf-textarea" rows={3} defaultValue="(URL本文が貼り付けられた状態) 長すぎるプロンプトです..." style={{borderColor: '#dc2626', boxShadow: '0 0 0 3px rgba(220,38,38,0.1)'}}></textarea>
            <div style={{color: '#dc2626', fontSize: 11, marginTop: 4}}>⚠ 1042/4000字 — 要約してください</div>
          </div>
        </div>
      </div>

      {/* Result tile states */}
      <div style={{marginBottom: 16}}>
        <div className="mf-label" style={{marginBottom: 12}}>生成結果タイル</div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16}}>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>default</div>
            <div className="mf-img-gen" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>hover (アクション浮上)</div>
            <div style={{position: 'relative'}}>
              <div className="mf-img-gen mf-img-gen-2" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
              <div style={{position: 'absolute', bottom: 8, right: 8, display: 'flex', gap: 4}}>
                <button className="mf-icon-btn"><MFIco.download/></button>
                <button className="mf-icon-btn"><MFIco.copy/></button>
                <button className="mf-icon-btn"><MFIco.edit/></button>
              </div>
            </div>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>selected</div>
            <div style={{outline: '2px solid var(--mf-accent)', outlineOffset: 2, borderRadius: 8}}>
              <div className="mf-img-gen mf-img-gen-3" style={{aspectRatio: '1/1', borderRadius: 8}}></div>
            </div>
          </div>
          <div>
            <div className="mf-small" style={{marginBottom: 6}}>loading (partial_images)</div>
            <div className="mf-img-ph" style={{aspectRatio: '1/1', borderRadius: 8, position: 'relative'}}>
              <div style={{position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontFamily: 'JetBrains Mono, monospace', fontSize: 11}}>
                生成中… 64% (preview 1/2)
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
);

window.PatternA1 = PatternA1;
window.PatternA2 = PatternA2;
window.PatternA3 = PatternA3;
window.ComponentStates = ComponentStates;
