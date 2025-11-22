import os

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


## TODO: 줄바꿈, 폰트 관리 (font_manager?), 페이지 관리


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

        self.cursor_x = self.margin[1]
        self.cursor_y = self.margin[0]

        self._default_font = (
            Path(
                r"C:\Users\ailur\Documents\GitHub\pillow-document-writer\src\pillow_document\fonts"
            )
            / "Roboto-Regular.ttf"
        )
        self._default_font_size = 12
        self._font_cache = {}

        self._font_cache[(str(self._default_font), self._default_font_size)] = (
            ImageFont.truetype(self._default_font, self._default_font_size)
        )

    def write(self, text: str, font: str = None, font_size: int = None):
        if font is None:
            font = self._default_font
        if font_size is None:
            font_size = self._default_font_size
        font_image = self._font_cache.get(
            (str(font), font_size), ImageFont.truetype(font, font_size)
        )
        self.draw.text((self.cursor_x, self.cursor_y), text, "black", font_image)

        bbox = self.draw.textbbox((0, 0), text, font=font_image)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        self.cursor_x += text_width

    def write_line(self, text: str):
        pass

    def save(self, path: os.PathLike):
        self.image.save(path)
