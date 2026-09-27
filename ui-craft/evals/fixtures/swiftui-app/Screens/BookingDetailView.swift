import SwiftUI

struct BookingDetailView: View {
    let id: String

    var body: some View {
        Form {
            LabeledContent("Berth", value: "B4 · Inner basin")
            LabeledContent("Nights", value: "2")
            NavigationLink(value: Route.receipt(id: id)) {
                Text("Receipt")
            }
        }
        .navigationTitle("Booking")
    }
}
