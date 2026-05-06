"""
PCR POC — Grounding dict → cell references.
Maps Gemini-extracted metric keys to (sheet, cell) tuples for openpyxl.
"""

from config import (
    SUMMARY_CELLS,
    TV_DATA_CELLS, TV_DETAIL_CELLS, TV_MARKET_ROWS,
    RADIO_DATA_CELLS, RADIO_DETAIL_CELLS, RADIO_NETWORK_ROWS,
    OOH_DATA_CELLS, OOH_DETAIL_CELLS, OOH_PROVIDER_ROWS,
    DIGITAL_DATA_CELLS, DIGITAL_DETAIL_CELLS, DIGITAL_VENDOR_ROWS,
    CINEMA_DATA_CELLS,
    CHANNEL_LABELS,
)


# ── Channel → detail cell mapping for commentary ──────────────────────────────
CHANNEL_COMMENTARY_CELLS = {
    "tv_regional":      TV_DETAIL_CELLS,
    "radio_metro":      RADIO_DETAIL_CELLS,
    "radio_regional":   RADIO_DETAIL_CELLS,
    "radio_cald":       RADIO_DETAIL_CELLS,
    "ooh_billboard":    OOH_DETAIL_CELLS,
    "ooh_indoor":       OOH_DETAIL_CELLS,
    "ooh_digital":      OOH_DETAIL_CELLS,
    "digital_biddable": DIGITAL_DETAIL_CELLS,
    "digital_direct":   DIGITAL_DETAIL_CELLS,
    "cinema":           {},  # no detail sheet for cinema in template
    "press":            {},
}


def map_tv_grounding(grounding_dict: dict) -> list[tuple[str, str, object]]:
    """
    Map TV grounding dict entries to (sheet, cell_address, value) triples.
    Keys expected:
      tarps_bought_{Market}, tarps_delivered_{Market},
      reach_planned_{Market}, reach_delivered_{Market},
      spend_gross_{Network}, bonus_gross_{Network}
    """
    writes = []

    for market, row in TV_MARKET_ROWS.items():
        safe = market.replace(" ", "_")
        for metric, col in [
            ("tarps_bought", "D"),
            ("tarps_delivered", "E"),
            ("reach_planned", "F"),
            ("reach_delivered", "G"),
        ]:
            key = f"{metric}_{safe}"
            if key in grounding_dict and grounding_dict[key] is not None:
                writes.append(("TV Data", f"{col}{row}", grounding_dict[key]))

    for network, cell in TV_DATA_CELLS["network_spend_gross"].items():
        safe = network.replace(" ", "_")
        key = f"spend_gross_{safe}"
        if key in grounding_dict and grounding_dict[key] is not None:
            writes.append((cell[0], cell[1], grounding_dict[key]))

    for network, cell in TV_DATA_CELLS["network_bonus_gross"].items():
        safe = network.replace(" ", "_")
        key = f"bonus_gross_{safe}"
        if key in grounding_dict and grounding_dict[key] is not None:
            writes.append((cell[0], cell[1], grounding_dict[key]))

    return writes


def map_radio_grounding(grounding_dict: dict) -> list[tuple[str, str, object]]:
    writes = []
    for network, row in RADIO_NETWORK_ROWS.items():
        safe = network.replace(" ", "_")
        for metric, col in [
            ("spots_booked", "D"),
            ("spots_delivered", "E"),
            ("spend_gross", "F"),
            ("bonus_gross", "G"),
        ]:
            key = f"{metric}_{safe}"
            if key in grounding_dict and grounding_dict[key] is not None:
                writes.append(("Radio Data", f"{col}{row}", grounding_dict[key]))
    return writes


def map_ooh_grounding(grounding_dict: dict) -> list[tuple[str, str, object]]:
    writes = []
    for provider, row in OOH_PROVIDER_ROWS.items():
        safe = provider.replace(" ", "_").replace("!", "")
        for metric, col in [
            ("panels_booked", "D"),
            ("panels_delivered", "E"),
            ("spend_gross", "F"),
            ("bonus_gross", "G"),
        ]:
            key = f"{metric}_{safe}"
            if key in grounding_dict and grounding_dict[key] is not None:
                writes.append(("OOH Data", f"{col}{row}", grounding_dict[key]))
    return writes


