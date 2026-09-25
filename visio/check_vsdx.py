"""Перевірка згенерованих .vsdx: структура пакета, фігури, текст, шрифти.

Запуск: python3 check_vsdx.py schema_1.vsdx schema_2.vsdx schema_3.vsdx
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

V = "{http://schemas.microsoft.com/office/visio/2012/main}"
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

REQUIRED_PARTS = [
    "[Content_Types].xml", "_rels/.rels", "docProps/app.xml", "docProps/core.xml",
    "visio/document.xml", "visio/_rels/document.xml.rels", "visio/windows.xml",
    "visio/pages/pages.xml", "visio/pages/_rels/pages.xml.rels", "visio/pages/page1.xml",
]
CHAR_CELLS = ["Font", "Color", "Style", "Case", "Pos", "FontScale", "Size", "DblUnderline",
              "Overline", "Strikethru", "DoubleStrikethrough", "Letterspace", "ColorTrans",
              "AsianFont", "ComplexScriptFont", "ComplexScriptSize", "LangID"]
IMAGE_EXT = re.compile(r"\.(png|jpe?g|gif|bmp|emf|wmf|svg|tiff?)$", re.I)

# Рядки, які мають бути в схемах цілим текстом (кирилиця, латиниця, довгі рядки)
EXPECTED = {
    "schema_1.vsdx": ["Сховище JSON", "запуск конвеєра", "мережа залізниць",
                      "GeoJSON лінії фронту (кешується)", "api_server.py — Flask REST API"],
    "schema_2.vsdx": ["Прогнозні показники: час, вартість, втрати; порівняльна аналітика",
                      "Дані логістичної мережі: міста, маршрути, залізниці OSM",
                      "Розроблене ПЗ (Python, Flask, OR-Tools, Leaflet.js)"],
    "schema_3.vsdx": ["Моделі (3.27)–(3.29), (3.31)–(3.35); ваги ω1, ω2, ω3",
                      "Візуалізація та порівняльний аналіз результатів",
                      "Раціональний сценарій: маршрути, транспорт, план рейсів"],
}


def shape_text(sh):
    t = sh.find(V + "Text")
    return None if t is None else "".join(t.itertext())


def cells(el):
    return {c.get("N"): c.get("V") for c in el.findall(V + "Cell")}


def check(path):
    name = path.rsplit("/", 1)[-1]
    ok = []

    def need(cond, msg):
        if not cond:
            raise AssertionError(f"{name}: {msg}")

    with open(path, "rb") as f:
        head = f.read(4)
    need(head == b"PK\x03\x04", "не ZIP-архів (можливо, перейменований SVG/PNG)")
    z = zipfile.ZipFile(path)
    need(z.testzip() is None, "пошкоджений ZIP")
    names = set(z.namelist())
    ok.append(f"ZIP/OPC-пакет, {len(names)} частин, CRC без помилок")

    missing = [p for p in REQUIRED_PARTS if p not in names]
    need(not missing, f"немає частин {missing}")
    trees = {n: ET.fromstring(z.read(n)) for n in names if n.endswith((".xml", ".rels"))}
    ok.append("усі обов'язкові частини Visio є, усі XML коректні")

    # Типи вмісту та зв'язки
    ct = trees["[Content_Types].xml"]
    overrides = {o.get("PartName") for o in ct.iter(CT + "Override")}
    defaults = {d.get("Extension") for d in ct.iter(CT + "Default")}
    for n in names:
        if n == "[Content_Types].xml":
            continue
        need("/" + n in overrides or n.rsplit(".", 1)[-1] in defaults, f"немає типу вмісту для {n}")
    need(any(o.endswith("document.xml") for o in overrides) and
         "application/vnd.ms-visio.drawing.main+xml" in z.read("[Content_Types].xml").decode(),
         "основна частина не позначена як документ Visio")
    for n, t in trees.items():
        if not n.endswith(".rels"):
            continue
        base = n.replace("_rels/", "").rsplit(".rels", 1)[0]
        folder = base.rsplit("/", 1)[0] + "/" if "/" in base else ""
        for r in t.iter(REL + "Relationship"):
            if r.get("TargetMode") == "External":
                continue
            target = r.get("Target")
            parts = (folder + target).split("/")
            norm = []
            for p in parts:
                if p == "..":
                    norm.pop()
                elif p:
                    norm.append(p)
            need("/".join(norm) in names, f"зв'язок {n} → {target} веде в нікуди")
    ok.append("типи вмісту та зв'язки пакета узгоджені (тип: application/vnd.ms-visio.drawing.main+xml)")

    # Жодних зображень
    imgs = [n for n in names if IMAGE_EXT.search(n)]
    page = trees["visio/pages/page1.xml"]
    need(not imgs, f"є зображення {imgs}")
    need(not list(page.iter(V + "ForeignData")), "є вбудовані об'єкти ForeignData")
    ok.append("немає зображень, SVG чи вбудованих об'єктів")

    # Фігури
    shapes = list(page.iter(V + "Shape"))
    ids = [s.get("ID") for s in shapes]
    need(len(ids) == len(set(ids)), "повторювані ID фігур")
    two_d = [s for s in shapes if shape_text(s) is not None]
    one_d = [s for s in shapes if "BeginX" in cells(s)]
    arrows = [s for s in one_d if cells(s).get("EndArrow") not in (None, "0")]
    for s in shapes:
        need(s.find(V + "Section[@N='Geometry']") is not None, f"фігура {s.get('ID')} без геометрії")
    for s in one_d:
        c = cells(s)
        need(c.get("ObjType") == "2", f"лінія {s.get('ID')} не позначена як 1-D")
    ok.append(f"{len(shapes)} фігур Visio: {len(two_d)} з текстом (блоки/підписи), "
              f"{len(one_d)} ліній 1-D, з них {len(arrows)} зі стрілками")

    # Текст. Visio Desktop не підставляє значення за замовчуванням для клітинок,
    # яких бракує в рядку Character з IX≥1 (стилі задають лише рядок 0): пропущений
    # FontScale дає ширину символів 0 — увесь рядок злипається в один символ.
    fonts_ok = True
    for s in two_d:
        rows = s.findall(V + "Section[@N='Character']/" + V + "Row")
        row_ix = {r.get("IX") for r in rows}
        for r in rows:
            c = cells(r)
            miss = [n for n in CHAR_CELLS if n not in c]
            need(not miss, f"фігура {s.get('ID')}: рядок Character IX={r.get('IX')} без клітинок {miss}")
            need(float(c["FontScale"]) == 1 and float(c["Letterspace"]) == 0,
                 f"фігура {s.get('ID')}: FontScale={c['FontScale']}, Letterspace={c['Letterspace']}")
            fonts_ok &= c.get("Font") == "Arial"
        cps = s.find(V + "Text").findall(V + "cp")
        used = {cp.get("IX") for cp in cps} or {"0"}
        need(used <= row_ix or not rows, f"фігура {s.get('ID')}: посилання на неіснуючий рядок шрифту")
        need(row_ix <= used, f"фігура {s.get('ID')}: зайві рядки Character {sorted(row_ix - used)}")
        need(len(cps) <= 2, f"фігура {s.get('ID')}: текст розбитий на {len(cps)} фрагментів")
    need(fonts_ok, "не всі фрагменти тексту мають шрифт Arial")
    doc = z.read("visio/document.xml").decode()
    need("NameU='Arial'" in doc, "Arial не зареєстровано у списку шрифтів документа")
    ok.append("кожен рядок Character має всі 17 клітинок, як у Visio (FontScale=1, Letterspace=0), "
              "шрифт Arial; немає зайвих чи неіснуючих рядків")

    texts = [shape_text(s) for s in two_d]
    alltext = "\n".join(texts)
    cyr = sum(1 for ch in alltext if "Ѐ" <= ch <= "ӿ")
    need(any(ch in alltext for ch in "іїєґІЇЄҐ"), "немає українських літер")
    missing = [e for e in EXPECTED.get(name, []) if not any(e in t.replace("\n", " ") for t in texts)]
    need(not missing, f"не знайдено цілим текстом: {missing}")
    longest = max(texts, key=len)
    ok.append(f"текст у елементах <Text> фігур: {cyr} кириличних символів (з і/ї/є), "
              f"контрольні рядки знайдено цілими; найдовший текст {len(longest)} симв.")
    return ok


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p)
        for line in check(p):
            print("  ✓", line)
