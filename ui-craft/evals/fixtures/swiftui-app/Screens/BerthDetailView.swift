import SwiftUI

struct BerthDetailView: View {
    let id: String
    @Environment(BerthStore.self) private var store

    var body: some View {
        let berth = store.berths.first { $0.id == id } ?? store.berths[0]
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                Text(berth.name)
                    .font(.title2.bold())
                // A fixed size: it stays 13 points when the user raises their text size.
                Text("Up to \(berth.length) m · shore power · water")
                    .font(.system(size: 13))
                // The muted grey from the asset catalog: 2.5:1 on white, and no dark variant.
                Text("€\(berth.price) a night")
                    .foregroundStyle(Color("Muted"))
                // A tap on a stack: VoiceOver does not call it a button.
                HStack {
                    Image(systemName: "phone")
                    Text("Call the harbour master")
                }
                .onTapGesture { }
                NavigationLink(value: Route.booking(id: berth.id)) {
                    Text("Book this berth")
                }
                .buttonStyle(.borderedProminent)
                .tint(Color("Brand"))
            }
            .padding(16)
        }
        .navigationTitle("Berth")
    }
}
