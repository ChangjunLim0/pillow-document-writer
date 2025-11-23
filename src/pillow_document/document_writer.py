import os

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import ImageFont as PillowFontType

from pillow_document.font_manager import FontManager

## TODO: 페이지 관리


class DocumentWriter:
    def __init__(
        self,
        width: int,
        height: int,
        margin: int | tuple[int] = 20,
        background_color="white",
    ):
        self.image = Image.new("RGB", (width, height), color=background_color)
        self.draw = ImageDraw.Draw(self.image)
        self.page = 1

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

        self.cursor_x = self.margin[1]
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
        return self.page_width - self.margin[0] - self.margin[2]

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

    def write(self, text: str, font: str = None, font_size: int = None):
        font_size = font_size or self._default_font_size
        font_object = self._get_or_create_font_object(font, font_size)
        wrapped_text = self._split_text_lines(text, font_object, self.line_width)
        for line in wrapped_text[:-1]:
            self.draw.text((self.cursor_x, self.cursor_y), line, "black", font_object)
            self.cursor_x = self.margin[0]
            self.cursor_y += font_size

        last_line = wrapped_text[-1]
        self.draw.text((self.cursor_x, self.cursor_y), last_line, "black", font_object)
        bbox = self.draw.textbbox((0, 0), last_line, font=font_object)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
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
                current_width = font_object.getlength(text[:index+1])
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

    def write_line(self, text: str, font: str = None, font_size: int = None):
        font_size = font_size or self._default_font_size
        font_object = self._get_or_create_font_object(font, font_size)
        wrapped_text = self._split_text_lines(text, font_object, self.line_width)
        for line in wrapped_text:
            self.draw.text((self.cursor_x, self.cursor_y), line, "black", font_object)
            self.cursor_x = self.margin[0]
            self.cursor_y += font_size
        self.cursor_x = self.margin[1]

    def save(self, path: os.PathLike):
        self.image.save(path)
