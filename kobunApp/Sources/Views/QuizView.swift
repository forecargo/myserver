import SwiftData
import SwiftUI

/// クイズ（4 択・古語→意味）。採点は answer_index で端末側。
struct QuizView: View {
    @Environment(\.modelContext) private var context
    @Query private var allProgress: [WordProgress]

    @State private var questions: [QuizQuestion] = []
    @State private var wrongQuestions: [QuizQuestion] = []   // 結果画面の「間違えた語」一覧
    @State private var index = 0
    @State private var selected: Int?
    @State private var correctPop = false   // 正解のスケール演出トリガ
    @State private var celebrate = false    // 正解バッジ（✨正解！）の表示
    @State private var loading = false
    @State private var errorMessage: String?

    private let choiceLabels = ["ア", "イ", "ウ", "エ", "オ", "カ"]
    private let quizCount = 10
    private let poolCount = 30        // 多めに取得して 3連続正解の語を間引く
    private let masteryStreak = 3     // 3連続正解で「習得」扱い（出題を後回しに）

    var body: some View {
        ZStack {
            Color.kbBackground.ignoresSafeArea()
            if loading {
                ProgressView()
            } else if let errorMessage {
                VStack(spacing: Spacing.s) {
                    Text(errorMessage).font(KBFont.gothic(13)).foregroundStyle(Color.kbTextMuted)
                    Button("再読み込み") { Task { await load() } }
                }
            } else if index < questions.count {
                quizBody(questions[index])
            } else if !questions.isEmpty {
                resultView
            }

            if celebrate { celebrationBadge }
        }
        .navigationTitle("クイズ")
        .navigationBarTitleDisplayMode(.inline)
        // 回答時に正解＝success・誤答＝error のハプティクス
        .sensoryFeedback(trigger: selected) { _, newValue in
            guard let newValue, index < questions.count else { return nil }
            return newValue == questions[index].answer_index ? .success : .error
        }
        .task { await load() }
    }

