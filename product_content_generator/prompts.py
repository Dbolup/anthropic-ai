"""Prompt templates for product content generation."""

import json
from typing import Any


SYSTEM_PROMPT = """\
You are an expert product copywriter specialising in compelling, accurate product descriptions \
for e-commerce. You write in a clear, engaging voice that highlights genuine benefits without \
hyperbole. You always derive claims directly from the provided product specifications — you never \
invent or embellish features.

When given a product's structured data you will return a JSON object with exactly two keys:
- "description": a single paragraph (60-120 words) that introduces the product and its primary \
value proposition.
- "feature_copy": a list of 4-6 concise bullet-point strings (each 10-20 words) that call out \
the most important features or benefits, written in an active, benefit-led style.

Return ONLY valid JSON. Do not include markdown fences or any text outside the JSON object.\
"""


def build_user_prompt(
    product_name: str,
    category: str,
    attributes: dict[str, Any],
) -> str:
    """Build the user message for a single product."""
    attrs_text = json.dumps(attributes, indent=2, ensure_ascii=False)
    return (
        f"Product name: {product_name}\n"
        f"Category: {category}\n"
        f"Specifications:\n{attrs_text}\n\n"
        "Generate the product description and feature bullet points as specified."
    )
