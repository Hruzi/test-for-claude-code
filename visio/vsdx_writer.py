"""Спільні засоби для побудови .vsdx-схем з окремих фігур, які можна редагувати.

Координати задаються в пікселях (вісь Y спрямована вниз, як на картинці) і
переводяться в дюйми Visio через масштаб `scale`.
"""
import os
import re
import zipfile
from xml.sax.saxutils import escape

NS = ("xmlns='http://schemas.microsoft.com/office/visio/2012/main' "
      "xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships' "
      "xml:space='preserve'")


def cell(n, v, u=None):
    return f'<Cell N="{n}" V="{v}"' + (f' U="{u}"' if u else '') + '/>'


def _rect_geometry(W, H, no_line=0):
    return f'''<Section N="Geometry" IX="0">{cell("NoFill", 0)}{cell("NoLine", no_line)}
<Row T="MoveTo" IX="1">{cell("X", 0)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="2">{cell("X", W)}{cell("Y", 0)}</Row>
<Row T="LineTo" IX="3">{cell("X", W)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="4">{cell("X", 0)}{cell("Y", H)}</Row>
<Row T="LineTo" IX="5">{cell("X", 0)}{cell("Y", 0)}</Row>
</Section>'''


class Diagram:
    def __init__(self, width_px, height_px, scale, page_name):
        self.S = scale
        self.PW, self.PH = width_px * scale, height_px * scale
        self.page_name = page_name
        self.shapes = []
        self._id = 0

    def X(self, px): return px * self.S
    def Y(self, py): return self.PH - py * self.S   # у Visio вісь Y спрямована вгору

    def _nid(self):
        self._id += 1
        return self._id

    def box(self, x, y, w, h, title, body="", fill="#FFFFFF", line="#999999",
            dashed=False, label_top=False, round_=0.08, size=9, line_weight=0.0104, bold=True):
        """Прямокутник із жирним заголовком і (необов'язково) звичайним текстом під ним."""
        X, Y = self.X, self.Y
        cx, cy = X(x + w / 2), Y(y + h / 2)
        W, H = X(w), X(h)
        text = f'<cp IX="0"/>{escape(title)}'
        if body:
            text += f'\n<cp IX="1"/>{escape(body)}'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", cx)}{cell("PinY", cy)}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2)}{cell("LocPinY", H / 2)}
{cell("FillForegnd", fill)}{cell("FillPattern", 1)}
{cell("LineColor", line)}{cell("LineWeight", line_weight)}{cell("LinePattern", 2 if dashed else 1)}
{cell("Rounding", round_)}
{cell("VerticalAlign", 0 if label_top else 1)}
{cell("TopMargin", 0.06)}{cell("LeftMargin", 0.1)}
<Section N="Character">
<Row IX="0">{cell("Size", size / 72, "PT")}{cell("Style", 1 if bold else 0)}{cell("Color", "#1F1F1F")}</Row>
<Row IX="1">{cell("Size", (size - 1) / 72, "PT")}{cell("Style", 0)}{cell("Color", "#333333")}</Row>
</Section>
<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", 0 if label_top else 1)}</Row></Section>
{_rect_geometry(W, H)}
<Text>{text}</Text>
</Shape>''')

    def arrow(self, *pts, color="#444444", weight=0.0139):
        """Ламана зі стрілкою на кінці; pts — точки у пікселях."""
        xs = [self.X(p[0]) for p in pts]
        ys = [self.Y(p[1]) for p in pts]
        mx, my = min(xs), min(ys)
        W, H = max(max(xs) - mx, 0.01), max(max(ys) - my, 0.01)
        rows = ""
        for i, (px, py) in enumerate(zip(xs, ys)):
            t = "MoveTo" if i == 0 else "LineTo"
            rows += f'<Row T="{t}" IX="{i + 1}">{cell("X", px - mx)}{cell("Y", py - my)}</Row>'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", mx)}{cell("PinY", my)}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", 0)}{cell("LocPinY", 0)}
{cell("LineColor", color)}{cell("LineWeight", weight)}{cell("EndArrow", 4)}{cell("EndArrowSize", 1)}
<Section N="Geometry" IX="0">{cell("NoFill", 1)}{cell("NoLine", 0)}{rows}</Section>
</Shape>''')

    def label(self, x, y, w, text, h=14, size=7.5, align=None, valign=None,
              color="#333333", bold=False):
        """Текстовий блок без рамки на білому тлі.

        align: 0 — ліворуч, 1 — по центру, 2 — праворуч; valign: 0 — вгорі, 1 — по центру, 2 — внизу.
        """
        W, H = self.X(w), self.X(h)
        extra = ""
        if valign is not None:
            extra += cell("VerticalAlign", valign)
        char = cell("Size", size / 72, "PT") + cell("Color", color)
        if bold:
            char += cell("Style", 1)
        para = ""
        if align is not None:
            para = f'<Section N="Paragraph"><Row IX="0">{cell("HorzAlign", align)}</Row></Section>\n'
        self.shapes.append(f'''<Shape ID="{self._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", self.X(x + w / 2))}{cell("PinY", self.Y(y + h / 2))}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2)}{cell("LocPinY", H / 2)}
{cell("FillForegnd", "#FFFFFF")}{cell("FillPattern", 1)}{cell("LinePattern", 0)}{extra}
<Section N="Character"><Row IX="0">{char}</Row></Section>
{para}{_rect_geometry(W, H, no_line=1)}
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
                elif item.filename == "visio/windows.xml":
                    data = self._view_center(data.decode("utf-8")).encode("utf-8")
                z.writestr(item.filename, data)
        print("written", out)
