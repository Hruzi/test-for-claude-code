"""Генерує idef0_a0_decomposition.vsdx — декомпозицію IDEF0-діаграми A0 (блоки A1–A5)."""
import os

from vsdx_writer import Diagram

d = Diagram(2200, 1230, scale=0.0125, page_name="IDEF0 A0 — декомпозиція")
BLACK = "#000000"
ARROW = dict(color=BLACK, weight=0.0208)
FONT = 11          # розмір шрифту підписів стрілок, pt

# ---- Функціональні блоки «сходинками» ----
W, H = 220, 130
STEP_X, STEP_Y = 370, 190
blocks = [
    "Формування вхідних даних місії та мережі",
    "Оцінювання ризиків логістичної мережі",
    "Генерація та оптимізація сценаріїв постачання",
    "Імітаційне моделювання виконання місії",
    "Візуалізація та порівняльний аналіз результатів",
]
B = []   # (x, y) лівого верхнього кута кожного блоку
for i, text in enumerate(blocks):
    x, y = 200 + i * STEP_X, 170 + i * STEP_Y
    B.append((x, y))
    d.box(x, y, W, H, text, fill="#FFFFFF", line=BLACK, round_=0, size=12,
          line_weight=0.0208, bold=False)
    d.label(x + 6, y + H - 28, 40, f"A{i + 1}", h=24, size=11, align=0, color=BLACK)


def left(i): return B[i][0]
def right(i): return B[i][0] + W
def top(i): return B[i][1]
def bottom(i): return B[i][1] + H
def at(i, f): return B[i][0] + W * f      # x-координата на частці f ширини блоку


def text(x, y, w, s, h=44, align=0, valign=2):
    d.label(x, y, w, s, h=h, size=FONT, align=align, valign=valign, color=BLACK)


# ---- Керування (зверху) ----
controls = [
    (0.5, "Схеми та формати даних (JSON)"),
    (0.5, "Методика зонування ризиків (розд. 2)"),
    (0.7, "Моделі (3.27)–(3.29), (3.31)–(3.35); ваги ω1, ω2, ω3"),
    (0.7, "Дедлайни, потужність, мінімальні партії"),
    (0.5, "Критерії порівняння сценаріїв"),
]
for i, (f, s) in enumerate(controls):
    x = at(i, f)
    text(x - 140, 30, 280, s, h=66, align=1)
    d.arrow((x, 100), (x, top(i)), **ARROW)

# ---- Механізми (знизу) ----
mechanisms = [
    (90, "utils.py, extract_railways.py"),
    (70, "mission.py; Shapely"),
    (200, "optimizer.py; Google OR-Tools"),
    (90, "production.py, timeline_builder.py"),
    (90, "map_view.py, analytics.py; Leaflet.js, Chart.js"),
]
for i, (length, s) in enumerate(mechanisms):
    x = at(i, 0.5)
    d.arrow((x, bottom(i) + length), (x, bottom(i)), **ARROW)
    text(x - 115, bottom(i) + length + 5, 230, s, h=44, align=1, valign=0)

# ---- Входи A1 (зліва) ----
for y, s in [(210, "Параметри місії та транспорту"),
             (265, "Геодані: OSM, OSRM, DeepState")]:
    text(20, y - 46, 170, s)
    d.arrow((20, y), (left(0), y), **ARROW)

# ---- Зв'язки між блоками ----
# A1 → A3, A4 (зверху): дані місії та довідники маршрутів
yd, xa3, xa4 = 210, at(2, 0.3), at(3, 0.3)
d.arrow((right(0), yd), (xa4, yd), (xa4, top(3)), **ARROW)
d.arrow((xa3, yd), (xa3, top(2)), **ARROW)
text(440, yd - 46, 220, "Дані місії, довідники маршрутів")

# A1 → A2: нормалізовані дані
y1, y2, xv = 270, top(1) + 65, right(0) + 75
d.arrow((right(0), y1), (xv, y1), (xv, y2), (left(1), y2), **ARROW)
text(xv + 8, y1 + 30, 160, "Нормалізовані дані місії та мережі", h=66, valign=0)

# A2 → A3: зони ризику
y1, y2, xv = top(1) + 40, top(2) + 65, right(1) + 75
d.arrow((right(1), y1), (xv, y1), (xv, y2), (left(2), y2), **ARROW)
text(xv + 8, y1 + 30, 128, "Зони ризику, коефіцієнти втрат маршрутів", h=66, valign=0)

# A2 → A4: коефіцієнти втрат
y1, y2, xv = top(1) + 100, top(3) + 95, right(1) + 50
d.arrow((right(1), y1), (xv, y1), (xv, y2), (left(3), y2), **ARROW)
text(left(3) - 140, y2 - 30, 130, "Коефіцієнти втрат", h=26, align=2)

# A3 → A4: раціональний сценарій
y1, y2, xv = top(2) + 65, top(3) + 50, right(2) + 75
d.arrow((right(2), y1), (xv, y1), (xv, y2), (left(3), y2), **ARROW)
text(xv + 8, y1 + 25, 128, "Раціональний сценарій: маршрути, транспорт, план рейсів", h=88, valign=0)

# A4 → A5: результати моделювання
y1, y2, xv = top(3) + 65, top(4) + 65, right(3) + 75
d.arrow((right(3), y1), (xv, y1), (xv, y2), (left(4), y2), **ARROW)
text(xv + 8, y1 + 25, 150, "Виробничий розклад, таймлайн агентів, статистика втрат", h=66, valign=0)

# ---- Виходи A5 (справа) ----
for y, s in [(top(4) + 40, "Інтерактивна карта, порівняльна аналітика, звіти"),
             (top(4) + 100, "Оцінки показників: час, вартість, ризик")]:
    text(right(4) + 20, y - 46, 250, s, align=2)
    d.arrow((right(4), y), (2180, y), **ARROW)

if __name__ == "__main__":
    d.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "idef0_a0_decomposition.vsdx"))
