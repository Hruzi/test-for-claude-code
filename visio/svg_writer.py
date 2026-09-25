"""SVG-варіант схем, сумісний з імпортом у Microsoft Visio Desktop.

Visio Desktop імпортує SVG значно простіше, ніж браузер, тому тут навмисно
використовується лише мінімальний набір конструкцій:

* кожен рядок тексту — окремий <text x y> з атрибутами font-family, font-size,
  font-weight і fill. Жодних <tspan>, textLength, lengthAdjust, letter-spacing,
  word-spacing, text-anchor, dominant-baseline, transform, xml:space, CSS-класів
  і атрибута style. Вирівнювання й перенесення рядків розраховуються тут, за
  метриками шрифту Arial (Liberation Sans має такі самі ширини символів);
* лінії — <polyline>, наконечники стрілок — <polygon> (без <marker>);
* без <g>, <defs>, <use>, <style> і без вкладених <svg>.

`check()` перевіряє готовий SVG на відповідність цим правилам.
"""
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

FONT_FAMILY = "Arial"
FONT_FILES = {
    False: "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    True: "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
}
LINE_HEIGHT = 1.2      # міжрядковий інтервал, частки розміру шрифту
CAP_HEIGHT = 0.716     # висота великих літер Arial, частки розміру шрифту

ALLOWED = {
    "svg": {"xmlns", "version", "width", "height", "viewBox"},
    "rect": {"x", "y", "width", "height", "rx", "ry", "fill", "stroke",
             "stroke-width", "stroke-dasharray"},
    "polyline": {"points", "fill", "stroke", "stroke-width"},
    "polygon": {"points", "fill", "stroke", "stroke-width"},
    "text": {"x", "y", "font-family", "font-size", "font-weight", "fill"},
}

_metrics = {}


def _font(bold):
    if bold not in _metrics:
        from fontTools.ttLib import TTFont
        f = TTFont(FONT_FILES[bold])
        _metrics[bold] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    return _metrics[bold]


def text_width(s, size, bold=False):
    cmap, hmtx, upm = _font(bold)
    notdef = hmtx[".notdef"][0]
    return sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else notdef for c in s) * size / upm


def wrap(s, width, size, bold=False):
    """Перенесення по словах, як це робить Visio; довге слово не розривається."""
    lines = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = f"{cur} {word}" if cur else word
            if cur and text_width(cand, size, bold) > width:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        lines.append(cur)
    return lines


def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


class SvgCanvas:
    def __init__(self, width, height, pt_per_px):
        self.W, self.H = width, height
        self.pt = pt_per_px          # скільки пунктів в одному пікселі схеми
        self.items = []

    def px(self, pt):
        return pt / self.pt

    def rect(self, x, y, w, h, fill="none", stroke="none", stroke_width=1, rx=0, dashed=False):
        a = f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}"'
        if rx:
            a += f' rx="{_n(rx)}" ry="{_n(rx)}"'
        a += f' fill="{fill}" stroke="{stroke}"'
        if stroke != "none":
            a += f' stroke-width="{_n(stroke_width)}"'
            if dashed:
                a += ' stroke-dasharray="6 4"'
        self.items.append(a + "/>")

    def arrow(self, pts, color, stroke_width, head_len, head_w):
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5 or 1
        ux, uy = dx / L, dy / L
        bx, by = x2 - ux * head_len, y2 - uy * head_len      # основа наконечника
        line = list(pts[:-1]) + [(bx, by)]
        self.items.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"/>'
                          % (" ".join(f"{_n(px)},{_n(py)}" for px, py in line), color, _n(stroke_width)))
        head = [(x2, y2), (bx - uy * head_w / 2, by + ux * head_w / 2),
                (bx + uy * head_w / 2, by - ux * head_w / 2)]
        self.items.append('<polygon points="%s" fill="%s" stroke="none"/>'
                          % (" ".join(f"{_n(px)},{_n(py)}" for px, py in head), color))

    def text_block(self, x, y, w, h, runs, align=1, valign=1, margin_x=0, margin_y=0):
        """runs: [(текст, розмір_pt, жирний, колір)] — абзаци, що йдуть один за одним.

        align: 0 — ліворуч, 1 — по центру, 2 — праворуч; valign: 0 — вгорі, 1 — по центру, 2 — внизу.
        """
        inner_w = w - 2 * margin_x
        lines = []    # (рядок, розмір_px, жирний, колір)
        for s, size_pt, bold, color in runs:
            size = self.px(size_pt)
            lines += [(ln, size, bold, color) for ln in wrap(s, inner_w, size, bold)]
        total = sum(size * LINE_HEIGHT for _, size, _, _ in lines)
        if valign == 0:
            top = y + margin_y
        elif valign == 2:
            top = y + h - margin_y - total
        else:
            top = y + (h - total) / 2
        for s, size, bold, color in lines:
            lh = size * LINE_HEIGHT
            baseline = top + (lh + CAP_HEIGHT * size) / 2
            top += lh
            if not s:
                continue
            tw = text_width(s, size, bold)
            if align == 0:
                tx = x + margin_x
            elif align == 2:
                tx = x + w - margin_x - tw
            else:
                tx = x + (w - tw) / 2
            a = (f'<text x="{_n(tx)}" y="{_n(baseline)}" font-family="{FONT_FAMILY}" '
                 f'font-size="{_n(size)}"')
            if bold:
                a += ' font-weight="bold"'
            self.items.append(f'{a} fill="{color}">{escape(s)}</text>')

    def to_string(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                f'width="{_n(self.W)}" height="{_n(self.H)}" viewBox="0 0 {_n(self.W)} {_n(self.H)}">\n'
                + "\n".join(self.items) + "\n</svg>\n")

    def save(self, path):
        data = self.to_string()
        check(data)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print("written", path)


def check(svg):
    """Перевіряє, що SVG містить лише дозволені Visio-сумісні конструкції."""
    root = ET.fromstring(svg.encode("utf-8"))
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ALLOWED:
            raise ValueError(f"недозволений елемент <{tag}>")
        extra = set(el.attrib) - ALLOWED[tag]
        if extra:
            raise ValueError(f"<{tag}>: недозволені атрибути {sorted(extra)}")
        if tag == "text" and len(el):
            raise ValueError("<text> не може мати вкладених елементів")
    if re.search(r"textLength|lengthAdjust|letter-spacing|tspan|transform|style=|class=", svg):
        raise ValueError("знайдено заборонену конструкцію")
