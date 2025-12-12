import importlib.resources
import logging
import os
import sys

from fontTools.ttLib import TTFont
from pathlib import Path

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class FontManager:
    SUPPPORTED_FONT = [".ttf", ".otf", ".ttc"]
    DEFAULT_FONT = "Roboto-Regular"

    def __init__(self) -> None:
        self._fonts: dict[str, Path] = {}
        self._supported_codepoints: dict[str, set] = {}
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
        default_font_path = self._get_default_font_path()
        self._fonts[self.DEFAULT_FONT] = default_font_path
        self._supported_codepoints[self.DEFAULT_FONT] = self._get_supported_characters(
            default_font_path
        )

    @property
    def fonts(self) -> list[str]:
        return list(self._fonts.keys())

    def get_font(self, font_name: str) -> Path | None:
        return self._fonts.get(font_name)

    def get_system_font(self, font_name: str) -> Path:
        for directory in self.system_font_directories:
            try:
                for extension in self.SUPPPORTED_FONT:
                    for path in Path(directory).rglob(f"{font_name}.{extension}"):
                        return path
            except OSError:
                continue
        logger.warning(
            f"Font not found: '{font_name}'. Using default font ({self.DEFAULT_FONT}) instead."
        )

    def add_font(self, font: str):
        font_path = Path(font)
        if font_path.exists():
            self._fonts[font_path.stem] = font_path
            self._supported_codepoints[font_path.stem] = self._get_supported_characters(
                font_path
            )
            return
        if font in self._fonts:
            return
        self._fonts[font] = self.get_system_font(font)

    def _get_default_font_path(self) -> Path:
        with importlib.resources.path(
            "pillow_document.fonts", f"{self.DEFAULT_FONT}.ttf"
        ) as font_path:
            return font_path

    @classmethod
    def _get_supported_characters(cls, font_path: Path) -> set[int]:
        font = TTFont(str(font_path))
        supported_codepoints = set()
        for table in font["cmap"].tables:
            supported_codepoints.update(table.cmap.keys())
        return supported_codepoints

    def get_unsupported_chars(self, font: str, text: str) -> list[str]:
        supported_codepoints = self._supported_codepoints[font]
        unsupported_chars = list()
        for char in text:
            if char == "\n":
                continue
            codepoint = ord(char)
            if codepoint not in supported_codepoints:
                unsupported_chars.append(char)
        return unsupported_chars
