/* global React, Ico, PromptBox, Placeholder, Section, Row, ParamGroup, CostEstimate */

// ============ WIREFRAME 1: Classic Sidebar (params left, big canvas) ============
const Wireframe1 = () => (
  <div className="wf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    {/* top bar */}
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1.5px solid var(--line)'}}>
      <Row gap={12}>
        <div className="wf-h2">⌬ Image Studio</div>
        <span className="wf-mono" style={{color: 'var(--ink-faint)'}}>gpt-image-2</span>
      </Row>
      <Row gap={8}>
        <span className="wf-chip"><Ico.history/> 履歴</span>
        <span className="wf-chip"><Ico.grid/> ギャラリー</span>
        <span className="wf-chip"><Ico.cog/> 設定</span>
      </Row>
    </div>

    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      {/* left sidebar — params */}
      <div style={{width: 320, padding: 16, borderRight: '1.5px solid var(--line)', overflow: 'auto', background: 'var(--paper)'}}>
        <Section title="① モード">
          <Row gap={4}>
            <span className="wf-chip wf-chip-active"><Ico.spark/> 生成</span>
            <span className="wf-chip"><Ico.image/> 参照</span>
            <span className="wf-chip"><Ico.brush/> 編集</span>
          </Row>
        </Section>
        <hr className="wf-divider"/>
        <ParamGroup/>
        <hr className="wf-divider"/>
        <CostEstimate/>
      </div>

      {/* main canvas */}
      <div style={{flex: 1, padding: 24, display: 'flex', flexDirection: 'column', gap: 16, background: 'var(--paper)'}}>
        {/* empty canvas */}
        <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'}}>
          <div className="wf-box-dashed" style={{width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderWidth: '2px'}}>
            <div style={{textAlign: 'center'}}>
              <svg width="80" height="80" viewBox="0 0 80 80" style={{margin: '0 auto 12px', display: 'block'}}>
                <rect x="10" y="14" width="60" height="50" stroke="#1a1a1a" strokeWidth="1.5" fill="none" rx="3"/>
                <circle cx="26" cy="32" r="5" stroke="#1a1a1a" strokeWidth="1.5" fill="none"/>
                <path d="M14 60l16-16 12 10 18-18 6 6" stroke="#1a1a1a" strokeWidth="1.5" fill="none"/>
              </svg>
              <div className="wf-h2" style={{marginBottom: 6}}>まだ画像がありません</div>
              <div className="wf-small" style={{maxWidth: 320, margin: '0 auto'}}>下のプロンプト欄に作りたい画像を書いて、<br/>「生成」を押してください</div>
              <div style={{marginTop: 16}}>
                <span className="wf-annotation">↓ プロンプト欄から始める</span>
              </div>
            </div>
          </div>

          {/* annotations floating around */}
          <div style={{position: 'absolute', top: 8, right: 8}}>
            <span className="wf-stamp">empty state</span>
          </div>
        </div>

        {/* prompt area at bottom */}
        <div className="wf-box-rough" style={{padding: 12}}>
          <Row style={{justifyContent: 'space-between', marginBottom: 6}}>
            <span className="wf-label">プロンプト</span>
            <Row gap={6}>
              <span className="wf-chip" style={{fontSize: 10}}>📝 テンプレ</span>
              <span className="wf-chip" style={{fontSize: 10}}><Ico.spark/> 改善</span>
            </Row>
          </Row>
          <PromptBox placeholder="例: 夜カフェでノートPCを開いている女性、暖色のあかり、シネマティックな構図…" lines={3}/>
          <Row style={{justifyContent: 'space-between', marginTop: 10}}>
            <Row gap={6}>
              <span className="wf-chip"><Ico.upload/> 参照画像 (最大10)</span>
              <span className="wf-chip"><Ico.brush/> マスクで編集</span>
            </Row>
            <button className="wf-btn wf-btn-accent"><Ico.spark/> 生成する</button>
          </Row>
        </div>
      </div>
    </div>
    <div style={{position: 'absolute', top: 8, right: 16}}>
      <span className="wf-annotation" style={{fontSize: 12}}>※ 参照記事「GPT Image 2 API実践ガイド」を反映</span>
    </div>
  </div>
);

