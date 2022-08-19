from ...models.honeyimpact import domains


def format_information(domain: domains.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"⚔Подземелье: {domain.name}\n"
        f"⚙Тип: {domain.type}\n"
        f"📖Описание: {domain.description}"
    )
    return formatted_information
