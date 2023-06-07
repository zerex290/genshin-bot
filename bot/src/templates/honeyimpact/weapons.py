from typing import Optional, List

from ...models.honeyimpact import weapons


def format_information(weapon: Optional[weapons.Information]) -> str:
    if weapon is None:
        return 'Информация пока отсутствует!'

    return (
        f"🖼Основная информация:\n"
        f"🔫Оружие: {weapon.name}\n"
        f"⚔Тип: {weapon.type}\n"
        f"💫Редкость: {weapon.rarity}⭐\n"
        f"🔨{weapon.primary_stat_title}: {weapon.primary_stat_value}\n"
        f"🔨{weapon.secondary_stat_title}: {weapon.secondary_stat_value}\n"
        f"📖Описание: {weapon.description}"
    )


def format_ability(ability: Optional[weapons.Ability]) -> str:
    if ability is None:
        return 'Информация пока отсутствует!'

    return (
        f"📋Пассивная способность:\n"
        f"✨Название: {ability.title}\n"
        f"📖Описание: {ability.description}"
    )


def format_refinement(refinements: List[weapons.Refinement]) -> str:
    if not refinements:
        return 'Информация пока отсутствует!'

    formatted_refinement = ['⚒Пробуждение оружия:']
    for r in refinements:
        formatted_refinement.append(
            f"• Лв {r.level}: {r.description}"
        )
    return '\n'.join(formatted_refinement)


def format_story(story: str) -> str:
    return 'Информация пока отсутствует!' if not story else f"📚История оружия:\n{story}"
