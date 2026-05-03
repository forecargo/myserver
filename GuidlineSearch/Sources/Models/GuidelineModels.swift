import Foundation

struct SearchRequest: Encodable {
    let query: String
    let top_k: Int
}

struct SearchResponse: Decodable {
    let results: [SearchResult]
    let query: String
    let total_chunks: Int
}

struct SearchResult: Decodable, Identifiable, Hashable {
    var id: String { section_id + requirement_type + title }
    let section_id: String
    let title: String
    let text: String
    let snippet: String
    let similarity_score: Double
    let requirement_type: String
    let breadcrumb: String
    let footnotes: [Footnote]

    var requirementKind: RequirementKind {
        switch requirement_type {
        case "basic":     return .basic
        case "desirable": return .desirable
        default:          return .general
        }
    }
}

struct Footnote: Decodable, Hashable {
    let ref: String
    let text: String
}

enum RequirementKind {
    case basic, desirable, general
}
