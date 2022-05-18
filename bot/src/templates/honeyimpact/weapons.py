from bot.src.models.honeyimpact import weapons


def format_information(weapon: weapons.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"🔫Оружие: {weapon.name}\n"
        f"⚔Тип: {weapon.weapon_type}\n"
        f"💫Редкость: {weapon.rarity}⭐\n"
        f"🔨{weapon.primary_stat_title}: {weapon.primary_stat_value}\n"
        f"🔨{weapon.secondary_stat_title}: {weapon.secondary_stat_value}\n"
        f"📖Описание: {weapon.description}"
    )
    return formatted_information


def format_ability(ability: weapons.Ability) -> str:
    formatted_ability = (
        f"📋Пассивная способность:\n"
        f"✨Название: {ability.title}\n"
        f"📖Описание: {ability.description}"
    )
    return formatted_ability


def format_progression(progression: weapons.Progression) -> str:
    formatted_progression = ['🏹Прогрессия оружия:']
    for row in progression.information:
        formatted_progression.append(
            f"• Лв: {row.level} / {row.primary_stat_title}: {row.primary_stat_value} / "
            f"{row.secondary_stat_title}: {row.secondary_stat_value}"
        )
    return '\n'.join(formatted_progression)


def format_refinement(refinement: weapons.Refinement) -> str:
    formatted_refinement = ['⚒Пробуждение оружия:']
    for row in refinement.information:
        formatted_refinement.append(
            f"• Лв {row.level}: {row.description}"
        )
    return '\n'.join(formatted_refinement)


def format_story(story: str) -> str:
    formatted_story = (
        f"📚История оружия:\n"
        f"{story}"
    )
    return formatted_story
