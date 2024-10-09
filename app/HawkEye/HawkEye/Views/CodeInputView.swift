import SwiftUI

struct CodeInputView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var code: String = ""
    var onConfirm: (String) -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Enter 6-Digit Code")
                .font(.headline)
            
            TextField("Code", text: $code)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.center)
                .font(.largeTitle)
                .padding()
                .background(Color(.secondarySystemBackground))
                .cornerRadius(10)
                .padding(.horizontal, 40)
            
            Button(action: {
                if code.count == 6 {
                    onConfirm(code)
                    presentationMode.wrappedValue.dismiss()
                }
            }) {
                Text("Confirm")
                    .font(.headline)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(code.count == 6 ? Color.blue : Color.gray)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .padding(.horizontal, 40)
            }
            .disabled(code.count != 6)
        }
        .padding()
    }
}
