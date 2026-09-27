import SwiftUI

struct FiltersView: View {
    @State private var minLength = 10
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Picker("Minimum length", selection: $minLength) {
                    ForEach([8, 10, 12, 15], id: \.self) { Text("\($0) m") }
                }
            }
            .navigationTitle("Filters")
            .toolbar {
                Button("Done") { dismiss() }
            }
        }
    }
}
