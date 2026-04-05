import logging
import os

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import ImageFont as PillowFontType

from pillow_document.font_manager import FontManager

## TODO: header/footer

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DocumentWriter:
    def __init__(
        self,
        width: int,
        height: int,
        margin: int | tuple[int, ...] = 20,
        background_color="white",
        auto_page_break: bool = True,
        line_spacing: float = 1.2,
    ):
        self.current_canvas = Image.new("RGB", (width, height), color=background_color)
        self.draw = ImageDraw.Draw(self.current_canvas)
        self.page = 1
        self.images = [self.current_canvas]

        self.margin = self.get_margin_trbl(margin)

        self.page_width = width
        self.page_height = height
        self.background_color = background_color
        self.auto_page_break = auto_page_break
        self.line_spacing = line_spacing

        self.cursor_x = self.left_margin
        self.cursor_y = self.content_top

        self._default_font = "Roboto-Regular"
        self._default_font_size = 12

        self.font_manager = FontManager()
        self._font_object_cache = {}
        self._font_object_cache[(self._default_font, self._default_font_size)] = (
            ImageFont.truetype(
                self.font_manager.get_font(self._default_font), self._default_font_size
            )
        )
        self._page_number_config = None

    @classmethod
    def get_margin_trbl(cls, margin: int | tuple[int, ...] | None) -> tuple[int, ...]:
        # (top, right, bottom, left)
        if margin is None:
            return (0, 0, 0, 0)
        if isinstance(margin, int):
            return (margin, margin, margin, margin)
        elif isinstance(margin, tuple):
            if len(margin) == 1:
                return (margin[0], margin[0], margin[0], margin[0])
            if len(margin) == 2:
                return (margin[0], margin[1], margin[0], margin[1])
            elif len(margin) == 4:
                return margin
            else:
                raise ValueError
        else:
            raise ValueError

    @property
    def content_top(self) -> int:
        return self.margin[0]

    @property
    def content_bottom(self) -> int:
        return self.page_height - self.margin[2]

    @property
    def line_width(self) -> int:
        return self.page_width - self.margin[1] - self.margin[3]

    @property
    def left_margin(self) -> int:
        return self.margin[3]

    def set_default_font(self, font: str):
        font = self.font_manager.ensure_font(font)
        self._default_font = font

    def _get_or_create_font_object(self, font: str, font_size: int) -> PillowFontType:
        font_object = self._font_object_cache.get((font, font_size))
        if font_object is None:
            font_object = ImageFont.truetype(
                str(self.font_manager.get_font(font)), font_size
            )
            self._font_object_cache[(font, font_size)] = font_object
        return font_object

    def _go_to_next_page(self):
        self.current_canvas = Image.new(
            "RGB", (self.page_width, self.page_height), color=self.background_color
        )
        self.draw = ImageDraw.Draw(self.current_canvas)
        self.page += 1
        self.images.append(self.current_canvas)

        self.cursor_x = self.left_margin
        self.cursor_y = self.content_top

    def _check_and_go_to_next_page(self, line_height: int):
        if self.cursor_y + line_height > self.content_bottom:
            if self.auto_page_break:
                self._go_to_next_page()
            else:
                logger.warning(
                    f"Content overflows page {self.page}. "
                    "Set auto_page_break=True to enable automatic pagination."
                )

    def new_page(self):
        self._go_to_next_page()

    def write(
        self,
        text: str,
        font: str = None,
        font_size: int = None,
        color="black",
        min_width: int = 0,
        align: str = "left",
        line_spacing: float = None,
    ):
        font_size = font_size or self._default_font_size
        font = font or self._default_font
        font = self.font_manager.ensure_font(font)
        initial_cursor_x = self.cursor_x
        initial_cursor_y = self.cursor_y
        self._check_if_font_supports(font, text)
        font_object = self._get_or_create_font_object(font, font_size)
        line_spacing = line_spacing if line_spacing is not None else self.line_spacing
        line_texts = text.split("\n")
        for line in line_texts[:-1]:
            self._write_text(
                line,
                font_object,
                color,
                line_break=True,
                align=align,
                line_spacing=line_spacing,
            )
        last_line = line_texts[-1]
        self._write_text(
            last_line,
            font_object,
            color,
            line_break=False,
            align=align,
            line_spacing=line_spacing,
        )
        if self.cursor_y == initial_cursor_y:
            self.cursor_x = max(self.cursor_x, initial_cursor_x + min_width)

    def write_line(
        self,
        text: str,
        font: str = None,
        font_size: int = None,
        color="black",
        min_height: int = 0,
        align: str = "left",
        line_spacing: float = None,
    ):
        font_size = font_size or self._default_font_size
        font = font or self._default_font
        font = self.font_manager.ensure_font(font)
        initial_page = self.page
        initial_cursor_y = self.cursor_y
        self._check_if_font_supports(font, text)
        font_object = self._get_or_create_font_object(font, font_size)
        line_spacing = line_spacing if line_spacing is not None else self.line_spacing
        line_texts = text.split("\n")
        for line in line_texts:
            self._write_text(
                line,
                font_object,
                color,
                line_break=True,
                align=align,
                line_spacing=line_spacing,
            )
        if initial_page == self.page:
            self.cursor_y = max(self.cursor_y, initial_cursor_y + min_height)

    def _check_if_font_supports(self, font: str, text: str):
        unsupported_chars = self.font_manager.get_unsupported_chars(font, text)
        if len(unsupported_chars) > 0:
            logger.warning(
                f"'{font}' does not support {', '.join(list(unsupported_chars))}"
            )

    def _get_x_for_align(
        self, text: str, font_object: PillowFontType, align: str
    ) -> int:
        if align == "left":
            return self.left_margin
        text_width = int(self.draw.textlength(text, font=font_object))
        if align == "center":
            return self.left_margin + (self.line_width - text_width) // 2
        if align == "right":
            return self.left_margin + self.line_width - text_width
        return self.left_margin

    def _write_text(
        self,
        text: str,
        font_object: PillowFontType,
        color,
        line_break: bool = False,
        align: str = "left",
        line_spacing: float = 1.0,
    ):
        remaining_width = max(self.line_width - (self.cursor_x - self.left_margin), 0)
        wrapped_text = self._split_text_lines(
            text, font_object, remaining_width, self.line_width
        )
        line_height = int(font_object.size * line_spacing)

        for line in wrapped_text[:-1]:
            self._check_and_go_to_next_page(line_height)
            x = (
                self._get_x_for_align(line, font_object, align)
                if align != "left"
                else self.cursor_x
            )
            self.draw.text((x, self.cursor_y), line, color, font_object)
            self.cursor_x = self.left_margin
            self.cursor_y += line_height

        last_line = wrapped_text[-1]
        self._check_and_go_to_next_page(line_height)
        if line_break:
            x = (
                self._get_x_for_align(last_line, font_object, align)
                if align != "left"
                else self.cursor_x
            )
            self.draw.text((x, self.cursor_y), last_line, color, font_object)
            self.cursor_x = self.left_margin
            self.cursor_y += line_height
        else:
            self.draw.text(
                (self.cursor_x, self.cursor_y), last_line, color, font_object
            )
            bbox = self.draw.textbbox((0, 0), last_line, font=font_object)
            text_width = bbox[2] - bbox[0]
            self.cursor_x += text_width

    def _split_text_lines(
        self,
        text: str,
        font_object: PillowFontType,
        first_line_width: int,
        line_width: int,
        mode="word",
    ) -> list[str]:
        current_line_width = first_line_width
        space_width = font_object.getlength(" ")
        words = text.split(" ")
        current_line = []
        current_width = 0
        lines = []
        first_word = words[0]
        first_word_length = font_object.getlength(first_word)
        if first_word_length > first_line_width and first_line_width != line_width:
            lines.append("\n")
            current_line_width = line_width
        for word in words:
            word_length = font_object.getlength(word)
            if word_length > current_line_width:
                if current_line_width != line_width:  # first_line
                    lines.append("\n")
                if len(current_line) > 0:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_width = 0
                chunks = self._split_text_by_character(
                    word, font_object, current_line_width, line_width
                )
                lines.extend(chunks[:-1])
                last_chunk = chunks[-1]
                current_line.append(last_chunk)
                current_width += font_object.getlength(last_chunk)
                current_line_width = line_width
                continue

            if current_width + word_length <= current_line_width:
                if current_width > 0:
                    current_width += space_width
                current_width += word_length
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_length
                current_line_width = line_width
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
        self,
        text: str,
        font_object: PillowFontType,
        first_line_width: int,
        line_width: int = None,
    ) -> list[str]:
        lines = []
        remaining_text = text
        if line_width is None:
            line_width = first_line_width
        current_line_width = first_line_width
        while remaining_text:
            index = self._get_index_for_line(
                remaining_text, font_object, current_line_width
            )
            if index == 0:
                index = 1
            lines.append(remaining_text[:index])
            remaining_text = remaining_text[index:]
            current_line_width = line_width
        return lines

    def rectangle(
        self, width: int, height: int, color="black", line_break: bool = True
    ):
        xy = [
            (self.cursor_x, self.cursor_y),
            (self.cursor_x + width, self.cursor_y + height),
        ]
        self.draw.rectangle(xy, color)
        if line_break:
            self.cursor_y += height
        else:
            self.cursor_x += width

    def image(
        self,
        image_path: os.PathLike,
        width: int = None,
        height: int = None,
        margin: int | tuple[int, ...] = None,
        line_break: bool = True,
    ):
        if not Path(image_path).exists():
            logger.warning(f"Image {image_path} does not exists.")
            return
        image_margin = self.get_margin_trbl(margin)
        overlay_image = Image.open(image_path)
        if height and width:
            overlay_image = overlay_image.resize((width, height))
        elif height and not width:
            resized_width = int(overlay_image.width * height / overlay_image.height)
            overlay_image = overlay_image.resize((resized_width, height))
        elif not height and width:
            resized_height = int(overlay_image.height * width / overlay_image.width)
            overlay_image = overlay_image.resize((width, resized_height))
        self._check_and_go_to_next_page(
            overlay_image.height + image_margin[0] + image_margin[2]
        )
        image_xy = (self.cursor_x + image_margin[3], self.cursor_y + image_margin[0])
        self.current_canvas.paste(overlay_image, image_xy)

        if line_break:
            self.cursor_x = self.left_margin
            self.cursor_y += overlay_image.height + image_margin[0] + image_margin[2]
        else:
            self.cursor_x += overlay_image.width + image_margin[1] + image_margin[3]

    def set_page_number(
        self,
        position: str = "bottom-center",
        format: str = "{page}",
        font: str = None,
        font_size: int = None,
        color="black",
    ):
        self._page_number_config = {
            "position": position,
            "format": format,
            "font": font or self._default_font,
            "font_size": font_size or self._default_font_size,
            "color": color,
        }

    def _get_images_with_page_numbers(self) -> list[Image.Image]:
        if self._page_number_config is None:
            return self.images
        cfg = self._page_number_config
        font_object = self._get_or_create_font_object(cfg["font"], cfg["font_size"])
        result = []
        for i, image in enumerate(self.images):
            copy = image.copy()
            text = cfg["format"].replace("{page}", str(i + 1))
            draw = ImageDraw.Draw(copy)
            bbox = draw.textbbox((0, 0), text, font=font_object)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = cfg["position"]

            if "left" in position:
                x = self.margin[3]
            elif "center" in position:
                x = (self.page_width - text_width) // 2
            else:  # right
                x = self.page_width - self.margin[1] - text_width

            if "top" in position:
                y = (self.margin[0] - text_height) // 2
            else:  # bottom
                y = (
                    self.page_height
                    - self.margin[2]
                    + (self.margin[2] - text_height) // 2
                )

            x = max(0, min(self.page_width - text_width, x))
            y = max(0, min(self.page_height - text_height, y))

            draw.text((x, y), text, cfg["color"], font_object)
            result.append(copy)
        return result

    def save(self, path: os.PathLike):
        images = self._get_images_with_page_numbers()
        file_path = Path(path)
        if len(images) == 1:
            images[0].save(file_path)
        else:
            for i, image in enumerate(images):
                image.save(file_path.with_stem(file_path.stem + f"_{i + 1}"))
