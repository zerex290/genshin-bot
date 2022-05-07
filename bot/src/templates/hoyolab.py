import datetime
import re
from typing import Sequence

from genshin.models.genshin import Notes, Exploration, ClaimedDailyReward, PartialGenshinUserStats

from bot.utils import get_current_timestamp
from bot.src.types.genshin import Characters, ElementSymbols, Regions, Rewards


def _get_estimated_recovery_time(object_recovery_time: datetime.datetime) -> str:
    current_time = get_current_timestamp(3)

    if object_recovery_time <= current_time:
        return '0 сек.'

    time = re.sub(r'\sday[s,]+\s', ':', str(object_recovery_time - current_time).split('.')[0]).split(':')
    match len(time):
        case 4:
            return '{} д. {} ч. {} мин.'.format(*time[:-1])
        case 3:
            return '{} ч. {} мин.'.format(*time[:-1])
        case 2:
            return '{} мин. {} сек.'.format(*time)
        case 1:
            return '{} сек.'.format(*time)


def format_notes(notes: Notes) -> str:
    expeditions = []
    for e in notes.expeditions:
        expedition_status = '♻' if e.status == 'Ongoing' else '✅'
        expeditions.append(
            f"{expedition_status}"
            f"{Characters[e.character.name.lower().replace(' ', '_')].value}: "
            f"🕑Осталось: {_get_estimated_recovery_time(e.completion_time)}\n"
        )

    formatted_notes = (
        f"🖼Игровые заметки в реальном времени:\n"
        f"🌙Смола: {notes.current_resin}, "
        f"🔃До восполнения: {_get_estimated_recovery_time(notes.resin_recovery_time)}\n"
        f"🎁Выполненные дейлики: {notes.completed_commissions}, "
        f"❓Собраны ли награды: {'Да' if notes.claimed_commission_reward else 'Нет'}\n"
        f"💹Скидки на боссов: {notes.remaining_resin_discounts}\n"
        f"💰Монеты обители: {notes.current_realm_currency}/{notes.max_realm_currency}, "
        f"⌛До восполнения: {_get_estimated_recovery_time(notes.realm_currency_recovery_time)}\n"
        f"☢Откат преобразователя: {_get_estimated_recovery_time(notes.transformer_recovery_time)}\n"
        f"🔰Начатые экспедиции: {len(notes.expeditions)}\n"
    ) + ''.join(expeditions)
    return formatted_notes


def _get_formatted_exploration_rewards(exploration: Exploration, region_en: str) -> str:
    match region_en:
        case 'Enkanomiya':
            return ''
        case 'Inazuma':
            return f"Ур. репутации: {exploration.level} ⛩Ур. Сакуры: {exploration.offerings[0].level}"
        case 'Dragonspine':
            return f"🌳Ур. Древа: {exploration.offerings[0].level}"
        case 'Liyue':
            return f"Ур. репутации: {exploration.level}"
        case 'Mondstadt':
            return f"Ур. репутации: {exploration.level}"
        case 'The Chasm':
            return ''
        case 'The Chasm: Underground Mines':
            return f"💎Ур. Адъюванта: {exploration.offerings[0].level}"
        case _:
            print(exploration.name)
            return 'Ошибка: регион не был обработан!'


def format_stats(stats: PartialGenshinUserStats) -> str:
    characters = []
    for c in stats.characters:
        characters.append(
            f"{c.rarity}⭐ "
            f"{ElementSymbols[c.element.lower()].value if c.element else '🌠'}"
            f"{Characters[c.name.lower().replace(' ', '_')].value} "
            f"Ур. {c.level} "
            f"🎮Ур. дружбы: {c.friendship}\n"
        )

    explorations = []
    for e in stats.explorations:
        if e.name:
            explorations.append(
                f"🌐{e.explored}% "
                f"{Regions[e.name.lower().replace(':', '').replace(' ', '_')].value} "
                f"{_get_formatted_exploration_rewards(e, e.name)}\n"
            )

    formatted_stats = (
        f"🖼Игровая статистика:\n"
        f"🏆Достижения: {stats.stats.achievements}\n"
        f"☀Дни активности: {stats.stats.days_active}\n"
        f"🌀Витая бездна: {stats.stats.spiral_abyss}\n"
        f"🍀Анемокулы: {stats.stats.anemoculi}\n"
        f"🏵Геокулы: {stats.stats.geoculi}\n"
        f"🌸Электрокулы: {stats.stats.electroculi}\n"
        f"🛸Точки телепортации: {stats.stats.unlocked_waypoints}\n"
        f"🚇Подземелья: {stats.stats.unlocked_domains}\n"
        f"🏡Чайник: Ур. {stats.teapot.level} 🧸Комфорт: {stats.teapot.comfort}\n\n"
        f"🧭Сундуки:\n"
        f"🗝Обычные сундуки: {stats.stats.common_chests}\n"
        f"🗝Богатые сундуки: {stats.stats.exquisite_chests}\n"
        f"🗝Драгоценные сундуки: {stats.stats.precious_chests}\n"
        f"🔑Роскошные сундуки: {stats.stats.luxurious_chests}\n\n"
        f"👥Персонажи:\n"
        f"📝Всего: {len(stats.characters)}\n"
        f"💌С 10 ур. дружбы: {len([c for c in stats.characters if c.friendship == 10])}\n"
    ) + ''.join(characters) + '\n🌍Прогресс исследований:\n' + ''.join(explorations)
    return formatted_stats


def _get_formatted_daily_reward_name(reward: ClaimedDailyReward) -> str:
    return Rewards[reward.name.lower().replace(' ', '_').replace("'s", "")].value


def format_daily_rewards(rewards: Sequence[ClaimedDailyReward]) -> str:
    current_month = get_current_timestamp(8).month  #: UTC+8 is login bonus offset on Europe
    current_month_rewards = [r for r in rewards if r.time.month == current_month]

    formatted_rewards = (
        f"🖼Информация о наградах на сайте:\n"
        f"🏆Собрано наград всего: {len(rewards)}\n"
        f"🏅Собрано наград за этот месяц: {len(current_month_rewards)}\n"
        f"🎖Последняя собранная награда: {_get_formatted_daily_reward_name(current_month_rewards[0])}"
    )
    return formatted_rewards
