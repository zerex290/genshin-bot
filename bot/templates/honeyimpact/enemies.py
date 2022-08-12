from ...models.honeyimpact import enemies


def format_information(enemy: enemies.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"👾Противник: {enemy.name}\n"
        f"🎭Тип: {enemy.enemy_type}\n"
        f"🧳Дроп: {enemy.drop}\n"
        f"📖Описание: {enemy.description}"
    )
    return formatted_information


def format_progression(progressions: list[enemies.Progression]) -> str:
    formatted_progression = ['🏹Прогрессия противника:']
    for p in progressions:
        formatted_progression.append(
            f"• Лв: {p.level} 💉: {p.one_player_hp} 🗡: {p.one_player_atk} 🛡: {p.one_player_def}\n"
            f"2⃣👤💉: {p.two_player_hp} 2⃣👤🗡: {p.two_player_atk} 2⃣👤🛡: {p.two_player_def}\n"
            f"3⃣👤💉: {p.three_player_hp} 3⃣👤🗡: {p.three_player_atk} 3⃣👤🛡: {p.three_player_def}\n"
            f"4⃣👤💉: {p.four_player_hp} 4⃣👤🗡: {p.four_player_atk} 4⃣👤🛡: {p.four_player_def}\n"
        )
    return '\n'.join(formatted_progression)
