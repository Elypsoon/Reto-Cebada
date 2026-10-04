"""Maqueta informe, bibliografía y dos páginas de anexos desde resultados locales."""
import csv
import hashlib
import json
import re
from html import escape
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
for name, filename in [("Arial", "arial.ttf"), ("ArialBold", "arialbd.ttf"), ("ArialItalic", "ariali.ttf")]:
    pdfmetrics.registerFont(TTFont(name, Path("C:/Windows/Fonts") / filename))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold", italic="ArialItalic")
green = colors.HexColor("#234D3B")
styles = {
    "body": ParagraphStyle("body", fontName="Arial", fontSize=10.2, leading=14.2, spaceAfter=8),
    "small": ParagraphStyle("small", fontName="Arial", fontSize=8.6, leading=11.6, spaceAfter=7),
    "title": ParagraphStyle("title", fontName="ArialBold", fontSize=20, leading=24, textColor=green, spaceAfter=16),
    "heading": ParagraphStyle("heading", fontName="ArialBold", fontSize=13, leading=17, textColor=green, spaceBefore=12, spaceAfter=8, keepWithNext=True),
    "subheading": ParagraphStyle("subheading", fontName="ArialBold", fontSize=10.5, leading=14, textColor=green, spaceBefore=8, spaceAfter=6, keepWithNext=True),
}


def inline(text):
    text = text.replace("–", "-").replace("—", "-").replace("\u2011", "-")
    text = escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*", r"<i>\1</i>", text)
    return text.replace("`", "")


def paragraph(text, style="body"):
    return Paragraph(inline(text), styles[style])


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#CBD7D0"))
    canvas.line(48, 42, letter[0] - 48, 42)
    canvas.setFont("Arial", 8)
    canvas.setFillColor(green)
    canvas.drawString(48, 29, "AgroCebada 2026 | Estimación retrospectiva del ciclo 2025")
    canvas.drawRightString(letter[0] - 48, 29, str(doc.page))


def build(path, story):
    SimpleDocTemplate(str(path), pagesize=letter, leftMargin=48, rightMargin=48, topMargin=46, bottomMargin=56, title=path.stem, author="Leonardo Alvarez Gonzalez; Ángel de Jesús Elvis Gutiérrez Pacheco; Diego Cannata Cárdenas").build(story, onFirstPage=footer, onLaterPages=footer)


def markdown(text):
    story = []
    bibliography=text.startswith("# Fuentes y registro de asistencia de IA")
    for block in re.split(r"\n\s*\n", text.strip()):
        if block.startswith("## Bibliografía"):bibliography=True
        body_style="small" if bibliography else "body"
        if block.startswith("# "):
            story.append(paragraph(block[2:], "title"))
        elif block.startswith("## "):
            story.append(paragraph(block[3:], "heading"))
        elif block.startswith("- "):
            for line in block.splitlines():
                story.append(paragraph("• " + line.removeprefix("- "), "small"))
        elif block.startswith("> "):
            quote=paragraph(block.removeprefix("> "), "small")
            quote.keepWithNext=True
            story.append(quote)
        else:
            story.append(paragraph(block.replace("\n", " "), body_style))
    return story


team = json.loads((ROOT / "docs/team-contributions.json").read_text(encoding="utf-8"))
validation = json.loads((ROOT / "artifacts/validation.json").read_text(encoding="utf-8"))
with (ROOT / "artifacts/predictions_59.csv").open(encoding="utf-8", newline="") as stream:
    predictions = list(csv.DictReader(stream))
assert len(predictions) == 59 and len({r["ID_POLIGONO"] for r in predictions}) == 59
annex = [paragraph("Anexo 1. Predicciones oficiales", "title"), paragraph("59 parcelas de PREDICCION. Rendimiento estimado en toneladas por hectárea; corte de información: 31 de octubre de 2025. Los identificadores oficiales ID_POLIGONO se presentan como ID_parcela.", "small")]
rows = [["ID_parcela", "Rendimiento (t/ha)", "ID_parcela", "Rendimiento (t/ha)"]]
for i in range(30):
    row = []
    for position in [i, i + 30]:
        row.extend([predictions[position]["ID_POLIGONO"], f"{float(predictions[position]['RENDIMIENTO_T_HA']):.12f}"] if position < len(predictions) else ["", ""])
    rows.append(row)
