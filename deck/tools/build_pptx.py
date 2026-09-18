#!/usr/bin/env python3
"""Package rendered slide PNGs into a 16:9 PowerPoint deck.

A .pptx is a ZIP of OOXML parts. Each slide holds one full-bleed picture of the
artwork, so it looks identical on any machine.

With --text, the slide copy is added back as native PowerPoint text boxes laid
out from measurements taken in the browser, and the picture is the artwork with
that copy hidden. The result is editable in PowerPoint, but needs the Trenda IG
fonts installed to render as designed.

Usage:
  python3 tools/build_pptx.py <pngDir> <out.pptx>
  python3 tools/build_pptx.py <bgPngDir> <out.pptx> --text measure.json
"""
import sys, json, zipfile, datetime, pathlib, struct

# The HTML deck is authored on a 1600x900 canvas; both axes map at 7620 EMU/px.
EMU_PER_PX = 7620
# 1600px across 13.333in means one CSS px is 0.6pt. OOXML wants hundredths.
HPT_PER_PX = 60

# 16:9 widescreen: 13.333in x 7.5in, in EMU (1in = 914400 EMU)
CX, CY = 12192000, 6858000

NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'not a PNG: {path}')
    return struct.unpack('>II', head[16:24])

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
{slide_overrides}
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>
<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>
<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

def presentation(n):
    # slides take rId1..rIdN in presentation.xml.rels; the master follows at rId(N+1)
    ids = ''.join(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, n + 1))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}" saveSubsetFonts="1">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{n + 1}"/></p:sldMasterIdLst>
<p:sldIdLst>{ids}</p:sldIdLst>
<p:sldSz cx="{CX}" cy="{CY}"/><p:notesSz cx="{CY}" cy="{CX}"/>
<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle>
</p:presentation>'''

def presentation_rels(n):
    rels = ''.join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, n + 1))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}
<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId{n + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>
<Relationship Id="rId{n + 3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>
<Relationship Id="rId{n + 4}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
<Relationship Id="rId{n + 5}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>
</Relationships>'''

def slide(name, descr, shapes=''):
    """One full-bleed picture, locked so a stray click can't nudge the artwork."""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>
<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:pic>
<p:nvPicPr>
<p:cNvPr id="2" name="{name}" descr="{descr}"/>
<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
<p:nvPr/>
</p:nvPicPr>
<p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
<p:spPr>
<a:xfrm><a:off x="0" y="0"/><a:ext cx="{CX}" cy="{CY}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
</p:spPr>
</p:pic>
{shapes}
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

def slide_rels(i):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide{i}.png"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''

EMPTY_TREE = '''<p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>
<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree>'''

TX_STYLES = ''.join(
    f'<p:{k}>' + ''.join(
        f'<a:lvl{i}pPr><a:defRPr/></a:lvl{i}pPr>' for i in range(1, 10)
    ) + f'</p:{k}>' for k in ('titleStyle', 'bodyStyle', 'otherStyle'))

SLIDE_MASTER = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
<a:effectLst/></p:bgPr></p:bg>{EMPTY_TREE}</p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2"
 accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6"
 hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
<p:txStyles>{TX_STYLES}</p:txStyles>
</p:sldMaster>'''

SLIDE_MASTER_RELS = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''

SLIDE_LAYOUT = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}" type="blank" preserve="1">
<p:cSld name="Blank">{EMPTY_TREE}</p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''

SLIDE_LAYOUT_RELS = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''

def _fill_styles():
    solid = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    return f'<a:fillStyleLst>{solid}{solid}{solid}</a:fillStyleLst>'

def _line_styles():
    ln = ('<a:ln w="{w}" cap="flat" cmpd="sng" algn="ctr">'
          '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:prstDash val="solid"/></a:ln>')
    return '<a:lnStyleLst>' + ''.join(ln.format(w=w) for w in (6350, 12700, 19050)) + '</a:lnStyleLst>'

# ShieldForge / Insight Global brand colours drive the theme palette.
THEME = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{NS_A}" name="ShieldForge">
<a:themeElements>
<a:clrScheme name="ShieldForge">
<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="0C1520"/></a:dk2>
<a:lt2><a:srgbClr val="F4F6F9"/></a:lt2>
<a:accent1><a:srgbClr val="22C1F0"/></a:accent1>
<a:accent2><a:srgbClr val="FFC629"/></a:accent2>
<a:accent3><a:srgbClr val="ED0F7E"/></a:accent3>
<a:accent4><a:srgbClr val="0E2233"/></a:accent4>
<a:accent5><a:srgbClr val="5A6573"/></a:accent5>
<a:accent6><a:srgbClr val="0FA8DC"/></a:accent6>
<a:hlink><a:srgbClr val="0FA8DC"/></a:hlink>
<a:folHlink><a:srgbClr val="5A6573"/></a:folHlink>
</a:clrScheme>
<a:fontScheme name="ShieldForge">
<a:majorFont><a:latin typeface="Trenda IG Display"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Trenda IG Text"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
</a:fontScheme>
<a:fmtScheme name="ShieldForge">
{_fill_styles()}
{_line_styles()}
<a:effectStyleLst>
<a:effectStyle><a:effectLst/></a:effectStyle>
<a:effectStyle><a:effectLst/></a:effectStyle>
<a:effectStyle><a:effectLst/></a:effectStyle>
</a:effectStyleLst>
{_fill_styles().replace('fillStyleLst', 'bgFillStyleLst')}
</a:fmtScheme>
</a:themeElements>
<a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>'''

