"""
PCR POC — Insight generation.
Consolidates scan results per channel and calls Gemini for commentary.
"""

import json
import re
from collections import defaultdict

import vertexai
from vertexai.generative_models import GenerativeModel

from config import (
    GCP_PROJECT, GCP_LOCATION, GEMINI_MODEL,
    DEFAULT_INSIGHT_PROMPT, CAMPAIGN_SUMMARY_PROMPT,
    DEFAULT_WORD_LIMIT, DEFAULT_TONE,
    CHANNEL_LABELS,
)


def _init_vertex():
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    return GenerativeModel(GEMINI_MODEL)


def _extract_json(raw: str) -> dict:
    """Extract and parse the first complete JSON object from a Gemini response."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found in response", raw, 0)
    return json.loads(raw[start:end + 1])


def group_results_by_channel(scan_results: list[dict]) -> dict[str, list[dict]]:
    """Group scan results by channel, excluding unknowns and unreadables."""
    grouped = defaultdict(list)
    for r in scan_results:
        channel = r.get("channel", "unknown")
        if r.get("status") not in ("unreadable",) and channel != "unknown":
            grouped[channel].append(r)
    return dict(grouped)


def generate_channel_insights(
    channel: str,
    scan_results: list[dict],
    campaign_name: str,
    prompt_template: str | None = None,
    word_limit: int = DEFAULT_WORD_LIMIT,
    tone: str = DEFAULT_TONE,
    model: GenerativeModel | None = None,
) -> dict:
    """
    Generate insights for a single channel from its scan results.
    Returns the Gemini response dict with grounding_dict + commentary.
    """
    if model is None:
        model = _init_vertex()

    template = prompt_template or DEFAULT_INSIGHT_PROMPT

    prompt = template.format(
        channel=CHANNEL_LABELS.get(channel, channel),
        campaign_name=campaign_name,
        scan_results_json=json.dumps(scan_results, indent=2),
        word_limit=word_limit,
        tone=tone,
    )

    try:
        response = model.generate_content(prompt)
        result = _extract_json(response.text)
        result["channel"] = channel
        return result
    except json.JSONDecodeError as exc:
        return {
            "channel": channel,
            "grounding_dict": {},
            "commentary": {
                "highlights": "[DATA REQUIRED]",
                "learnings": "[DATA REQUIRED]",
                "recommendations": "[DATA REQUIRED]",
            },
            "data_gaps": ["JSON parse error from Gemini"],
            "confidence": "low",
            "confidence_reason": f"JSON parse error: {exc}",
        }
    except Exception as exc:
        return {
            "channel": channel,
            "grounding_dict": {},
            "commentary": {
                "highlights": "[DATA REQUIRED]",
                "learnings": "[DATA REQUIRED]",
                "recommendations": "[DATA REQUIRED]",
            },
            "data_gaps": ["Gemini API error"],
            "confidence": "low",
            "confidence_reason": str(exc),
        }


def generate_all_insights(
    scan_results: list[dict],
    campaign_name: str,
    prompt_template: str | None = None,
    word_limit: int = DEFAULT_WORD_LIMIT,
    tone: str = DEFAULT_TONE,
    progress_callback=None,
) -> dict[str, dict]:
    """
    Generate insights for all detected channels.
    Returns dict keyed by channel with insight result dicts.
    """
    model = _init_vertex()
    grouped = group_results_by_channel(scan_results)
    insights = {}
    channels = list(grouped.keys())

    for i, channel in enumerate(channels):
        if progress_callback:
            progress_callback(channel, i, len(channels))
        insights[channel] = generate_channel_insights(
            channel=channel,
            scan_results=grouped[channel],
            campaign_name=campaign_name,
            prompt_template=prompt_template,
            word_limit=word_limit,
            tone=tone,
            model=model,
        )

    return insights


def generate_campaign_summary(
    all_insights: dict[str, dict],
    campaign_name: str,
    tone: str = DEFAULT_TONE,
    model: GenerativeModel | None = None,
) -> dict:
    """
    Generate a 150-word cross-channel campaign summary.
    Receives all channel grounding dicts simultaneously.
    """
    if model is None:
        model = _init_vertex()

    # Build compact payload — grounding dict + commentary per channel
    all_channels_payload = {
        channel: {
            "channel_label": CHANNEL_LABELS.get(channel, channel),
            "grounding_dict": data.get("grounding_dict", {}),
            "commentary": data.get("commentary", {}),
            "data_gaps": data.get("data_gaps", []),
            "confidence": data.get("confidence", "low"),
        }
        for channel, data in all_insights.items()
    }

    prompt = CAMPAIGN_SUMMARY_PROMPT.format(
        campaign_name=campaign_name,
        all_channels_json=json.dumps(all_channels_payload, indent=2),
        tone=tone,
    )

    try:
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    except Exception as exc:
        return {
            "campaign_summary": "[DATA REQUIRED]",
            "cross_channel_themes": [],
            "data_gaps": [f"Summary generation failed: {exc}"],
        }


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json as _json

    if len(sys.argv) < 3:
        print("Usage: python insights.py <scan_results.json> <campaign_name>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        scan_results = _json.load(f)

    campaign_name = sys.argv[2]
    insights = generate_all_insights(
        scan_results,
        campaign_name,
        progress_callback=lambda ch, i, n: print(f"  [{i+1}/{n}] {ch}"),
    )
    print(_json.dumps(insights, indent=2))
