import SwiftUI

struct SearchBarView: View {
    @Binding var text: String
    var onSubmit: () -> Void

    var body: some View {
        HStack(spacing: Spacing.sm) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(Color.glOnSurfaceVariant)
                .font(.system(size: 17))

            TextField("ガイドラインを検索…", text: $text)
                .font(.system(size: 16))
                .foregroundStyle(Color.glOnSurface)
                .submitLabel(.search)
                .onSubmit(onSubmit)
                .autocorrectionDisabled()

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(Color.glOutline)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, Spacing.md)
        .padding(.vertical, 10)
        .background(Color.glSurface)
        .overlay(
            RoundedRectangle(cornerRadius: Radius.md)
                .stroke(Color.glOutlineVariant, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: Radius.md))
    }
}