PRES_PROPS = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:presentationPr xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}"/>'
VIEW_PROPS = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:viewPr xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}"/>'
TABLE_STYLES = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<a:tblStyleLst xmlns:a="{NS_A}" def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>'

def core_props(title):
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>{title}</dc:title>
<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''

def app_props(titles):
    n = len(titles)
    parts = ''.join(f'<vt:lpstr>{t}</vt:lpstr>' for t in titles)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<Application>ShieldForge deck builder</Application>
<Slides>{n}</Slides><Paragraphs>0</Paragraphs><Words>0</Words>
<PresentationFormat>Widescreen</PresentationFormat>
<TitlesOfParts><vt:vector size="{n}" baseType="lpstr">{parts}</vt:vector></TitlesOfParts>
</Properties>'''


# ---------------------------------------------------------------- text boxes

# Each Trenda weight ships as its own Windows family name, which is how a
# non-bold weight like Black reaches PowerPoint at all.
FACES = {
    ('display', 300): 'Trenda IG Display Light',
    ('display', 400): 'Trenda IG Display',
    ('display', 500): 'Trenda IG Display',
    ('display', 600): 'Trenda IG Display Semibold',
    ('display', 700): 'Trenda IG Display Bold',
    ('display', 800): 'Trenda IG Display Heavy',
    ('display', 900): 'Trenda IG Display Black',
    ('text', 300): 'Trenda IG Text Light',
    ('text', 400): 'Trenda IG Text',
    ('text', 500): 'Trenda IG Text',
    ('text', 600): 'Trenda IG Text Semibold',
    ('text', 700): 'Trenda IG Text Bold',
}

def face(run):
    fam, w = run['family'], run['weight']
    if (fam, w) in FACES:
        return FACES[(fam, w)]
    if fam in ('display', 'text'):                       # nearest weight we ship
        have = sorted(k[1] for k in FACES if k[0] == fam)
        return FACES[(fam, min(have, key=lambda h: abs(h - w)))]
    return fam

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def run_xml(r):
    # The footer's "|" divider is spaced by CSS margin in HTML; in PowerPoint
    # that has to be real whitespace.
    text = '  |  ' if r['text'].strip() == '|' else r['text']
    sz = max(100, round(r['sizePx'] * HPT_PER_PX))
    spc = round(r['spacingPx'] * HPT_PER_PX)
    typeface = face(r)
    # DrawingML keeps whitespace in <a:t> verbatim; unlike w:t it takes no
    # xml:space attribute, and the schema rejects one.
    return (
        f'<a:r><a:rPr lang="en-US" sz="{sz}" b="0" i="{1 if r["italic"] else 0}"'
        f' spc="{spc}" dirty="0">'
        f'<a:solidFill><a:srgbClr val="{r["color"]}"/></a:solidFill>'
        f'<a:latin typeface="{typeface}"/><a:cs typeface="{typeface}"/>'
        f'</a:rPr><a:t>{esc(text)}</a:t></a:r>'
    )

def textbox(block, shape_id, name):
    """A block measured in the browser, rebuilt as an editable PowerPoint shape.

    The box keeps the measured rectangle and centres its text vertically, which
    survives the small ascent/descent differences between the two layout engines
    far better than anchoring to the top would.
    """
    x = round(block['x'] * EMU_PER_PX)
    y = round(block['y'] * EMU_PER_PX)
    # Trenda measures fractionally wider in PowerPoint than in the browser, so
    # give each box headroom rather than let a line wrap that should not.
    slack = min(block['w'] * 0.12, max(0.0, 1592 - block['x'] - block['w']))
    cx = round((block['w'] + slack) * EMU_PER_PX)
    cy = round(block['h'] * EMU_PER_PX)
    lnspc = round(block['lineHeightPx'] * HPT_PER_PX)

    paras = []
    for runs in block['paragraphs']:
        body = ''.join(run_xml(r) for r in runs)
        paras.append(
            f'<a:p><a:pPr algn="{block["align"]}">'
            f'<a:lnSpc><a:spcPts val="{lnspc}"/></a:lnSpc></a:pPr>{body}</a:p>'
        )

    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"'
        f' anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f'{"".join(paras)}</p:txBody></p:sp>'
    )

def shapes_for(blocks, slide_no):
    """Text boxes for one slide, named after their opening words."""
    out, sid = [], 3
    for b in [b for b in blocks if b['slide'] == slide_no]:
        first = b['paragraphs'][0][0]['text'].strip()
        label = (first[:28] + '...') if len(first) > 28 else first
        out.append(textbox(b, sid, esc(label) or f'Text {sid}'))
        sid += 1
    return ''.join(out)

SLIDES = [
    ('One platform for Salesforce governance',
     'Slide 1 of 3. Headline: One platform for Salesforce governance. Understand user '
     'access, assess security risks and simplify governance within your Salesforce org. '
     'Approved by Salesforce Security Review and live on AppExchange. Access '
     'intelligence, audit and compliance readiness, release and storage insights. '
     'Product view: org security dashboard, permission set comparison and compliance '
     'frameworks.'),
    ('Audit readiness. Security visibility.',
     'Slide 2 of 3. Headline: Audit readiness. Security visibility. Security posture, '
     'compliance findings and audit evidence in one workspace. SOX and compliance, '
     'segregation of duties, org security and health check, audit evidence. Product '
     'view: health check scores across SOX, HIPAA, PCI-DSS, GDPR and NIST, plus a '
     'segregation of duties violation report.'),
    ('Clearer access. Simpler administration.',
     'Slide 3 of 3. Headline: Clearer access. Simpler administration. Practical tools '
     'for admins, architects and support teams. User 360 and effective access, '
     'permission intelligence, profile migration, Release Radar and CAB reports, '
     'storage, FinOps and dev tools. Product view: User 360, profile migration steps '
     'and Release Radar updates.'),
]

def main():
    png_dir = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    blocks = []
    if '--text' in sys.argv:
        blocks = json.loads(pathlib.Path(sys.argv[sys.argv.index('--text') + 1]).read_text())
    pngs = sorted(png_dir.glob('shieldforge-slide-*.png'))
    if len(pngs) != len(SLIDES):
        sys.exit(f'expected {len(SLIDES)} slide PNGs in {png_dir}, found {len(pngs)}')

    for p in pngs:
        w, h = png_size(p)
        if abs(w / h - CX / CY) > 0.001:
            sys.exit(f'{p.name} is {w}x{h}, not 16:9')

    n = len(pngs)
    overrides = '\n'.join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, n + 1))

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES.format(slide_overrides=overrides))
        z.writestr('_rels/.rels', ROOT_RELS)
        z.writestr('docProps/core.xml', core_props('ShieldForge by Insight Global'))
        z.writestr('docProps/app.xml', app_props([t for t, _ in SLIDES]))
        z.writestr('ppt/presentation.xml', presentation(n))
        z.writestr('ppt/_rels/presentation.xml.rels', presentation_rels(n))
        z.writestr('ppt/presProps.xml', PRES_PROPS)
        z.writestr('ppt/viewProps.xml', VIEW_PROPS)
        z.writestr('ppt/tableStyles.xml', TABLE_STYLES)
        z.writestr('ppt/theme/theme1.xml', THEME)
        z.writestr('ppt/slideMasters/slideMaster1.xml', SLIDE_MASTER)
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', SLIDE_MASTER_RELS)
        z.writestr('ppt/slideLayouts/slideLayout1.xml', SLIDE_LAYOUT)
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', SLIDE_LAYOUT_RELS)
        for i, (png, (title, descr)) in enumerate(zip(pngs, SLIDES), start=1):
            z.writestr(f'ppt/slides/slide{i}.xml',
                       slide(title, descr, shapes_for(blocks, i)))
            z.writestr(f'ppt/slides/_rels/slide{i}.xml.rels', slide_rels(i))
            z.write(png, f'ppt/media/slide{i}.png')

    kind = f'{len(blocks)} text boxes' if blocks else 'flattened'
    print(f'  wrote {out} ({out.stat().st_size // 1024} KB, {n} slides, {kind})')

if __name__ == '__main__':
    main()
