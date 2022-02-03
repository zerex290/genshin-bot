"""Service use only"""


import datetime

from constants import Genshin


class HoYoLAB:
    @staticmethod
    def notes(n: dict) -> str:
        def title():
            return '🖼Ваши заметки в реальном времени:'

        def resin():
            response = (
                f"🌙Смола: {n['resin']}, 🔃До восполнения: "
                f"{int(n['until_resin_limit']) // 3600} ч. {int(n['until_resin_limit']) % 3600 // 60} мин."
            )
            return response

        def dailies():
            response = (
                f"🎁Выполненные дейлики: {n['completed_commissions']}, "
                f"❓Собраны ли награды: {'Да' if n['claimed_commission_reward'] else 'Нет'}"
            )
            return response

        def discounts():
            return f"💹Скидки на боссов: {n['remaining_boss_discounts']}"

        def expeditions():
            prettified = [f"🔰Начатые экспедиции: {len(n['expeditions'])}\n"]

            for expedition in n['expeditions']:
                prettified.append(
                    f"👤Персонаж: {Genshin.CHARACTER[expedition['icon'].split('_')[-1][:-4]]}, "
                    f"🕑Осталось: {int(expedition['remaining_time']) // 3600} ч. "
                    f"{int(expedition['remaining_time']) % 3600 // 60} мин.\n"
                )
            return ''.join(prettified)
        return '\n'.join([title(), resin(), dailies(), discounts(), expeditions()])

    @staticmethod
    def rewards(r: list) -> dict:
        def title():
            return '🖼Информация о наградах на сайте:'

        def monthly_rewards():
            current_month = str(datetime.datetime.now()).split('-')[1]
            monthly = [reward for reward in r[0] if reward['created_at'].split('-')[1] == current_month]
            summary = (
                f"🏅Собрано наград за этот месяц: {len(monthly)}\n"
                f"❓Сегодняшняя награда: "
                f"{'уже была собрана...' if r[1] is None else 'успешно собрана!'}\n"
                f"🎖Последняя собранная награда: {monthly[0]['name']}\n", monthly[0]['img']
            )
            return summary

        rewards, icon = monthly_rewards()
        return {'title': title(), 'rewards': rewards, 'icon_link': icon}

    @staticmethod
    def stats(s: dict) -> str:
        def title():
            return '🖼Ваша статистика:'

        def achievements():
            return f"🏆Достижения: {s['stats']['achievements']}"

        def active_days():
            return f"☀Дни активности: {s['stats']['active_days']}"

        def abyss():
            return f"🌀Витая бездна: {s['stats']['spiral_abyss']}"

        def anemoculi():
            return f"🍀Анемокулы: {s['stats']['anemoculi']}"

        def geoculi():
            return f"🏵Геокулы: {s['stats']['geoculi']}"

        def electroculi():
            return f"🌸Электрокулы: {s['stats']['electroculi']}"

        def chests():
            response_ = (
                f"🗝Обычные сундуки: {s['stats']['common_chests']}\n"
                f"🗝Богатые сундуки: {s['stats']['exquisite_chests']}\n"
                f"🗝Драгоценные сундуки: {s['stats']['precious_chests']}\n"
                f"🔑Роскошные сундуки: {s['stats']['luxurious_chests']}"
            )
            return response_

        def waypoints():
            return f"🛸Точки телепортации: {s['stats']['unlocked_waypoints']}"

        def domains():
            return f"🚇Подземелья: {s['stats']['unlocked_domains']}"

        def teapot():
            if s.get('teapot'):
                return f"🏡Чайник: Ур. {s['teapot']['level']} 🧸Комфорт: {s['teapot']['comfort']}"
            else:
                return '🏡Чайник: еще не открыт!'

        def characters():
            friendship = [ch['friendship'] for ch in s['characters'] if ch['friendship'] == 10]
            response_ = [
                '👥Персонажи:', f"📝всего -- {s['stats']['characters']}", f"💌с 10 ур. дружбы -- {len(friendship)}"
            ]

            for i, character in enumerate(s['characters']):
                response_.append(
                    f"{s['characters'][i]['rarity']}⭐ "
                    f"{Genshin.ELEMENT[s['characters'][i]['element']]['symbol']}"
                    f"{s['characters'][i]['name']} "
                    f"Ур. {s['characters'][i]['level']} "
                    f"🎮Ур. дружбы: {s['characters'][i]['friendship']}"
                )
            return '\n'.join(response_)

        def explorations():
            """I have to do that shitty 2-lined lambda templates, cuz i don't know how to solve it better"""
            regions = {
                'Инадзума': lambda r: f"Ур. репутации: {s['explorations'][r]['level']}\n"
                                      f"⛩Благосклонность Сакуры: Ур. {s['explorations'][r]['offerings'][0]['level']}",
                'Драконий хребет': lambda r: f"🌳Древо вечной мерзлоты: "
                                             f"Ур. {s['explorations'][r]['offerings'][0]['level']}",
                'Ли Юэ': lambda r: f"Ур. репутации:  {s['explorations'][r]['level']}",
                'Мондштадт': lambda r: f"Ур. репутации:  {s['explorations'][r]['level']}",
                'Энканомия': lambda r: f"",
                '': lambda r: f"Неизвестный регион: подробная информация будет доступна после открытия..."
            }
            response_ = []

            for i, exploration in enumerate(s['explorations']):
                r_name = s['explorations'][i]['name']
                response_.append(
                    f"🌐{r_name} 🧩Прогресс: {s['explorations'][i]['explored']}% "
                    f"{regions.get(r_name, lambda r: f'Ошибка на итерации {r}')(i)}"
                )
            return '\n'.join(response_)

        response = '\n'.join(
            [title(), achievements(), active_days(), abyss(), anemoculi(), geoculi(),
             electroculi(), chests(), waypoints(), domains(), teapot(), characters(), explorations()]
        )
        return response


