"""Генерує architecture.vsdx — схему архітектури системи для Microsoft Visio."""
import zipfile
from xml.sax.saxutils import escape

S = 0.016            # дюймів на піксель вихідного зображення
PW, PH = 1060 * S, 580 * S   # розмір сторінки, дюйми

def X(px): return px * S
def Y(py): return PH - py * S   # у Visio вісь Y спрямована вгору

shapes = []
_id = [0]
def nid():
    _id[0] += 1
    return _id[0]

def cell(n, v, u=None):
    return f'<Cell N="{n}" V="{v}"' + (f' U="{u}"' if u else '') + '/>'

def box(x, y, w, h, title, body="", fill="#FFFFFF", line="#999999",
        dashed=False, label_top=False, round_=0.08, size=9):
    sid = nid()
    cx, cy = X(x + w / 2), Y(y + h / 2)
    W, H = X(w), X(h)
    text = f'<cp IX="0"/>{escape(title)}'
    if body:
        text += f'\n<cp IX="1"/>{escape(body)}'
    shapes.append(f'''<Shape ID="{sid}" Type="Shape" LineStyle="0" FillStyle="0" TextStyle="0">
{cell("PinX", cx)}{cell("PinY", cy)}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2)}{cell("LocPinY", H / 2)}
{cell("FillForegnd", fill)}{cell("FillPattern", 1)}
{cell("LineColor", line)}{cell("LineWeight", 0.0104)}{cell("LinePattern", 2 if dashed else 1)}
{cell("Rounding", round_)}
{cell("VerticalAlign", 0 if label_top else 1)}
{cell("TopMargin", 0.06)}{cell("LeftMargin", 0.1)}
<Section N="Character">
<Row IX="0">{cell("Size", size / 72, "PT")}{cell("Style", 1)}{cell("Color", "#1F1F1F")}</Row>
<Row IX="1">{cell("Size", (size - 1) / 72, "PT")}{cell("Style", 0)}{cell("Color", "#333333")}</Row>
</Section>
<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", 0 if label_top else 1)}</Row></Section>
<Section N="Geometry" IX="0">{cell("NoFill", 0)}{cell("NoLine", 0)}
<Row T="MoveTo" IX="1">{cell("X", 0)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="2">{cell("X", W)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="3">{cell("X", W)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="4">{cell("X", 0)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="5">{cell("X", 0)}{cell("Y", 0)}</Row>
</Section>
<Text>{text}</Text>
</Shape>''')

def arrow(*pts, color="#444444"):
    """Ламана зі стрілкою на кінці; pts — точки у пікселях."""
    sid = nid()
    xs = [X(p[0]) for p in pts]
    ys = [Y(p[1]) for p in pts]
    mx, my = min(xs), min(ys)
    W, H = max(max(xs) - mx, 0.01), max(max(ys) - my, 0.01)
    rows = ""
    for i, (px, py) in enumerate(zip(xs, ys)):
        t = "MoveTo" if i == 0 else "LineTo"
        rows += f'<Row T="{t}" IX="{i + 1}">{cell("X", px - mx)}{cell("Y", py - my)}</Row>'
    shapes.append(f'''<Shape ID="{sid}" Type="Shape" LineStyle="0" FillStyle="0" TextStyle="0">
{cell("PinX", mx)}{cell("PinY", my)}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", 0)}{cell("LocPinY", 0)}
{cell("LineColor", color)}{cell("LineWeight", 0.0139)}{cell("EndArrow", 4)}{cell("EndArrowSize", 1)}
<Section N="Geometry" IX="0">{cell("NoFill", 1)}{cell("NoLine", 0)}{rows}</Section>
</Shape>''')

