import SwiftUI

@main
struct HarborApp: App {
    @State private var store = BerthStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
        }
    }
}
