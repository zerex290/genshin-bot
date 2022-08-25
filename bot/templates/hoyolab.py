import datetime
import re
from typing import Sequence, Literal, TypeAlias

from vkbottle_types.objects import UsersUserFull

from genshin.models import Notes, ClaimedDailyReward, PartialGenshinUserStats, Diary
from genshin.models.genshin.chronicle.abyss import SpiralAbyss, AbyssRankCharacter

from ..utils import get_current_timestamp
from ..types.genshin import Characters, ElementSymbols, Regions, Offerings, DiaryCategories, DiaryCategorySymbols
from ..types.uncategorized import MonthIntegers, Months


_Display: TypeAlias = Literal['short', 'long']


def _format_recovery_time(object_recovery_time: datetime.datetime) -> str:
    current_time = get_current_timestamp(3)

    if object_recovery_time is None:
        return 'данные не были получены'

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


def format_notes(notes: Notes, user: UsersUserFull, display: _Display) -> str:
    header = f"🖼Игровые заметки пользователя {user.first_name} {user.last_name}:"
    if display == 'short':
        return header

    expeditions = []
    for e in notes.expeditions:
        expedition_status = '♻' if e.status == 'Ongoing' else '✅'
        expeditions.append(
            f"{expedition_status}"
            f"{Characters[e.character.name.upper().replace(' ', '_')].value}: "
            f"🕑Осталось: {_format_recovery_time(e.completion_time)}\n"
        )

    formatted_notes = (
        f"{header}\n"
        f"🌙Смола: {notes.current_resin}, "
        f"🔃До восполнения: {_format_recovery_time(notes.resin_recovery_time)}\n"
        f"🎁Выполненные дейлики: {notes.completed_commissions}, "
        f"❓Собраны ли награды: {'Да' if notes.claimed_commission_reward else 'Нет'}\n"
        f"💹Скидки на боссов: {notes.remaining_resin_discounts}\n"
        f"💰Монеты обители: {notes.current_realm_currency}/{notes.max_realm_currency}, "
        f"⌛До восполнения: {_format_recovery_time(notes.realm_currency_recovery_time)}\n"
        f"☢Откат преобразователя: {_format_recovery_time(notes.transformer_recovery_time)}\n"
        f"🔰Начатые экспедиции: {len(notes.expeditions)}\n"
    ) + ''.join(expeditions)
    return formatted_notes


def format_stats(stats: PartialGenshinUserStats, user: UsersUserFull, display: _Display) -> str:
    header = f"🖼Игровая статистика пользователя {user.first_name} {user.last_name}:"
    if display == 'short':
        return header

    characters = []
    five_star = []
    four_star = []
    for c in stats.characters:
        five_star.append(c) if c.rarity == 5 else four_star.append(c)
        characters.append(
            f"{c.rarity}⭐ "
            f"{ElementSymbols[c.element.upper()].value if c.element else '🌠'}"
            f"{Characters[c.name.upper().replace(' ', '_')].value} "
            f"Ур. {c.level} "
            f"🎮Ур. дружбы: {c.friendship}\n"
        )

    explorations = []
    for e in stats.explorations:
        if e.name:
            offerings = []
            for o in e.offerings:
                o_name = Offerings[re.sub(r"'s|:|-", '', o.name).replace(' ', '_').upper()].value
                offerings.append(f"🍥{o_name}: {o.level}")
            e_name = Regions[re.sub(r"'s|:|-", '', e.name).replace(' ', '_').upper()].value
            explorations.append(f"🌐{e.explored}% {e_name} {' '.join(offerings)}\n")

    if stats.teapot is None:
        teapot = 'Не открыт'
    else:
        teapot = f"Ур. {stats.teapot.level} 🧸Комфорт: {stats.teapot.comfort}"

    formatted_stats = (
        f"{header}\n"
        f"🏆Достижения: {stats.stats.achievements}\n"
        f"☀Дни активности: {stats.stats.days_active}\n"
        f"🌀Витая бездна: {stats.stats.spiral_abyss}\n"
        f"🍀Анемокулы: {stats.stats.anemoculi}\n"
        f"🏵Геокулы: {stats.stats.geoculi}\n"
        f"🌸Электрокулы: {stats.stats.electroculi}\n"
        f"🛸Точки телепортации: {stats.stats.unlocked_waypoints}\n"
        f"🚇Подземелья: {stats.stats.unlocked_domains}\n"
        f"🏡Чайник: {teapot}\n\n"
        f"🧭Сундуки:\n"
        f"🗝Обычные сундуки: {stats.stats.common_chests}\n"
        f"🗝Богатые сундуки: {stats.stats.exquisite_chests}\n"
        f"🗝Драгоценные сундуки: {stats.stats.precious_chests}\n"
        f"🔑Роскошные сундуки: {stats.stats.luxurious_chests}\n"
        f"🔑Удивительные сундуки: {stats.stats.remarkable_chests}\n\n"
        f"👥Персонажи:\n"
        f"📝Всего: {len(stats.characters)} (5⭐: {len(five_star)} | 4⭐: {len(four_star)})\n"
        f"💌С 10 ур. дружбы: {len([c for c in stats.characters if c.friendship == 10])}\n"
        f"{''.join(characters)}\n\n"
        f"🌍Прогресс исследований:\n"
        f"{''.join(explorations)}"
    )
    return formatted_stats


