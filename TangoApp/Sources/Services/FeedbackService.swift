import AVFoundation
import UIKit

// クイズの正誤フィードバック (合成サウンド + Haptic)。
// 標準システムサウンドだと「ピロピロリン」「ブー」が再現できないため、
// AVAudioPlayer + 動的に生成した PCM WAV データを再生する。

@MainActor
final class FeedbackService {
    static let shared = FeedbackService()

    private let notification = UINotificationFeedbackGenerator()
    private var activePlayers: [AVAudioPlayer] = []

    private init() {
        // AudioSession は App.swift で `.playback` カテゴリで初期化されている。
    }

    func playCorrect() {
        // ピロピロリン: C5 → E5 → G5 → C6 の上昇メロディ
        let melody: [Tone] = [
            Tone(frequency: 523.25, duration: 0.09),   // C5
            Tone(frequency: 659.25, duration: 0.09),   // E5
            Tone(frequency: 783.99, duration: 0.09),   // G5
            Tone(frequency: 1046.5, duration: 0.20),   // C6
        ]
        let data = WaveSynth.makeMelody(tones: melody, waveform: .sine)
        play(data: data)
        notification.notificationOccurred(.success)
    }

    func playWrong() {
        // ブー: 低音の方形波 (ブザー風) 0.45 秒
        let data = WaveSynth.makeMelody(
            tones: [Tone(frequency: 130.81, duration: 0.45)],  // C3
            waveform: .square
        )
        play(data: data)
        notification.notificationOccurred(.error)
    }

    func prepare() {
        notification.prepare()
    }

    // MARK: - 内部

    private func play(data: Data) {
        do {
            let player = try AVAudioPlayer(data: data)
            player.prepareToPlay()
            player.play()
            activePlayers.append(player)
            // 終了済みプレイヤを定期掃除
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
                self?.activePlayers.removeAll { !$0.isPlaying }
            }
        } catch {
            // フォールバックは何もしない (Haptic は別経路で動作している)
        }
    }
}

// MARK: - 波形合成

struct Tone {
    let frequency: Double  // Hz
    let duration: Double   // 秒
}

enum Waveform {
    case sine
    case square
}

enum WaveSynth {
    static let sampleRate: Double = 44100

    static func makeMelody(tones: [Tone], waveform: Waveform) -> Data {
        var samples: [Int16] = []
        samples.reserveCapacity(tones.reduce(0) { $0 + Int(sampleRate * $1.duration) })
        for tone in tones {
            samples.append(contentsOf: renderTone(tone, waveform: waveform))
        }
        return wavData(samples: samples)
    }

    private static func renderTone(_ tone: Tone, waveform: Waveform) -> [Int16] {
        let count = Int(sampleRate * tone.duration)
        var out: [Int16] = []
        out.reserveCapacity(count)
        let twoPi = 2.0 * .pi

        for i in 0..<count {
            let t = Double(i) / sampleRate
            let phase = twoPi * tone.frequency * t

            let raw: Double
            switch waveform {
            case .sine:
                raw = sin(phase)
            case .square:
                // 純粋方形波は耳障りなので 1 次フィルタ的に丸める
                let s = sin(phase)
                raw = s >= 0 ? min(s * 4, 1.0) : max(s * 4, -1.0)
            }

            // ADSR 風包絡 (アタック 5ms / リリース 30ms、間は緩やかな減衰)
            let attack = 0.005
            let release = 0.03
            let envelope: Double
            if t < attack {
                envelope = t / attack
            } else if t > tone.duration - release {
                envelope = max(0, (tone.duration - t) / release)
            } else {
                // メロディ用にはほぼ平坦、ブザー用にも一定
                envelope = (waveform == .sine)
                    ? exp(-1.5 * (t - attack) / max(tone.duration - attack, 0.001))
                    : 1.0
            }

            let amp = raw * envelope * 0.6  // -6dB
            out.append(Int16(amp * Double(Int16.max)))
        }
        return out
    }

    // MARK: - WAV ヘッダ生成

    private static func wavData(samples: [Int16]) -> Data {
        var data = Data()
        let dataSize = samples.count * MemoryLayout<Int16>.size
        let fileSize = 36 + dataSize
        let rate = UInt32(sampleRate)

        data.append(contentsOf: [0x52, 0x49, 0x46, 0x46])               // "RIFF"
        data.append(contentsOf: le32(UInt32(fileSize)))
        data.append(contentsOf: [0x57, 0x41, 0x56, 0x45])               // "WAVE"

        data.append(contentsOf: [0x66, 0x6D, 0x74, 0x20])               // "fmt "
        data.append(contentsOf: le32(16))                               // PCM chunk size
        data.append(contentsOf: le16(1))                                // format = PCM
        data.append(contentsOf: le16(1))                                // mono
        data.append(contentsOf: le32(rate))                             // sample rate
        data.append(contentsOf: le32(rate * 2))                         // byte rate
        data.append(contentsOf: le16(2))                                // block align
        data.append(contentsOf: le16(16))                               // bits/sample

        data.append(contentsOf: [0x64, 0x61, 0x74, 0x61])               // "data"
        data.append(contentsOf: le32(UInt32(dataSize)))
        for s in samples {
            data.append(contentsOf: le16(UInt16(bitPattern: s)))
        }
        return data
    }

    private static func le16(_ v: UInt16) -> [UInt8] {
        [UInt8(v & 0xFF), UInt8((v >> 8) & 0xFF)]
    }
    private static func le32(_ v: UInt32) -> [UInt8] {
        [
            UInt8(v & 0xFF),
            UInt8((v >> 8) & 0xFF),
            UInt8((v >> 16) & 0xFF),
            UInt8((v >> 24) & 0xFF),
        ]
    }
}
