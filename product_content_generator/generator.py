"""Core product content generator using the Anthropic API."""

import json
import logging
import time
from typing import Iterator

import anthropic

from .models import GeneratedContent, Product
from .prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-5"
MAX_TOKENS = 1024
# Seconds to wait between API calls to stay within rate limits
INTER_REQUEST_DELAY = 0.5


class GenerationError(Exception):
    """Raised when content generation fails for a product."""


class ProductContentGenerator:
    """Generates marketing copy for products using the Anthropic API.

    Usage::

        generator = ProductContentGenerator()
        results = list(generator.generate_batch(products))

    Args:
        api_key: Anthropic API key. Defaults to the ``ANTHROPIC_API_KEY``
            environment variable when *None*.
        model: Claude model identifier to use.
        max_tokens: Maximum tokens to generate per product.
        delay: Seconds to sleep between consecutive API calls.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS,
        delay: float = INTER_REQUEST_DELAY,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.delay = delay
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, product: Product) -> GeneratedContent:
        """Generate content for a single product.

        Args:
            product: The product to generate content for.

        Returns:
            A :class:`GeneratedContent` instance with description and
            feature bullet points.

        Raises:
            GenerationError: If the API call fails or the response cannot
                be parsed as the expected JSON structure.
        """
        user_prompt = build_user_prompt(product.name, product.category, product.attributes)
        logger.info("Generating content for %s (%s)", product.id, product.name)

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            raise GenerationError(f"API error for product {product.id}: {exc}") from exc

        raw_text = response.content[0].text.strip()
        parsed = self._parse_response(raw_text, product.id)

        return GeneratedContent(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            description=parsed["description"],
            feature_copy=parsed["feature_copy"],
            model=self.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

    def generate_batch(
        self,
        products: list[Product],
        *,
        skip_errors: bool = False,
    ) -> Iterator[GeneratedContent]:
        """Generate content for a list of products, yielding results one by one.

        Args:
            products: Products to process.
            skip_errors: When *True*, log errors and continue rather than
                re-raising :class:`GenerationError`.

        Yields:
            :class:`GeneratedContent` objects in the same order as *products*.
        """
        for i, product in enumerate(products):
            if i > 0:
                time.sleep(self.delay)
            try:
                yield self.generate(product)
            except GenerationError as exc:
                if skip_errors:
                    logger.error("Skipping %s: %s", product.id, exc)
                else:
                    raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(raw: str, product_id: str) -> dict:
        """Parse the LLM's JSON response into a validated dict.

        Args:
            raw: Raw text returned by the model.
            product_id: Used only in error messages.

        Returns:
            Dict with ``description`` (str) and ``feature_copy`` (list[str]).

        Raises:
            GenerationError: If JSON is invalid or required keys are missing.
        """
        # Strip optional markdown fences the model may include despite instructions
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenerationError(
                f"Could not parse JSON for product {product_id}: {exc}\nRaw: {raw[:500]}"
            ) from exc

        missing = [k for k in ("description", "feature_copy") if k not in data]
        if missing:
            raise GenerationError(
                f"Response for {product_id} is missing keys: {missing}"
            )

        if not isinstance(data["description"], str):
            raise GenerationError(
                f"'description' must be a string for product {product_id}"
            )
        if not isinstance(data["feature_copy"], list) or not all(
            isinstance(b, str) for b in data["feature_copy"]
        ):
            raise GenerationError(
                f"'feature_copy' must be a list of strings for product {product_id}"
            )

        return data
