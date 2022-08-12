from ...models.honeyimpact import characters


def format_information(character: characters.Information) -> str:
    formatted_information = (
        f"🖼Основная информация:\n"
        f"👤Персонаж: {character.name}\n"
        f"👑Титул: {character.title}\n"
        f"🧰Группа: {character.allegiance}\n"
        f"💫Редкость: {character.rarity}⭐\n"
        f"⚔Оружие: {character.weapon}\n"
        f"⚱Глаз Бога: {character.element}\n"
        f"📈Стат возвышения: {character.ascension_stat}\n"
        f"🎉День рождения: {character.birthday}\n"
        f"🔮Созвездие: {character.astrolabe_name}\n"
        f"📖Описание: {character.description}"
    )
    return formatted_information


def format_active_skills(
        auto_attack: characters.Skill,
        elemental_skill: characters.Skill,
        alternative_sprint: characters.Skill,
        elemental_burst: characters.Skill
) -> str:
    formatted_active_skills = (
        f"♟Навыки:\n"
        f"• Авто-атака: {auto_attack.title} -- {auto_attack.description}\n"
        f"• Элем. навык: {elemental_skill.title} -- {elemental_skill.description}\n"
        f"• Доп. навык: {alternative_sprint.title} -- {alternative_sprint.description}\n"
        f"• Взрыв стихии: {elemental_burst.title} -- {elemental_burst.description}"
    )
    return formatted_active_skills


def format_passive_skills(
        first_passive: characters.Skill,
        second_passive: characters.Skill,
        third_passive: characters.Skill
) -> str:
    formatted_passive_skills = (
        f"🎳Пассивные навыки:\n"
        f"• {first_passive.title}: {first_passive.description}\n"
        f"• {second_passive.title}: {second_passive.description}\n"
        f"• {third_passive.title}: {third_passive.description}"
    )
    return formatted_passive_skills


def format_constellations(
        first_constellation: characters.Skill,
        second_constellation: characters.Skill,
        third_constellation: characters.Skill,
        fourth_constellation: characters.Skill,
        fifth_constellation: characters.Skill,
        sixth_constellation: characters.Skill
) -> str:
    formatted_constellations = (
        f"🎆Описание созвездий:\n"
        f"• {first_constellation.title}: {first_constellation.description}\n"
        f"• {second_constellation.title}: {second_constellation.description}\n"
        f"• {third_constellation.title}: {third_constellation.description}\n"
        f"• {fourth_constellation.title}: {fourth_constellation.description}\n"
        f"• {fifth_constellation.title}: {fifth_constellation.description}\n"
        f"• {sixth_constellation.title}: {sixth_constellation.description}"
    )
    return formatted_constellations
