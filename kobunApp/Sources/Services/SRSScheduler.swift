import Foundation

/// 間隔反復（SM-2 簡易版）。復習の出題間隔を端末側で管理する。
enum SRSScheduler {
    private static let day: TimeInterval = 86_400

    /// 復習結果を反映して次回出題日を更新する。
    static func apply(remembered: Bool, to p: WordProgress, now: Date = .now) {
        if remembered {
            p.correctStreak += 1
            p.intervalDays = p.intervalDays == 0 ? 1 : max(1, Int(Double(p.intervalDays) * p.ease))
            p.ease = min(p.ease + 0.1, 3.0)
            p.status = p.correctStreak >= 3 ? .mastered : .learning
        } else {
            p.correctStreak = 0
            p.intervalDays = 0
            p.ease = max(p.ease - 0.2, 1.3)
            p.status = .learning
        }
        p.lastReviewedAt = now
        // interval 0 のときは当日（すぐ復習）に設定。
        p.dueDate = now.addingTimeInterval(Double(p.intervalDays) * day)
    }

    /// 復習の忘却度カテゴリ。
    enum Bucket {
        case soon     // もうすぐ忘れる（期限切れ）
        case check    // そろそろ確認（2日以内）
        case relaxed  // まだ余裕

        static func of(_ p: WordProgress, now: Date = .now) -> Bucket {
            guard let due = p.dueDate else { return .relaxed }
            if due <= now { return .soon }
            if due <= now.addingTimeInterval(2 * day) { return .check }
            return .relaxed
        }
    }
}
