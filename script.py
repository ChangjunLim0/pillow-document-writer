import sys

sys.path.insert(0, "/Users/dolgom/Documents/GitHub/pillow-document-writer/src")

from pillow_document import DocumentWriter

writer = DocumentWriter(200, 600)

writer.write_line("Hello World!", font_size=70)
writer.write(
    "I am Document Writer. Today is my birthday. Say hello to my potential users"
)

writer.save("a.png")
