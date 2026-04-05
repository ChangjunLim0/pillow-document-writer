# pillow-document-writer

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python wrapper for Pillow (PIL) to create text-heavy images like a word processor. Easily write multi-line documents on an image canvas, with features like automatic word-wrapping, font caching, and simple layout management.

## Installation

```bash
pip install pillow-document-writer
```

For dev mode
```bash
pip install -e ".[dev]"
```

## Usage

```python
from pillow_document import DocumentWriter

doc = DocumentWriter()
doc.save("output.png")
```

## Examples

```bash
python examples/tale.py
```

## Using Custom Fonts

You can write text with either a system-installed font name or a direct font file path.

- System font: `writer.write("Hello", font="Times New Roman")`
- Font file path: `writer.write("Hello", font="/path/to/YourFont.ttf")`

Under the hood, the font is registered and cached so repeated calls reuse the same font object. Unsupported characters for the chosen font are logged as warnings. Supported formats: `.ttf`, `.otf`, `.ttc`.
