import SwiftUI

struct ContentView: View {
    private let chineseDate = ChineseDateHelper.getChineseDate()
    private let gregorianCN = ChineseDateHelper.formattedGregorianDate()
    private let gregorianEN = ChineseDateHelper.formattedGregorianDateEN()

    var body: some View {
        ZStack {
            // Background gradient — traditional Chinese red-to-gold
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(red: 0.6, green: 0.05, blue: 0.05),
                    Color(red: 0.75, green: 0.15, blue: 0.08),
                    Color(red: 0.85, green: 0.55, blue: 0.15)
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            // Horse watermark — SF Symbol
            Image(systemName: "figure.equestrian.sports")
                .font(.system(size: 200, weight: .thin))
                .foregroundColor(.white.opacity(0.15))
                .offset(x: 10, y: 30)

            // Main content
            VStack(spacing: 24) {
                // Header
                Text("中国农历")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.white.opacity(0.7))

                // Ganzhi year + Zodiac
                HStack(spacing: 8) {
                    Text(chineseDate.ganzhiYear)
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.white)
                    Text("【\(chineseDate.zodiacAnimal)年】")
                        .font(.system(size: 24, weight: .medium))
                        .foregroundColor(Color(red: 1.0, green: 0.85, blue: 0.35))
                }

                // Lunar month and day — large display
                Text("\(chineseDate.lunarMonthName) \(chineseDate.lunarDayName)")
                    .font(.system(size: 48, weight: .bold))
                    .foregroundColor(.white)

                Divider()
                    .frame(width: 200)
                    .background(Color.white.opacity(0.3))

                // Detail grid
                VStack(alignment: .leading, spacing: 12) {
                    detailRow(label: "天干", value: chineseDate.heavenlyStem)
                    detailRow(label: "地支", value: chineseDate.earthlyBranch)
                    detailRow(label: "生肖", value: chineseDate.zodiacAnimal)
                    detailRow(label: "农历日期",
                              value: "\(chineseDate.ganzhiYear) \(chineseDate.lunarMonthName)\(chineseDate.lunarDayName)")
                }
                .padding(.horizontal, 20)

                Divider()
                    .frame(width: 200)
                    .background(Color.white.opacity(0.3))

                // Gregorian reference
                VStack(spacing: 4) {
                    Text(gregorianCN)
                        .font(.system(size: 14))
                        .foregroundColor(.white.opacity(0.7))
                    Text(gregorianEN)
                        .font(.system(size: 13))
                        .foregroundColor(.white.opacity(0.55))
                }
            }
            .padding(40)
        }
        .frame(minWidth: 400, minHeight: 480)
    }

    private func detailRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.white.opacity(0.6))
                .frame(width: 60, alignment: .trailing)
            Text(value)
                .font(.system(size: 16))
                .foregroundColor(.white.opacity(0.9))
        }
    }
}


