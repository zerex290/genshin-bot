"""Service use only"""


class Characters:
    @staticmethod
    def main(info: dict) -> str:
        response = (
            f"🖼Основная информация:\n"
            f"👤Персонаж: {info['name']}\n"
            f"👑Титул: {info['title']}\n"
            f"🧰Группа: {info['allegiance']}\n"
            f"💫Редкость: {info['rarity']}⭐\n"
            f"⚔Оружие: {info['weapon_type']}\n"
            f"⚱Глаз Бога: {info['element']}\n"
            f"🎉День рождения: {info['birthday']}\n"
            f"🔮Созвездие: {info['constellation_title']}\n"
            f"📖Описание: {info['description']}"
        )
        return response

    @staticmethod
    def skills(info: dict) -> str:
        sprint = f"{info['sprint']['title']} -- {info['sprint']['description']}"
        sprint = 'Отсутствует' if info['sprint']['title'] == '' else sprint

        response = (
            f"♟Навыки:\n"
            f"• Авто-атака: {info['auto_attack']['title']} -- {info['auto_attack']['description']}\n"
            f"• Элем. навык: {info['elemental_skill']['title']} -- {info['elemental_skill']['description']}\n"
            f"• Доп. навык: {sprint}\n"
            f"• Взрыв стихии: {info['elemental_burst']['title']} -- {info['elemental_burst']['description']}"
        )
        return response

    @staticmethod
    def passives(info: dict) -> str:
        response = (
            f"🎳Пассивные навыки:\n"
            f"• {info['first_passive']['title']}: {info['first_passive']['description']}\n"
            f"• {info['second_passive']['title']}: {info['second_passive']['description']}\n"
            f"• {info['third_passive']['title']}: {info['third_passive']['description']}"
        )
        return response

    @staticmethod
    def constellations(info: dict) -> str:
        response = (
            f"🎆Описание созвездий:\n"
            f"• {info['first_constellation']['title']}: {info['first_constellation']['description']}\n"
            f"• {info['second_constellation']['title']}: {info['second_constellation']['description']}\n"
            f"• {info['third_constellation']['title']}: {info['third_constellation']['description']}\n"
            f"• {info['fourth_constellation']['title']}: {info['fourth_constellation']['description']}\n"
            f"• {info['fifth_constellation']['title']}: {info['fifth_constellation']['description']}\n"
            f"• {info['sixth_constellation']['title']}: {info['sixth_constellation']['description']}"
        )
        return response


class Weapons:
    @staticmethod
    def main(info: dict) -> str:
        response = (
            f"🖼Основная информация:\n"
            f"🔫Оружие: {info['name']}\n"
            f"⚔Тип: {info['type']}\n"
            f"💫Редкость: {info['rarity']}⭐\n"
            f"🔨{info['primary_stat']}: {info['primary_stat_value']}\n"
            f"🔨{info['secondary_stat']}: {info['secondary_stat_value']}\n"
            f"📖Описание: {info['description']}"
        )
        return response

    @staticmethod
    def ability(info: dict) -> str:
        response = (
            f"📋Пассивная способность:\n"
            f"✨Название: {info['ability_title']}\n"
            f"📖Описание: {info['ability_description']}"
        )
        return response

    @staticmethod
    def progression(info: list) -> str:
        response = ['📈Прогрессия оружия:']

        for i in info:
            response.append(f"• Лв: {i['Лв']} / Атака: {i['Атака']} / {list(i)[-1]}: {i[list(i)[-1]]}")
        return '\n'.join(response)

    @staticmethod
    def story(info: list) -> str:
        response = (
            f"📚История оружия:\n"
            f"{''.join(info)}"
        )
        return response


class Artifacts:
    @staticmethod
    def main(info: dict) -> str:
        response = (
            f"🖼Основная информация:\n"
            f"🔱Сет: {info['name']}\n"
            f"🎭Тип: {info['type']}\n"
            f"💫Редкость: {info['rarity']}⭐\n"
            f"2️⃣ предмета: {info['two_piece_bonus']}\n"
            f"4️⃣ предмета: {info['four_piece_bonus']}"
        )
        return response


class Enemies:
    @staticmethod
    def main(info: dict) -> str:
        response = (
            f"🖼Основная информация:\n"
            f"👾Противник: {info['name']}\n"
            f"🎭Тип: {info['type']}\n"
            f"📖Описание: {info['description']}\n"
            f"🧳Дроп: {info['drop']}"
        )
        return response

    @staticmethod
    def progression(info: list) -> str:
        response = ['📈Прогрессия противника:']

        for i in info:
            response.append(
                f"• Лв: {i['Лв']} 💉: {i['💉']} 🗡: {i['🗡']} 🛡: {i['🛡']}\n"
                f"2⃣👤💉: {i['2⃣👤💉']} 2⃣👤🗡: {i['2⃣👤🗡']} 2⃣👤🛡: {i['2⃣👤🛡']}\n"
                f"3⃣👤💉: {i['3⃣👤💉']} 3⃣👤🗡: {i['3⃣👤🗡']} 3⃣👤🛡: {i['3⃣👤🛡']}\n"
                f"4⃣👤💉: {i['4⃣👤💉']} 4⃣👤🗡: {i['4⃣👤🗡']} 4⃣👤🛡: {i['4⃣👤🛡']}\n"
            )
        return '\n'.join(response)