def label(x, y, w, text, h=14):
    sid = nid()
    W, H = X(w), X(h)
    shapes.append(f'''<Shape ID="{sid}" Type="Shape" LineStyle="0" FillStyle="0" TextStyle="0">
{cell("PinX", X(x + w / 2))}{cell("PinY", Y(y + h / 2))}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2)}{cell("LocPinY", H / 2)}
{cell("FillForegnd", "#FFFFFF")}{cell("FillPattern", 1)}{cell("LinePattern", 0)}
<Section N="Character"><Row IX="0">{cell("Size", 7.5 / 72, "PT")}{cell("Color", "#333333")}</Row></Section>
<Section N="Geometry" IX="0">{cell("NoFill", 0)}{cell("NoLine", 1)}
<Row T="MoveTo" IX="1">{cell("X", 0)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="2">{cell("X", W)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="3">{cell("X", W)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="4">{cell("X", 0)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="5">{cell("X", 0)}{cell("Y", 0)}</Row>
</Section>
<Text>{escape(text)}</Text>
</Shape>''')

# ---- Рівні (контейнери) ----
LAYER = dict(fill="#F7F7F7", line="#A0A0A0", dashed=True, label_top=True, round_=0.1)
box(5, 18, 797, 137, "Клієнтський рівень — веб-браузер", **LAYER)
box(5, 185, 797, 80, "Рівень доступу — REST API", **LAYER)
box(5, 285, 797, 152, "Розрахунковий конвеєр (Python 3.11)", **LAYER)
box(5, 462, 797, 105, "Рівень даних", **LAYER)
box(827, 185, 172, 382, "Зовнішні геосервіси", **LAYER)

# ---- Клієнтський рівень ----
BLUE = dict(fill="#E8F0FB", line="#6B8FD6")
box(22, 50, 233, 93, "Інтерактивна карта", "Leaflet.js\n(маршрути, зони, агенти)", **BLUE)
box(271, 50, 233, 93, "Панель керування", "статистика місії,\nпараметри сценарію", **BLUE)
box(519, 50, 233, 93, "Аналітичні графіки", "Chart.js,\nпорівняння сценаріїв", **BLUE)

# ---- REST API ----
box(71, 212, 430, 40, "api_server.py — Flask REST API",
    "черга задач, конкурентний запуск конвеєра", fill="#FDF0E1", line="#D9A05B")

# ---- Конвеєр ----
GREEN = dict(fill="#E8F5E9", line="#6BAF6E")
LGREEN = dict(fill="#F3FAF3", line="#9CCB9E")
box(22, 312, 183, 42, "mission_planning.py", "планування місій, ризики", **GREEN)
box(212, 312, 183, 42, "production.py", "виробництво продукції", **GREEN)
box(403, 312, 178, 42, "timeline_builder.py", "рух транспортних агентів", **GREEN)
box(593, 312, 178, 42, "map_view.py", "побудова HTML-карти", **GREEN)
box(212, 370, 178, 36, "optimizer.py", "VRP, Score (OR-Tools)", **LGREEN)
box(403, 370, 178, 36, "analytics.py", "порівняльні графіки", **LGREEN)

# ---- Дані ----
box(71, 489, 430, 60, "Сховище JSON",
    "cargo_mission, mission_plan, production_plan,\nagent_timeline, cities, routes, кеші",
    fill="#F1E8F5", line="#A67BB5")

# ---- Зовнішні сервіси ----
RED = dict(fill="#FDECEC", line="#D66B6B")
box(839, 213, 147, 67, "DeepState API", "дані про лінію фронту", **RED)
box(839, 293, 147, 67, "OSRM", "автомобільні маршрути", **RED)
box(839, 373, 147, 67, "Overpass API", "дані про залізниці", **RED)
box(839, 453, 147, 67, "OSM / CartoDB", "тайли базової карти", **RED)

