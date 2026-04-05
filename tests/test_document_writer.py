import pytest
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

from PIL import Image
from pillow_document.document_writer import DocumentWriter


@pytest.fixture
def writer():
    return DocumentWriter(width=400, height=600, margin=20)


@pytest.fixture
def small_writer():
    """Writer whose page fills up quickly for multi-page tests."""
    return DocumentWriter(width=200, height=60, margin=5)


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (100, 80), color="blue")
    img_path = tmp_path / "sample.png"
    img.save(img_path)
    return img_path


# ---------------------------------------------------------------------------
# write()
# ---------------------------------------------------------------------------


def test_write_advances_cursor_x(writer):
    initial_x = writer.cursor_x
    writer.write("Hello")
    assert writer.cursor_x > initial_x


def test_write_does_not_change_cursor_y_for_single_line(writer):
    initial_y = writer.cursor_y
    writer.write("Hello")
    assert writer.cursor_y == initial_y


def test_write_newline_advances_cursor_y(writer):
    initial_y = writer.cursor_y
    writer.write("Hello\nWorld")
    assert writer.cursor_y > initial_y


def test_write_newline_resets_cursor_x(writer):
    writer.write("Hello\nWorld")
    assert writer.cursor_x > writer.left_margin  # "World" leaves cursor after it


def test_write_min_width_respected(writer):
    initial_x = writer.cursor_x
    writer.write("Hi", min_width=200)
    assert writer.cursor_x >= initial_x + 200


def test_write_consecutive_on_same_line(writer):
    writer.write("Hello ")
    mid_x = writer.cursor_x
    writer.write("World")
    assert writer.cursor_x > mid_x


# ---------------------------------------------------------------------------
# write_line()
# ---------------------------------------------------------------------------


def test_write_line_advances_cursor_y(writer):
    initial_y = writer.cursor_y
    writer.write_line("Hello")
    assert writer.cursor_y > initial_y


def test_write_line_resets_cursor_x(writer):
    writer.write_line("Hello")
    assert writer.cursor_x == writer.left_margin


def test_write_line_multiple_newlines(writer):
    initial_y = writer.cursor_y
    writer.write_line("Line1\nLine2\nLine3")
    # Three rendered lines means cursor advanced by at least 2 line heights
    assert writer.cursor_y >= initial_y + writer._default_font_size * 2


def test_write_line_min_height_respected(writer):
    initial_y = writer.cursor_y
    writer.write_line("Hi", min_height=100)
    assert writer.cursor_y >= initial_y + 100


# ---------------------------------------------------------------------------
# image()
# ---------------------------------------------------------------------------


def test_image_line_break_true_advances_cursor_y(writer, sample_image):
    initial_y = writer.cursor_y
    writer.image(sample_image, line_break=True)
    assert writer.cursor_y > initial_y


def test_image_line_break_true_resets_cursor_x(writer, sample_image):
    writer.image(sample_image, line_break=True)
    assert writer.cursor_x == writer.left_margin


def test_image_line_break_false_advances_cursor_x(writer, sample_image):
    initial_x = writer.cursor_x
    writer.image(sample_image, line_break=False)
    assert writer.cursor_x > initial_x


def test_image_line_break_false_does_not_advance_cursor_y(writer, sample_image):
    initial_y = writer.cursor_y
    writer.image(sample_image, line_break=False)
    assert writer.cursor_y == initial_y


def test_image_resize_width_only(writer, sample_image, tmp_path):
    writer.image(sample_image, width=50, line_break=True)
    # No error; cursor moved down by (50 * original_h / original_w) + margins
    assert writer.cursor_y > writer.margin[0]


def test_image_resize_height_only(writer, sample_image):
    writer.image(sample_image, height=40, line_break=True)
    assert writer.cursor_y > writer.margin[0]


def test_image_resize_both(writer, sample_image):
    writer.image(sample_image, width=60, height=30, line_break=True)
    assert writer.cursor_y > writer.margin[0]


def test_image_nonexistent_file_does_not_raise(writer, tmp_path):
    missing = tmp_path / "missing.png"
    writer.image(missing)  # should log a warning and return


def test_image_aspect_ratio_height_only(tmp_path):
    """Resizing by height only must preserve aspect ratio (Bug #2 fix)."""
    img = Image.new("RGB", (200, 100), color="red")
    img_path = tmp_path / "wide.png"
    img.save(img_path)

    writer = DocumentWriter(width=600, height=800, margin=10)
    writer.image(img_path, height=50, line_break=True)
    # cursor_y advanced by height=50 (plus margins), not by 50*50=2500
    assert writer.cursor_y <= 800


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------


def test_save_single_page(writer, tmp_path):
    writer.write_line("Hello")
    out = tmp_path / "output.png"
    writer.save(out)
    assert out.exists()
    # No suffixed variants for a single page
    assert not (tmp_path / "output_1.png").exists()


def test_save_multi_page(small_writer, tmp_path):
    for _ in range(20):
        small_writer.write_line("Fill the page with text")
    assert small_writer.page > 1, "Expected at least 2 pages"

    out = tmp_path / "output.png"
    small_writer.save(out)
    assert (tmp_path / "output_1.png").exists()
    assert (tmp_path / "output_2.png").exists()
    assert not out.exists()


# ---------------------------------------------------------------------------
# Multi-page behavior
# ---------------------------------------------------------------------------


def test_new_page_created_when_text_overflows(small_writer):
    initial_page = small_writer.page
    for _ in range(20):
        small_writer.write_line("Text")
    assert small_writer.page > initial_page


def test_cursor_resets_on_new_page(small_writer):
    for _ in range(20):
        small_writer.write_line("Text")
    assert small_writer.cursor_y <= small_writer.page_height - small_writer.margin[2]
    assert small_writer.cursor_x == small_writer.left_margin


def test_image_triggers_new_page_when_too_tall(tmp_path):
    """An image taller than the remaining space must push to the next page."""
    writer = DocumentWriter(width=300, height=150, margin=10)
    # Fill ~half the page first
    writer.write_line("First line")
    writer.write_line("Second line")
    page_before = writer.page

    # Image that won't fit in remaining space
    tall_img = Image.new("RGB", (50, 200), color="green")
    img_path = tmp_path / "tall.png"
    tall_img.save(img_path)

    writer.image(img_path, line_break=True)
    assert writer.page > page_before
