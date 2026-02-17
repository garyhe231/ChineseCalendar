import SwiftUI
import AppKit

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!

    func applicationDidFinishLaunching(_ notification: Notification) {
        let contentView = ContentView()

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 450, height: 520),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "中国农历 - Chinese Calendar"
        window.contentView = NSHostingView(rootView: contentView)

        // Center on primary screen (the one with the menu bar)
        if let screen = NSScreen.screens.first {
            let screenFrame = screen.visibleFrame
            let x = screenFrame.origin.x + (screenFrame.width - window.frame.width) / 2
            let y = screenFrame.origin.y + (screenFrame.height - window.frame.height) / 2
            window.setFrameOrigin(NSPoint(x: x, y: y))
        }

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
