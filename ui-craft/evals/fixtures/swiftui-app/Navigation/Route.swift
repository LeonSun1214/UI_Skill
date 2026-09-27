import SwiftUI

/// Every screen that is pushed onto a stack, by value.
enum Route: Hashable {
    case berth(id: String)
    case booking(id: String)
    case receipt(id: String)
}

extension View {
    /// The one place that says which screen each route shows.
    func withRoutes() -> some View {
        navigationDestination(for: Route.self) { route in
            switch route {
            case .berth(let id):
                BerthDetailView(id: id)
            case .booking(let id):
                BookingDetailView(id: id)
            case .receipt(let id):
                ReceiptView(id: id)
            }
        }
    }
}
