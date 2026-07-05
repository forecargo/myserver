import SwiftData
import SwiftUI

/// ホーム / ダッシュボード（達成リング・メニュー導線）。
struct HomeView: View {
    @AppStorage("daily_goal") private var dailyGoal = 20
    @Query private var logs: [DailyStudyLog]
    @Query private var progress: [WordProgress]

    private var todayCount: Int {
        logs.first { $0.dayKey == DayKey.today }?.learnedCount ?? 0
    }

    private var progressRatio: Double {
        dailyGoal > 0 ? min(Double(todayCount) / Double(dailyGoal), 1) : 0
    }

    private var dueCount: Int {
        progress.filter { ($0.dueDate ?? .distantFuture) <= .now }.count
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: Spacing.l) {
                    Text("ホーム").font(KBFont.mincho(18))

                    ZStack {
                        ProgressRing(progress: progressRatio).frame(width: 200, height: 200)
                        KotodamaView(size: 104)
                    }
                    .padding(.top, Spacing.s)

                    VStack(spacing: 2) {
                        Text("\(Int(progressRatio * 100))%")
                            .font(KBFont.mincho(30))
                            .foregroundStyle(Color.kbPrimaryDeep)
                        Text("今日の達成度 · \(todayCount) / \(dailyGoal) 語")
                            .font(KBFont.gothic(12))
                            .foregroundStyle(Color.kbTextMuted)
                    }

                    VStack(spacing: Spacing.m) {
                        NavigationLink {
                            FlashcardView()
                        } label: {
                            HomeMenuRow(title: "暗記カードをめくる", subtitle: "カードでイメージ暗記",
                                        systemImage: "rectangle.on.rectangle", filled: true, badge: nil)
                        }
                        NavigationLink {
                            QuizView()
                        } label: {
                            HomeMenuRow(title: "クイズに挑戦", subtitle: "4択 · 全10問",
                                        systemImage: "magnifyingglass", filled: false, badge: nil)
                        }
                        NavigationLink {
                            ReviewView()
                        } label: {
                            HomeMenuRow(title: "復習する", subtitle: "そろそろ忘れる頃",
                                        systemImage: "arrow.triangle.2.circlepath", filled: false,
                                        badge: dueCount > 0 ? "\(dueCount)" : nil)
                        }
                    }
                    .buttonStyle(.plain)
                }
                .padding(Spacing.l)
            }
            .background(Color.kbBackground)
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
