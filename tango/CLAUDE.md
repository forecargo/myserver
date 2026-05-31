# tango — 単語帳抽出ツール

紙の単語帳スキャン画像から学習用 JSON データを抽出する CLI + 確認 UI。
**仕様は [SPEC.md](./SPEC.md) を参照する** こと。本ファイルは運用規約のみ記載する。

***

## 仮想環境

- `.venv/` を使用 (uv venv 作成、Python 3.13)
- 依存: `requirements.txt` (本番) / `requirements-dev.txt` (pytest 含む)
- 実行は `.venv/bin/python <script>` 形式 (絶対パス想定)

```bash
uv venv .venv
uv pip install -r requirements-dev.txt
```

## 環境変数

- API キー (`GEMINI_API_KEY`) はプロジェクトルート `/Users/nobuhiro/Python/myserver/.env` を共用する
- `tango/.env` は作らない (`config.py` が親ディレクトリの `.env` を直接ロード)
- `tango/.env.template` は記入例の参照ドキュメントとして追跡する

## 触らないディレクトリ

| パス | 用途 |
| --- | --- |
| `sample_jpg/` | テスト基準データ (pytest が依存) |
| `output/` | テスト回帰用の JSON 基準データ (pytest が依存) |
| `template_layoute.json` | SPEC §3 のスキーマ契約サンプル |

## 主要コマンド

```bash
# バッチ抽出 (画像が右 90° 回転している場合)
.venv/bin/python main.py -i scans/part1 -o data/part1 --rotate 90

# 既存 JSON は --overwrite を付けない限りスキップ (レジューム可)

# 確認 UI 起動 → http://127.0.0.1:8765/
.venv/bin/python viewer.py

# テスト
.venv/bin/python -m pytest tests/ -q
```

## Git 管理方針

- `scans/` は著作物 (紙の単語帳) のため `.gitignore` で除外
- `data/` は git 管理 (抽出結果の履歴を残す)
- `.env.template` は親リポジトリの `.env.*` ルールを `!.env.template` で救済済み

## モデル/プロンプト変更時の影響

- `models.py` のスキーマ変更は iOS アプリ側との契約変更にあたるため**要相談**
- `extractor.py` の `SYSTEM_INSTRUCTION` 変更後は、最低 `sample_jpg/` の 3 枚で抽出傾向を確認してから本番バッチへ展開する
