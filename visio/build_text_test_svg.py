"""Генерує visio_text_test.svg — мінімальний тест імпорту тексту SVG у Visio Desktop."""
import os

from svg_writer import SvgCanvas

LINES = [
    "іваіваівавіаіваіва",
    "Сховище JSON",
    "запуск конвеєра",
    "мережа залізниць",
    "Latin text: api_server.py — Flask REST API",
]

c = SvgCanvas(480, 40 + 36 * len(LINES), pt_per_px=0.75)   # 1 px = 0.75 pt (96 dpi)
for i, s in enumerate(LINES):
    c.rect(20, 20 + i * 36, 440, 28, fill="#FFFFFF", stroke="#999999")
    c.text_block(20, 20 + i * 36, 440, 28, [(s, 12, i == 1, "#000000")], align=0, margin_x=8)

if __name__ == "__main__":
    c.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "visio_text_test.svg"))
