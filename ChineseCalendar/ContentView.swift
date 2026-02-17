import SwiftUI

struct ContentView: View {
    private let chineseDate = ChineseDateHelper.getChineseDate()
    private let gregorianCN = ChineseDateHelper.formattedGregorianDate()
    private let gregorianEN = ChineseDateHelper.formattedGregorianDateEN()

    var body: some View {
        VStack(spacing: 24) {
            // Header
            Text("中国农历")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.secondary)

            // Ganzhi year + Zodiac
            HStack(spacing: 8) {
                Text(chineseDate.ganzhiYear)
                    .font(.system(size: 28, weight: .bold))
                Text("【\(chineseDate.zodiacAnimal)年】")
                    .font(.system(size: 24, weight: .medium))
                    .foregroundColor(.orange)
            }

            // Lunar month and day — large display
            Text("\(chineseDate.lunarMonthName) \(chineseDate.lunarDayName)")
                .font(.system(size: 48, weight: .bold))
                .foregroundColor(.primary)

            Divider()
                .frame(width: 200)

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

            // Gregorian reference
            VStack(spacing: 4) {
                Text(gregorianCN)
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
                Text(gregorianEN)
                    .font(.system(size: 13))
                    .foregroundColor(.secondary.opacity(0.8))
            }
        }
        .padding(40)
        .frame(minWidth: 400, minHeight: 480)
    }

    private func detailRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.secondary)
                .frame(width: 60, alignment: .trailing)
            Text(value)
                .font(.system(size: 16))
        }
    }
}

