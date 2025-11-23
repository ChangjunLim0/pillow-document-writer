import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

from pillow_document import DocumentWriter

writer = DocumentWriter(200, 600, margin=40)

writer.write_line("Hello World!", font_size=70)
writer.write(
    "I am Document Writer. Today is my birthday. Say hello to my potential users"
)

writer.save("a.png")
