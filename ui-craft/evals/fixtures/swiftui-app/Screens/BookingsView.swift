import SwiftUI

struct BookingsView: View {
    var body: some View {
        NavigationStack {
            List {
                NavigationLink(value: Route.booking(id: "b4")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("B4 · Inner basin")
                            .font(.headline)
                        Text("12–14 June · 2 nights")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Bookings")
            .withRoutes()
        }
    }
}
