from ...models.honeyimpact import enemies


def format_information(enemy: enemies.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"👾Противник: {enemy.name}\n"
        f"🎭Тип: {enemy.enemy_type}\n"
        f"❇Класс: {enemy.grade}\n"
        f"📖Описание: {enemy.description}"
    )
    return formatted_information
