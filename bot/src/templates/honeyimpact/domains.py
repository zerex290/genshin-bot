from bot.src.models.honeyimpact import domains


def format_information(domain: domains.Information) -> str:
    indent = '\n• '
    formatted_information = (
        f"🖼Основная информация:\n"
        f"⚔Подземелье: {domain.name}\n"
        f"⚙Тип: {domain.type}\n"
        f"📖Описание: {domain.description}\n"
        f"🎯Рек. стихии: {' | '.join(domain.recommended_elements) if domain.recommended_elements else '-'}\n"
    )
    if domain.disorders is not None:
        formatted_information += f"✨Эффекты:\n• {indent.join(domain.disorders)}"
    return formatted_information
