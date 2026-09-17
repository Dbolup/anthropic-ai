"""Tests for the CLI entrypoint (generate_content.py)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import generate_content as cli
from product_content_generator.models import GeneratedContent, Product


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_generated_content(product_id: str = "PROD-001", **kwargs) -> GeneratedContent:
    defaults = dict(
        product_id=product_id,
        product_name=f"Product {product_id}",
        category="Electronics",
        description="A great product.",
        feature_copy=["Great feature 1.", "Great feature 2."],
        model="claude-opus-4-5",
        prompt_tokens=100,
        completion_tokens=50,
    )
    defaults.update(kwargs)
    return GeneratedContent(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadProducts:
    def test_loads_valid_file(self, tmp_path):
        data = [
            {"id": "P1", "name": "Widget", "category": "Cat", "attributes": {"k": "v"}}
        ]
        f = tmp_path / "products.json"
        f.write_text(json.dumps(data))

        products = cli.load_products(f)
        assert len(products) == 1
        assert products[0].id == "P1"
        assert isinstance(products[0], Product)

    def test_loads_all_sample_products(self):
        sample = Path(__file__).parent.parent / "data" / "sample_products.json"
        products = cli.load_products(sample)
        assert len(products) == 25
        for p in products:
            assert p.id
            assert p.name
            assert p.category
            assert isinstance(p.attributes, dict)


class TestSaveResults:
    def test_creates_output_files(self, tmp_path):
        results = [make_generated_content().to_dict()]
        full_path, summary_path = cli.save_results(results, tmp_path, "20240101T000000Z")

        assert full_path.exists()
        assert summary_path.exists()

    def test_full_output_is_valid_json(self, tmp_path):
        results = [make_generated_content().to_dict()]
        full_path, _ = cli.save_results(results, tmp_path, "run1")

        loaded = json.loads(full_path.read_text())
        assert len(loaded) == 1
        assert loaded[0]["product_id"] == "PROD-001"

    def test_summary_is_jsonl(self, tmp_path):
        results = [
            make_generated_content("P1").to_dict(),
            make_generated_content("P2").to_dict(),
        ]
        _, summary_path = cli.save_results(results, tmp_path, "run1")

        lines = summary_path.read_text().strip().splitlines()
        assert len(lines) == 2
        row = json.loads(lines[0])
        assert set(row.keys()) == {"product_id", "product_name", "description", "feature_copy"}

    def test_summary_excludes_usage_and_model(self, tmp_path):
        results = [make_generated_content().to_dict()]
        _, summary_path = cli.save_results(results, tmp_path, "run1")

        row = json.loads(summary_path.read_text().strip())
        assert "model" not in row
        assert "usage" not in row

    def test_creates_output_dir_if_missing(self, tmp_path):
        subdir = tmp_path / "nested" / "output"
        assert not subdir.exists()
        cli.save_results([make_generated_content().to_dict()], subdir, "run1")
        assert subdir.exists()


class TestMain:
    @patch("generate_content.ProductContentGenerator")
    def test_main_returns_0_on_success(self, mock_gen_cls, tmp_path):
        products_file = tmp_path / "products.json"
        products_file.write_text(
            json.dumps(
                [{"id": "P1", "name": "Widget", "category": "Cat", "attributes": {}}]
            )
        )

        mock_gen = MagicMock()
        mock_gen.generate_batch.return_value = iter([make_generated_content("P1")])
        mock_gen_cls.return_value = mock_gen

        output_dir = tmp_path / "output"
        ret = cli.main(
            ["--input", str(products_file), "--output-dir", str(output_dir)]
        )

        assert ret == 0
        assert any(output_dir.glob("generated_content_*.json"))

    def test_main_returns_1_for_missing_input(self, tmp_path):
        ret = cli.main(
            [
                "--input",
                str(tmp_path / "nonexistent.json"),
                "--output-dir",
                str(tmp_path),
            ]
        )
        assert ret == 1

    @patch("generate_content.ProductContentGenerator")
    def test_main_returns_1_when_no_results(self, mock_gen_cls, tmp_path):
        products_file = tmp_path / "products.json"
        products_file.write_text(
            json.dumps(
                [{"id": "P1", "name": "Widget", "category": "Cat", "attributes": {}}]
            )
        )
        mock_gen = MagicMock()
        mock_gen.generate_batch.return_value = iter([])
        mock_gen_cls.return_value = mock_gen

        ret = cli.main(
            ["--input", str(products_file), "--output-dir", str(tmp_path / "out")]
        )
        assert ret == 1
