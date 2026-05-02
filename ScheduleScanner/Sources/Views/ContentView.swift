import SwiftUI

struct ContentView: View {
    @EnvironmentObject var vm: ScheduleViewModel
    @State private var capturedImage: UIImage?

    var body: some View {
        ZStack {
            NavigationStack {
                Group {
                    switch vm.phase {
                    case .idle, .cropping:
                        idleView
                    case .uploading:
                        progressView(message: "AIが解析中…")
                    case .reviewing(let items):
                        ScheduleListView(items: items)
                    case .saving:
                        progressView(message: "カレンダーに保存中…")
                    case .done(let count):
                        doneView(count: count)
                    case .error(let message):
                        errorView(message: message)
                    }
                }
                .navigationTitle("スケジュールスキャナー")
                .sheet(isPresented: $vm.showCamera, onDismiss: {
                    if let image = capturedImage {
                        capturedImage = nil
                        vm.startCropping(image)
                    }
                }) {
                    CameraPickerView(selectedImage: $capturedImage)
                        .ignoresSafeArea()
                }
            }

            if case .cropping(let img) = vm.phase {
                CropView(image: img, onCrop: { cropped in
                    vm.uploadImage(cropped)
                }, onCancel: {
                    vm.cancelCrop()
                })
                .ignoresSafeArea()
            }
        }
    }

    private func progressView(message: String) -> some View {
        VStack(spacing: 16) {
            ProgressView()
                .progressViewStyle(.circular)
                .scaleEffect(1.5)
            Text(message)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var idleView: some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: "camera.viewfinder")
                .font(.system(size: 80))
                .foregroundStyle(.blue)
            Text("グループウェアの\nスケジュール画面を撮影してください")
                .font(.title3)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button {
                vm.showCamera = true
            } label: {
                Label("カメラを起動", systemImage: "camera")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal, 40)
            Spacer()
        }
        .padding()
    }

    private func doneView(count: Int) -> some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 72))
                .foregroundStyle(.green)
            Text("\(count)件の予定を\nカレンダーに登録しました")
                .font(.title2)
                .multilineTextAlignment(.center)
            Button("最初に戻る") { vm.reset() }
                .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }

    private func errorView(message: String) -> some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 72))
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button("やり直す") { vm.reset() }
                .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }
}