# ---- Зв'язки ----
arrow((376, 143), (376, 212))                       # панель -> API
arrow((394, 212), (394, 143))                       # API -> панель
label(400, 158, 60, "HTTP / JSON")
arrow((384, 252), (384, 312))                       # API -> конвеєр
label(392, 262, 80, "запуск конвеєра")
arrow((205, 333), (212, 333))
arrow((395, 333), (403, 333))
arrow((581, 333), (593, 333))
arrow((301, 354), (301, 370))
arrow((492, 354), (492, 370))
arrow((277, 437), (277, 489))                       # конвеєр -> сховище
arrow((295, 489), (295, 437))                       # сховище -> конвеєр
label(240, 452, 95, "читання / запис JSON")
arrow((839, 246), (501, 226))                       # DeepState -> API
label(595, 222, 150, "GeoJSON лінії фронту (кешується)")
arrow((839, 406), (812, 406), (812, 291), (301, 291), (301, 312))  # Overpass -> production
label(525, 276, 80, "мережа залізниць")
arrow((839, 326), (771, 326))                       # OSRM -> map_view
label(740, 334, 70, "геометрія доріг")
arrow((986, 486), (1028, 486), (1028, 8), (138, 8), (138, 50))     # тайли -> карта
label(1003, 238, 52, "тайли карти")

# ---- Пакування у .vsdx (OPC-архів) ----
NS = 'xmlns="http://schemas.microsoft.com/office/visio/2012/main" ' \
     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
HDR = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'

files = {
"[Content_Types].xml": HDR + '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>
<Override PartName="/visio/pages/pages.xml" ContentType="application/vnd.ms-visio.pages+xml"/>
<Override PartName="/visio/pages/page1.xml" ContentType="application/vnd.ms-visio.page+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>''',
"_rels/.rels": HDR + '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document" Target="visio/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>''',
"docProps/core.xml": HDR + '''<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Архітектура системи</dc:title></cp:coreProperties>''',
"docProps/app.xml": HDR + '''<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
<Application>Microsoft Visio</Application></Properties>''',
"visio/document.xml": HDR + f'''<VisioDocument {NS}>
<DocumentSettings/>
<Colors/>
<FaceNames><FaceName NameU="Calibri" UnicodeRanges="-536859905 -1073732485 9 0" CharSets="536871423 0"/></FaceNames>
<StyleSheets>
<StyleSheet ID="0" NameU="No Style" Name="No Style">
{cell("LineWeight", 0.0104)}{cell("LineColor", "#000000")}{cell("LinePattern", 1)}
{cell("FillForegnd", "#FFFFFF")}{cell("FillPattern", 1)}
{cell("VerticalAlign", 1)}{cell("LeftMargin", 0.1)}{cell("RightMargin", 0.1)}
{cell("TopMargin", 0.05)}{cell("BottomMargin", 0.05)}
<Section N="Character"><Row IX="0">{cell("Font", "Calibri")}{cell("Size", 0.125)}{cell("Color", "#000000")}{cell("Style", 0)}</Row></Section>
<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", 1)}</Row></Section>
</StyleSheet>
</StyleSheets>
</VisioDocument>''',
"visio/_rels/document.xml.rels": HDR + '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/pages" Target="pages/pages.xml"/>
</Relationships>''',
"visio/pages/pages.xml": HDR + f'''<Pages {NS}>
<Page ID="0" NameU="Архітектура" Name="Архітектура">
<PageSheet>{cell("PageWidth", PW)}{cell("PageHeight", PH)}{cell("PageScale", 1)}{cell("DrawingScale", 1)}{cell("DrawingSizeType", 0)}</PageSheet>
<Rel r:id="rId1"/>
</Page>
</Pages>''',
"visio/pages/_rels/pages.xml.rels": HDR + '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page1.xml"/>
</Relationships>''',
"visio/pages/page1.xml": HDR + f'<PageContents {NS}><Shapes>\n' + "\n".join(shapes) + '\n</Shapes></PageContents>',
}

if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture.vsdx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", files.pop("[Content_Types].xml"))
        for name, data in files.items():
            z.writestr(name, data)
    print("written", out)
