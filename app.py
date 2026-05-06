"""
PCR POC — Streamlit application.
Three screens: Scan → Insights → Export
"""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import (
    DEFAULT_INSIGHT_PROMPT, DEFAULT_WORD_LIMIT, DEFAULT_TONE,
    CHANNEL_LABELS, SUMMARY_CELLS,
)
from scanner import scan_folder, SUPPORTED_EXTENSIONS
from insights import (
    generate_channel_insights, generate_all_insights,
    generate_campaign_summary, group_results_by_channel,
)
from writer import write_pcr, TEMPLATE_PATH

OUTPUT_DIR = Path(__file__).parent / "output"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PCR Automation — POC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state initialisation ──────────────────────────────────────────────
if "screen" not in st.session_state:
    st.session_state.screen = 1
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "insights" not in st.session_state:
    st.session_state.insights = {}
if "campaign_summary" not in st.session_state:
    st.session_state.campaign_summary = None
if "edited_commentary" not in st.session_state:
    st.session_state.edited_commentary = {}
if "insight_prompt" not in st.session_state:
    st.session_state.insight_prompt = DEFAULT_INSIGHT_PROMPT
if "word_limit" not in st.session_state:
    st.session_state.word_limit = DEFAULT_WORD_LIMIT
if "tone" not in st.session_state:
    st.session_state.tone = DEFAULT_TONE
if "campaign_name" not in st.session_state:
    st.session_state.campaign_name = ""


# ── Navigation helpers ────────────────────────────────────────────────────────
def go_to(screen: int):
    st.session_state.screen = screen


def status_icon(status: str) -> str:
    return {
        "ready": "✅",
        "partial": "⚠️",
        "unreadable": "❌",
        "unclassified": "⚠️",
    }.get(status, "❓")


def confidence_badge(level: str) -> str:
    colours = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    return f"{colours.get(level, '⚪')} {level.capitalize()}"


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1 — SCAN
# ─────────────────────────────────────────────────────────────────────────────

