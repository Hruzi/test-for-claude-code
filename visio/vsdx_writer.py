"""Спільні засоби для побудови .vsdx-схем з окремих фігур, які можна редагувати.

Координати задаються в пікселях (вісь Y спрямована вниз, як на картинці) і
переводяться в дюйми Visio через масштаб `scale`.
"""
import math
import os
import re
import zipfile
from xml.sax.saxutils import escape

from svg_writer import SvgCanvas

STYLE_MARGIN = 4 / 72   # поля тексту в стилі Normal шаблону, дюйми
FONT = "Arial"          # явно заданий шрифт з повною підтримкою кирилиці
# Запис Arial для списку шрифтів документа (значення з таблиці OS/2 шрифту Arial)
ARIAL_FACE = ("<FaceName NameU='Arial' UnicodeRanges='-536859905 -1073711037 9 0' "
              "CharSets='1073742335 -65536' Panose='2 11 6 4 2 2 2 2 2 4' Flags='325'/>")

NS = ("xmlns='http://schemas.microsoft.com/office/visio/2012/main' "
      "xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships' "
      "xml:space='preserve'")


def cell(n, v, u=None, f=None):
    return (f'<Cell N="{n}" V="{v}"' + (f' U="{u}"' if u else '')
            + (f' F="{f}"' if f else '') + '/>')


def _rect_geometry(no_line=0):
    """Прямокутник у відносних координатах (частки ширини/висоти) — масштабується разом із фігурою."""
    return f'''<Section N="Geometry" IX="0">{cell("NoFill", 0)}{cell("NoLine", no_line)}
<Row T="RelMoveTo" IX="1">{cell("X", 0)}{cell("Y", 0)}</Row>
<Row T="RelLineTo" IX="2">{cell("X", 1)}{cell("Y", 0)}</Row>
<Row T="RelLineTo" IX="3">{cell("X", 1)}{cell("Y", 1)}</Row>
<Row T="RelLineTo" IX="4">{cell("X", 0)}{cell("Y", 1)}</Row>
<Row T="RelLineTo" IX="5">{cell("X", 0)}{cell("Y", 0)}</Row>
</Section>'''


def _char(size_pt, color, bold=False):
    return (cell("Font", FONT) + cell("Size", size_pt / 72, "PT") + cell("Style", 1 if bold else 0)
            + cell("Color", color))


