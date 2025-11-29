import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

from pillow_document import DocumentWriter

writer = DocumentWriter(300, 500, margin=40)

writer.write_line("The Fox and the Grapes", font_size=40)
writer.write(
    """A Fox one day spied a beautiful bunch of ripe grapes hanging from a vine trained along the branches of a tree. The grapes seemed ready to burst with juice, and the Fox’s mouth watered as he gazed longingly at them.\n
The bunch hung from a high branch, and the Fox had to jump for it. The first time he jumped he missed it by a long way. So he walked off a short distance and took a running leap at it, only to fall short once more.\n
Again and again he tried, but in vain. Now he sat down and looked at the grapes in disgust\n
"What a fool I am," he said. "Here I am wearing myself out to get a bunch of sour grapes that are not worth gaping for."\n
And off he walked very, very scornfully.""",
    font_size=18,
)

writer.save("a.png")
