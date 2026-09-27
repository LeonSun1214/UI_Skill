import SwiftUI

struct BerthRow: View {
    let berth: Berth

    var body: some View {
        HStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color("Brand"))
                .frame(width: 36, height: 36)
            VStack(alignment: .leading, spacing: 4) {
                // A custom face at a fixed size: no relativeTo, so it does not scale.
                Text(berth.name)
                    .font(.custom("Avenir Next", size: 17))
                Text("\(berth.length) m")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
}
