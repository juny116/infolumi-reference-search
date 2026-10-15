"""Batch reference lines and decode structured model output."""

import json


def batches(items, size=5):
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i : i + size] for i in range(0, len(items), size)]


def decode_references(response, expected_count):
    """Keep positional alignment when a model returns invalid or partial JSON."""
    text = response.strip()
    if text.startswith("```") and text.endswith("```"):
        text = "\n".join(text.splitlines()[1:-1])
    try:
        items = json.loads(text)
    except (ValueError, TypeError):
        items = []
    if not isinstance(items, list):
        items = []
    items = [x if isinstance(x, dict) else None for x in items[:expected_count]]
    return items + [None] * (expected_count - len(items))
