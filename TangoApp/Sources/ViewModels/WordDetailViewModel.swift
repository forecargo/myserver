import Foundation
import Observation
import SwiftData

@MainActor
@Observable
final class WordDetailViewModel {
    let domain: DomainWord

    var progress: WordProgress?
    var autoSpeakOnAppear: Bool = false

    init(domain: DomainWord) {
        self.domain = domain
    }

    var key: String { domain.id }
    var item: APIVocabularyItem { domain.item }

    func onAppear(context: ModelContext) {
        // 進捗の加算のみ。自動発音は View 側の `.task(id:)` で遅延させる。
        let p = fetchOrCreate(context: context)
        p.viewCount += 1
        p.lastViewedAt = .now
        try? context.save()
        self.progress = p
    }

    func toggleFavorite(context: ModelContext) {
        let p = fetchOrCreate(context: context)
        p.isFavorite.toggle()
        try? context.save()
        self.progress = p
    }

    func toggleLearned(context: ModelContext) {
        let p = fetchOrCreate(context: context)
        p.isLearned.toggle()
        try? context.save()
        self.progress = p
    }

    func speakWord() {
        SpeechService.shared.speakWord(item)
    }

    func speakExample(_ ex: APIExampleSentence) {
        SpeechService.shared.speakExample(ex)
    }

    func speakAll() {
        SpeechService.shared.speakAll(item)
    }

    // MARK: - 内部

    private func fetchOrCreate(context: ModelContext) -> WordProgress {
        let key = domain.id
        let descriptor = FetchDescriptor<WordProgress>(
            predicate: #Predicate { $0.key == key }
        )
        if let existing = try? context.fetch(descriptor).first {
            return existing
        }
        let new = WordProgress(
            key: key,
            batch: domain.batch,
            stem: domain.stem,
            wordId: item.id,
            wordSnapshot: item.word,
            phoneticSnapshot: item.phonetic
        )
        context.insert(new)
        return new
    }
}
