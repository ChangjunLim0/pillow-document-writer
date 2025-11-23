import pytest
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

from PIL import ImageFont
from pillow_document.document_writer import DocumentWriter
from pillow_document.font_manager import FontManager


@pytest.fixture
def font_object():
    font_manager = FontManager()
    font_path = font_manager.get_font(font_manager.DEFAULT_FONT)
    font_size = 70
    return ImageFont.truetype(str(font_path), font_size)


def test_get_index_for_line_hello_world(font_object):
    writer = DocumentWriter(width=200, height=600, margin=40)
    line_width = writer.line_width
    
    assert line_width == 120, (
        f"line_width should be width({writer.page_width}) - margin[0]({writer.margin[0]}) - margin[2]({writer.margin[2]})"
    )
    text = "Hello World!"
    
    index = writer._get_index_for_line(text, font_object, line_width)
    
    assert index > 0, "Index should be greater than 0"
    assert index <= len(text), "Index should be less than or equal to text length"
    
    first_line = text[:index]
    first_line_width = font_object.getlength(first_line)
    assert first_line_width <= line_width, (
        f"The width of the first line '{first_line}'({first_line_width}) exceeds line_width({line_width})"
    )
    
    if index < len(text):
        next_char_width = font_object.getlength(text[:index + 1])
        assert next_char_width > line_width, (
            f"Adding the next character at index {index} should exceed line_width. "
            f"Width: {next_char_width}, line_width: {line_width}"
        )


def test_split_text_by_character_hello_world(font_object):
    """Test that _split_text_by_character() correctly splits 'Hello World!'"""
    writer = DocumentWriter(width=200, height=1000, margin=40)
    line_width = writer.line_width  # 120
    
    text = "Hello World!"
    chunks = writer._split_text_by_character(text, font_object, line_width)
    
    for i, chunk in enumerate(chunks):
        chunk_width = font_object.getlength(chunk)
        assert chunk_width <= line_width, (
            f"Chunk {i} '{chunk}' width ({chunk_width}) exceeds line_width ({line_width})"
        )
    
    combined = "".join(chunks)
    assert combined == text, (
        f"Combined chunks '{combined}' do not match original text '{text}'"
    )
    
    all_text = "".join(chunks)
    assert "rld!" in all_text, "'rld!' should be present in the text"
    
    for i in range(len(chunks) - 1):
        if chunks[i].endswith("rl") and chunks[i + 1].startswith("d!"):
            pytest.fail(
                f"'rld!' was incorrectly split into 'rl' and 'd!'. "
                f"Chunk {i}: '{chunks[i]}', Chunk {i+1}: '{chunks[i+1]}'"
            )


def test_get_index_for_line_edge_cases(font_object):
    writer = DocumentWriter(width=200, height=600, margin=40)
    line_width = writer.line_width
    
    short_text = "Hi"
    index = writer._get_index_for_line(short_text, font_object, line_width)
    assert index == len(short_text), "short text returns the text length"
    
    long_text = "This is a very long text that should be split"
    index = writer._get_index_for_line(long_text, font_object, line_width)
    assert index > 0, "Long text should return an index greater than 0"
    assert index <= len(long_text), "Index should not exceed text length"

