from typing import Optional

from ...models.honeyimpact import enemies


def format_information(enemy: Optional[enemies.Information]) -> str:
    if enemy is None:
        return 'Информация пока отсутствует!'

    return (
        f"🖼Основная информация:\n"
        f"👾Противник: {enemy.name}\n"
        f"🎭Тип: {enemy.enemy_type}\n"
        f"❇Класс: {enemy.grade}\n"
        f"📖Описание: {enemy.description}"
    )