    private func quizBody(_ q: QuizQuestion) -> some View {
        VStack(spacing: Spacing.l) {
            ProgressView(value: Double(index + 1), total: Double(questions.count))
                .tint(.kbPrimary)
                .padding(.horizontal, Spacing.l)

            VStack(spacing: 4) {
                KotodamaView(size: 56)
                Text("次の古語の意味は？").font(KBFont.gothic(12)).foregroundStyle(Color.kbTextMuted)
                Text(q.prompt.headword).font(KBFont.mincho(44))
            }

            VStack(spacing: 11) {
                ForEach(Array(q.choices.enumerated()), id: \.offset) { i, choice in
                    choiceRow(q: q, i: i, choice: choice)
                }
            }
            .padding(.horizontal, Spacing.l)

            Spacer()

            if selected != nil {
                Button(action: next) {
                    Text(index + 1 < questions.count ? "次の問題 ▸" : "結果を見る ▸")
                        .font(KBFont.gothic(15, weight: .bold))
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity).padding(.vertical, 15)
                        .background(Color.kbPrimaryGradient, in: RoundedRectangle(cornerRadius: Radius.m))
                }
                .buttonStyle(.plain)
                .padding(.horizontal, Spacing.l)
                .padding(.bottom, Spacing.l)
            }
        }
        .padding(.top, Spacing.l)
    }

    private func choiceRow(q: QuizQuestion, i: Int, choice: QuizChoice) -> some View {
        let isAnswer = i == q.answer_index
        let answered = selected != nil
        let isCorrect = answered && isAnswer            // 正解（回答後に強調）
        let isWrongPick = answered && selected == i && !isAnswer  // 自分が選んだ外れ
        let answeredWrong = answered && selected != q.answer_index  // 回答が不正解だった

        // 正解は濃い緑のベタ塗り＋白文字でハッキリ、外れは赤系、それ以外は通常面。
        let bg: Color = isCorrect ? .kbCorrectFill
            : (isWrongPick ? Color.kbAccent.opacity(0.16) : Color.kbSurface)
        let border: Color = isCorrect ? .kbCorrectFill
            : (isWrongPick ? .kbAccentSoft : .kbBorder)
        let glossColor: Color = isCorrect ? .white : Color.kbText
        let labelFg: Color = isCorrect ? .kbCorrectFill : (isWrongPick ? .white : Color.kbTextSub)
        let labelBg: Color = isCorrect ? .white : (isWrongPick ? Color.kbAccentSoft : Color.kbBorder)

        return Button {
            if selected == nil { select(i, q: q) }
        } label: {
            HStack(spacing: 12) {
                Text(choiceLabels[safe: i] ?? "?")
                    .font(KBFont.gothic(13, weight: .bold))
                    .foregroundStyle(labelFg)
                    .frame(width: 26, height: 26)
                    .background(labelBg, in: Circle())
                Text(choice.gloss)
                    .font(KBFont.mincho(16, weight: isCorrect ? .bold : .regular))
                    .foregroundStyle(glossColor)
                    .multilineTextAlignment(.leading)
                Spacer()
                if isCorrect {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(.white)
                        .symbolEffect(.bounce, value: correctPop)
                } else if isWrongPick {
                    Image(systemName: "xmark.circle.fill").foregroundStyle(Color.kbAccent)
                }
            }
            .padding(15)
            .background(bg, in: RoundedRectangle(cornerRadius: Radius.m))
            .overlay(RoundedRectangle(cornerRadius: Radius.m).stroke(border, lineWidth: isCorrect ? 2 : 1.5))
            // 正解はポップ＋緑グロー、不正解時は正解以外の選択肢を縮める
            .scaleEffect(isCorrect ? (correctPop ? 1.0 : 0.85) : (answeredWrong ? 0.82 : 1))
            .opacity(answeredWrong && !isCorrect ? 0.6 : 1)
            .shadow(color: isCorrect && correctPop ? Color.kbCorrectFill.opacity(0.5) : .clear,
                    radius: isCorrect && correctPop ? 16 : 0, y: 5)
        }
        .buttonStyle(.plain)
        // .disabled だと無効化ボタン全体が減光され色あせるため、当たり判定だけ無効化する
        .allowsHitTesting(!answered)
    }

    /// 正解時に中央へポップする「✨正解！」バッジ（自動で消える）。
    private var celebrationBadge: some View {
        VStack(spacing: 6) {
            Image(systemName: "sparkles")
                .font(.system(size: 46))
                .foregroundStyle(Color.kbGold)
                .symbolEffect(.bounce, value: celebrate)
            Text("正解！")
                .font(KBFont.mincho(30))
                .foregroundStyle(Color.kbCorrectFill)
        }
        .padding(.horizontal, 30).padding(.vertical, 20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: Radius.l))
        .overlay(RoundedRectangle(cornerRadius: Radius.l).stroke(Color.kbCorrectFill.opacity(0.45), lineWidth: 2))
        .shadow(color: Color.kbCorrectFill.opacity(0.3), radius: 18, y: 8)
        .scaleEffect(celebrate ? 1 : 0.5)
        .transition(.scale.combined(with: .opacity))
        .allowsHitTesting(false)
    }

    private var resultView: some View {
        let correct = correctCount
        return ScrollView {
            VStack(spacing: Spacing.m) {
                KotodamaView(size: 96)
                KotodamaBubble(text: correct == questions.count ? "全問正解！すごい！" : "おつかれさま。よくがんばったね")
                Text("\(correct) / \(questions.count) 正解")
                    .font(KBFont.mincho(28)).foregroundStyle(Color.kbPrimaryDeep)
                Button("もう一度") { Task { await load() } }
                    .font(KBFont.gothic(14, weight: .bold)).foregroundStyle(Color.kbPrimaryDeep)

                if !wrongQuestions.isEmpty { wrongList }
            }
            .padding(Spacing.l)
        }
    }

    /// 結果画面の「間違えた語」一覧。タップで詳細（誤答語をスワイプで見直せる）へ。
    private var wrongList: some View {
        VStack(alignment: .leading, spacing: Spacing.s) {
            Text("間違えた語（復習に追加しました）")
                .font(KBFont.gothic(13, weight: .bold)).foregroundStyle(Color.kbTextSub)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, Spacing.s)

            VStack(spacing: 0) {
                ForEach(Array(wrongQuestions.enumerated()), id: \.element.id) { i, q in
                    NavigationLink {
                        WordPagerView(items: wrongItems, startEntryNo: q.entry_no)
                    } label: {
                        HStack(spacing: 12) {
                            Text(q.entry_no)
                                .font(KBFont.mincho(13)).foregroundStyle(Color.kbAccent)
                                .frame(width: 30)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(q.prompt.headword).font(KBFont.mincho(18))
                                if let r = q.prompt.reading {
                                    Text(r).font(KBFont.gothic(11)).foregroundStyle(Color.kbTextMuted)
                                }
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption).foregroundStyle(Color.kbTextMuted)
                        }
                        .padding(.vertical, 10).padding(.horizontal, 14)
                    }
                    .buttonStyle(.plain)
                    if i < wrongQuestions.count - 1 { Divider() }
                }
            }
            .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.l))
            .overlay(RoundedRectangle(cornerRadius: Radius.l).stroke(Color.kbBorder))
        }
    }

    /// 誤答語をスワイプ閲覧するための WordListItem スタブ（本文は詳細取得で補完）。
    private var wrongItems: [WordListItem] {
        wrongQuestions.map {
            WordListItem(entry_no: $0.entry_no, section: "", pos_category: $0.pos_category,
                         headword: $0.prompt.headword, reading: $0.prompt.reading,
                         image_url: nil, short_gloss: "")
        }
    }

    @State private var correctCount = 0

    private func select(_ i: Int, q: QuizQuestion) {
        let isCorrect = i == q.answer_index
        SFXPlayer.shared.play(isCorrect ? "good" : "bad")   // 正解=good / 不正解=bad
        if isCorrect { correctCount += 1 }
        context.insert(QuizAttempt(questionKey: q.entry_no, isCorrect: isCorrect))

        // 正誤を SRS に反映（誤答は当日復習・正答は間隔を伸ばす）。誤答は結果一覧へ。
        let p = ProgressStore.progress(for: q.entry_no, in: context)
        SRSScheduler.apply(remembered: isCorrect, to: p)
        if !isCorrect { wrongQuestions.append(q) }

        // 回答確定。不正解時は正解以外が縮むのをアニメーションさせる
        correctPop = false
        celebrate = false
        withAnimation(.spring(response: 0.32, dampingFraction: 0.6)) { selected = i }

        // 正解の行は（正解・不正解どちらでも）一旦 0.85 → バネ拡大でポップさせ目立たせる
        DispatchQueue.main.async {
            withAnimation(.spring(response: 0.34, dampingFraction: 0.38)) { correctPop = true }
            if isCorrect {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.5)) { celebrate = true }
            }
        }
        // 正解バッジは少し見せてから自動で消す
        guard isCorrect else { return }
        Task {
            try? await Task.sleep(nanoseconds: 1_300_000_000)
            withAnimation(.easeIn(duration: 0.3)) { celebrate = false }
        }
    }

    private func next() {
        selected = nil
        correctPop = false
        celebrate = false
        index += 1
    }

    private func load() async {
        loading = true
        errorMessage = nil
        index = 0
        selected = nil
        correctPop = false
        celebrate = false
        correctCount = 0
        wrongQuestions = []
        do {
            // 多めに取得し、3連続正解の語を後回しにして最大 quizCount 問を選ぶ
            let pool = try await KobunAPIService.shared.quiz(count: poolCount, choices: 4).questions
            questions = pickQuestions(from: pool)
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "読み込みに失敗しました。"
        }
        loading = false
    }

    /// 3連続正解（correctStreak >= masteryStreak）の語を後回しにして出題を選ぶ。
    /// 未習得を優先し、足りなければ習得済みで補充して最大 quizCount 問にする。
    private func pickQuestions(from pool: [QuizQuestion]) -> [QuizQuestion] {
        // entry_no の重複を除く（順序維持）
        var seen = Set<String>()
        let unique = pool.filter { seen.insert($0.entry_no).inserted }

        let masteredKeys = Set(allProgress.filter { $0.correctStreak >= masteryStreak }.map(\.key))
        let fresh = unique.filter { !masteredKeys.contains($0.entry_no) }
        let stale = unique.filter { masteredKeys.contains($0.entry_no) }

        var picked = Array(fresh.prefix(quizCount))
        if picked.count < quizCount {
            picked += stale.prefix(quizCount - picked.count)
        }
        return picked
    }
}

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
