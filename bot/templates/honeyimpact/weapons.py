from ...models.honeyimpact import weapons


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


def format_progression(progressions: list[weapons.Progression]) -> str:
    formatted_progression = ['🏹Прогрессия оружия:']
    for p in progressions:
        formatted_progression.append(
            f"• Лв: {p.level} / {p.primary_stat_title}: {p.primary_stat_value} / "
            f"{p.secondary_stat_title}: {p.secondary_stat_value}"
        )
    return '\n'.join(formatted_progression)


def format_refinement(refinements: list[weapons.Refinement]) -> str:
    formatted_refinement = ['⚒Пробуждение оружия:']
    for r in refinements:
        formatted_refinement.append(
            f"• Лв {r.level}: {r.description}"
        )
    return '\n'.join(formatted_refinement)


def format_story(story: str) -> str:
    formatted_story = (
        f"📚История оружия:\n"
        f"{story}"
    )
    return formatted_story
