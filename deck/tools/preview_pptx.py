#!/usr/bin/env python3
"""Rebuild an HTML preview from a generated .pptx, for visual QA.

Reads the shapes back out of the PowerPoint XML — not from the measurements
that produced them — so the EMU maths, font mapping and colour conversion are
all checked against what actually shipped in the file.

Usage: python3 tools/preview_pptx.py <deck.pptx> <outDir>
"""
import sys, zipfile, pathlib, base64, re
import xml.etree.ElementTree as ET

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU_PER_PX = 7620
HPT_PER_PX = 60

# Each PowerPoint family name maps to the face file it would resolve to on a
# machine with Trenda installed, so the preview shows the real metrics.
FACE_FILES = {
    'Trenda IG Display': 'TrendaIGDisplay-Regular.otf',
    'Trenda IG Display Light': 'TrendaIGDisplay-Light.otf',
    'Trenda IG Display Semibold': 'TrendaIGDisplay-Semibold.otf',
    'Trenda IG Display Bold': 'TrendaIGDisplay-Bold.otf',
    'Trenda IG Display Heavy': 'TrendaIGDisplay-Heavy.otf',
    'Trenda IG Display Black': 'TrendaIGDisplay-Black.otf',
    'Trenda IG Text': 'TrendaIGText-Regular.otf',
    'Trenda IG Text Light': 'TrendaIGText-Light.otf',
    'Trenda IG Text Semibold': 'TrendaIGText-Semibold.otf',
    'Trenda IG Text Bold': 'TrendaIGText-Bold.otf',
}

FACE_CSS = '\n'.join(
    "@font-face{font-family:'%s';src:url('../fonts/%s') format('opentype');"
    "font-weight:400;font-style:normal;font-display:block}" % (fam, f)
    for fam, f in FACE_FILES.items())

def main():
    deck = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(deck)

    slides = sorted(n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n))
    for idx, name in enumerate(slides, start=1):
        root = ET.fromstring(z.read(name))
        img = base64.b64encode(z.read(f'ppt/media/slide{idx}.png')).decode()
        html = [
            '<!DOCTYPE html><html><head><meta charset="utf-8">',
            '<style>' + FACE_CSS,
            'html,body{margin:0;width:1600px;height:900px;overflow:hidden}',
            '.s{position:relative;width:1600px;height:900px}',
            '.s img{position:absolute;inset:0;width:1600px;height:900px}',
            '.t{position:absolute;display:flex;flex-direction:column;justify-content:center}',
            '.t p{margin:0}</style></head><body><div class="s">',
            f'<img src="data:image/png;base64,{img}">',
        ]
        for sp in root.iter(P + 'sp'):
            off = sp.find(f'.//{A}off')
            ext = sp.find(f'.//{A}ext')
            x = int(off.get('x')) / EMU_PER_PX
            y = int(off.get('y')) / EMU_PER_PX
            w = int(ext.get('cx')) / EMU_PER_PX
            h = int(ext.get('cy')) / EMU_PER_PX
            paras = []
            for p in sp.iter(A + 'p'):
                ppr = p.find(A + 'pPr')
                align = {'r': 'right', 'ctr': 'center'}.get(ppr.get('algn'), 'left')
                lnspc = ppr.find(f'{A}lnSpc/{A}spcPts')
                lh = int(lnspc.get('val')) / HPT_PER_PX
                runs, first = [], None
                for r in p.iter(A + 'r'):
                    rpr = r.find(A + 'rPr')
                    fam = rpr.find(A + 'latin').get('typeface')
                    if first is None:
                        first = (fam, int(rpr.get('sz')) / HPT_PER_PX)
                    runs.append(
                        '<span style="font-family:\'{f}\';font-weight:400;'
                        'font-size:{s}px;letter-spacing:{sp}px;color:#{c};'
                        'font-style:{i}">{t}</span>'.format(
                            f=fam,
                            s=int(rpr.get('sz')) / HPT_PER_PX,
                            sp=int(rpr.get('spc', 0)) / HPT_PER_PX,
                            c=rpr.find(f'{A}solidFill/{A}srgbClr').get('val'),
                            i='italic' if rpr.get('i') == '1' else 'normal',
                            t=(r.find(A + 't').text or '').replace('&', '&amp;')
                               .replace('<', '&lt;').replace('>', '&gt;')))
                paras.append((lh, align, ''.join(runs), first))
            lh, align, _, lead = paras[0]
            body = '<br>'.join(r for _, _, r, _ in paras)
            # The paragraph itself must carry the leading run's font, or the
            # browser sizes the line box from the default 16px strut and the
            # block comes out taller than the line-height asks for. PowerPoint's
            # spcPts line spacing is exact, so this is what it will do.
            html.append(
                f'<div class="t" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
                f'<p style="line-height:{lh}px;text-align:{align};'
                f'font-family:\'{lead[0]}\';font-size:{lead[1]}px">{body}</p></div>')
        html.append('</div></body></html>')
        (out / f'preview-{idx}.html').write_text('\n'.join(html))
    print(f'  wrote {len(slides)} previews to {out}')

if __name__ == '__main__':
    main()
