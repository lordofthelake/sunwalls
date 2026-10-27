// Builds a macOS dynamic (solar) wallpaper HEIC with Apple's ImageIO (hardware HEVC encoder).
// usage: swift pack.swift <out.heic> <base64-solar-plist> <light-index> <dark-index> <frame0.jpg> ... <frameN.jpg>
import Foundation
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
let out = URL(fileURLWithPath: a[1]); let solar = a[2]
let frames = Array(a[5...])
guard let dest = CGImageDestinationCreateWithURL(out as CFURL, UTType.heic.identifier as CFString, frames.count, nil) else { fatalError("dest") }
let meta = CGImageMetadataCreateMutable()
let ns = "http://ns.apple.com/namespace/1.0/" as CFString
guard CGImageMetadataRegisterNamespaceForPrefix(meta, ns, "apple_desktop" as CFString, nil) else { fatalError("ns") }
let tag = CGImageMetadataTagCreate(ns, "apple_desktop" as CFString, "solar" as CFString, .string, solar as CFString)!
guard CGImageMetadataSetTagWithPath(meta, nil, "apple_desktop:solar" as CFString, tag) else { fatalError("tag") }
let opts = [kCGImageDestinationLossyCompressionQuality: 0.92] as CFDictionary
for (i, f) in frames.enumerated() {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: f) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { fatalError("read \(f)") }
    if i == 0 { CGImageDestinationAddImageAndMetadata(dest, img, meta, opts) }
    else { CGImageDestinationAddImage(dest, img, opts) }
}
guard CGImageDestinationFinalize(dest) else { fatalError("finalize") }
// verify
let chk = CGImageSourceCreateWithURL(out as CFURL, nil)!
let m = CGImageSourceCopyMetadataAtIndex(chk, 0, nil)!
let s = CGImageMetadataCopyStringValueWithPath(m, nil, "apple_desktop:solar" as CFString) as String?
print(out.lastPathComponent, "frames:", CGImageSourceGetCount(chk), "solar tag:", s == solar ? "ok" : "MISSING")
