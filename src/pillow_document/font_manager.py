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

    def ensure_font(self, font: str) -> str:
        """Return resolved_name. Accepts font name or font file path.
        - If not found or unsupported, fall back to DEFAULT_FONT with a warning.
        """
        is_file_path = any([font.endswith(ext) for ext in self.SUPPPORTED_FONT])
        if is_file_path:
            font_path = Path(font)
            if not font_path.exists():
                logger.warning(
                    f"Font file not found: '{font}'. Falling back to default font '{self.DEFAULT_FONT}'.",
                )
                return self.DEFAULT_FONT
            name = font_path.stem
            self._register_font(name, font_path)
            return name

        if font in self._fonts:
            return font
        self._register_font(name, font_path)
        system_path = self.get_system_font(font)
        if system_path:
            self._register_font(font, system_path)
            return font
        logger.warning(
            f"Font not found: '{font}'. Falling back to default font '{self.DEFAULT_FONT}'.",
        )
        return self.DEFAULT_FONT

    def _register_font(self, name: str, path: Path):
        self._fonts[name] = path
        self._supported_codepoints[name] = self._get_supported_characters(path)

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
