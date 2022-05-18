from bot.src.models.honeyimpact import enemies


def format_information(enemy: enemies.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"👾Противник: {enemy.name}\n"
        f"🎭Тип: {enemy.enemy_type}\n"
        f"🧳Дроп: {enemy.drop}\n"
        f"📖Описание: {enemy.description}"
    )
    return formatted_information


def format_progression(progression: enemies.Progression) -> str:
    formatted_progression = ['🏹Прогрессия противника:']
    for row in progression.information:
        formatted_progression.append(
            f"• Лв: {row.level} 💉: {row.one_player_hp} 🗡: {row.one_player_atk} 🛡: {row.one_player_def}\n"
            f"2⃣👤💉: {row.two_player_hp} 2⃣👤🗡: {row.two_player_atk} 2⃣👤🛡: {row.two_player_def}\n"
            f"3⃣👤💉: {row.three_player_hp} 3⃣👤🗡: {row.three_player_atk} 3⃣👤🛡: {row.three_player_def}\n"
            f"4⃣👤💉: {row.four_player_hp} 4⃣👤🗡: {row.four_player_atk} 4⃣👤🛡: {row.four_player_def}\n"
        )
    return '\n'.join(formatted_progression)