def map_digital_grounding(grounding_dict: dict) -> list[tuple[str, str, object]]:
    writes = []
    for vendor, row in DIGITAL_VENDOR_ROWS.items():
        safe = vendor.replace(" ", "_")
        for metric, col in [
            ("spend_gross", "D"),
            ("bonus_gross", "E"),
            ("impressions_booked", "F"),
            ("impressions_delivered", "G"),
            ("clicks", "H"),
            # J=CPM, K=CTR are formula cells — never write
        ]:
            key = f"{metric}_{safe}"
            if key in grounding_dict and grounding_dict[key] is not None:
                writes.append(("Direct Digi Data", f"{col}{row}", grounding_dict[key]))
    return writes


def map_cinema_grounding(grounding_dict: dict) -> list[tuple[str, str, object]]:
    writes = []
    for key, (sheet, cell) in CINEMA_DATA_CELLS.items():
        if key in grounding_dict and grounding_dict[key] is not None:
            writes.append((sheet, cell, grounding_dict[key]))
    return writes


# ── Channel dispatcher ────────────────────────────────────────────────────────

CHANNEL_MAPPERS = {
    "tv_regional":      map_tv_grounding,
    "radio_metro":      map_radio_grounding,
    "radio_regional":   map_radio_grounding,
    "radio_cald":       map_radio_grounding,
    "ooh_billboard":    map_ooh_grounding,
    "ooh_indoor":       map_ooh_grounding,
    "ooh_digital":      map_ooh_grounding,
    "digital_biddable": map_digital_grounding,
    "digital_direct":   map_digital_grounding,
    "cinema":           map_cinema_grounding,
}


def map_grounding_dict(channel: str, grounding_dict: dict) -> list[tuple[str, str, object]]:
    """
    Return list of (sheet, cell, value) write operations for a channel's grounding dict.
    Falls back to empty list for unmapped channels.
    """
    mapper = CHANNEL_MAPPERS.get(channel)
    if mapper is None:
        return []
    return mapper(grounding_dict)


def map_commentary(channel: str, commentary: dict) -> list[tuple[str, str, object]]:
    """
    Return (sheet, cell, value) triples for highlights/learnings/recommendations.
    """
    detail_cells = CHANNEL_COMMENTARY_CELLS.get(channel, {})
    writes = []
    for section in ("highlights", "learnings", "recommendations"):
        if section in detail_cells and section in commentary:
            sheet, cell = detail_cells[section]
            writes.append((sheet, cell, commentary[section]))
    return writes


def map_summary_fields(form_data: dict) -> list[tuple[str, str, object]]:
    """Map campaign form fields to PCR Summary cells."""
    writes = []
    for field, value in form_data.items():
        if field in SUMMARY_CELLS and value:
            sheet, cell = SUMMARY_CELLS[field]
            writes.append((sheet, cell, value))
    return writes


# ── Unit test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Smoke test with known inputs
    tv_grounding = {
        "tarps_bought_Regional_VIC": 120,
        "tarps_delivered_Regional_VIC": 118,
        "spend_gross_WIN": 45000,
        "bonus_gross_WIN": 5000,
    }
    writes = map_grounding_dict("tv_regional", tv_grounding)
    print("TV writes:")
    for w in writes:
        print(f"  {w[0]} {w[1]} = {w[2]}")

    commentary = {
        "highlights": "Campaign delivered 98% of planned TARPs.",
        "learnings": "WIN network outperformed benchmarks.",
        "recommendations": "Increase WIN weighting in future buys.",
    }
    c_writes = map_commentary("tv_regional", commentary)
    print("\nTV commentary writes:")
    for w in c_writes:
        print(f"  {w[0]} {w[1]} = {w[2]!r}")

    print("\nAll mapper tests passed.")
