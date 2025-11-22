import AppKit

let currentDirectoryPath = FileManager.default.currentDirectoryPath
let absolutePath = (currentDirectoryPath as NSString).appendingPathComponent("test.md")
let fileURL = URL(fileURLWithPath: absolutePath)

guard let content = try? String(contentsOf: fileURL, encoding: .utf8) else {
    print("无法读取文件内容")
    exit(1)
}
let pasteBoard = NSPasteboard.general
pasteBoard.clearContents()
pasteBoard.setString(content, forType: .html)