def screen_scan():
    st.title("PCR Automation — POC")
    st.subheader("Step 1 — Scan Campaign Files")

    folder_path = st.text_input(
        "Campaign folder path",
        placeholder="/Users/you/Desktop/Vic gov pcr test",
        help="Paste the full path to the folder containing campaign files.",
    )

    campaign_name = st.text_input(
        "Campaign name",
        value=st.session_state.campaign_name or "",
        placeholder="C60161 Victorian Fire Season",
    )

    scan_clicked = st.button("Scan", type="primary", disabled=not folder_path)

    if scan_clicked and folder_path:
        st.session_state.campaign_name = campaign_name or Path(folder_path).name
        st.session_state.scan_results = None
        st.session_state.insights = {}
        st.session_state.campaign_summary = None
        st.session_state.edited_commentary = {}

        progress_bar = st.progress(0, text="Initialising...")
        status_text = st.empty()
        results_placeholder = st.empty()

        results = []
        try:
            folder = Path(folder_path)
            all_files = sorted(
                [f for f in folder.iterdir()
                 if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
            )
            total = max(len(all_files), 1)

            def on_progress(name, i, n):
                pct = int((i / max(n, 1)) * 100)
                progress_bar.progress(pct, text=f"Scanning {name}...")
                status_text.text(f"File {i+1} of {n}: {name}")

            results = scan_folder(folder_path, progress_callback=on_progress)
            progress_bar.progress(100, text="Scan complete.")
            status_text.empty()
        except Exception as exc:
            st.error(f"Scan failed: {exc}")
            return

        st.session_state.scan_results = results

    # ── Results display ───────────────────────────────────────────────────────
    if st.session_state.scan_results:
        results = st.session_state.scan_results

        # Summary stats
        channels_found = {
            r["channel"] for r in results
            if r["channel"] not in ("unknown", None)
        }
        unreadable = [r for r in results if r["status"] == "unreadable"]
        blockers = [r for r in results if r["status"] == "unreadable"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Files found", len(results))
        col2.metric("Channels detected", len(channels_found))
        col3.metric("Unreadable", len(unreadable))
        col4.metric("Blockers", len(blockers))

        st.markdown("### Scan Results")

        table_data = []
        for r in results:
            issues_str = "; ".join(r.get("issues", [])) if r.get("issues") else "—"
            table_data.append({
                "File": r["filename"],
                "Channel": CHANNEL_LABELS.get(r.get("channel", "unknown"), r.get("channel", "unknown")),
                "Vendor": r.get("vendor") or "—",
                "Format": r.get("format_detected") or "—",
                "Status": f"{status_icon(r.get('status',''))} {r.get('status','').capitalize()}",
                "Issues": issues_str,
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

        # Expand to see raw metrics per file
        with st.expander("View raw metrics by file"):
            for r in results:
                st.markdown(f"**{r['filename']}**")
                metrics = r.get("metrics", {})
                if metrics:
                    st.json(metrics)
                else:
                    st.caption("No metrics extracted.")
                st.caption(r.get("raw_summary", ""))

        if blockers:
            st.warning(
                f"{len(blockers)} file(s) could not be read. "
                "Resolve these before proceeding to ensure full coverage."
            )

        can_proceed = any(
            r.get("channel") not in ("unknown", None)
            and r.get("status") != "unreadable"
            for r in results
        )

        if st.button(
            "Generate Insights →",
            type="primary",
            disabled=not can_proceed,
        ):
            go_to(2)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2 — INSIGHTS & PROMPT EDITOR
# ─────────────────────────────────────────────────────────────────────────────

def screen_insights():
    # ── Sidebar prompt editor ─────────────────────────────────────────────────
    with st.sidebar:
        st.header("Prompt Editor")

        st.session_state.insight_prompt = st.text_area(
            "Insight Generation Prompt — edit to adjust tone, focus areas, or output structure.",
            value=st.session_state.insight_prompt,
            height=300,
        )

        col_reset, col_save = st.columns(2)
        with col_reset:
            if st.button("Reset to default"):
                st.session_state.insight_prompt = DEFAULT_INSIGHT_PROMPT
                st.rerun()
        with col_save:
            if st.button("Save prompt"):
                st.success("Prompt saved to session.")

        st.divider()

        st.session_state.word_limit = st.slider(
            "Max words per section",
            min_value=40,
            max_value=150,
            value=st.session_state.word_limit,
        )

        st.session_state.tone = st.text_input(
            "Tone instruction",
            value=st.session_state.tone,
        )

    st.title("PCR Automation — POC")
    st.subheader("Step 2 — Insights & Commentary")

    scan_results = st.session_state.scan_results
    campaign_name = st.session_state.campaign_name or "Unknown Campaign"

    if not scan_results:
        st.warning("No scan results. Go back to Step 1.")
        if st.button("← Back to Scan"):
            go_to(1)
            st.rerun()
        return

    grouped = group_results_by_channel(scan_results)

    # ── Generate all insights if not yet done ─────────────────────────────────
    if not st.session_state.insights:
        if st.button("Generate All Insights", type="primary"):
            progress_bar = st.progress(0, text="Initialising...")
            channels = list(grouped.keys())

            insights = {}
            for i, channel in enumerate(channels):
                pct = int((i / max(len(channels), 1)) * 100)
                progress_bar.progress(pct, text=f"Generating {CHANNEL_LABELS.get(channel, channel)}...")

                result = generate_channel_insights(
                    channel=channel,
                    scan_results=grouped[channel],
                    campaign_name=campaign_name,
                    prompt_template=st.session_state.insight_prompt,
                    word_limit=st.session_state.word_limit,
                    tone=st.session_state.tone,
                )
                insights[channel] = result

            # Initialise edited_commentary from generated commentary
            for channel, data in insights.items():
                if channel not in st.session_state.edited_commentary:
                    st.session_state.edited_commentary[channel] = dict(
                        data.get("commentary", {})
                    )

            progress_bar.progress(80, text="Generating campaign summary...")
            st.session_state.insights = insights
            st.session_state.campaign_summary = generate_campaign_summary(
                insights, campaign_name, tone=st.session_state.tone
            )
            progress_bar.progress(100, text="Done.")
            st.rerun()
        return

    # ── Channel tabs + campaign summary ───────────────────────────────────────
    channel_list = list(st.session_state.insights.keys())
    tab_labels = [CHANNEL_LABELS.get(ch, ch) for ch in channel_list] + ["Campaign Summary"]
    tabs = st.tabs(tab_labels)

    for tab, channel in zip(tabs[:-1], channel_list):
        with tab:
            insight = st.session_state.insights[channel]
            grounding = insight.get("grounding_dict", {})
            commentary = insight.get("commentary", {})
            data_gaps = insight.get("data_gaps", [])
            confidence = insight.get("confidence", "low")

            col_header, col_badge = st.columns([4, 1])
            with col_header:
                st.markdown(f"### {CHANNEL_LABELS.get(channel, channel)}")
            with col_badge:
                st.markdown(confidence_badge(confidence))

            if data_gaps:
                st.info(f"Data gaps: {', '.join(data_gaps)}")

            col_metrics, col_commentary = st.columns([2, 3])

            with col_metrics:
                st.markdown("**Metrics**")
                if grounding:
                    for k, v in grounding.items():
                        colour = "🟡" if v is None else ""
                        display_v = "[DATA REQUIRED]" if v is None else v
                        st.markdown(f"`{k}` {colour} **{display_v}**")
                else:
                    st.caption("No metrics extracted.")

            with col_commentary:
                for section in ("highlights", "learnings", "recommendations"):
                    text = st.session_state.edited_commentary.get(channel, {}).get(section, "")
                    with st.expander(section.capitalize(), expanded=True):
                        word_count = len(text.split()) if text else 0
                        edited = st.text_area(
                            label=f"{section} ({word_count} words)",
                            value=text,
                            height=120,
                            key=f"edit_{channel}_{section}",
                        )
                        if edited != text:
                            st.session_state.edited_commentary.setdefault(channel, {})[section] = edited

            # Per-channel regenerate
            if st.button(f"Regenerate {CHANNEL_LABELS.get(channel, channel)}", key=f"regen_{channel}"):
                with st.spinner("Regenerating..."):
                    result = generate_channel_insights(
                        channel=channel,
                        scan_results=grouped[channel],
                        campaign_name=campaign_name,
                        prompt_template=st.session_state.insight_prompt,
                        word_limit=st.session_state.word_limit,
                        tone=st.session_state.tone,
                    )
                    st.session_state.insights[channel] = result
                    st.session_state.edited_commentary[channel] = dict(
                        result.get("commentary", {})
                    )
                st.rerun()

    # ── Campaign Summary tab ───────────────────────────────────────────────────
    with tabs[-1]:
        st.markdown("### Campaign Summary")
        summary = st.session_state.campaign_summary

        if summary:
            themes = summary.get("cross_channel_themes", [])
            if themes:
                st.markdown("**Cross-channel themes:**")
                for t in themes:
                    st.markdown(f"- {t}")

            summary_text = summary.get("campaign_summary", "")
            edited_summary = st.text_area(
                "Campaign summary (editable)",
                value=summary_text,
                height=150,
                key="edit_campaign_summary",
            )
            if edited_summary != summary_text:
                st.session_state.campaign_summary["campaign_summary"] = edited_summary

            if summary.get("data_gaps"):
                st.info(f"Data gaps: {', '.join(summary['data_gaps'])}")

        if st.button("Regenerate Summary"):
            with st.spinner("Regenerating..."):
                st.session_state.campaign_summary = generate_campaign_summary(
                    st.session_state.insights,
                    campaign_name,
                    tone=st.session_state.tone,
                )
            st.rerun()

    st.divider()
    col_back, _, col_next = st.columns([1, 6, 1])
    with col_back:
        if st.button("← Back"):
            go_to(1)
            st.rerun()
    with col_next:
        if st.button("Export →", type="primary"):
            go_to(3)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3 — EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def screen_export():
    st.title("PCR Automation — POC")
    st.subheader("Step 3 — Export PCR")

    scan_results = st.session_state.scan_results or []
    insights = st.session_state.insights
    campaign_summary = st.session_state.campaign_summary

    # Try to pre-populate fields from scan results
    def first_non_null(key):
        for r in scan_results:
            metrics = r.get("metrics", {})
            if key in metrics and metrics[key]:
                return metrics[key]
        return ""

    st.markdown("### Campaign Details")
    st.caption("Pre-populated where detected from scan results. Confirm or edit before export.")

    with st.form("campaign_form"):
        col1, col2 = st.columns(2)
        with col1:
            department = st.text_input("Client / Department", value="")
            campaign_name = st.text_input(
                "Campaign name",
                value=st.session_state.campaign_name or "",
            )
            contact_name = st.text_input("Contact name", value="")
            contact_email = st.text_input("Contact email", value="")
            contact_phone = st.text_input("Contact phone", value="")
            mams_number = st.text_input("MAMS number", value="")

        with col2:
            tier = st.selectbox("Tier", options=["", "B", "C"])
            buying_audience = st.text_input("Buying audience", value="P18+")
            campaign_timing = st.text_input(
                "Campaign timing",
                value=first_non_null("campaign_timing") or "",
                placeholder="e.g. Oct 2025 – Feb 2026",
            )
            regional_budget = st.number_input("Regional budget (Gross $)", value=0.0, min_value=0.0)
            cald_budget = st.number_input("CALD budget (Gross $)", value=0.0, min_value=0.0)
            digital_budget = st.number_input("Digital budget (Gross $)", value=0.0, min_value=0.0)

        export_clicked = st.form_submit_button("Export PCR Excel", type="primary")

    if export_clicked:
        if not TEMPLATE_PATH.exists():
            st.error(
                f"PCR template not found at `{TEMPLATE_PATH}`.\n\n"
                "Place `PCR_BLANK_TEMPLATE.xlsx` in the `templates/` folder and try again."
            )
            return

        form_data = {
            "department": department,
            "campaign_name": campaign_name,
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "mams_number": mams_number,
            "tier": tier or None,
            "buying_audience": buying_audience,
            "campaign_timing": campaign_timing,
            "regional_budget": regional_budget or None,
            "cald_budget": cald_budget or None,
            "digital_budget": digital_budget or None,
        }

        # Inject edited commentary back into insights
        merged_insights = {}
        for channel, data in insights.items():
            merged = dict(data)
            edited = st.session_state.edited_commentary.get(channel, {})
            if edited:
                merged["commentary"] = edited
            merged_insights[channel] = merged

        # Inject campaign summary commentary into form_data
        if campaign_summary:
            form_data["summary_highlights"] = campaign_summary.get("campaign_summary", "")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = (campaign_name or "PCR").replace(" ", "_")[:40]
        output_path = OUTPUT_DIR / f"{safe_name}_{timestamp}.xlsx"

        with st.spinner("Writing PCR Excel..."):
            try:
                log = write_pcr(
                    output_path=output_path,
                    all_insights=merged_insights,
                    form_data=form_data,
                )
            except FileNotFoundError as exc:
                st.error(str(exc))
                return
            except Exception as exc:
                st.error(f"Export failed: {exc}")
                return

        st.success(f"PCR exported to `{output_path}`")

        # Validation summary
        st.markdown("### Validation Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Cells written", len(log["written"]))
        col2.metric("[DATA REQUIRED]", len(log["data_required"]))
        col3.metric("Skipped (formula)", len(log["skipped"]))
        col4.metric("Errors", len(log["errors"]))

        if log["written"]:
            with st.expander(f"Written cells ({len(log['written'])})"):
                for item in log["written"]:
                    st.markdown(f"- `{item}`")

        if log["data_required"]:
            with st.expander(f"[DATA REQUIRED] cells ({len(log['data_required'])})", expanded=True):
                for item in log["data_required"]:
                    st.markdown(f"- `{item}`")

        if log["unmapped"]:
            with st.expander(f"Unmapped metrics ({len(log['unmapped'])})"):
                st.caption("These metrics were extracted but have no cell mapping. Log for v2.")
                for item in log["unmapped"]:
                    st.markdown(f"- `{item}`")

        if log["skipped"]:
            with st.expander(f"Skipped cells ({len(log['skipped'])})"):
                for item in log["skipped"]:
                    st.markdown(f"- `{item}`")

        if log["errors"]:
            st.error("Errors encountered during write:")
            for item in log["errors"]:
                st.markdown(f"- `{item}`")

        # Download button
        with open(output_path, "rb") as f:
            st.download_button(
                label="Download PCR Excel",
                data=f,
                file_name=output_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← Back to Insights"):
            go_to(2)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Top navigation breadcrumb
    steps = {1: "1 — Scan", 2: "2 — Insights", 3: "3 — Export"}
    current = st.session_state.screen
    nav_cols = st.columns(len(steps))
    for col, (num, label) in zip(nav_cols, steps.items()):
        if num == current:
            col.markdown(f"**{label}**")
        elif num < current:
            col.markdown(f"[{label}](#)")  # decorative — actual nav via buttons
        else:
            col.markdown(f"*{label}*")

    if current == 1:
        screen_scan()
    elif current == 2:
        screen_insights()
    elif current == 3:
        screen_export()


if __name__ == "__main__":
    main()
