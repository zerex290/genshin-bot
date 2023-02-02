from ...models.honeyimpact import books


def format_information(book: books.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"📚Серия книг: {book.name}\n"
        f"📗Часть: {book.volume}\n"
        f"📖Содержание:\n"
    )
    full_info = formatted_information + book.story
    restricted_info = formatted_information + 'Недоступно из-за ограничения Вконтакте на максимальную длину сообщения.'
    return full_info if len(full_info) <= 4096 else restricted_info
