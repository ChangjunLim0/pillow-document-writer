import os
from PIL import Image, ImageDraw


class DocumentWriter:
    def __init__(self, width: int, height: int):
        self.image = Image.new("RGB", (width, height), color="white")
        self.draw = ImageDraw.Draw(self.image)
        self.cursor_x = 0
        self.cursor_y = 0
        self._font_cache = {}

    def write(text: str):
        pass

    def write_line(text: str):
        pass

    def save(self, path: os.PathLike):
        self.image.save(path)