table = Table(rows, colWidths=[72, 180, 72, 180], repeatRows=1, rowHeights=16)
table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Arial"), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("BACKGROUND", (0, 0), (-1, 0), green), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "ArialBold"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F5F2")]), ("ALIGN", (1, 1), (1, -1), "RIGHT"), ("ALIGN", (3, 1), (3, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEAFTER", (1, 0), (1, -1), 0.5, colors.HexColor("#CBD7D0"))]))
annex += [table, Spacer(1, 10), paragraph("Fuente: artifacts/predictions_59.csv. Se muestran 12 decimales por presentación; el CSV conserva la precisión original. Son estimaciones del modelo; los rendimientos reales de estas 59 parcelas permanecen ocultos.", "small"), PageBreak(), paragraph("Anexo 2. Evidencia e integrantes", "title"), paragraph("Validación espacial y trazabilidad", "subheading")]
summary = [["Procedimiento", "RMSE (t/ha)", "MAE (t/ha)", "R²"]]
for key, label in [("selected", "Selección anidada"), ("official", "Variante solo datos oficiales"), ("regional_mean", "Referencia: media regional")]:
    m = validation["metrics"][key]
    summary.append([label, f"{m['rmse']:.3f}", f"{m['mae']:.3f}", f"{m['r2']:.3f}"])
metric_table = Table(summary, colWidths=[243, 96, 96, 69], rowHeights=22)
metric_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Arial"), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("BACKGROUND", (0, 0), (-1, 0), green), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F5F2")])]))
interval=validation["interval"]
comparison="redujo" if validation["metrics"]["selected"]["rmse"]<validation["metrics"]["regional_mean"]["rmse"] else "no redujo"
sources=sorted({s for c in validation["final_selection"]["candidates"] for s in c["sources"]})
source_text="Fuentes externas del rendimiento final: "+(", ".join(sources) if sources else "ninguna; únicamente insumos del reto")+". NASA POWER y DGSIAP fueron comparadas dentro del entrenamiento."
annex += [metric_table, Spacer(1, 9), paragraph(f"Evaluación: 138 parcelas y cinco grupos espaciales. La revisión {comparison} el RMSE frente a la media regional. Reutiliza las etiquetas del desarrollo; no es el test oculto. Intervalos nominales del 90%: cobertura {interval['coverage']:.1%}, amplitud {interval['mean_width']:.3f} t/ha; presentación {'admitida' if interval['available'] else 'no admitida'}, sin garantía por estado o campaña futura.", "small"), paragraph(source_text+" Fuentes, columnas, dependencias y hashes: data/processed/source-manifest.json y artifacts/contract_selected.json. Predicciones reproducidas desde el modelo local.", "small"), paragraph("Integrantes y aportaciones", "subheading")]
for member in team["members"]:
    annex.append(KeepTogether([paragraph(member["name"], "subheading"), paragraph(member["contributions"], "small")]))
annex += [paragraph("Distribución de aportaciones realizada por indicación del usuario; nombres proporcionados por el equipo. No constituye una auditoría individual del historial de trabajo.", "small"), paragraph("Asistencia de IA", "subheading"), paragraph("Se utilizó OpenAI Codex como asistencia en revisión, programación, documentación y maquetación. Bibliografía, herramientas, prompts y sus propósitos se incluyen en agrocebada-bibliografia.pdf. La interpretación y revisión final corresponden al equipo.", "small")]
annex_path = OUT / "agrocebada-anexos.pdf"
build(annex_path, annex)
assert len(PdfReader(annex_path).pages) == 2, "Los anexos deben ocupar exactamente dos páginas"
bibliography_path = OUT / "agrocebada-bibliografia.pdf"
build(bibliography_path, markdown((ROOT / "docs/ai-tools-and-bibliography.md").read_text(encoding="utf-8")))
report_path = OUT / "agrocebada-informe-tecnico.pdf"
body = (ROOT / "docs/technical-report.md").read_text(encoding="utf-8").split("\n## Anexos\n", 1)[0]
build(report_path, markdown(body))
writer = PdfWriter()
writer.append(report_path)
writer.append(annex_path)
writer.write(report_path)
reader = PdfReader(annex_path)
annex_text = "\n".join(page.extract_text() for page in reader.pages)
for row in predictions:
    assert annex_text.count(row["ID_POLIGONO"]) == 1
    assert f"{float(row['RENDIMIENTO_T_HA']):.12f}" in annex_text
for member in team["members"]:
    assert member["name"] in annex_text
check_path = ROOT / "artifacts/technical-report-check.json"
check = json.loads(check_path.read_text(encoding="utf-8"))
check.update({"annex_pages": 2, "annex_predictions": 59, "annex_identifiers_verified": True, "annex_values_verified": True, "team_names_verified": True, "pdfs": {p.name: {"pages": len(PdfReader(p).pages), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [report_path, bibliography_path, annex_path]}})
check_path.write_text(json.dumps(check, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(check["pdfs"], ensure_ascii=False, indent=2))
