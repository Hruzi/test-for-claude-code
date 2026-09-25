"""Генерує architecture.vsdx — схему архітектури системи для Microsoft Visio."""
import os

from vsdx_writer import Diagram

d = Diagram(1060, 580, scale=0.016, page_name="Архітектура")
box, arrow, label = d.box, d.arrow, d.label

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
label(773, 331, 64, "геометрія доріг")
arrow((986, 486), (1028, 486), (1028, 8), (138, 8), (138, 50))     # тайли -> карта
label(1003, 238, 52, "тайли карти")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    d.save(os.path.join(here, "architecture.vsdx"))
    d.save_svg(os.path.join(here, "architecture.svg"))
