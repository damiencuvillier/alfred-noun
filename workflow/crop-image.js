#!/usr/bin/env osascript -l JavaScript
// Rogne un PNG en conservant les `keep` lignes du HAUT (largeur inchangée).
// L'analyse (où couper) est faite côté Python — voir download.py, qui décide
// de la hauteur à garder d'après la bande d'attribution Noun Project.
//
// Usage : osascript -l JavaScript crop-image.js /chemin/image.png <keep>
// Sortie : "CROPPED WxH", "SKIP" ou "FAIL raison".
ObjC.import('Cocoa')

function run(argv) {
  const path = argv[0]
  const keep = parseInt(argv[1], 10)
  if (!keep || keep <= 0) return 'FAIL hauteur invalide'
  const data = $.NSData.dataWithContentsOfFile(path)
  if (data.isNil()) return 'FAIL lecture'
  const src = $.NSBitmapImageRep.imageRepWithData(data)
  if (src.isNil()) return 'FAIL décodage'
  const W = src.pixelsWide
  const H = src.pixelsHigh
  if (keep >= H) return 'SKIP'

  const dst = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
    null, W, keep, 8, 4, true, false, $.NSDeviceRGBColorSpace, 0, 0
  )
  if (dst.isNil()) return 'FAIL allocation'
  const ctx = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(dst)
  $.NSGraphicsContext.saveGraphicsState
  $.NSGraphicsContext.setCurrentContext(ctx)
  // drawInRect : origine AppKit en BAS à gauche — le haut visuel = y élevés
  src.drawInRectFromRectOperationFractionRespectFlippedHints(
    $.NSMakeRect(0, 0, W, keep),
    $.NSMakeRect(0, H - keep, W, keep),
    $.NSCompositingOperationCopy,
    1.0,
    false,
    $.NSDictionary.dictionary
  )
  $.NSGraphicsContext.restoreGraphicsState

  const png = dst.representationUsingTypeProperties(
    $.NSBitmapImageFileTypePNG,
    $.NSDictionary.dictionary
  )
  if (png.isNil()) return 'FAIL encodage'
  if (!png.writeToFileAtomically(path, true)) return 'FAIL écriture'
  return 'CROPPED ' + W + 'x' + keep
}
