"""
PCR POC — openpyxl PCR template writer.

Rules enforced here:
  - Always copy blank template — never modify it in place
  - Write to Data/Detail sheets only
  - Never overwrite formula cells (data_type == 'f')
  - Never write to columns J or K in Direct Digi Data
  - PCR Summary sheet name has a trailing space: "PCR Summary "
  - All spend/bonus values must be Gross before calling this module
"""

import shutil
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from mapper import map_grounding_dict, map_commentary, map_summary_fields

TEMPLATE_PATH = Path(__file__).parent / "templates" / "OMD - PCR - Tier B and C Template 1 (1).xlsx"

# Columns that are always formula-calculated in Direct Digi Data — never write
DIGI_FORMULA_COLS = {"J", "K"}


def _safe_cell_address(cell_ref: str) -> tuple[str, int]:
    """Split 'D19' into ('D', 19)."""
    col = "".join(c for c in cell_ref if c.isalpha()).upper()
    row = int("".join(c for c in cell_ref if c.isdigit()))
    return col, row


def _is_formula_cell(ws, cell_ref: str) -> bool:
    col, row = _safe_cell_address(cell_ref)
    cell = ws[cell_ref]
    return cell.data_type == "f" or (
        isinstance(cell.value, str) and cell.value.startswith("=")
    )


def _write_cell(ws, sheet_name: str, cell_ref: str, value: Any, log: dict) -> None:
    col, row = _safe_cell_address(cell_ref)

    # Guard: never write formula-calculated columns in Direct Digi Data
    if sheet_name == "Direct Digi Data" and col in DIGI_FORMULA_COLS:
        log["skipped"].append(f"{sheet_name}!{cell_ref} — formula column (J/K protected)")
        return

    # Guard: never overwrite formula cells
    if _is_formula_cell(ws, cell_ref):
        log["skipped"].append(f"{sheet_name}!{cell_ref} — formula cell protected")
        return

    if value is None or (isinstance(value, str) and value.strip() == ""):
        log["data_required"].append(f"{sheet_name}!{cell_ref}")
        ws[cell_ref] = "[DATA REQUIRED]"
    else:
        ws[cell_ref] = value
        log["written"].append(f"{sheet_name}!{cell_ref} = {value!r}")


def write_pcr(
    output_path: str | Path,
    all_insights: dict[str, dict],
    form_data: dict,
    template_path: str | Path = TEMPLATE_PATH,
) -> dict:
    """
    Write a populated PCR Excel from insights + form data.

    Parameters
    ----------
    output_path    Destination path for the populated PCR.
    all_insights   Dict keyed by channel — each value is the insight result dict
                   containing grounding_dict and commentary.
    form_data      Campaign metadata from the Screen 3 form.
    template_path  Path to blank PCR template (default: templates/PCR_BLANK_TEMPLATE.xlsx).

    Returns
    -------
    log dict with keys: written, data_required, skipped, errors, unmapped
    """
    template_path = Path(template_path)
    output_path = Path(output_path)

    if not template_path.exists():
        raise FileNotFoundError(
            f"PCR template not found at {template_path}. "
            "Place PCR_BLANK_TEMPLATE.xlsx in the templates/ folder."
        )

    # Always copy — never modify the template
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    wb = load_workbook(output_path)

    log = {
        "written": [],
        "data_required": [],
        "skipped": [],
        "errors": [],
        "unmapped": [],
    }

    def get_sheet(name: str):
        if name in wb.sheetnames:
            return wb[name]
        log["errors"].append(f"Sheet not found in template: {name!r}")
        return None

    # ── 1. Campaign summary fields ────────────────────────────────────────────
    summary_writes = map_summary_fields(form_data)
    for sheet_name, cell_ref, value in summary_writes:
        ws = get_sheet(sheet_name)
        if ws:
            _write_cell(ws, sheet_name, cell_ref, value, log)

    # ── 2. Channel data + commentary ─────────────────────────────────────────
    for channel, insight in all_insights.items():
        grounding_dict = insight.get("grounding_dict", {})
        commentary = insight.get("commentary", {})

        # Metric writes
        metric_writes = map_grounding_dict(channel, grounding_dict)
        for sheet_name, cell_ref, value in metric_writes:
            ws = get_sheet(sheet_name)
            if ws:
                _write_cell(ws, sheet_name, cell_ref, value, log)

        # Log grounding dict keys that produced no cell writes
        if not metric_writes and grounding_dict:
            log["unmapped"].extend(
                [f"{channel}: {k}" for k in grounding_dict.keys()]
            )

        # Commentary writes
        commentary_writes = map_commentary(channel, commentary)
        for sheet_name, cell_ref, value in commentary_writes:
            ws = get_sheet(sheet_name)
            if ws:
                _write_cell(ws, sheet_name, cell_ref, value, log)

    # ── 3. PCR Summary campaign commentary (row 56) ───────────────────────────
    # Campaign summary is stored under form_data keys summary_highlights etc.
    # These are already handled by map_summary_fields above.

    # ── 4. Save ───────────────────────────────────────────────────────────────
    wb.save(output_path)
    wb.close()

    return log


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys
    from pathlib import Path

    if len(sys.argv) < 3:
        print("Usage: python writer.py <insights.json> <output.xlsx>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        payload = json.load(f)

    log = write_pcr(
        output_path=sys.argv[2],
        all_insights=payload.get("insights", {}),
        form_data=payload.get("form_data", {}),
    )

    print("Written:", log["written"])
    print("Data required:", log["data_required"])
    print("Skipped:", log["skipped"])
    print("Errors:", log["errors"])
    print("Unmapped:", log["unmapped"])
