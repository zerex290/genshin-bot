import asyncio
import os
from typing import Tuple, Dict

from vkbottle.bot import Blueprint, Message

from genshin.types import Game
from genshin.errors import GenshinException, InvalidCookies

import bot.src.templates as tpl
from bot.rules import CommandRule
from bot.utils import PostgresConnection, GenshinClient
from bot.utils.files import download, upload
from bot.utils.postgres import has_postgres_data
from bot.utils.genshin import is_genshin_account, get_genshin_account_by_id
from bot.src.types.help import hoyolab as hints
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('HoYoLabCommands')


async def _get_formatted_notes(account: Dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            notes = await client.get_genshin_notes(account['uid'])
            return tpl.hoyolab.format_notes(notes)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_stats(account: Dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            stats = await client.get_partial_genshin_user(account['uid'])
            return tpl.hoyolab.format_stats(stats)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_rewards(account: Dict[str, str | int]) -> Tuple[str, str] | str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            rewards = await client.claimed_rewards(game=Game.GENSHIN.value)
            return tpl.hoyolab.format_daily_rewards(rewards), rewards[0].icon
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


@bp.on.message(CommandRule(('линк',), options=('-[default]', '-[error]', '-п')))
async def link_genshin_account(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.AccountLink.slots.value:
        await message.answer(hints.AccountLink.slots.value[options[0]])
        return None

    if await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {message.from_id};"):
        await message.answer('Ошибка: ваши данные уже имеются в базе!')
        return None
    cookies = message.text.lstrip('!линк').strip().split()
    if not cookies or len(cookies) != 4:
        await message.answer('Ошибка: вы указали не все необходимые для привязки данные!')
        return None
    try:
        cookies = {c.lower().split('=')[0]: c.split('=')[1] for c in cookies}
        assert {'ltuid', 'ltoken', 'uid', 'cookie_token'} == set(cookies)
    except (IndexError, AssertionError):
        await message.answer('Ошибка: при указании данных нарушен синтаксис!')
        return None
    if not await is_genshin_account(**cookies):
        await message.answer('Ошибка: указанные игровые данные не являются действительными!')
        return None

    async with PostgresConnection() as connection:
        await connection.execute(f"""
            INSERT INTO genshin_accounts (user_id, uid, ltuid, ltoken, cookie_token) VALUES (
                {message.from_id}, {cookies['uid']}, {cookies['ltuid']}, 
                '{cookies['ltoken']}', '{cookies['cookie_token']}'
            ); 
        """)
    await message.answer('Привязка вашего аккаунта прошла успешно!')


@bp.on.message(CommandRule(('анлинк',), options=('-[default]', '-[error]', '-п')))
async def unlink_genshin_account(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.AccountUnlink.slots.value:
        await message.answer(hints.AccountUnlink.slots.value[options[0]])
        return

    if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {message.from_id};"):
        await message.answer('Ошибка: ваших данных нет в базе!')
        return
    async with PostgresConnection() as connection:
        await connection.execute(f"DELETE FROM genshin_accounts WHERE user_id = {message.from_id};")
    await message.answer('Ваш игровой аккаунт был успешно отвязан!')


@bp.on.message(CommandRule(('заметки',), options=('-[default]', '-[error]', '-п', '-у')))
async def get_notes(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    match options:
        case ('-[error]',) | ('-п',):
            await message.answer(hints.Notes.slots.value[options[0]])
        case ('-у',) if message.reply_message:
            reply_message_user_id = message.reply_message.from_id
            account = await get_genshin_account_by_id(reply_message_user_id, True, True, True)
            if not account:
                await message.answer('Ошибка: в базе отсутствуют данные указанного игрока!')
                return
            await message.answer(await _get_formatted_notes(account))
        case ('-у',) if not message.reply_message:
            await message.answer('Ошибка: не прикреплено сообщение другого игрока для просмотра его заметок!')
        case ('-[default]',):
            account = await get_genshin_account_by_id(message.from_id, True, True, True)
            if not account:
                await message.answer('Ошибка: в базе отсутствуют ваши данные!')
                return
            await message.answer(await _get_formatted_notes(account))
        case _:
            await message.answer(f"Ошибка: переданы несовместимые опции: {' '.join(options)}!")


@bp.on.message(CommandRule(('статы',), options=('-[default]', '-[error]', '-п', '-у')))
async def get_stats(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    match options:
        case ('-[error]',) | ('-п',):
            await message.answer(hints.Stats.slots.value[options[0]])
        case ('-у',) if message.reply_message:
            reply_message_user_id = message.reply_message.from_id
            account = await get_genshin_account_by_id(reply_message_user_id, True, True, True)
            if not account:
                await message.answer('Ошибка: в базе отсутствуют данные указанного игрока!')
                return
            await message.answer(await _get_formatted_stats(account))
        case ('-у',) if not message.reply_message:
            await message.answer('Ошибка: не прикреплено сообщение другого игрока для просмотра его статистики!')
        case ('-[default]',):
            account = await get_genshin_account_by_id(message.from_id, True, True, True)
            if not account:
                await message.answer('Ошибка: в базе отсутствуют ваши данные!')
                return
            await message.answer(await _get_formatted_stats(account))
        case _:
            await message.answer(f"Ошибка: переданы несовместимые опции: {' '.join(options)}!")


@bp.on.message(CommandRule(('награды',), options=('-[default]', '-[error]', '-п')))
async def get_claimed_rewards(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.Rewards.slots.value:
        await message.answer(hints.Rewards.slots.value[options[0]])
        return

    account = await get_genshin_account_by_id(message.from_id, False, True, True)
    if not account:
        await message.answer('Ошибка: в базе отсутствуют ваши данные!')
        return
    formatted_rewards = await _get_formatted_rewards(account)
    if isinstance(formatted_rewards, tuple):
        formatted_rewards, icon = formatted_rewards
        icon = await download(icon, FILECACHE, f"id{message.from_id}_reward", 'png')
        attachment = await upload(bp.api, 'photo_messages', icon)
        os.remove(icon)
    else:
        attachment = None
    await message.answer(formatted_rewards, attachment)


@bp.on.message(CommandRule(('пром',), options=('-[default]', '-[error]', '-п')))
async def activate_redeem_code(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.RedeemCode.slots.value:
        await message.answer(hints.RedeemCode.slots.value[options[0]])
        return

    account = await get_genshin_account_by_id(message.from_id, True, True, True, True)
    if not account:
        await message.answer('Ошибка: в базе отсутствуют ваши данные!')
        return
    codes = message.text.lstrip('!пром').strip().split()
    if not codes:
        await message.answer('Ошибка: не указан не один промокод!')
        return

    response = []
    async with GenshinClient(account_id=account['ltuid'], cookie_token=account['cookie_token']) as client:
        for code in codes:
            try:
                await client.redeem_code(code, account['uid'])
                response.append(f"Успешно активирован промокод {code}!")
            except InvalidCookies:
                await message.answer('Ошибка: указанные игровые данные больше недействительны!')
                return
            except GenshinException as e:
                match e.retcode:
                    case -2003 | -2004:
                        response.append(f"Ошибка активации промокода {code}: промокод не является действительным!")
                    case -2001:
                        response.append(f"Ошибка активации промокода {code}: срок действия промокода истек!")
                    case -2021:
                        response.append(f"Ошибка активации промокода {code}: ваш ранг приключений меньше 10!")
                    case -2017 | -2018:
                        response.append(f"Ошибка активации промокода {code}: данный промокод уже был активирован!")
                    case _:
                        response.append(
                            f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"
                        )
            await asyncio.sleep(5)  #: required cooldown time to successfully activate redeem codes
    await message.answer('\n'.join(response))


@bp.on.chat_message(CommandRule(('резинноут',), options=('-[default]', '-[error]', '-п', '-выкл', '-вкл')))
async def manage_resin_notifications(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.ResinNotifications.slots.value and len(options) == 1:
        await message.answer(hints.ResinNotifications.slots.value[options[0]])
        return
    if not await get_genshin_account_by_id(message.from_id, True):
        await message.answer(
            'Ошибка: вы не можете воспользоваться данной командой, т.к. не привязали свой игровой аккаунт!'
        )
        return

    match options:
        case ('-[default]',):
            async with PostgresConnection() as connection:
                status = dict(await connection.fetchrow(f"""
                    SELECT resin_notifications FROM users_in_chats 
                    WHERE user_id = {message.from_id} AND chat_id = {message.peer_id};
                """))
                await message.answer(
                    f"В текущем чате у вас {'включены' if status['resin_notifications'] else 'выключены'} "
                    f"оповещения о трате смолы!"
                )
        case ('-выкл',):
            async with PostgresConnection() as connection:
                await connection.execute(f"""
                    UPDATE users_in_chats SET resin_notifications = false 
                    WHERE user_id = {message.from_id} AND chat_id = {message.peer_id};
                """)
            await message.answer('Автоматическое напоминание потратить смолу выключено!')
        case ('-вкл',):
            async with PostgresConnection() as connection:
                await connection.execute(f"""
                    UPDATE users_in_chats SET resin_notifications = true 
                    WHERE user_id = {message.from_id} AND chat_id = {message.peer_id};
                """)
            await message.answer('Автоматическое напоминание потратить смолу включено!')
        case ('-выкл', '-вкл') | ('-вкл', '-выкл'):
            await message.answer(f"Ошибка: переданы несовместимые опции: {' '.join(options)}!")
        case _:
            await message.answer(f"Ошибка: переданы несовместимые опции: {' '.join(options)}!")