def format_daily_rewards(rewards: Sequence[ClaimedDailyReward], user: UsersUserFull, display: _Display) -> str:
    header = f"🖼Награды пользователя {user.first_name} {user.last_name}:"
    if display == 'short':
        return header

    current_month = get_current_timestamp(8).month  #: UTC+8 is login bonus offset on Europe
    current_month_rewards = [r for r in rewards if r.time.month == current_month]

    formatted_rewards = (
        f"{header}\n"
        f"🏆Собрано наград всего: {len(rewards)}\n"
        f"🏅Собрано наград за этот месяц: {len(current_month_rewards)}\n"
        f"🎖Последняя собранная награда:"
    )
    return formatted_rewards


def format_traveler_diary(diary: Diary, user: UsersUserFull, display: _Display) -> str:
    header = f"🖼Дневник пользователя {user.first_name} {user.last_name}:"
    if display == 'short':
        return header

    categories = []
    for c in diary.data.categories:
        category = DiaryCategories[c.name.replace(' ', '_').upper()]
        categories.append(
            f"{DiaryCategorySymbols[category.name].value}{category.value}: {c.amount} примогемов ({c.percentage}%)\n"
        )

    month = Months[MonthIntegers(diary.month).name].value
    formatted_traveler_diary = (
        f"{header}\n"
        f"💰Получено моры за день: {diary.day_data.current_mora}\n"
        f"💎Получено примогемов за день: {diary.day_data.current_primogems}\n"
        f"💰Получено моры за {month}: {diary.data.current_mora}\n"
        f"💎Получено примогемов за {month}: {diary.data.current_primogems}\n\n"
        f"🏅Получено примогемов по категориям:\n"
        f"{''.join(categories)}"
    )
    return formatted_traveler_diary


def _format_abyss_character(ch: AbyssRankCharacter) -> str:
    return f"{ElementSymbols[ch.element.upper()].value}{Characters[ch.name.upper().replace(' ', '_')].value}"


def _format_abyss_ranks(characters: Sequence[AbyssRankCharacter]) -> str:
    if not characters:
        return 'данные отсутствуют'
    return f"{_format_abyss_character(characters[0])} -> {characters[0].value}"


def format_spiral_abyss(abyss: SpiralAbyss) -> str:
    most_played = [f"{_format_abyss_character(c)}-{c.value}" for c in abyss.ranks.most_played]
    formatted_spiral_abyss = (
        f"🖼Витая бездна:\n"
        f"♨Период: с {abyss.start_time.strftime('%d.%m.%Y')} по {abyss.end_time.strftime('%d.%m.%Y')}\n"
        f"🌀Макс. глубина: {abyss.max_floor} | {abyss.total_stars}⭐\n"
        f"⚔Битвы: {abyss.total_battles}\n"
        f"👥Попыток битв: {', '.join(most_played)}\n"
        f"🏅Максимум побед: {_format_abyss_ranks(abyss.ranks.most_kills)}\n"
        f"👊Самый мощный удар: {_format_abyss_ranks(abyss.ranks.strongest_strike)}\n"
        f"💢Макс. полученного урона: {_format_abyss_ranks(abyss.ranks.most_damage_taken)}\n"
        f"💥Выполнено взрывов стихий: {_format_abyss_ranks(abyss.ranks.most_bursts_used)}\n"
        f"💣Элементальные навыки: {_format_abyss_ranks(abyss.ranks.most_skills_used)}"
    )
    return formatted_spiral_abyss
