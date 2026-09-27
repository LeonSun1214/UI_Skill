import SwiftUI

struct AccountView: View {
    @AppStorage("notifyArrivals") private var notifyArrivals = true

    var body: some View {
        NavigationStack {
            Form {
                Section("Notifications") {
                    Toggle("Arrival reminders", isOn: $notifyArrivals)
                }
            }
            .navigationTitle("Account")
        }
    }
}
