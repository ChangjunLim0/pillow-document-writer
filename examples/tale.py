from pillow_document import DocumentWriter

writer = DocumentWriter(400, 500, margin=40)

writer.write_line("The Fox and the Grapes", font_size=40)
writer.rectangle(200, 2)
writer.write_line("")
writer.write(
    "A Fox one day spied a beautiful bunch of ripe grapes hanging from a vine trained "
    "along the branches of a tree. The grapes seemed ready to burst with juice, and the "
    "Fox’s mouth watered as he gazed longingly at them.\nThe bunch hung from a high branch, "
    "and the Fox had to jump for it. The first time he jumped he missed it by a long way. "
    "So he walked off a short distance and took a running leap at it, only to fall short "
    "once more.\nAgain and again he tried, but in vain. Now he sat down and looked at the "
    'grapes in disgust\n"What a fool I am," he said. "Here I am wearing myself out to '
    'get a bunch of sour grapes that are not worth gaping for."\nAnd off he walked very, '
    "very scornfully.",
    font_size=18,
)
writer.set_page_number()
writer.save("The fox and the grapes.png")
