import Foundation
import PDFKit
import Vision
import AppKit

let args = CommandLine.arguments
if args.count < 4 {
    fputs("Usage: swift ocr_pdf.swift input.pdf output_dir output.txt\n", stderr)
    exit(1)
}

let pdfURL = URL(fileURLWithPath: args[1])
let outputDir = URL(fileURLWithPath: args[2], isDirectory: true)
let outputURL = URL(fileURLWithPath: args[3])

try FileManager.default.createDirectory(at: outputDir, withIntermediateDirectories: true)

// Ensure the output text file's parent directory exists.
let outputParent = outputURL.deletingLastPathComponent()
if !FileManager.default.fileExists(atPath: outputParent.path) {
    try FileManager.default.createDirectory(at: outputParent, withIntermediateDirectories: true)
}

guard let document = PDFDocument(url: pdfURL) else {
    fputs("Cannot open PDF: \(pdfURL.path)\n", stderr)
    exit(1)
}

func cgImage(from image: NSImage) -> CGImage? {
    var rect = CGRect(origin: .zero, size: image.size)
    return image.cgImage(forProposedRect: &rect, context: nil, hints: nil)
}

func ocr(_ cgImage: CGImage) -> (String, Float) {
    let semaphore = DispatchSemaphore(value: 0)
    var pageText = ""
    var confidenceSum: Float = 0
    var count: Float = 0

    let request = VNRecognizeTextRequest { request, error in
        defer { semaphore.signal() }
        if let error = error {
            pageText += "[OCR error: \(error)]\n"
            return
        }
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
        let sorted = observations.sorted { a, b in
            let ay = a.boundingBox.midY
            let by = b.boundingBox.midY
            if abs(ay - by) > 0.01 { return ay > by }
            return a.boundingBox.minX < b.boundingBox.minX
        }
        for observation in sorted {
            if let candidate = observation.topCandidates(1).first {
                pageText += candidate.string + "\n"
                confidenceSum += candidate.confidence
                count += 1
            }
        }
    }
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
        semaphore.wait()
    } catch {
        pageText += "[OCR perform error: \(error)]\n"
    }
    return (pageText, count > 0 ? confidenceSum / count : 0)
}

var result = ""

for pageIndex in 0..<document.pageCount {
    guard let page = document.page(at: pageIndex) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let maxWidth: CGFloat = 2400
    let scale = maxWidth / bounds.width
    let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = page.thumbnail(of: size, for: .mediaBox)

    if let tiff = image.tiffRepresentation,
       let rep = NSBitmapImageRep(data: tiff),
       let png = rep.representation(using: .png, properties: [:]) {
        let imgURL = outputDir.appendingPathComponent(String(format: "page_%02d.png", pageIndex + 1))
        try png.write(to: imgURL)
    }

    guard let base = cgImage(from: image) else { continue }
    let (text, conf) = ocr(base)
    result += "===== 第\(pageIndex + 1)页，置信度 \(String(format: "%.3f", conf)) =====\n"
    result += text
    result += "\n"
    print("OCR page \(pageIndex + 1)/\(document.pageCount), confidence \(String(format: "%.3f", conf))")
}

try result.write(to: outputURL, atomically: true, encoding: .utf8)
print("Wrote \(outputURL.path)")
