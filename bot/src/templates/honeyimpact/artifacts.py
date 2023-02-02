from typing import Optional

from ...models.honeyimpact import artifacts


def format_information(artifact: Optional[artifacts.Information]) -> str:
    if artifact is None:
        return 'Информация пока отсутствует!'

    formatted_information = [
        f"🖼Основная информация:",
        f"🔱Сет: {artifact.name}",
        f"🎭Тип: {artifact.type}",
        f"💫Редкость: {artifact.rarity}⭐"
    ]
    if len(artifact.affix) == 2:
        formatted_information.append(
            f"2️⃣ предмета: {artifact.affix[0]}\n"
            f"4️⃣ предмета: {artifact.affix[1]}"
        )
    else:
        formatted_information.append(f"1️⃣ предмет: {artifact.affix[0]}")
    return '\n'.join(formatted_information)
