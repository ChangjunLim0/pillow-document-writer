import importlib.resources
import os
import sys

from pathlib import Path


class FontManager:
    SUPPPORTED_FONT = [".ttf", ".otf", ".ttc"]

    def __init__(self) -> None:
        self._fonts = {}
        if sys.platform == "darwin":  # macOS
            self.system_font_directories = [
                "/Library/Fonts",
                "/System/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
            ]
        elif sys.platform == "win32":  # Windows
            self.system_font_directories = [
                "C:\\Windows\\Fonts",
                os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Fonts"),
            ]
        else:  # Linux
            self.system_font_directories = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.local/share/fonts"),
                os.path.expanduser("~/.fonts"),
            ]
        self._add_default_font()

    @property
    def fonts(self) -> list[str]:
        return list(self._fonts.keys())

    def get_font(self, font_name: str):
        return self._fonts.get(font_name)

    def get_system_font(self, font_name: str) -> str:
        for directory in self.system_font_directories:
            try:
                for extension in self.SUPPPORTED_FONT:
                    for path in Path(directory).rglob(f"{font_name}.{extension}"):
                        return str(path)
            except OSError:
                continue
        raise FileNotFoundError
        ## TODO: log warning message

    def add_font(self, font: str):
        font_path = Path(font)
        if font_path.exists():
            self._fonts[font_path.stem] = font_path
            return
        if font in self._fonts:
            return
        self._fonts[font] = self.get_system_font(font)

    def _add_default_font(self):
        with importlib.resources.path(
            "pillow_document.fonts", "Roboto-Regular.ttf"
        ) as font_path:
            self._fonts["Roboto-Regular"] = font_path
