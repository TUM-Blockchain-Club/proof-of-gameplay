import SwiftUI

struct ContentView: View {
    @StateObject private var cameraViewModel = CameraViewModel()

    var body: some View {
        ZStack {
            Color.black
                .ignoresSafeArea()
            
            if let previewLayer = cameraViewModel.previewLayer {
                CameraPreviewView(previewLayer: previewLayer)
                    .edgesIgnoringSafeArea(.all)
            } else {
                ProgressView()
            }
            
            VStack {
                Spacer()
                
                // Shutter Button
                Button(action: {
                    cameraViewModel.toggleRecording()
                }) {
                    Circle()
                        .fill(cameraViewModel.isRecording ? Color.red : Color.white)
                        .frame(width: 70, height: 70)
                        .overlay(
                            Circle()
                                .stroke(Color.gray, lineWidth: 4)
                        )
                }
                .padding(.bottom, 20)
                
                // Delete and Upload Buttons
                if cameraViewModel.showPostRecordingOptions {
                    HStack(spacing: 40) {
                        // Delete Button
                        Button(action: {
                            cameraViewModel.discardRecording()
                        }) {
                            Image(systemName: "trash")
                                .foregroundColor(.white)
                                .font(.largeTitle)
                        }
                        
                        // Upload Button
                        Button(action: {
                            cameraViewModel.showCodeInput = true
                        }) {
                            Image(systemName: "arrow.up.circle")
                                .foregroundColor(.white)
                                .font(.largeTitle)
                        }
                    }
                    .padding(.bottom, 20)
                }
            }
        }
        .sheet(isPresented: $cameraViewModel.showCodeInput) {
            CodeInputView { code in
                cameraViewModel.uploadVideo(with: code)
            }
        }
    }
}
