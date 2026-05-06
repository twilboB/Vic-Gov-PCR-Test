"""
PCR POC — Central configuration.
All cell references, model settings, and default prompts live here.
"""

# ── Vertex AI ────────────────────────────────────────────────────────────────
GCP_PROJECT = "res-apac-dev-skynet-au"
GCP_LOCATION = "us-central1"
GEMINI_MODEL = "gemini-2.5-pro"

# ── Channel taxonomy ─────────────────────────────────────────────────────────
CHANNELS = [
    "tv_regional",
    "radio_metro",
    "radio_regional",
    "radio_cald",
    "cinema",
    "press",
    "ooh_billboard",
    "ooh_indoor",
    "ooh_digital",
    "digital_biddable",
    "digital_direct",
    "unknown",
]

# Human-readable labels for UI
CHANNEL_LABELS = {
    "tv_regional":     "TV (Regional)",
    "radio_metro":     "Radio (Metro)",
    "radio_regional":  "Radio (Regional)",
    "radio_cald":      "Radio (CALD)",
    "cinema":          "Cinema",
    "press":           "Press",
    "ooh_billboard":   "OOH — Billboard",
    "ooh_indoor":      "OOH — Indoor",
    "ooh_digital":     "OOH — Digital",
    "digital_biddable": "Digital (Biddable)",
    "digital_direct":  "Digital (Direct)",
    "unknown":         "Unknown",
}

# ── PCR Summary — writable cells ─────────────────────────────────────────────
# Sheet name has a trailing space — this is correct per the template.
PCR_SUMMARY_SHEET = "PCR Summary "

SUMMARY_CELLS = {
    "department":        ("PCR Summary ", "D7"),
    "campaign_name":     ("PCR Summary ", "D8"),
    "contact_name":      ("PCR Summary ", "D9"),
    "contact_email":     ("PCR Summary ", "D10"),
    "contact_phone":     ("PCR Summary ", "D11"),
    "mams_number":       ("PCR Summary ", "D12"),
    "tier":              ("PCR Summary ", "D13"),
    "buying_audience":   ("PCR Summary ", "F9"),
    "campaign_timing":   ("PCR Summary ", "F10"),
    "regional_budget":   ("PCR Summary ", "D27"),
    "cald_budget":       ("PCR Summary ", "D28"),
    "digital_budget":    ("PCR Summary ", "D29"),
    # Campaign commentary — row 56
    "summary_highlights":       ("PCR Summary ", "D56"),
    "summary_learnings":        ("PCR Summary ", "E56"),
    "summary_recommendations":  ("PCR Summary ", "F56"),
}

# ── TV Data cells ─────────────────────────────────────────────────────────────
# Markets: Sydney, Melbourne, Brisbane, Adelaide, Perth, Regional NSW,
#          Regional VIC, Regional QLD, Regional SA, Regional WA
TV_MARKET_ROWS = {
    "Sydney":         7,
    "Melbourne":      8,
    "Brisbane":       9,
    "Adelaide":       10,
    "Perth":          11,
    "Regional NSW":   12,
    "Regional VIC":   13,
    "Regional QLD":   14,
    "Regional SA":    15,
    "Regional WA":    16,
}

TV_DATA_CELLS = {
    # TARPs — D bought, E delivered (per market row above)
    "tarps_bought":    ("TV Data", "D", TV_MARKET_ROWS),
    "tarps_delivered": ("TV Data", "E", TV_MARKET_ROWS),
    "reach_planned":   ("TV Data", "F", TV_MARKET_ROWS),
    "reach_delivered": ("TV Data", "G", TV_MARKET_ROWS),
    # Network spend/bonus — gross — D19:D26 / F19:F26
    "network_spend_gross": {
        "Seven":   ("TV Data", "D19"),
        "Nine":    ("TV Data", "D20"),
        "Ten":     ("TV Data", "D21"),
        "SBS":     ("TV Data", "D22"),
        "SAS":     ("TV Data", "D23"),
        "SCA":     ("TV Data", "D24"),
        "WIN":     ("TV Data", "D25"),
        "SBS Reg": ("TV Data", "D26"),
    },
    "network_bonus_gross": {
        "Seven":   ("TV Data", "F19"),
        "Nine":    ("TV Data", "F20"),
        "Ten":     ("TV Data", "F21"),
        "SBS":     ("TV Data", "F22"),
        "SAS":     ("TV Data", "F23"),
        "SCA":     ("TV Data", "F24"),
        "WIN":     ("TV Data", "F25"),
        "SBS Reg": ("TV Data", "F26"),
    },
}

