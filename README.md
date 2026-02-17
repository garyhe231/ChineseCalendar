# Chinese Calendar (中国农历)

A native macOS app that displays today's date in the Chinese lunar calendar.

![macOS](https://img.shields.io/badge/macOS-13%2B-blue)
![Swift](https://img.shields.io/badge/Swift-5-orange)

## Features

- Chinese lunar date (year, month, day)
- Chinese zodiac animal (生肖)
- Heavenly Stem + Earthly Branch year name (天干地支)
- Gregorian date reference in Chinese and English

## Screenshot

The app displays a clean, centered window with the current lunar date:

```
        中国农历

     丙午年 【马年】

      正月 初一

    天干  丙
    地支  午
    生肖  马

  2026年2月17日 星期二
  Tuesday, February 17, 2026
```

## Build

Requires macOS 13+ and Swift 5.

### With Xcode

Open `ChineseCalendar.xcodeproj` and build.

### With Command Line Tools

```bash
swiftc -framework SwiftUI -framework AppKit \
  -o ChineseCalendar_bin \
  ChineseCalendar/ChineseDateHelper.swift \
  ChineseCalendar/ContentView.swift \
  ChineseCalendar/main.swift
```

To create an app bundle:

```bash
mkdir -p ChineseCalendar.app/Contents/MacOS
cp ChineseCalendar_bin ChineseCalendar.app/Contents/MacOS/ChineseCalendar
open ChineseCalendar.app
```

## How It Works

Uses Apple's built-in `Calendar(identifier: .chinese)` API from the Foundation framework to convert Gregorian dates to the Chinese lunar calendar. No third-party dependencies.
