# ScheduleScanner — 構造ドキュメント

Xcode 向けの iOS アプリ。グループウェアのスケジュール画面を撮影し、OCR API で解析して iOS カレンダーへ登録する。

## 全体フロー

```
カメラ撮影 → トリミング → OCR API (POST /schedule) → 予定一覧確認 → カレンダー保存
```

## ディレクトリ構成

```
ScheduleScanner/
├── project.yml                       # XcodeGen スペック
├── ScheduleScanner.xcodeproj         # Xcode プロジェクト (xcodegen 生成)
├── ScheduleScanner.entitlements
└── Sources/
    ├── App.swift                     # @main エントリポイント
    ├── Models/
    │   └── ScheduleModels.swift      # データモデル
    ├── Services/
    │   ├── APIService.swift          # HTTP クライアント (OCR API)
    │   └── CalendarService.swift     # EventKit ラッパー
    ├── ViewModels/
    │   └── ScheduleViewModel.swift   # 状態機械 (AppPhase)
    └── Views/
        ├── ContentView.swift         # ルートビュー (phase スイッチ)
        ├── CameraPickerView.swift    # UIImagePickerController ラッパー
        ├── CropView.swift            # 4 コーナードラッグでトリミング
        ├── ScheduleListView.swift    # 解析結果一覧・選択
        └── ScheduleRowView.swift     # 1 予定の行表示
```

## 主要コンポーネント

### project.yml (XcodeGen)
- プラットフォーム: iOS 16.0+
- Bundle ID: `com.example.ScheduleScanner`
- 権限: `NSCameraUsageDescription`, `NSCalendarsUsageDescription`, `NSCalendarsWriteOnlyAccessUsageDescription`
- `.xcodeproj` 再生成: `cd ScheduleScanner && xcodegen generate`

### App.swift
- `ScheduleScannerApp` が `ScheduleViewModel` を `environmentObject` として注入

### Models/ScheduleModels.swift

| 型 | 役割 |
|---|---|
| `ScheduleResponse` | API レスポンスのルート (`{ "schedules": [...] }`) |
| `ScheduleItem` | 1 件の予定。`Decodable` + `Identifiable` |

`ScheduleItem` フィールド:
- `date` (yyyy/MM/dd), `dayOfWeek`, `startTime`, `endTime` (HH:mm)
- `category`, `title`, `location`, `reserver`
- `startDate()` / `endDate()` で `Date` 変換

### Services/APIService.swift

- `actor APIService` (シングルトン `shared`)
- エンドポイント: `https://forecargo.ngrok.app/schedule`
- `uploadImage(_ image: UIImage) async throws -> [ScheduleItem]`
  - JPEG (品質 0.85) を `multipart/form-data` で POST
  - レスポンスを `ScheduleResponse` にデコード
- エラー型: `APIError` (invalidImage / networkError / httpError / decodingError)

### Services/CalendarService.swift

- `actor CalendarService` (シングルトン `shared`)
- `requestAccess()`: iOS 17+ は `requestWriteOnlyAccessToEvents`、それ以前は `requestAccess(to:)`
- `save(_ items: [ScheduleItem])`: `EKEvent` を生成してデフォルトカレンダーへ保存
  - `notes` に category と reserver を記録
- エラー型: `CalendarError` (denied / saveFailed)

### ViewModels/ScheduleViewModel.swift

状態機械 `AppPhase`:

```
idle
 → cropping(UIImage)   # CropView 表示中
 → uploading           # API 通信中
 → reviewing([ScheduleItem])  # 確認画面
 → saving              # カレンダー書き込み中
 → done(Int)           # 登録完了 (件数)
 → error(String)       # エラーメッセージ
```

`@MainActor final class ScheduleViewModel: ObservableObject`

主要メソッド:
- `startCropping(_ image:)` / `cancelCrop()`
- `uploadImage(_ image:)` → APIService を呼び出し phase 遷移
- `saveSelected(_ items:)` → CalendarService を呼び出し phase 遷移
- `reset()` → idle に戻す

### Views/ContentView.swift

- `vm.phase` を `switch` して子 View を切り替えるルートビュー
- カメラシートは `vm.showCamera` で制御
- トリミングは `fullScreenCover` で `CropView` を表示

### Views/CameraPickerView.swift

- `UIViewControllerRepresentable` で `UIImagePickerController` をラップ
- 実機カメラが使えない場合はフォトライブラリにフォールバック

### Views/CropView.swift

- 4 コーナーに `CropHandle` (ドラッグ可能な白丸) を配置
- `Canvas` + `compositingGroup` でクロップ外領域を暗くするオーバーレイ
- `performCrop()` でピクセル座標に変換し `CGImage.cropping(to:)` を実行
- `UIImage.normalizedToUpOrientation()` で向き正規化

### Views/ScheduleListView.swift

- `List` を `.active` EditMode で表示し複数選択可能
- ツールバーに「選択した予定を登録 (N 件)」ボタン

### Views/ScheduleRowView.swift

- タイトル、日付・時刻、場所 (mappin アイコン)、カテゴリバッジ、予約者を縦に並べる

## 依存関係

| フレームワーク | 用途 |
|---|---|
| SwiftUI | UI 全般 |
| UIKit | UIImagePickerController, UIImage 操作 |
| EventKit | カレンダーへのイベント保存 |
| Foundation | HTTP 通信, JSONDecoder |

## API 仕様 (クライアント側から見た仕様)

- `POST https://forecargo.ngrok.app/schedule`
- Content-Type: `multipart/form-data`
- フィールド名: `file` (JPEG)
- レスポンス:
  ```json
  {
    "schedules": [
      {
        "date": "2024/04/01",
        "day_of_week": "月",
        "start_time": "09:00",
        "end_time": "10:00",
        "category": "会議",
        "title": "朝会",
        "location": "会議室A",
        "reserver": "山田太郎"
      }
    ]
  }
  ```
