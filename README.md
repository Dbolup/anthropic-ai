# anthropic-ai

Experiments and tooling built on the Anthropic API.

---

## AI Product Content Generation Script (MSD-20)

A command-line tool that generates marketing copy (product descriptions and feature bullet points) for a set of products from their structured attributes/specs, using Claude as the LLM backend.

The primary goal is to produce AI-generated content alongside product identifiers so it can be matched against a human-written baseline for blind quality review.

### Project layout

```
.
├── generate_content.py           # CLI entrypoint
├── product_content_generator/
│   ├── __init__.py
│   ├── generator.py              # Core generator (Anthropic API calls)
│   ├── models.py                 # Product / GeneratedContent data classes
│   └── prompts.py                # System + user prompt templates
├── data/
│   ├── sample_products.json      # 25 sample products (input)
│   └── output/                   # Generated content is written here (git-ignored)
├── tests/
│   ├── test_models.py
│   ├── test_generator.py
│   └── test_cli.py
├── requirements.txt
└── pyproject.toml
```

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Running the script

```bash
# Generate content for all 25 sample products (default settings)
python generate_content.py

# Verbose output + custom output directory
python generate_content.py --verbose --output-dir results/

# Use a different model
python generate_content.py --model claude-haiku-4-5

# Skip errors and continue if a product fails
python generate_content.py --skip-errors
```

Run `python generate_content.py --help` for the full list of options.

### Output

Each run produces two timestamped files in `data/output/` (or your `--output-dir`):

| File | Contents |
|---|---|
| `generated_content_<timestamp>.json` | Full structured output including token usage, model name, and all generated fields |
| `generated_content_<timestamp>_summary.jsonl` | One JSON object per line with only `product_id`, `product_name`, `description`, and `feature_copy` — ready for blind review |

**Example summary row:**
```json
{
  "product_id": "PROD-001",
  "product_name": "UltraSound Pro X5 Wireless Headphones",
  "description": "The UltraSound Pro X5 delivers studio-quality audio in a lightweight 250g package...",
  "feature_copy": [
    "30-hour battery life keeps the music going all day and night.",
    "Active Noise Cancellation blocks distractions so you stay in the zone.",
    "Bluetooth 5.2 ensures a stable, low-latency connection up to 10m away.",
    "IPX4 water resistance handles sweat and light rain with ease."
  ]
}
```

### Input format

Products are read from a JSON file — an array of objects with the following shape:

```json
[
  {
    "id": "PROD-001",
    "name": "UltraSound Pro X5 Wireless Headphones",
    "category": "Consumer Electronics",
    "attributes": {
      "battery_life": "30 hours",
      "connectivity": "Bluetooth 5.2",
      "noise_cancellation": "Active Noise Cancellation (ANC)"
    }
  }
]
```

`attributes` can contain any nested JSON — strings, numbers, lists, or objects.

### Running tests

```bash
pytest
```

No real API calls are made during tests; the Anthropic client is fully mocked.
