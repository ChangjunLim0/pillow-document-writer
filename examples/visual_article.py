from pathlib import Path
from pillow_document import DocumentWriter

script_directory = Path(__file__).resolve().parent
image_path = script_directory / "assets" / "arctic_fox.jpg"

writer = DocumentWriter(600, 900, margin=40)

writer.write_line("The Artic Fox", font_size=40, color="#445c5b")

writer.image(image_path, width=400, margin=20)
writer.write(
    "The Arctic fox, also known as the white fox, polar fox, or snow fox, is a small "
    "species of fox native to the Arctic regions of the Northern Hemisphere and common "
    "throughout the Arctic tundra biome. It is well adapted to living in cold environments, "
    "and is best known for its thick, warm fur that is also used as camouflage. It has a "
    "large and very fluffy tail. In the wild, most individuals do not live past their first"
    "year but some exceptional ones survive up to 11 years. (from Wikipedia)"
    "",
    font_size=18,
)

writer.save("The arctic fox visual article.png")