class Database:
    @staticmethod
    def character(user_id: int, name: str, filter_: str) -> dict:
        response = {
            'main': {
                'label': 'Основная информация', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'character',
                            'filter': filter_, 'name': name, 'data': 'main'}
            },
            'skills': {
                'label': 'Активные навыки', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'character',
                            'filter': filter_, 'name': name, 'data': 'skills'}
            },
            'passives': {
                'label': 'Пассивные навыки', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'character',
                            'filter': filter_, 'name': name, 'data': 'passives'}
            },
            'constellations': {
                'label': 'Созвездия', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'character',
                            'filter': filter_, 'name': name, 'data': 'constellations'}
            }
        }
        return response

    @staticmethod
    def weapon(user_id: int, name: str, filter_: str) -> dict:
        response = {
            'main': {
                'label': 'Основная информация', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'weapon',
                            'filter': filter_, 'name': name, 'data': 'main'}
            },
            'ability': {
                'label': 'Способность оружия', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'weapon',
                            'filter': filter_, 'name': name, 'data': 'ability'}
            },
            'progression': {
                'label': 'Прогрессия оружия', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'weapon',
                            'filter': filter_, 'name': name, 'data': 'progression'}
            },
            'story': {
                'label': 'История оружия', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'weapon',
                            'filter': filter_, 'name': name, 'data': 'story'}
            }
        }
        return response

    @staticmethod
    def enemy(user_id: int, name: str, filter_: str) -> dict:
        response = {
            'main': {
                'label': 'Основная информация', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'enemie',
                            'filter': filter_, 'name': name, 'data': 'main'}
            },
            'progression': {
                'label': 'Прогрессия противника', 'color': 'secondary',
                'payload': {'user_id': user_id, 'type': 'enemie',
                            'filter': filter_, 'name': name, 'data': 'progression'}
            }
        }
        return response
