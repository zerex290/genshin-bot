from bot.src.models.honeyimpact import artifacts


def format_information(artifact: artifacts.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"🔱Сет: {artifact.name}\n"
        f"🎭Тип: {artifact.artifact_type}\n"
        f"💫Редкость: {artifact.rarity}⭐\n"
        f"2️⃣ предмета: {artifact.two_piece_bonus}\n"
        f"4️⃣ предмета: {artifact.four_piece_bonus}"
    )
    return formatted_information
