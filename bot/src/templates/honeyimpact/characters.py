from typing import Optional, List

from ...models.honeyimpact import characters


def format_information(character: Optional[characters.Information]) -> str:
    if character is None:
        return 'Информация пока отсутствует!'

    return (
        f"🖼Основная информация:\n"
        f"👤Персонаж: {character.name}\n"
        f"👑Титул: {character.title}\n"
        f"🧰Группа: {character.occupation}\n"
        f"🌎Регион: {character.association}\n"
        f"💫Редкость: {character.rarity}⭐\n"
        f"⚔Оружие: {character.weapon}\n"
        f"⚱Глаз Бога: {character.element}\n"
        f"📈Стат возвышения: {character.ascension_stat}\n"
        f"🎉Дата рождения: {character.birthdate}\n"
        f"🔮Созвездие: {character.constellation}\n"
        f"📖Описание: {character.description}"
    )


def format_active_skills(
        auto_attack: Optional[characters.Skill] = None,
        elemental_skill: Optional[characters.Skill] = None,
        elemental_burst: Optional[characters.Skill] = None,
        alternative_sprint: Optional[characters.Skill] = None
) -> str:
    if not any(locals().values()):
        return 'Информация пока отсутствует'

    formatted_active_skills = [
        '♟Активные Навыки:',
        f"• Авто-атака: {auto_attack.title} -- {auto_attack.description}",
        f"• Элем. навык: {elemental_skill.title} -- {elemental_skill.description}",
        f"• Взрыв стихии: {elemental_burst.title} -- {elemental_burst.description}"
    ]
    if alternative_sprint is not None:
        formatted_active_skills.append(f"• Доп. навык: {alternative_sprint.title} -- {alternative_sprint.description}")
    return '\n'.join(formatted_active_skills)


def format_passive_skills(skills: List[characters.Skill]) -> str:
    if not skills:
        return 'Информация пока отсутствует!'

    formatted_passive_skills = [f"🎳Пассивные навыки:"]
    for skill in skills:
        formatted_passive_skills.append(f"• {skill.title}: {skill.description}")
    return '\n'.join(formatted_passive_skills)


def format_constellations(constellations: List[characters.Skill]) -> str:
    if not constellations:
        return 'Информация пока отсутствует!'

    formatted_constellations = [f"🎆Описание созвездий:"]
    indexes = ['❶', '❷', '❸', '❹', '❺', '❻']
    for i, constellation in enumerate(constellations):
        formatted_constellations.append(f"{indexes[i]} {constellation.title}: {constellation.description}")
    return '\n'.join(formatted_constellations)
