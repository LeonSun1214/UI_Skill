import SwiftUI

struct ReceiptView: View {
    let id: String

    var body: some View {
        VStack(spacing: 8) {
            Text("Paid")
                .font(.largeTitle)
            Text("Booking \(id)")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(24)
        .navigationTitle("Receipt")
    }
}
