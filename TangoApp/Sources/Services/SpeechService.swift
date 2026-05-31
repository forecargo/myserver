import AVFoundation
import Foundation

// AVSpeechSynthesizer の薄いラッパ。
// 重要: phonetic (IPA) は読み上げない。AVSpeechSynthesizer は IPA を音素として解釈せず
//      記号を文字通り読むため意味不明な音になる (SPEC_SwiftUI.md §9 / §17)。

@MainActor
final class SpeechService: NSObject {
    static let shared = SpeechService()

    private let synthesizer = AVSpeechSynthesizer()

    var rate: Float = 0.45              // 0.30 - 0.60 推奨

    private override init() {
        super.init()
    }

    func speak(_ text: String, language: String = "en-US") {
        guard !text.isEmpty else { return }
        synthesizer.stopSpeaking(at: .immediate)
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = Self.preferredVoice(for: language)
        utterance.rate = clamp(rate, lower: 0.20, upper: 0.65)
        synthesizer.speak(utterance)
    }

    func speakWord(_ item: APIVocabularyItem) {
        speak(item.word)
    }

    func speakExample(_ ex: APIExampleSentence) {
        speak(ex.en)
    }

    func speakAll(_ item: APIVocabularyItem) {
        synthesizer.stopSpeaking(at: .immediate)
        enqueue(item.word)
        for ex in item.examples {
            enqueue(ex.en)
        }
    }

    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
    }

    // MARK: - 内部

    private func enqueue(_ text: String, language: String = "en-US") {
        guard !text.isEmpty else { return }
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = Self.preferredVoice(for: language)
        utterance.rate = clamp(rate, lower: 0.20, upper: 0.65)
        synthesizer.speak(utterance)
    }

    private static func preferredVoice(for language: String) -> AVSpeechSynthesisVoice? {
        // Enhanced voice を優先、未インストール時はデフォルトへフォールバック。
        let candidates = [
            "com.apple.voice.enhanced.en-US.Samantha",
            "com.apple.voice.premium.en-US.Ava",
        ]
        for id in candidates {
            if let v = AVSpeechSynthesisVoice(identifier: id) {
                return v
            }
        }
        return AVSpeechSynthesisVoice(language: language)
    }

    private func clamp(_ v: Float, lower: Float, upper: Float) -> Float {
        max(lower, min(upper, v))
    }
}
