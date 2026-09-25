"""Генерує idef0_a0.vsdx — контекстну IDEF0-діаграму A0 для Microsoft Visio."""
import os

from vsdx_writer import Diagram

d = Diagram(1400, 760, scale=0.0125, page_name="IDEF0 A0")
BLACK = "#000000"
ARROW = dict(color=BLACK, weight=0.0208)
FONT = 11          # розмір шрифту підписів стрілок, pt

# ---- Функціональний блок ----
BX, BY, BW, BH = 380, 230, 640, 270
d.box(BX, BY, BW, BH,
      "Моделювати логістичні канали\nвиробничого підприємства\nз урахуванням ризиків",
      fill="#FFFFFF", line=BLACK, round_=0, size=16, line_weight=0.0208, bold=False)
d.label(BX + 10, BY + BH - 40, 60, "A0", h=32, size=14, align=0, color=BLACK)

# Позиції стрілок зверху/знизу та зліва/справа
COLS = [BX + BW / 6, BX + BW / 2, BX + BW * 5 / 6]     # 487, 700, 913
ROWS = [BY + 60, BY + 135, BY + 210]                    # 290, 365, 440
LW = 190                                                # ширина підписів зверху/знизу

# ---- Керування (зверху) ----
controls = [
    "Математичні моделі та методи (розділ 2)",
    "Методика зонування ризиків, коефіцієнти втрат",
    "Обмеження бюджету та дедлайнів",
]
for x, text in zip(COLS, controls):
    d.label(x - LW / 2, BY - 210, LW, text, h=70, size=FONT, align=1, valign=2, color=BLACK)
    d.arrow((x, BY - 130), (x, BY), **ARROW)

# ---- Входи (зліва) ----
inputs = [
    "Параметри місії: продукт, обсяги, дедлайни, бюджет",
    "Дані логістичної мережі: міста, маршрути, залізниці OSM",
    "Геодані лінії фронту (DeepState)",
]
for y, text in zip(ROWS, inputs):
    d.label(20, y - 48, 330, text, h=44, size=FONT, align=0, valign=2, color=BLACK)
    d.arrow((20, y), (BX, y), **ARROW)

# ---- Виходи (справа) ----
outputs = [
    "Раціональний сценарій логістики: структура, маршрути, транспорт",
    "План виробництва та графік доставки",
    "Прогнозні показники: час, вартість, втрати; порівняльна аналітика",
]
for y, text in zip(ROWS, outputs):
    d.label(BX + BW + 30, y - 48, 330, text, h=44, size=FONT, align=2, valign=2, color=BLACK)
    d.arrow((BX + BW, y), (1380, y), **ARROW)

# ---- Механізми (знизу) ----
mechanisms = [
    "Розроблене ПЗ (Python, Flask, OR-Tools, Leaflet.js)",
    "Зовнішні геосервіси (OSRM, Overpass, DeepState)",
    "Користувач (ОПР)",
]
for x, text in zip(COLS, mechanisms):
    d.arrow((x, BY + BH + 130), (x, BY + BH), **ARROW)
    d.label(x - LW / 2, BY + BH + 140, LW, text, h=70, size=FONT, align=1, valign=0, color=BLACK)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    d.save(os.path.join(here, "schema_2.vsdx"))
    d.save_svg(os.path.join(here, "idef0_a0.svg"))
