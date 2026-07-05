import SwiftData
import SwiftUI

/// 設定（学習・表示・ことだま・接続先）。値は端末保持。
struct SettingsView: View {
    @AppStorage("daily_goal") private var dailyGoal = 20
    @AppStorage("srs_enabled") private var srsEnabled = true
    @AppStorage("vertical_text") private var verticalText = true
    @AppStorage("show_furigana") private var showFurigana = true
    @AppStorage("dark_mode") private var darkMode = false
    @AppStorage("mascot_messages") private var mascotMessages = true
    @AppStorage("character_voice") private var characterVoice = false
    @AppStorage("bgm_enabled") private var bgmEnabled = true
    @AppStorage("bgm_volume") private var bgmVolume = 0.15
    @AppStorage("api_base_url") private var apiBaseURL = KobunAPIService.defaultBaseURL

    @Query private var progress: [WordProgress]
    @State private var draftBaseURL = ""
    @State private var healthText = "未確認"

    private var masteredCount: Int { progress.filter { $0.status == .mastered }.count }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    HStack(spacing: 13) {
                        KotodamaView(size: 50)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("学びの記録").font(KBFont.mincho(17))
                            Text("覚えた \(masteredCount)語")
                                .font(KBFont.gothic(12)).foregroundStyle(Color.kbTextMuted)
                        }
                    }
                }

                Section("学習") {
                    Stepper("1日の目標語数：\(dailyGoal)語", value: $dailyGoal, in: 5...100, step: 5)
                    Toggle("SRS（間隔反復）で出題", isOn: $srsEnabled)
                }

                Section("表示") {
                    Toggle("例文を縦書きで表示", isOn: $verticalText)
                    Toggle("ふりがなを表示", isOn: $showFurigana)
                    Toggle("ダークモード（夜の勉強）", isOn: $darkMode)
                }

                Section("ことだま") {
                    Toggle("応援メッセージ", isOn: $mascotMessages)
                    Toggle("キャラクターボイス", isOn: $characterVoice)
                }

                Section("サウンド") {
                    Toggle("BGMを鳴らす", isOn: $bgmEnabled)
                    if bgmEnabled {
                        HStack(spacing: 12) {
                            Image(systemName: "speaker.fill")
                                .foregroundStyle(Color.kbTextMuted)
                            Slider(value: $bgmVolume, in: 0...1)
                                .tint(.kbPrimary)
                            Image(systemName: "speaker.wave.3.fill")
                                .foregroundStyle(Color.kbTextMuted)
                        }
                    }
                }

                Section {
                    TextField("API ベース URL", text: $draftBaseURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .font(KBFont.gothic(13))
                    Button("接続先を保存して確認") { Task { await applyAndCheck() } }
                    HStack {
                        Text("接続状態")
                        Spacer()
                        Text(healthText).foregroundStyle(Color.kbTextMuted)
                    }
                } header: {
                    Text("接続先")
                } footer: {
                    Text("既定: \(KobunAPIService.defaultBaseURL)\nローカル開発時は http://localhost:8006 を指定。")
                }

                Section {
                    HStack {
                        Text("このアプリについて")
                        Spacer()
                        Text("ver 1.0.0").foregroundStyle(Color.kbTextMuted)
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.kbBackground)
            .navigationTitle("設定")
            .onAppear { draftBaseURL = apiBaseURL }
        }
    }

    private func applyAndCheck() async {
        let trimmed = draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        apiBaseURL = trimmed
        await KobunAPIService.shared.setBaseURL(trimmed)
        do {
            let health = try await KobunAPIService.shared.health()
            healthText = "OK（単語\(health.words)・慣用句\(health.idioms)）"
        } catch {
            healthText = (error as? LocalizedError)?.errorDescription ?? "接続できません"
        }
    }
}
