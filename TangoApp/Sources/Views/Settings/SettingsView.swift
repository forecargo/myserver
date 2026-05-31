import SwiftUI
import SwiftData

struct SettingsView: View {
    @State private var vm = SettingsViewModel()
    @Environment(\.modelContext) private var modelContext
    @AppStorage("tts_autoplay") private var ttsAutoplay: Bool = false
    @AppStorage("tts_rate") private var ttsRate: Double = 0.45

    enum ActiveAlert: Identifiable {
        case saved, clearFav, clearHist, clearQuiz, clearCache, cacheCleared
        var id: Int { hashValue }
    }
    @State private var activeAlert: ActiveAlert?

    var body: some View {
        @Bindable var vmBindable = vm

        Form {
            apiSection(vm: vmBindable)
            ttsSection
            dataClearSection
            versionSection
        }
        .navigationTitle("設定")
        .alert(item: $activeAlert, content: alertFor)
        .onAppear {
            SpeechService.shared.rate = Float(ttsRate)
        }
    }

    // MARK: - セクション

    @ViewBuilder
    private func apiSection(vm: SettingsViewModel) -> some View {
        @Bindable var vmBindable = vm
        Section("API 接続") {
            TextField("ベース URL", text: $vmBindable.draftBaseURL)
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            if let err = vm.urlValidationError {
                Text(err).font(.caption).foregroundStyle(.red)
            }
            Button("保存") {
                Task {
                    if await vm.saveBaseURL() {
                        activeAlert = .saved
                    }
                }
            }
        }
    }

    private var ttsSection: some View {
        Section("音声") {
            Toggle("詳細画面を開いたら自動再生", isOn: $ttsAutoplay)
            VStack(alignment: .leading) {
                Text("発話速度: \(String(format: "%.2f", ttsRate))")
                    .font(.caption)
                Slider(value: $ttsRate, in: 0.30...0.60, step: 0.05) {
                    Text("速度")
                }
                .onChange(of: ttsRate) { _, newValue in
                    SpeechService.shared.rate = Float(newValue)
                }
            }
        }
    }

    private var dataClearSection: some View {
        Section("データクリア") {
            Button("お気に入りを解除") { activeAlert = .clearFav }
                .foregroundStyle(.orange)
            Button("学習履歴をリセット") { activeAlert = .clearHist }
                .foregroundStyle(.orange)
            Button("クイズ履歴を削除") { activeAlert = .clearQuiz }
                .foregroundStyle(.red)
            Button("単語データのキャッシュをクリア") { activeAlert = .clearCache }
                .foregroundStyle(.blue)
        }
    }

    private var versionSection: some View {
        Section("バージョン") {
            HStack {
                Text("バージョン")
                Spacer()
                Text(appVersion)
                    .foregroundStyle(Color.taOnSurfaceVariant)
            }
        }
    }

    // MARK: - Alert

    private func alertFor(_ kind: ActiveAlert) -> Alert {
        switch kind {
        case .saved:
            return Alert(title: Text("保存しました"))
        case .clearFav:
            return Alert(
                title: Text("お気に入りをすべて解除しますか？"),
                primaryButton: .destructive(Text("解除する")) {
                    vm.clearFavorites(context: modelContext)
                },
                secondaryButton: .cancel(Text("キャンセル"))
            )
        case .clearHist:
            return Alert(
                title: Text("学習履歴をすべてリセットしますか？"),
                primaryButton: .destructive(Text("リセットする")) {
                    vm.clearHistory(context: modelContext)
                },
                secondaryButton: .cancel(Text("キャンセル"))
            )
        case .clearQuiz:
            return Alert(
                title: Text("クイズ履歴をすべて削除しますか？"),
                primaryButton: .destructive(Text("削除する")) {
                    vm.clearQuizHistory(context: modelContext)
                },
                secondaryButton: .cancel(Text("キャンセル"))
            )
        case .clearCache:
            return Alert(
                title: Text("単語データのキャッシュをクリアしますか？"),
                message: Text("次回 API から再取得されます。お気に入り・学習履歴は影響しません。"),
                primaryButton: .destructive(Text("クリアする")) {
                    Task {
                        await TangoAPIService.shared.clearAllCache()
                        activeAlert = .cacheCleared
                    }
                },
                secondaryButton: .cancel(Text("キャンセル"))
            )
        case .cacheCleared:
            return Alert(title: Text("キャッシュをクリアしました"))
        }
    }

    private var appVersion: String {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        let b = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        return "\(v) (\(b))"
    }
}
