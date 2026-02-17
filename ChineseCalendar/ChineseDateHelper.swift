import Foundation

struct ChineseDateInfo {
    let lunarYear: Int
    let lunarMonth: Int
    let lunarDay: Int
    let isLeapMonth: Bool
    let zodiacAnimal: String
    let heavenlyStem: String
    let earthlyBranch: String
    let ganzhiYear: String
    let lunarMonthName: String
    let lunarDayName: String
    let gregorianDate: Date
}

struct ChineseDateHelper {

    private static let heavenlyStems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    private static let earthlyBranches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    private static let zodiacAnimals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

    private static let monthNames = [
        "正月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "冬月", "腊月"
    ]

    private static let dayNames = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
    ]

    static func getChineseDate(for date: Date = Date()) -> ChineseDateInfo {
        let chineseCalendar = Calendar(identifier: .chinese)

        let components = chineseCalendar.dateComponents([.year, .month, .day], from: date)
        let lunarYear = components.year!
        let lunarMonth = components.month!
        let lunarDay = components.day!
        let isLeapMonth = components.isLeapMonth ?? false

        // The Chinese calendar year cycle repeats every 60 years.
        // Calendar(identifier: .chinese) returns year as the cycle year (1-60).
        // We need to map this to the Heavenly Stem and Earthly Branch.
        // Year 1 in the cycle = 甲子 (index 0 for stem, index 0 for branch)
        let stemIndex = (lunarYear - 1) % 10
        let branchIndex = (lunarYear - 1) % 12

        let heavenlyStem = heavenlyStems[stemIndex]
        let earthlyBranch = earthlyBranches[branchIndex]
        let zodiacAnimal = zodiacAnimals[branchIndex]
        let ganzhiYear = "\(heavenlyStem)\(earthlyBranch)年"

        let lunarMonthName: String
        if lunarMonth >= 1 && lunarMonth <= 12 {
            let prefix = isLeapMonth ? "闰" : ""
            lunarMonthName = "\(prefix)\(monthNames[lunarMonth - 1])"
        } else {
            lunarMonthName = "第\(lunarMonth)月"
        }

        let lunarDayName: String
        if lunarDay >= 1 && lunarDay <= 30 {
            lunarDayName = dayNames[lunarDay - 1]
        } else {
            lunarDayName = "第\(lunarDay)日"
        }

        return ChineseDateInfo(
            lunarYear: lunarYear,
            lunarMonth: lunarMonth,
            lunarDay: lunarDay,
            isLeapMonth: isLeapMonth,
            zodiacAnimal: zodiacAnimal,
            heavenlyStem: heavenlyStem,
            earthlyBranch: earthlyBranch,
            ganzhiYear: ganzhiYear,
            lunarMonthName: lunarMonthName,
            lunarDayName: lunarDayName,
            gregorianDate: date
        )
    }

    static func formattedGregorianDate(for date: Date = Date()) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.locale = Locale(identifier: "zh_CN")
        return formatter.string(from: date)
    }

    static func formattedGregorianDateEN(for date: Date = Date()) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.locale = Locale(identifier: "en_US")
        return formatter.string(from: date)
    }
}
