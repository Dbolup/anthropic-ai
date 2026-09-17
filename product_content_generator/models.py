"""Data models for product content generation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Product:
    """Represents a product with structured attributes."""

    id: str
    name: str
    category: str
    attributes: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            attributes=data.get("attributes", {}),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "attributes": self.attributes,
        }


@dataclass
class GeneratedContent:
    """Generated content for a single product."""

    product_id: str
    product_name: str
    category: str
    description: str
    feature_copy: list[str]
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "description": self.description,
            "feature_copy": self.feature_copy,
            "model": self.model,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.prompt_tokens + self.completion_tokens,
            },
        }
