import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            Tab("Berths", systemImage: "ferry") {
                BerthsView()
            }
            Tab("Bookings", systemImage: "calendar") {
                BookingsView()
            }
            Tab("Account", systemImage: "person.crop.circle") {
                AccountView()
            }
        }
    }
}

#Preview {
    RootView()
        .environment(BerthStore())
}