// ============ WIREFRAME 2: Two-Pane Form-First ============
const Wireframe2 = () => (
  <div className="wf" style={{width: 1280, height: 800, display: 'flex', flexDirection: 'column'}}>
    <div style={{padding: '12px 20px', borderBottom: '1.5px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
      <Row gap={10}>
        <div className="wf-h1">画像をつくる</div>
        <span className="wf-mono" style={{color: 'var(--ink-faint)'}}>powered by gpt-image-2</span>
      </Row>
      <Row gap={8}>
        <span className="wf-chip"><Ico.history/> 最近</span>
        <span className="wf-chip"><Ico.grid/> ギャラリー</span>
      </Row>
    </div>

    <div style={{display: 'flex', flex: 1, minHeight: 0}}>
      {/* left: form */}
      <div style={{width: 540, padding: 24, borderRight: '1.5px solid var(--line)', overflow: 'auto'}}>
        <div style={{marginBottom: 18}}>
          <div className="wf-label" style={{marginBottom: 6}}>1. なにを作りますか？</div>
          <div className="wf-tabs" style={{marginBottom: 0}}>
            <span className="wf-tab wf-tab-active"><Ico.spark/> テキストから</span>
            <span className="wf-tab"><Ico.image/> 参照画像から</span>
            <span className="wf-tab"><Ico.brush/> 既存画像を編集</span>
          </div>
        </div>

        <Section title="2. プロンプト">
          <PromptBox placeholder="ここに作りたい画像の説明を書く…" lines={5}/>
          <Row gap={6} style={{marginTop: 8, flexWrap: 'wrap'}}>
            <span className="wf-chip">📝 ブログカバー</span>
            <span className="wf-chip">📝 SNSアイコン</span>
            <span className="wf-chip">📝 商品モックアップ</span>
            <span className="wf-chip">+ 追加</span>
          </Row>
        </Section>

        <Section title="3. 参照画像 (任意・最大10枚)">
          <Row gap={8}>
            <Placeholder height={70} style={{flex: 1}}>+ 参照1</Placeholder>
            <Placeholder height={70} style={{flex: 1}}>+ 参照2</Placeholder>
            <Placeholder height={70} style={{flex: 1}}>+ 参照3</Placeholder>
          </Row>
          <div className="wf-small" style={{marginTop: 4}}>※ RGBAは自動でRGB変換されます</div>
        </Section>

        <hr className="wf-divider"/>

        <details open>
          <summary className="wf-label" style={{cursor: 'pointer', marginBottom: 10}}>4. 詳細パラメータ ▾</summary>
          <ParamGroup compact/>
        </details>

        <hr className="wf-divider"/>
        <Row style={{justifyContent: 'space-between'}}>
          <CostEstimate compact/>
          <button className="wf-btn wf-btn-accent" style={{fontSize: 16, padding: '10px 20px'}}><Ico.spark/> 画像を生成</button>
        </Row>
      </div>

      {/* right: preview */}
      <div style={{flex: 1, padding: 24, background: 'var(--paper-warm)', display: 'flex', flexDirection: 'column'}}>
        <Row style={{justifyContent: 'space-between', marginBottom: 12}}>
          <span className="wf-label">プレビュー</span>
          <span className="wf-stamp">empty</span>
        </Row>
        <div className="wf-box-dashed" style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 40}}>
          <div>
            <div style={{fontSize: 60, lineHeight: 1, marginBottom: 16, fontFamily: 'Caveat, cursive', color: 'var(--ink-faint)'}}>?</div>
            <div className="wf-h2">プロンプトを書くと<br/>ここに画像が出ます</div>
            <div className="wf-small" style={{marginTop: 8}}>左のフォームに沿って入力してください</div>
            <div style={{marginTop: 24}}>
              <span className="wf-annotation">「テンプレ」から始めてもOK</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

window.Wireframe1 = Wireframe1;
window.Wireframe2 = Wireframe2;
