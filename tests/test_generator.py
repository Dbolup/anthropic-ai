"""Tests for the ProductContentGenerator."""

import json
from unittest.mock import MagicMock, patch

import pytest

from product_content_generator.generator import (
    GenerationError,
    ProductContentGenerator,
)
from product_content_generator.models import GeneratedContent, Product


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_product(**kwargs) -> Product:
    defaults = dict(
        id="PROD-TEST",
        name="Test Wireless Headphones",
        category="Electronics",
        attributes={"battery_life": "30h", "connectivity": "Bluetooth 5.2"},
    )
    defaults.update(kwargs)
    return Product(**defaults)


def make_api_response(description: str, feature_copy: list[str], model: str = "claude-opus-4-5") -> MagicMock:
    """Build a mock Anthropic messages.create() response."""
    content_block = MagicMock()
    content_block.text = json.dumps(
        {"description": description, "feature_copy": feature_copy}
    )
    response = MagicMock()
    response.content = [content_block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 80
    return response


# ---------------------------------------------------------------------------
# _parse_response tests
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_valid_json_returns_dict(self):
        raw = json.dumps({"description": "Great product.", "feature_copy": ["Fast"]})
        result = ProductContentGenerator._parse_response(raw, "P1")
        assert result["description"] == "Great product."
        assert result["feature_copy"] == ["Fast"]

    def test_strips_markdown_fences(self):
        raw = "```json\n{\"description\": \"Hi.\", \"feature_copy\": [\"A\"]}\n```"
        result = ProductContentGenerator._parse_response(raw, "P1")
        assert result["description"] == "Hi."

    def test_invalid_json_raises(self):
        with pytest.raises(GenerationError, match="Could not parse JSON"):
            ProductContentGenerator._parse_response("not json", "P1")

    def test_missing_description_raises(self):
        raw = json.dumps({"feature_copy": ["A"]})
        with pytest.raises(GenerationError, match="missing keys"):
            ProductContentGenerator._parse_response(raw, "P1")

    def test_missing_feature_copy_raises(self):
        raw = json.dumps({"description": "Hello."})
        with pytest.raises(GenerationError, match="missing keys"):
            ProductContentGenerator._parse_response(raw, "P1")

    def test_description_not_string_raises(self):
        raw = json.dumps({"description": 42, "feature_copy": ["A"]})
        with pytest.raises(GenerationError, match="must be a string"):
            ProductContentGenerator._parse_response(raw, "P1")

    def test_feature_copy_not_list_raises(self):
        raw = json.dumps({"description": "Hi.", "feature_copy": "bullet"})
        with pytest.raises(GenerationError, match="must be a list of strings"):
            ProductContentGenerator._parse_response(raw, "P1")

    def test_feature_copy_non_string_items_raises(self):
        raw = json.dumps({"description": "Hi.", "feature_copy": [1, 2]})
        with pytest.raises(GenerationError, match="must be a list of strings"):
            ProductContentGenerator._parse_response(raw, "P1")


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------


class TestGenerate:
    @patch("product_content_generator.generator.anthropic.Anthropic")
    def test_generate_returns_generated_content(self, mock_anthropic_cls):
        product = make_product()
        expected_description = "These headphones are excellent."
        expected_bullets = ["30-hour battery keeps you going all day.", "Bluetooth 5.2 for stable connections."]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_api_response(
            expected_description, expected_bullets
        )
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator()
        result = gen.generate(product)

        assert isinstance(result, GeneratedContent)
        assert result.product_id == product.id
        assert result.product_name == product.name
        assert result.description == expected_description
        assert result.feature_copy == expected_bullets
        assert result.prompt_tokens == 100
        assert result.completion_tokens == 80

    @patch("product_content_generator.generator.anthropic.Anthropic")
    def test_generate_passes_correct_model(self, mock_anthropic_cls):
        product = make_product()
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_api_response("Desc.", ["Bullet."])
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator(model="claude-haiku-4-5")
        gen.generate(product)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5"

    @patch("product_content_generator.generator.anthropic.Anthropic")
    def test_generate_raises_on_api_error(self, mock_anthropic_cls):
        import anthropic as anthropic_module

        product = make_product()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic_module.APIStatusError(
            "rate limit", response=MagicMock(status_code=429), body={}
        )
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator()
        with pytest.raises(GenerationError, match="API error"):
            gen.generate(product)


# ---------------------------------------------------------------------------
# generate_batch() tests
# ---------------------------------------------------------------------------


class TestGenerateBatch:
    @patch("product_content_generator.generator.anthropic.Anthropic")
    @patch("product_content_generator.generator.time.sleep")
    def test_batch_yields_all_results(self, mock_sleep, mock_anthropic_cls):
        products = [make_product(id=f"P{i}", name=f"Product {i}") for i in range(3)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_api_response("Desc.", ["Bullet."])
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator(delay=0.1)
        results = list(gen.generate_batch(products))

        assert len(results) == 3
        assert [r.product_id for r in results] == ["P0", "P1", "P2"]

    @patch("product_content_generator.generator.anthropic.Anthropic")
    @patch("product_content_generator.generator.time.sleep")
    def test_batch_sleeps_between_calls(self, mock_sleep, mock_anthropic_cls):
        products = [make_product(id=f"P{i}") for i in range(3)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_api_response("Desc.", ["Bullet."])
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator(delay=0.5)
        list(gen.generate_batch(products))

        # sleep called once between each pair of calls (n-1 times total)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)

    @patch("product_content_generator.generator.anthropic.Anthropic")
    @patch("product_content_generator.generator.time.sleep")
    def test_batch_skip_errors_continues(self, mock_sleep, mock_anthropic_cls):
        import anthropic as anthropic_module

        products = [make_product(id=f"P{i}") for i in range(3)]
        mock_client = MagicMock()

        def side_effect(**kwargs):
            # Fail on second call (P1), succeed otherwise
            if mock_client.messages.create.call_count == 2:
                raise anthropic_module.APIStatusError(
                    "error", response=MagicMock(status_code=500), body={}
                )
            return make_api_response("Desc.", ["Bullet."])

        mock_client.messages.create.side_effect = side_effect
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator(delay=0)
        results = list(gen.generate_batch(products, skip_errors=True))

        assert len(results) == 2
        assert {r.product_id for r in results} == {"P0", "P2"}

    @patch("product_content_generator.generator.anthropic.Anthropic")
    @patch("product_content_generator.generator.time.sleep")
    def test_batch_raises_by_default_on_error(self, mock_sleep, mock_anthropic_cls):
        import anthropic as anthropic_module

        products = [make_product(id=f"P{i}") for i in range(2)]
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic_module.APIStatusError(
            "error", response=MagicMock(status_code=500), body={}
        )
        mock_anthropic_cls.return_value = mock_client

        gen = ProductContentGenerator(delay=0)
        with pytest.raises(GenerationError):
            list(gen.generate_batch(products))