TV_DETAIL_CELLS = {
    "budget_nett":        ("TV Detail", "F9"),  # only nett input in template
    "highlights":         ("TV Detail", "D17"),
    "learnings":          ("TV Detail", "E17"),
    "recommendations":    ("TV Detail", "F17"),
}

# ── Radio Data cells ──────────────────────────────────────────────────────────
# Networks occupy rows 3–12 in Radio Data
RADIO_NETWORK_ROWS = {
    "NOVA":       3,
    "ARN":        4,
    "SCA":        5,
    "ABC":        6,
    "Ethnic":     7,
    "Vision AU":  8,
    "3ZZZ":       9,
    "SBS Radio":  10,
    "Other":      11,
    "Total":      12,
}

RADIO_DATA_CELLS = {
    "spots_booked":    ("Radio Data", "D", RADIO_NETWORK_ROWS),
    "spots_delivered": ("Radio Data", "E", RADIO_NETWORK_ROWS),
    "spend_gross":     ("Radio Data", "F", RADIO_NETWORK_ROWS),
    "bonus_gross":     ("Radio Data", "G", RADIO_NETWORK_ROWS),
}

RADIO_DETAIL_CELLS = {
    "highlights":      ("Radio Detail", "D15"),
    "learnings":       ("Radio Detail", "E15"),
    "recommendations": ("Radio Detail", "F15"),
}

# ── OOH Data cells ────────────────────────────────────────────────────────────
OOH_PROVIDER_ROWS = {
    "oOh!":         3,
    "JCDecaux":     4,
    "QMS":          5,
    "Bishopp":      6,
    "goa":          7,
    "Adshel":       8,
    "APN":          9,
    "Other":        10,
    "Total":        15,
}

OOH_DATA_CELLS = {
    "panels_booked":    ("OOH Data", "D", OOH_PROVIDER_ROWS),
    "panels_delivered": ("OOH Data", "E", OOH_PROVIDER_ROWS),
    "spend_gross":      ("OOH Data", "F", OOH_PROVIDER_ROWS),
    "bonus_gross":      ("OOH Data", "G", OOH_PROVIDER_ROWS),
}

OOH_DETAIL_CELLS = {
    "highlights":      ("OOH Detail", "D15"),
    "learnings":       ("OOH Detail", "E15"),
    "recommendations": ("OOH Detail", "F15"),
}

# ── Digital Direct Data cells ─────────────────────────────────────────────────
# Columns: D spend_gross, E bonus_gross, F impressions_booked, G impressions_delivered,
#          H clicks — J and K are formula-calculated (CPM, CTR) — never write these
DIGITAL_VENDOR_ROWS = {
    "Teads":       3,
    "DoubleVerify": 4,
    "Spotify":     5,
    "YouTube":     6,
    "LinkedIn":    7,
    "Meta":        8,
    "DV360":       9,
    "Xandr":       10,
    "Other":       11,
    "Total":       12,
}

DIGITAL_DATA_CELLS = {
    "spend_gross":           ("Direct Digi Data", "D", DIGITAL_VENDOR_ROWS),
    "bonus_gross":           ("Direct Digi Data", "E", DIGITAL_VENDOR_ROWS),
    "impressions_booked":    ("Direct Digi Data", "F", DIGITAL_VENDOR_ROWS),
    "impressions_delivered": ("Direct Digi Data", "G", DIGITAL_VENDOR_ROWS),
    "clicks":                ("Direct Digi Data", "H", DIGITAL_VENDOR_ROWS),
    # J = CPM (formula), K = CTR (formula) — never write
}

DIGITAL_DETAIL_CELLS = {
    "highlights":      ("Direct Digi Detail", "D15"),
    "learnings":       ("Direct Digi Detail", "F15"),   # note: D/F/H not D/E/F
    "recommendations": ("Direct Digi Detail", "H15"),
}

