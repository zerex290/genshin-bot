from ...models.honeyimpact import books


def format_information(book: books.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"📚Серия книг: {book.name}\n"
        f"📗Номер тома: {book.volume}\n"
        f"📖Содержание:\n{book.story}"
    )
    return formatted_information
