from bot.src.models import honeyimpact


class Characters:
    @staticmethod
    def format_information(character: honeyimpact.characters.Information) -> str:
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

    @staticmethod
    def format_active_skills(
            auto_attack: honeyimpact.characters.Skill,
            elemental_skill: honeyimpact.characters.Skill,
            alternative_sprint: honeyimpact.characters.Skill,
            elemental_burst: honeyimpact.characters.Skill
    ) -> str:

        formatted_active_skills = (
            f"♟Навыки:\n"
            f"• Авто-атака: {auto_attack.title} -- {auto_attack.description}\n"
            f"• Элем. навык: {elemental_skill.title} -- {elemental_skill.description}\n"
            f"• Доп. навык: {alternative_sprint.title} -- {alternative_sprint.description}\n"
            f"• Взрыв стихии: {elemental_burst.title} -- {elemental_burst.description}"
        )
        return formatted_active_skills

    @staticmethod
    def format_passive_skills(
            first_passive: honeyimpact.characters.Skill,
            second_passive: honeyimpact.characters.Skill,
            third_passive: honeyimpact.characters.Skill
    ) -> str:
        formatted_passive_skills = (
            f"🎳Пассивные навыки:\n"
            f"• {first_passive.title}: {first_passive.description}\n"
            f"• {second_passive.title}: {second_passive.description}\n"
            f"• {third_passive.title}: {third_passive.description}"
        )
        return formatted_passive_skills

    @staticmethod
    def format_constellations(
            first_constellation: honeyimpact.characters.Skill,
            second_constellation: honeyimpact.characters.Skill,
            third_constellation: honeyimpact.characters.Skill,
            fourth_constellation: honeyimpact.characters.Skill,
            fifth_constellation: honeyimpact.characters.Skill,
            sixth_constellation: honeyimpact.characters.Skill
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


class Weapons:
    @staticmethod
    def format_information(weapon: honeyimpact.weapons.Information) -> str:
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

    @staticmethod
    def format_ability(ability: honeyimpact.weapons.Ability) -> str:
        formatted_ability = (
            f"📋Пассивная способность:\n"
            f"✨Название: {ability.title}\n"
            f"📖Описание: {ability.description}"
        )
        return formatted_ability

    @staticmethod
    def format_progression(progression: honeyimpact.weapons.Progression) -> str:
        formatted_progression = []
        for row in progression.information:
            formatted_progression.append(
                f"• Лв: {row.level} / {row.primary_stat_title}: {row.primary_stat_value} / "
                f"{row.secondary_stat_title}: {row.secondary_stat_value}"
            )
        return '\n'.join(formatted_progression)

    @staticmethod
    def format_story(story: str) -> str:
        formatted_story = (
            f"📚История оружия:\n"
            f"{story}"
        )
        return formatted_story


class Artifacts:
    @staticmethod
    def format_information(artifact: honeyimpact.artifacts.Information) -> str:
        formatted_information = (
            f"🖼Основная информация:\n"
            f"🔱Сет: {artifact.name}\n"
            f"🎭Тип: {artifact.artifact_type}\n"
            f"💫Редкость: {artifact.rarity}⭐\n"
            f"2️⃣ предмета: {artifact.two_piece_bonus}\n"
            f"4️⃣ предмета: {artifact.four_piece_bonus}"
        )
        return formatted_information


class Enemies:
    @staticmethod
    def format_information(enemy: honeyimpact.enemies.Information) -> str:
        formatted_information = (
            f"🖼Основная информация:\n"
            f"👾Противник: {enemy.name}\n"
            f"🎭Тип: {enemy.enemy_type}\n"
            f"🧳Дроп: {enemy.drop}\n"
            f"📖Описание: {enemy.description}"
        )
        return formatted_information

    @staticmethod
    def format_progression(progression: honeyimpact.enemies.Progression) -> str:
        formatted_progression = []
        for row in progression.information:
            formatted_progression.append(
                f"• Лв: {row.level} 💉: {row.one_player_hp} 🗡: {row.one_player_atk} 🛡: {row.one_player_def}\n"
                f"2⃣👤💉: {row.two_player_hp} 2⃣👤🗡: {row.two_player_atk} 2⃣👤🛡: {row.two_player_def}\n"
                f"3⃣👤💉: {row.three_player_hp} 3⃣👤🗡: {row.three_player_atk} 3⃣👤🛡: {row.three_player_def}\n"
                f"4⃣👤💉: {row.four_player_hp} 4⃣👤🗡: {row.four_player_atk} 4⃣👤🛡: {row.four_player_def}\n"
            )
        return '\n'.join(formatted_progression)


class Books:
    @staticmethod
    def format_information(book: honeyimpact.books.Information) -> str:
        formatted_information = (
            f"🖼Основная информация:\n"
            f"📚Серия книг: {book.name}\n"
            f"📗Номер тома: {book.volume}\n"
            f"📖Содержание:\n{book.story}"
        )
        return formatted_information