class Diagram:
    def __init__(self, width_px, height_px, scale, page_name):
        self.S = scale
        self.PW, self.PH = width_px * scale, height_px * scale
        self.page_name = page_name
        self.shapes = []
        self._id = 0
        # Паралельно будується SVG-варіант тієї самої схеми (у пікселях схеми).
        self.svg = SvgCanvas(width_px, height_px, pt_per_px=scale * 72)

    def X(self, px): return px * self.S
    def Y(self, py): return self.PH - py * self.S   # у Visio вісь Y спрямована вгору

    def _nid(self):
        self._id += 1
        return self._id

    def box(self, x, y, w, h, title, body="", fill="#FFFFFF", line="#999999",
            dashed=False, label_top=False, round_=0.08, size=9, line_weight=0.0104, bold=True):
        """Прямокутник із жирним заголовком і (необов'язково) звичайним текстом під ним."""
        self.svg.rect(x, y, w, h, fill=fill, stroke=line, stroke_width=line_weight / self.S,
                      rx=round_ / self.S, dashed=dashed)
        runs = [(title, size, bold, "#1F1F1F")]
        if body:
            runs.append((body, size - 1, False, "#333333"))
        self.svg.text_block(x, y, w, h, runs, align=0 if label_top else 1,
                            valign=0 if label_top else 1,
                            margin_x=0.1 / self.S, margin_y=0.06 / self.S)
        X, Y = self.X, self.Y
        cx, cy = X(x + w / 2), Y(y + h / 2)
        W, H = X(w), X(h)
        text = f'<cp IX="0"/>{escape(title)}'
        if body:
            text += f'\n<cp IX="1"/>{escape(body)}'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", cx)}{cell("PinY", cy)}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2, f="Width*0.5")}{cell("LocPinY", H / 2, f="Height*0.5")}
{cell("FillForegnd", fill)}{cell("FillPattern", 1)}
{cell("LineColor", line)}{cell("LineWeight", line_weight)}{cell("LinePattern", 2 if dashed else 1)}
{cell("Rounding", round_)}
{cell("VerticalAlign", 0 if label_top else 1)}
{cell("TopMargin", 0.06)}{cell("LeftMargin", 0.1)}
<Section N="Character">
<Row IX="0">{_char(size, "#1F1F1F", bold)}</Row>
<Row IX="1">{_char(size - 1, "#333333")}</Row>
</Section>
<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", 0 if label_top else 1)}</Row></Section>
{_rect_geometry()}
<Text>{text}</Text>
</Shape>''')

    def arrow(self, *pts, color="#444444", weight=0.0139):
        """Ламана зі стрілкою на кінці; pts — точки у пікселях."""
        # EndArrow=4, EndArrowSize=1 у Visio — наконечник приблизно 0.1 × 0.07 дюйма
        self.svg.arrow(pts, color, weight / self.S, head_len=0.1 / self.S, head_w=0.07 / self.S)
        P = [(self.X(px), self.Y(py)) for px, py in pts]
        (bx, by), (ex, ey) = P[0], P[-1]
        length = max(math.hypot(ex - bx, ey - by), 0.001)
        ang = math.atan2(ey - by, ex - bx)
        # Лінія як 1-D фігура Visio (з початковою і кінцевою точками, як інструмент «Лінія»).
        # Локальна система координат: початок — у BeginX/BeginY, вісь X — у напрямку EndX/EndY.
        ca, sa = math.cos(-ang), math.sin(-ang)
        if len(P) == 2:
            rows = (f'<Row T="MoveTo" IX="1">{cell("X", 0, f="Width*0")}{cell("Y", 0, f="Height*0.5")}</Row>'
                    f'<Row T="LineTo" IX="2">{cell("X", length, f="Width*1")}{cell("Y", 0, f="Height*0.5")}</Row>')
        else:
            rows = ""
            for i, (px, py) in enumerate(P):
                dx, dy = px - bx, py - by
                lx, ly = dx * ca - dy * sa, dx * sa + dy * ca
                t = "MoveTo" if i == 0 else "LineTo"
                rows += f'<Row T="{t}" IX="{i + 1}">{cell("X", lx)}{cell("Y", ly)}</Row>'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", (bx + ex) / 2, f="(BeginX+EndX)/2")}{cell("PinY", (by + ey) / 2, f="(BeginY+EndY)/2")}
{cell("Width", length, f="SQRT((EndX-BeginX)^2+(EndY-BeginY)^2)")}{cell("Height", 0)}
{cell("LocPinX", length / 2, f="Width*0.5")}{cell("LocPinY", 0, f="Height*0.5")}
{cell("Angle", ang, f="ATAN2(EndY-BeginY,EndX-BeginX)")}
{cell("BeginX", bx)}{cell("BeginY", by)}{cell("EndX", ex)}{cell("EndY", ey)}
{cell("ObjType", 2)}
{cell("LineColor", color)}{cell("LineWeight", weight)}{cell("EndArrow", 4)}{cell("EndArrowSize", 1)}
<Section N="Geometry" IX="0">{cell("NoFill", 1)}{cell("NoLine", 0)}{rows}</Section>
</Shape>''')

    def label(self, x, y, w, text, h=14, size=7.5, align=None, valign=None,
              color="#333333", bold=False):
        """Текстовий блок без рамки на білому тлі.

        align: 0 — ліворуч, 1 — по центру, 2 — праворуч; valign: 0 — вгорі, 1 — по центру, 2 — внизу.
        """
        self.svg.rect(x, y, w, h, fill="#FFFFFF")
        self.svg.text_block(x, y, w, h, [(text, size, bold, color)],
                            align=1 if align is None else align,
                            valign=1 if valign is None else valign,
                            margin_x=STYLE_MARGIN / self.S, margin_y=STYLE_MARGIN / self.S)
        W, H = self.X(w), self.X(h)
        extra = ""
        if valign is not None:
            extra += cell("VerticalAlign", valign)
        char = _char(size, color, bold)
        para = ""
        if align is not None:
            para = f'<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", align)}</Row></Section>\n'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", self.X(x + w / 2))}{cell("PinY", self.Y(y + h / 2))}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2, f="Width*0.5")}{cell("LocPinY", H / 2, f="Height*0.5")}
{cell("FillForegnd", "#FFFFFF")}{cell("FillPattern", 1)}{cell("LinePattern", 0)}{extra}
<Section N="Character"><Row IX="0">{char}</Row></Section>
{para}{_rect_geometry(no_line=1)}
<Text>{escape(text)}</Text>
</Shape>''')

    # ---- Пакування у .vsdx ----
    # Основою є шаблон, збережений самим Visio (з пакета `vsdx`, pip install vsdx):
    # стилі, теми, windows.xml і docProps беруться з нього, замінюється лише сторінка.

    @staticmethod
    def template_path():
        import vsdx
        return os.path.join(os.path.dirname(vsdx.__file__), "media", "media.vsdx")

    def _view_center(self, xml):
        xml = re.sub(r"ViewCenterX='[^']*'", f"ViewCenterX='{self.PW / 2}'", xml)
        return re.sub(r"ViewCenterY='[^']*'", f"ViewCenterY='{self.PH / 2}'", xml)

    def _patch_pages(self, xml):
        xml = re.sub(r"<Cell N='PageWidth' V='[^']*'/>", f"<Cell N='PageWidth' V='{self.PW}'/>", xml)
        xml = re.sub(r"<Cell N='PageHeight' V='[^']*'/>", f"<Cell N='PageHeight' V='{self.PH}'/>", xml)
        xml = re.sub(r"<Cell N='(PageScale|DrawingScale)' V='[^']*' U='MM'/>",
                     r"<Cell N='\1' V='1' U='IN'/>", xml)
        xml = self._view_center(xml)
        return xml.replace("NameU='Page-1' Name='Page-1'",
                           f"NameU='Page-1' Name='{escape(self.page_name)}'")

    def save_svg(self, out):
        self.svg.save(out)

    def save(self, out):
        page = ("<?xml version='1.0' encoding='utf-8' ?>\n"
                f"<PageContents {NS}><Shapes>\n" + "\n".join(self.shapes) + "\n</Shapes></PageContents>")
        with zipfile.ZipFile(self.template_path()) as tpl, \
                zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for item in tpl.infolist():
                if item.filename == "docProps/thumbnail.emf":
                    continue    # мініатюра шаблону, не цієї схеми
                data = tpl.read(item.filename)
                if item.filename == "_rels/.rels":
                    data = re.sub(rb'<Relationship [^>]*Target="docProps/thumbnail.emf"/>', b"", data)
                elif item.filename == "visio/pages/page1.xml":
                    data = page.encode("utf-8")
                elif item.filename == "visio/pages/pages.xml":
                    data = self._patch_pages(data.decode("utf-8")).encode("utf-8")
                elif item.filename == "visio/document.xml":
                    data = data.replace(b"</FaceNames>", ARIAL_FACE.encode() + b"</FaceNames>")
                elif item.filename == "visio/windows.xml":
                    data = self._view_center(data.decode("utf-8")).encode("utf-8")
                z.writestr(item.filename, data)
        print("written", out)
