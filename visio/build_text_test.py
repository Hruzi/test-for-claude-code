"""Діагностика тексту у Visio Desktop.

test_text.vsdx              — 4 текстові фігури в структурі, найближчій до тієї, що зберігає Visio (варіант D).
test_text_experiments.vsdx  — варіанти A–F поруч, зокрема відтворення помилки схем (E1, E2) і виправлення (F).
"""
import os
from xml.sax.saxutils import escape

from vsdx_writer import Diagram, cell, char_row_full, para_row_full

TEST = "іваіваівавіаіваіва"


def text_shape(d, x, y, w, h, text, char_rows, para_rows="", visio_like=False, border=True):
    """Текстова фігура з довільними рядками Character/Paragraph і текстом (з розміткою cp)."""
    X, Y = d.X, d.Y
    W, H = X(w), X(h)
    txt_cells = ""
    if visio_like:
        txt_cells = (cell("Angle", 0) + cell("FlipX", 0) + cell("FlipY", 0) + cell("ResizeMode", 0)
                     + cell("TxtPinX", W / 2, f="Width*0.5") + cell("TxtPinY", H / 2, f="Height*0.5")
                     + cell("TxtWidth", W, f="Width*1") + cell("TxtHeight", H, f="Height*1")
                     + cell("TxtLocPinX", W / 2, f="TxtWidth*0.5")
                     + cell("TxtLocPinY", H / 2, f="TxtHeight*0.5") + cell("TxtAngle", 0))
    d.shapes.append(f'''<Shape ID="{d._nid()}" Type="Shape" LineStyle="3" FillStyle="3" TextStyle="3">
{cell("PinX", X(x + w / 2))}{cell("PinY", Y(y + h / 2))}{cell("Width", W)}{cell("Height", H)}
{cell("LocPinX", W / 2, f="Width*0.5")}{cell("LocPinY", H / 2, f="Height*0.5")}{txt_cells}
{cell("FillForegnd", "#FFFFFF")}{cell("FillPattern", 1)}{cell("LineColor", "#999999")}{cell("LinePattern", 1 if border else 0)}
<Section N="Character">{char_rows}</Section>
{f'<Section N="Paragraph">{para_rows}</Section>' if para_rows else ""}
<Section N="Geometry" IX="0">{cell("NoFill", 0)}{cell("NoLine", 0 if border else 1)}
<Row T="RelMoveTo" IX="1">{cell("X", 0)}{cell("Y", 0)}</Row>
<Row T="RelLineTo" IX="2">{cell("X", 1)}{cell("Y", 0)}</Row>
<Row T="RelLineTo" IX="3">{cell("X", 1)}{cell("Y", 1)}</Row>
<Row T="RelLineTo" IX="4">{cell("X", 0)}{cell("Y", 1)}</Row>
<Row T="RelLineTo" IX="5">{cell("X", 0)}{cell("Y", 0)}</Row>
</Section>
<Text>{text}</Text>
</Shape>''')


def minimal_row(ix, size_pt, font=None, bold=False, color="#000000"):
    """Рядок у тому вигляді, як його досі писав генератор схем: лише 3–4 клітинки."""
    return (f'<Row IX="{ix}">' + (cell("Font", font) if font else "") + cell("Size", size_pt / 72, "PT")
            + cell("Style", 1 if bold else 0) + cell("Color", color) + "</Row>")


def visio_like(d, x, y, w, h, s, size=12, bold=False, align=1):
    text_shape(d, x, y, w, h, f"<cp IX='0'/><pp IX='0'/>{escape(s)}\n",
               char_row_full(0, size, bold=bold), para_row_full(0, align), visio_like=True)


def caption(d, y, s):
    visio_like(d, 20, y, 330, 50, s, size=10, align=0)


def build_test_text(path):
    d = Diagram(560, 300, scale=0.0125, page_name="test_text")
    for i, s in enumerate([TEST, "Сховище JSON", "запуск конвеєра", "api_server.py — Flask REST API"]):
        visio_like(d, 40, 30 + i * 65, 480, 45, s, size=14)
    d.save(path)


def build_experiments(path):
    d = Diagram(900, 700, scale=0.0125, page_name="experiments")
    rows = [
        ("A: Arial, мінімальний рядок (1 фрагмент)",
         f"<cp IX='0'/>{TEST}", minimal_row(0, 12, "Arial")),
        ("B: Calibri, мінімальний рядок (1 фрагмент)",
         f"<cp IX='0'/>{TEST}", minimal_row(0, 12, "Calibri")),
        ("C: без шрифту — Visio бере стандартний",
         f"<cp IX='0'/>{TEST}", minimal_row(0, 12)),
        ("D: як зберігає Visio — усі 17 клітинок Character",
         f"<cp IX='0'/><pp IX='0'/>{TEST}\n", char_row_full(0, 12)),
        ("E1: як у схемах — 2 фрагменти, рядок IX=1 неповний (очікується помилка)",
         f"<cp IX='0'/>Сховище JSON\n<cp IX='1'/>{TEST}",
         minimal_row(0, 12, "Arial", bold=True) + minimal_row(1, 11, "Arial")),
        ("E2: як контейнери схем — 1 фрагмент + зайвий неповний рядок IX=1",
         "<cp IX='0'/>Розрахунковий конвеєр (Python 3.11)",
         minimal_row(0, 12, "Arial", bold=True) + minimal_row(1, 11, "Arial")),
        ("F: виправлення — 2 фрагменти, обидва рядки повні",
         f"<cp IX='0'/>Сховище JSON\n<cp IX='1'/>{TEST}",
         char_row_full(0, 12, bold=True) + char_row_full(1, 11)),
    ]
    for i, (cap, text, char_rows) in enumerate(rows):
        y = 20 + i * 95
        caption(d, y + 10, cap)
        text_shape(d, 370, y, 500, 70, text, char_rows)
    d.save(path)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    build_test_text(os.path.join(here, "test_text.vsdx"))
    build_experiments(os.path.join(here, "test_text_experiments.vsdx"))
