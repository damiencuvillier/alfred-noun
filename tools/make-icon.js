#!/usr/bin/env osascript -l JavaScript
// Icône du workflow : bibliothèque d'icônes (grille de glyphes gris) en
// arrière-plan, grande loupe blanche au premier plan. Fond noir arrondi.
// AppKit : origine en BAS à gauche.
ObjC.import('Cocoa')

function poly(points) {
  const p = $.NSBezierPath.bezierPath
  p.moveToPoint($.NSMakePoint(points[0][0], points[0][1]))
  for (let i = 1; i < points.length; i++) p.lineToPoint($.NSMakePoint(points[i][0], points[i][1]))
  p.closePath
  return p
}

function run(argv) {
  const outPath = argv[0]
  const size = 512
  const img = $.NSImage.alloc.initWithSize($.NSMakeSize(size, size))
  img.lockFocus

  // Fond : carré arrondi noir
  const inset = 28
  const bgRect = $.NSMakeRect(inset, inset, size - 2 * inset, size - 2 * inset)
  $.NSColor.blackColor.setFill
  $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius(bgRect, 100, 100).fill

  // --- Bibliothèque d'icônes : grille 3×3 de glyphes gris ---
  const grey = $.NSColor.colorWithWhiteAlpha(1.0, 0.34)
  grey.setFill
  grey.setStroke
  const cells = [
    [128, 384], [256, 384], [384, 384],
    [128, 256], [256, 256], [384, 256],
    [128, 128], [256, 128], [384, 128],
  ]

  // maison
  let [cx, cy] = cells[0]
  poly([[cx - 28, cy - 30], [cx - 28, cy + 2], [cx, cy + 30], [cx + 28, cy + 2], [cx + 28, cy - 30]]).fill
  // cercle
  ;[cx, cy] = cells[1]
  $.NSBezierPath.bezierPathWithOvalInRect($.NSMakeRect(cx - 30, cy - 30, 60, 60)).fill
  // étoile 5 branches
  ;[cx, cy] = cells[2]
  const star = []
  for (let i = 0; i < 10; i++) {
    const angle = Math.PI / 2 + (i * Math.PI) / 5
    const radius = i % 2 === 0 ? 34 : 14
    star.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)])
  }
  poly(star).fill
  // carré arrondi
  ;[cx, cy] = cells[3]
  $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius($.NSMakeRect(cx - 28, cy - 28, 56, 56), 12, 12).fill
  // plus
  ;[cx, cy] = cells[4]
  $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius($.NSMakeRect(cx - 30, cy - 10, 60, 20), 8, 8).fill
  $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius($.NSMakeRect(cx - 10, cy - 30, 20, 60), 8, 8).fill
  // cœur (deux lobes + pointe)
  ;[cx, cy] = cells[5]
  $.NSBezierPath.bezierPathWithOvalInRect($.NSMakeRect(cx - 30, cy - 8, 32, 32)).fill
  $.NSBezierPath.bezierPathWithOvalInRect($.NSMakeRect(cx - 2, cy - 8, 32, 32)).fill
  poly([[cx - 29, cy + 4], [cx + 29, cy + 4], [cx, cy - 30]]).fill
  // triangle
  ;[cx, cy] = cells[6]
  poly([[cx - 30, cy - 26], [cx + 30, cy - 26], [cx, cy + 28]]).fill
  // éclair
  ;[cx, cy] = cells[7]
  poly([[cx + 6, cy + 30], [cx - 22, cy - 2], [cx - 2, cy - 2], [cx - 10, cy - 30], [cx + 22, cy + 4], [cx + 2, cy + 4]]).fill
  // anneau
  ;[cx, cy] = cells[8]
  const ring = $.NSBezierPath.bezierPathWithOvalInRect($.NSMakeRect(cx - 24, cy - 24, 48, 48))
  ring.setLineWidth(14)
  ring.stroke

  // --- Loupe blanche au premier plan ---
  const lensX = 297, lensY = 240, lensR = 94
  // verre légèrement translucide pour détacher la loupe du fond
  $.NSColor.colorWithWhiteAlpha(1.0, 0.14).setFill
  $.NSBezierPath.bezierPathWithOvalInRect(
    $.NSMakeRect(lensX - lensR, lensY - lensR, 2 * lensR, 2 * lensR)
  ).fill
  // liseré noir extérieur (sépare la loupe des glyphes qu'elle chevauche)
  const outline = $.NSBezierPath.bezierPathWithOvalInRect(
    $.NSMakeRect(lensX - lensR, lensY - lensR, 2 * lensR, 2 * lensR)
  )
  outline.setLineWidth(48)
  $.NSColor.blackColor.setStroke
  outline.stroke
  // anneau blanc
  const lens = $.NSBezierPath.bezierPathWithOvalInRect(
    $.NSMakeRect(lensX - lensR, lensY - lensR, 2 * lensR, 2 * lensR)
  )
  lens.setLineWidth(30)
  $.NSColor.whiteColor.setStroke
  lens.stroke
  // manche (vers le bas-droite), avec sous-couche noire
  const dir = Math.SQRT1_2
  const startX = lensX + (lensR + 15) * dir, startY = lensY - (lensR + 15) * dir
  const endX = 442, endY = 92
  const handleShadow = $.NSBezierPath.bezierPath
  handleShadow.moveToPoint($.NSMakePoint(startX, startY))
  handleShadow.lineToPoint($.NSMakePoint(endX, endY))
  handleShadow.setLineWidth(56)
  handleShadow.setLineCapStyle($.NSLineCapStyleRound)
  $.NSColor.blackColor.setStroke
  handleShadow.stroke
  const handle = $.NSBezierPath.bezierPath
  handle.moveToPoint($.NSMakePoint(startX, startY))
  handle.lineToPoint($.NSMakePoint(endX, endY))
  handle.setLineWidth(38)
  handle.setLineCapStyle($.NSLineCapStyleRound)
  $.NSColor.whiteColor.setStroke
  handle.stroke

  img.unlockFocus

  const tiff = img.TIFFRepresentation
  const rep = $.NSBitmapImageRep.imageRepWithData(tiff)
  const png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $.NSDictionary.dictionary)
  return png.writeToFileAtomically(outPath, true) ? 'OK' : 'FAIL'
}
