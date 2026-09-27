// swift-tools-version: 5.9

// An app playground (open it in Xcode or Swift Playgrounds): the app is the package's one target.
import PackageDescription
import AppleProductTypes

let package = Package(
    name: "Harbor",
    platforms: [
        .iOS("17.0")
    ],
    products: [
        .iOSApplication(
            name: "Harbor",
            targets: ["AppModule"],
            bundleIdentifier: "com.example.harbor",
            teamIdentifier: "",
            displayVersion: "1.0",
            bundleVersion: "1",
            appIcon: .placeholder(icon: .boat),
            accentColor: .asset("AccentColor"),
            supportedDeviceFamilies: [.pad, .phone],
            supportedInterfaceOrientations: [.portrait, .landscapeRight, .landscapeLeft]
        )
    ],
    targets: [
        .executableTarget(name: "AppModule", path: ".")
    ]
)
