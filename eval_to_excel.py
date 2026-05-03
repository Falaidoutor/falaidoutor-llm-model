"""
Converts eval_results.json into an Excel spreadsheet for comparison analysis.

Columns:
  - edstay_id
  - acuity_ground_truth     (ESI 1-5)
  - esi_label               (e.g. "1 - Ressuscitação")
  - llm_classificacao       (e.g. "ESI-1")
  - llm_nivel               (e.g. 1)
  - llm_confianca
  - match                   (SIM if ground truth ESI == LLM nivel)
  - validation_errors       (count)
  - validation_warnings     (count)

Summary sheet:
  - Confusion matrix: ESI ground truth (rows) x ESI LLM (columns)
  - Match count per ESI level
  - Total matches / accuracy

Usage:
    python eval_to_excel.py [--input PATH] [--output PATH]

Requires: openpyxl
    pip install openpyxl
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
    sys.exit(1)

DEFAULT_INPUT = Path(__file__).parent / "eval_results.json"
DEFAULT_OUTPUT = Path(__file__).parent / "eval_comparison.xlsx"

ESI_LABELS = {
    1: "1 - Ressuscitação",
    2: "2 - Emergente",
    3: "3 - Urgente",
    4: "4 - Menos urgente",
    5: "5 - Não urgente",
}

# ESI levels in priority order
ESI_LEVELS = ["ESI-1", "ESI-2", "ESI-3", "ESI-4", "ESI-5", "Indeterminado"]

ESI_FILLS = {
    1: PatternFill("solid", fgColor="FF4444"),
    2: PatternFill("solid", fgColor="FF9933"),
    3: PatternFill("solid", fgColor="FFE135"),
    4: PatternFill("solid", fgColor="44BB44"),
    5: PatternFill("solid", fgColor="5599FF"),
}

ESI_LEVEL_FILLS = {
    "ESI-1":         PatternFill("solid", fgColor="FF4444"),
    "ESI-2":         PatternFill("solid", fgColor="FF9933"),
    "ESI-3":         PatternFill("solid", fgColor="FFE135"),
    "ESI-4":         PatternFill("solid", fgColor="44BB44"),
    "ESI-5":         PatternFill("solid", fgColor="5599FF"),
    "Indeterminado": PatternFill("solid", fgColor="CCCCCC"),
}

MATCH_FILL_YES = PatternFill("solid", fgColor="C6EFCE")   # green
MATCH_FILL_NO  = PatternFill("solid", fgColor="FFC7CE")   # red

HEADER_FILL    = PatternFill("solid", fgColor="2D2D2D")
HEADER_FONT    = Font(bold=True, color="FFFFFF")
BOLD           = Font(bold=True)


def auto_width(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value or "")))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 60)


def style_header_row(ws, row=1):
    for cell in ws[row]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def build_detail_sheet(wb, records: list[dict]):
    ws = wb.active
    ws.title = "Resultados"

    headers = [
        "edstay_id",
        "acuity_ground_truth",
        "esi_label",
        "llm_classificacao",
        "llm_nivel",
        "llm_confianca",
        "match",
        "validation_errors",
        "validation_warnings",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.row_dimensions[1].height = 30

    for rec in records:
        esi = rec.get("acuity_ground_truth")
        llm = rec.get("llm_response") or {}
        classificacao = llm.get("classificacao", "Indeterminado")
        llm_nivel = llm.get("nivel")
        is_match = llm_nivel == esi

        row_data = [
            rec.get("edstay_id"),
            esi,
            ESI_LABELS.get(esi, str(esi)),
            classificacao,
            llm_nivel,
            llm.get("confianca", ""),
            "SIM" if is_match else "NÃO",
            len(llm.get("validation_errors") or []),
            len(llm.get("validation_warnings") or []),
        ]
        ws.append(row_data)

        row_idx = ws.max_row
        # Color: acuity_ground_truth (col B)
        if esi in ESI_FILLS:
            ws.cell(row_idx, 2).fill = ESI_FILLS[esi]
        # Color: llm_classificacao (col D)
        if classificacao in ESI_LEVEL_FILLS:
            ws.cell(row_idx, 4).fill = ESI_LEVEL_FILLS[classificacao]
        # Color: llm_nivel (col E)
        if llm_nivel in ESI_FILLS:
            ws.cell(row_idx, 5).fill = ESI_FILLS[llm_nivel]
        # Color: match (col G)
        ws.cell(row_idx, 7).fill = MATCH_FILL_YES if is_match else MATCH_FILL_NO
        ws.cell(row_idx, 7).font = BOLD
        ws.cell(row_idx, 7).alignment = Alignment(horizontal="center")

    ws.freeze_panes = "A2"
    auto_width(ws)


def build_summary_sheet(wb, records: list[dict]):
    ws = wb.create_sheet("Resumo")

    # ── Section 1: Match count per ESI level ──────────────────────────────
    ws.append(["ACERTOS POR NÍVEL ESI"])
    ws["A1"].font = Font(bold=True, size=12)

    ws.append(["ESI", "Label", "Total", "Acertos", "Taxa de Acerto (%)"])
    style_header_row(ws, row=2)

    esi_totals = {i: 0 for i in range(1, 6)}
    esi_matches = {i: 0 for i in range(1, 6)}

    for rec in records:
        esi = rec.get("acuity_ground_truth")
        llm = rec.get("llm_response") or {}
        llm_nivel = llm.get("nivel")
        if esi in esi_totals:
            esi_totals[esi] += 1
            if llm_nivel == esi:
                esi_matches[esi] += 1

    for esi in range(1, 6):
        total = esi_totals[esi]
        matches = esi_matches[esi]
        rate = round(matches / total * 100, 1) if total > 0 else 0
        ws.append([esi, ESI_LABELS[esi], total, matches, rate])
        row_idx = ws.max_row
        ws.cell(row_idx, 1).fill = ESI_FILLS[esi]
        ws.cell(row_idx, 1).font = BOLD

    # Total row
    grand_total = sum(esi_totals.values())
    grand_matches = sum(esi_matches.values())
    grand_rate = round(grand_matches / grand_total * 100, 1) if grand_total > 0 else 0
    ws.append(["TOTAL", "", grand_total, grand_matches, grand_rate])
    for col in range(1, 6):
        ws.cell(ws.max_row, col).font = BOLD
        ws.cell(ws.max_row, col).fill = PatternFill("solid", fgColor="DDDDDD")

    ws.append([])  # blank row

    # ── Section 2: Confusion matrix ───────────────────────────────────────
    matrix_start_row = ws.max_row + 1
    ws.cell(matrix_start_row, 1).value = "MATRIZ DE CONFUSÃO (ESI Ground Truth vs. ESI LLM)"
    ws.cell(matrix_start_row, 1).font = Font(bold=True, size=12)

    header_row = matrix_start_row + 1
    ws.cell(header_row, 1).value = "GT \\ LLM →"
    ws.cell(header_row, 1).font = BOLD
    ws.cell(header_row, 1).fill = HEADER_FILL
    ws.cell(header_row, 1).font = Font(bold=True, color="FFFFFF")

    for col_idx, level in enumerate(ESI_LEVELS, start=2):
        cell = ws.cell(header_row, col_idx)
        cell.value = level
        cell.fill = ESI_LEVEL_FILLS.get(level, PatternFill("solid", fgColor="CCCCCC"))
        cell.font = BOLD
        cell.alignment = Alignment(horizontal="center")

    # Build matrix counts (key: LLM classificacao string e.g. "ESI-1")
    matrix = {esi: {lvl: 0 for lvl in ESI_LEVELS} for esi in range(1, 6)}
    for rec in records:
        esi = rec.get("acuity_ground_truth")
        llm = rec.get("llm_response") or {}
        classificacao = llm.get("classificacao", "Indeterminado")
        if esi in matrix:
            key = classificacao if classificacao in ESI_LEVELS else "Indeterminado"
            matrix[esi][key] += 1

    for esi in range(1, 6):
        row_idx = header_row + esi
        label_cell = ws.cell(row_idx, 1)
        label_cell.value = ESI_LABELS[esi]
        label_cell.fill = ESI_FILLS[esi]
        label_cell.font = BOLD

        expected_level = f"ESI-{esi}"
        for col_idx, level in enumerate(ESI_LEVELS, start=2):
            count = matrix[esi][level]
            cell = ws.cell(row_idx, col_idx)
            cell.value = count if count > 0 else ""
            cell.alignment = Alignment(horizontal="center")
            # Highlight diagonal (correct predictions)
            if level == expected_level and count > 0:
                cell.fill = MATCH_FILL_YES
                cell.font = Font(bold=True, color="375623")
            elif count > 0:
                cell.fill = MATCH_FILL_NO

    ws.append([])

    # ── Section 3: Distribution of LLM classifications per ESI ───────────
    dist_start = ws.max_row + 1
    ws.cell(dist_start, 1).value = "DISTRIBUIÇÃO DE CLASSIFICAÇÕES LLM POR NÍVEL ESI"
    ws.cell(dist_start, 1).font = Font(bold=True, size=12)

    dist_header = dist_start + 1
    ws.cell(dist_header, 1).value = "ESI"
    ws.cell(dist_header, 1).font = HEADER_FONT
    ws.cell(dist_header, 1).fill = HEADER_FILL
    for col_idx, level in enumerate(ESI_LEVELS, start=2):
        cell = ws.cell(dist_header, col_idx)
        cell.value = level
        cell.fill = ESI_LEVEL_FILLS.get(level, PatternFill("solid", fgColor="CCCCCC"))
        cell.font = BOLD
        cell.alignment = Alignment(horizontal="center")
    ws.cell(dist_header, len(ESI_LEVELS) + 2).value = "Total"
    ws.cell(dist_header, len(ESI_LEVELS) + 2).font = BOLD

    for esi in range(1, 6):
        row_idx = dist_header + esi
        ws.cell(row_idx, 1).value = esi
        ws.cell(row_idx, 1).fill = ESI_FILLS[esi]
        ws.cell(row_idx, 1).font = BOLD
        row_total = 0
        for col_idx, level in enumerate(ESI_LEVELS, start=2):
            count = matrix[esi][level]
            cell = ws.cell(row_idx, col_idx)
            cell.value = count if count > 0 else ""
            cell.alignment = Alignment(horizontal="center")
            if count > 0:
                cell.fill = ESI_LEVEL_FILLS.get(level, PatternFill("solid", fgColor="CCCCCC"))
                cell.font = Font(color="000000")
            row_total += count
        ws.cell(row_idx, len(ESI_LEVELS) + 2).value = row_total
        ws.cell(row_idx, len(ESI_LEVELS) + 2).font = BOLD

    auto_width(ws)


def main():
    parser = argparse.ArgumentParser(description="Convert eval_results.json to Excel comparison sheet.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with args.input.open(encoding="utf-8") as f:
        records = json.load(f)

    # Filter out records with errors and no llm_response
    valid = [r for r in records if r.get("llm_response") is not None]
    skipped = len(records) - len(valid)
    print(f"Loaded {len(records)} records ({skipped} with errors skipped).")

    wb = openpyxl.Workbook()
    build_detail_sheet(wb, valid)
    build_summary_sheet(wb, valid)

    wb.save(args.output)
    print(f"Saved: {args.output}")

    # Print quick stats to terminal
    total = len(valid)
    matches = sum(
        1 for r in valid
        if (r.get("llm_response") or {}).get("nivel") == r.get("acuity_ground_truth")
    )
    print(f"\nOverall accuracy: {matches}/{total} = {matches/total*100:.1f}%")
    print("\nPer ESI level:")
    for esi in range(1, 6):
        grp = [r for r in valid if r.get("acuity_ground_truth") == esi]
        hits = sum(
            1 for r in grp
            if (r.get("llm_response") or {}).get("nivel") == esi
        )
        print(f"  ESI {esi} ({ESI_LABELS[esi]:>20}): {hits:>3}/{len(grp):<3} = {hits/len(grp)*100:.1f}%" if grp else f"  ESI {esi}: 0 records")


if __name__ == "__main__":
    main()
