import logging
import os

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import ImageFont as PillowFontType

from pillow_document.font_manager import FontManager

## TODO: 색상관리, 기타 pillow 이미지, header 작성

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.WARNING)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


class DocumentWriter:
    def __init__(
        self,
        width: int,
        height: int,
        margin: int | tuple[int] = 20,
        background_color="white",
    ):
        self.current_image = Image.new("RGB", (width, height), color=background_color)
        self.draw = ImageDraw.Draw(self.current_image)
        self.page = 1
        self.images = [self.current_image]

        # self.margin : up, right, down, left
        if isinstance(margin, int):
            self.margin = (margin, margin, margin, margin)
        elif isinstance(margin, tuple):
            if len(margin) == 2:
                self.margin = (margin[0], margin[1], margin[0], margin[1])
            elif len(margin) == 4:
                self.margin = margin
            else:
                raise ValueError
        else:
            raise ValueError

        self.page_width = width
        self.page_height = height
        self.background_color = background_color

        self.cursor_x = self.left_margin
        self.cursor_y = self.margin[0]

        self._default_font = "Roboto-Regular"
        self._default_font_size = 12

        self.font_manager = FontManager()
        self._font_object_cache = {}
        self._font_object_cache[(self._default_font, self._default_font_size)] = (
            ImageFont.truetype(
                self.font_manager.get_font(self._default_font), self._default_font_size
            )
        )

    @property
    def line_width(self) -> int:
        return self.page_width - self.margin[1] - self.margin[3]

    @property
    def left_margin(self) -> int:
        return self.margin[3]

    def _get_or_create_font_object(
        self, font: str | None, font_size: int | None
    ) -> PillowFontType:
        font = font or self._default_font
        font_size = font_size or self._default_font_size
        font_object = self._font_object_cache.get((font, font_size))
        if font_object is None:
            font_object = ImageFont.truetype(
                str(self.font_manager.get_font(font)), font_size
            )
            self._font_object_cache[(font, font_size)] = font_object
        return font_object

    def _go_to_next_page(self):
        self.current_image = Image.new(
            "RGB", (self.page_width, self.page_height), color=self.background_color
        )
        self.draw = ImageDraw.Draw(self.current_image)
        self.page += 1
        self.images.append(self.current_image)

        self.cursor_x = self.left_margin
        self.cursor_y = self.margin[0]

    def _check_and_go_to_next_page(self, line_height: int):
        if self.cursor_y + line_height > self.page_height - self.margin[2]:
            self._go_to_next_page()

    def write(
        self,
        text: str,
        font: str = None,
        font_size: int = None,
        color="black",
        min_width: int = 0,
    ):
        font_size = font_size or self._default_font_size
        font = font or self._default_font
        initial_cursor_x = self.cursor_x
        initial_cursor_y = self.cursor_y
        self._check_if_font_supports(font, text)
        font_object = self._get_or_create_font_object(font, font_size)
        line_texts = text.split("\n")
        for line in line_texts[:-1]:
            self._write_text(line, font_object, color, line_break=True)
        last_line = line_texts[-1]
        self._write_text(last_line, font_object, color, line_break=False)
        if self.cursor_y == initial_cursor_y:
            self.cursor_x = max(self.cursor_x, initial_cursor_x + min_width)

    def write_line(
        self,
        text: str,
        font: str = None,
        font_size: int = None,
        color="black",
        min_height: int = 0,
    ):
        font_size = font_size or self._default_font_size
        font = font or self._default_font
        initial_page = self.page
        initial_cursor_y = self.cursor_y
        self._check_if_font_supports(font, text)
        font_object = self._get_or_create_font_object(font, font_size)
        line_texts = text.split("\n")
        for line in line_texts:
            self._write_text(line, font_object, color, line_break=True)
        if initial_page == self.page:
            self.cursor_y = max(self.cursor_y, initial_cursor_y + min_height)

    def _check_if_font_supports(self, font: str, text: str):
        unsupported_chars = self.font_manager.get_unsupported_chars(font, text)
        if len(unsupported_chars) > 0:
            logger.warning(
                f"'{font}' does not support {', '.join(list(unsupported_chars))}"
            )

    def _write_text(
        self, text: str, font_object: PillowFontType, color, line_break: bool = False
    ):
        wrapped_text = self._split_text_lines(text, font_object, self.line_width)
        line_height = font_object.size

        for line in wrapped_text[:-1]:
            self._check_and_go_to_next_page(line_height)
            self.draw.text((self.cursor_x, self.cursor_y), line, color, font_object)
            self.cursor_x = self.left_margin
            self.cursor_y += line_height

        last_line = wrapped_text[-1]
        self._check_and_go_to_next_page(line_height)
        self.draw.text((self.cursor_x, self.cursor_y), last_line, color, font_object)
        if line_break:
            self.cursor_x = self.left_margin
            self.cursor_y += line_height
        else:
            bbox = self.draw.textbbox((0, 0), last_line, font=font_object)
            text_width = bbox[2] - bbox[0]
            self.cursor_x += text_width

    def _split_text_lines(
        self, text: str, font_object: PillowFontType, line_width: int, mode="word"
    ) -> list[str]:
        space_width = font_object.getlength(" ")
        words = text.split(" ")
        current_line = []
        current_width = 0
        lines = []
        for word in words:
            word_length = font_object.getlength(word)
            if word_length > line_width:
                if len(current_line) > 0:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_width = 0
                chunks = self._split_text_by_character(word, font_object, line_width)
                lines.extend(chunks[:-1])
                last_chunk = chunks[-1]
                current_line.append(last_chunk)
                current_width += font_object.getlength(last_chunk)
                continue

            if current_width + word_length <= line_width:
                if current_width > 0:
                    current_width += space_width
                current_width += word_length
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_length
        if len(current_line) > 0:
            lines.append(" ".join(current_line))
        return lines

    def _get_index_for_line(
        self, text: str, font_object: PillowFontType, line_width: int
    ):
        total_length = font_object.getlength(text)
        if total_length <= line_width:
            return len(text)
        char_width = font_object.getlength("a")

        estimated_line_count = int(line_width / char_width)

        index = estimated_line_count
        current_width = font_object.getlength(text[:index])
        if current_width > line_width:
            while current_width > line_width:
                index -= 1
                current_width = font_object.getlength(text[:index])
            return index
        else:
            while index < len(text):
                current_width = font_object.getlength(text[: index + 1])
                if current_width > line_width:
                    break
                index += 1
            return index

    def _split_text_by_character(
        self, text: str, font_object: PillowFontType, line_width: int
    ) -> list[str]:
        lines = []
        remaining_text = text

        while remaining_text:
            index = self._get_index_for_line(remaining_text, font_object, line_width)
            if index == 0:
                index = 1
            lines.append(remaining_text[:index])
            remaining_text = remaining_text[index:]
        return lines

    def save(self, path: os.PathLike):
        file_path = Path(path)
        if len(self.images) == 1:
            self.current_image.save(file_path)
        else:
            for i, image in enumerate(self.images):
                image.save(file_path.with_stem(file_path.stem + f"_{i+1}"))
