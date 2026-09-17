"""Tests for data models."""

import pytest
from product_content_generator.models import GeneratedContent, Product


class TestProduct:
    def test_from_dict_roundtrip(self):
        data = {
            "id": "PROD-001",
            "name": "Test Headphones",
            "category": "Electronics",
            "attributes": {"color": "black", "weight": "250g"},
        }
        product = Product.from_dict(data)
        assert product.id == "PROD-001"
        assert product.name == "Test Headphones"
        assert product.category == "Electronics"
        assert product.attributes == {"color": "black", "weight": "250g"}
        assert product.to_dict() == data

    def test_from_dict_missing_attributes_defaults_to_empty(self):
        data = {"id": "P1", "name": "Widget", "category": "Misc"}
        product = Product.from_dict(data)
        assert product.attributes == {}

    def test_to_dict_includes_all_fields(self):
        product = Product(id="P2", name="Gadget", category="Tech", attributes={"key": "val"})
        result = product.to_dict()
        assert set(result.keys()) == {"id", "name", "category", "attributes"}

    def test_from_dict_preserves_nested_attributes(self):
        data = {
            "id": "P3",
            "name": "Nested",
            "category": "Cat",
            "attributes": {"colors": ["red", "blue"], "specs": {"weight": 100}},
        }
        product = Product.from_dict(data)
        assert product.attributes["colors"] == ["red", "blue"]
        assert product.attributes["specs"]["weight"] == 100


class TestGeneratedContent:
    def _make_content(self, **kwargs):
        defaults = dict(
            product_id="PROD-001",
            product_name="Test Product",
            category="Electronics",
            description="A great product.",
            feature_copy=["Fast charging", "Lightweight design"],
            model="claude-opus-4-5",
            prompt_tokens=100,
            completion_tokens=50,
        )
        defaults.update(kwargs)
        return GeneratedContent(**defaults)

    def test_to_dict_structure(self):
        content = self._make_content()
        d = content.to_dict()
        assert d["product_id"] == "PROD-001"
        assert d["product_name"] == "Test Product"
        assert d["description"] == "A great product."
        assert d["feature_copy"] == ["Fast charging", "Lightweight design"]
        assert d["model"] == "claude-opus-4-5"

    def test_to_dict_usage_totals(self):
        content = self._make_content(prompt_tokens=200, completion_tokens=75)
        usage = content.to_dict()["usage"]
        assert usage["prompt_tokens"] == 200
        assert usage["completion_tokens"] == 75
        assert usage["total_tokens"] == 275

    def test_to_dict_zero_tokens_default(self):
        content = GeneratedContent(
            product_id="P",
            product_name="N",
            category="C",
            description="D",
            feature_copy=[],
            model="claude-opus-4-5",
        )
        usage = content.to_dict()["usage"]
        assert usage["total_tokens"] == 0
