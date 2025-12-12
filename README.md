# pillow-document-writer

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Python wrapper for Pillow (PIL) to create text-heavy images like a word processor. Easily write multi-line documents on an image canvas, with features like automatic word-wrapping, font caching, and simple layout management.

## Installation

```bash
pip install pillow-document-writer
```

## Usage

```python
from pillow_document import DocumentWriter

doc = DocumentWriter()
doc.save("output.png")
```

## Using Custom Fonts

You can write text with either a system-installed font name or a direct font file path.

- System font: `writer.write("Hello", font="Times New Roman")`
- Font file path: `writer.write("Hello", font="/path/to/YourFont.ttf")`

Under the hood, the font is registered and cached so repeated calls reuse the same font object. Unsupported characters for the chosen font are logged as warnings. Supported formats: `.ttf`, `.otf`, `.ttc`.