# ── Cinema Data cells ─────────────────────────────────────────────────────────
CINEMA_DATA_CELLS = {
    "audience_est_metro":       ("Cinema Data", "D3"),
    "audience_del_metro":       ("Cinema Data", "E3"),
    "spend_gross_metro":        ("Cinema Data", "F3"),
    "bonus_gross_metro":        ("Cinema Data", "G3"),
    "audience_est_regional":    ("Cinema Data", "D4"),
    "audience_del_regional":    ("Cinema Data", "E4"),
    "spend_gross_regional":     ("Cinema Data", "F4"),
    "bonus_gross_regional":     ("Cinema Data", "G4"),
    "audience_est_total":       ("Cinema Data", "D5"),
    "audience_del_total":       ("Cinema Data", "E5"),
    "spend_gross_total":        ("Cinema Data", "F5"),
    "bonus_gross_total":        ("Cinema Data", "G5"),
}

# ── Default prompts ───────────────────────────────────────────────────────────
SCAN_PROMPT = """You are a media analyst at an Australian media agency reviewing post-campaign data files.

Analyse the file content below and return JSON only — no explanation, no markdown.

Identify:
1. Which media channel this file relates to:
   tv_regional | radio_metro | radio_regional | radio_cald | cinema |
   press | ooh_billboard | ooh_indoor | ooh_digital |
   digital_biddable | digital_direct | unknown
2. Which vendor produced it
3. What format it is (OMD PCA template, MOVE PDF, eRAM RF, ATN spots, vendor native, unknown)
4. All numeric metric values present in the file
5. Any data quality issues

Rules:
- Never invent or estimate — return null for anything missing
- If a file contains multiple channels, return the primary and note the secondary in issues
- Note whether spend figures appear Gross or Nett
- If channel cannot be determined, return channel: "unknown"

Return format:
{
  "filename": "string",
  "channel": "string",
  "vendor": "string",
  "format_detected": "string",
  "status": "ready | partial | unreadable | unclassified",
  "issues": ["list of strings"],
  "metrics": {
    "spend_gross": null,
    "spend_nett": null,
    "bonus_gross": null,
    "bonus_nett": null
  },
  "raw_summary": "2-3 sentence plain English summary"
}

FILE CONTENT:
{file_text}
"""

DEFAULT_INSIGHT_PROMPT = """You are a senior media analyst writing post-campaign insights for a government client report in Australia.

You have been given scan results from one or more files relating to the {channel} channel for campaign: {campaign_name}

Scan results:
{scan_results_json}

Your task:
1. Consolidate all metrics into a single grounding dict
2. Generate three commentary sections — Highlights, Learnings, Recommendations
3. Return JSON only — no explanation, no markdown

Rules:
- Only reference metrics present in the scan results above
- Write [DATA REQUIRED] for any missing metric — never estimate
- Maximum {word_limit} words per section — do not pad to the limit
- Tone: {tone}
- Australian spelling and conventions
- All spend figures in AUD

Return format:
{
  "channel": "string",
  "grounding_dict": { "...all metrics used..." },
  "commentary": {
    "highlights": "string",
    "learnings": "string",
    "recommendations": "string"
  },
  "data_gaps": ["metrics that were null or missing"],
  "confidence": "high | medium | low",
  "confidence_reason": "string"
}
"""

CAMPAIGN_SUMMARY_PROMPT = """You are a senior media analyst writing a cross-channel campaign summary for a government client report in Australia.

Campaign: {campaign_name}

You have been given the consolidated grounding dicts and commentary from all channels:
{all_channels_json}

Write a 150-word cross-channel summary that identifies:
- Cross-channel themes (e.g. regional bonus delivery, audience completion quality)
- Efficiency observations across channels
- Key recommendations for future campaigns

Rules:
- Only reference metrics present in the channel data above
- Write [DATA REQUIRED] for anything missing — never estimate
- Tone: {tone}
- Australian spelling and conventions
- Return JSON only — no explanation, no markdown

Return format:
{
  "campaign_summary": "string (max 150 words)",
  "cross_channel_themes": ["list of themes"],
  "data_gaps": ["any missing data that would improve this summary"]
}
"""

DEFAULT_WORD_LIMIT = 80
DEFAULT_TONE = "Government client — formal register, avoid superlatives, lead with efficiency metrics"
