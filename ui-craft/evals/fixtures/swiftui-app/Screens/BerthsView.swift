import SwiftUI

struct BerthsView: View {
    @Environment(BerthStore.self) private var store
    @State private var query = ""
    @State private var showFilters = false

    var body: some View {
        NavigationStack {
            List(store.berths) { berth in
                NavigationLink(value: Route.berth(id: berth.id)) {
                    BerthRow(berth: berth)
                }
            }
            .navigationTitle("Berths")
            .searchable(text: $query)
            .withRoutes()
            .toolbar {
                // An icon-only button with no accessibilityLabel: VoiceOver reads the symbol's name.
                Button {
                    showFilters = true
                } label: {
                    Image(systemName: "line.3.horizontal.decrease.circle")
                }
            }
            .sheet(isPresented: $showFilters) {
                FiltersView()
            }
        }
    }
}

#Preview {
    BerthsView()
        .environment(BerthStore())
}
