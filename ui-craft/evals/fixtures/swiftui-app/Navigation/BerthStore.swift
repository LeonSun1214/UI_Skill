import SwiftUI

struct Berth: Identifiable, Hashable {
    let id: String
    let name: String
    let length: Int
    let price: Int
}

@Observable
final class BerthStore {
    var berths: [Berth] = [
        Berth(id: "a1", name: "A1 · Visitor pontoon", length: 12, price: 38),
        Berth(id: "b4", name: "B4 · Inner basin", length: 15, price: 52),
        Berth(id: "c9", name: "C9 · Fuel dock", length: 9, price: 29),
    ]
}
