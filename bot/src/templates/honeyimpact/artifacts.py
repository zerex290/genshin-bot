from ...models.honeyimpact import artifacts


def format_information(artifact: artifacts.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"🔱Сет: {artifact.name}\n"
        f"🎭Тип: {artifact.type}\n"
        f"💫Редкость: {artifact.rarity}⭐\n"
    )
    if len(artifact.affix) == 2:
        formatted_information += (
            f"2️⃣ предмета: {artifact.affix[0]}\n"
            f"4️⃣ предмета: {artifact.affix[1]}"
        )
    else:
        formatted_information += (
            f"1️⃣ предмет: {artifact.affix[0]}"
        )
    return formatted_information
