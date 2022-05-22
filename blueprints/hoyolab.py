import asyncio
import os
from typing import Tuple, Dict, List

from vkbottle.bot import Blueprint, Message

from genshin.types import Game
from genshin.errors import GenshinException, InvalidCookies

import bot.src.templates as tpl
from bot.errors import IncompatibleOptions
from bot.rules import CommandRule
from bot.utils import PostgresConnection, GenshinClient
from bot.utils.files import download, upload
from bot.utils.genshin import get_genshin_account_by_id
from bot.src.types.help import hoyolab as hints
from bot.validators.hoyolab import *
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('HoYoLabCommands')


async def _get_formatted_notes(account: Dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            notes = await client.get_genshin_notes(account['uid'])
            return tpl.hoyolab.format_notes(notes)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_stats(account: Dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            stats = await client.get_partial_genshin_user(account['uid'])
            return tpl.hoyolab.format_stats(stats)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_rewards(account: Dict[str, str | int]) -> Tuple[str, str] | str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            rewards = await client.claimed_rewards(game=Game.GENSHIN.value)
            return tpl.hoyolab.format_daily_rewards(rewards), rewards[0].icon
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_redeem_codes(account: Dict[str, str | int], codes: List[str]) -> str:
    async with GenshinClient(account_id=account['ltuid'], cookie_token=account['cookie_token']) as client:
        response: List[str] = []
        for code in codes:
            try:
                await client.redeem_code(code, account['uid'])
                response.append(f"Успешно активирован промокод {code}!")
            except InvalidCookies:
                response.append('Ошибка: указанные игровые данные больше недействительны!')
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
            if len(codes) > 1:
                await asyncio.sleep(5)  #: required cooldown time to successfully activate redeem codes
        return '\n'.join(response)


async def _get_formatted_diary(account: Dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            diary = await client.get_diary()
            return tpl.hoyolab.format_traveler_diary(diary)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


@bp.on.message(CommandRule(('линк',), options=('-п',)))
async def link_genshin_account(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.AccountLink.slots.value:
        await message.answer(hints.AccountLink.slots.value[options[0]])
        return None

    async with AccountLinkValidator(message) as validator:
        await validator.check_account_new(message.from_id)
        cookies = message.text.lstrip('!линк').strip().split()
        validator.check_cookie_amount(cookies)
        validator.check_cookie_syntax(cookies)
        cookies = {c.lower().split('=')[0]: c.split('=')[1] for c in cookies}
        await validator.check_cookies_valid(cookies)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO genshin_accounts (user_id, uid, ltuid, ltoken, cookie_token) VALUES (
                    {message.from_id}, {cookies['uid']}, {cookies['ltuid']}, 
                    '{cookies['ltoken']}', '{cookies['cookie_token']}'
                ); 
            """)
        await message.answer('Привязка вашего аккаунта прошла успешно!')


@bp.on.message(CommandRule(('анлинк',), options=('-п',)))
async def unlink_genshin_account(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.AccountUnlink.slots.value:
        await message.answer(hints.AccountUnlink.slots.value[options[0]])
        return

    async with AccountUnlinkValidator(message) as validator:
        await validator.check_account_linked(message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"DELETE FROM genshin_accounts WHERE user_id = {message.from_id};")
        await message.answer('Ваш игровой аккаунт был успешно отвязан!')


@bp.on.message(CommandRule(('заметки',), options=('-п', '-у')))
async def get_notes(message: Message, options: Tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Notes') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(hints.Notes.slots.value[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exists(account, True)
                await message.answer(await _get_formatted_notes(account))
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exists(account)
                await message.answer(await _get_formatted_notes(account))
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('статы',), options=('-п', '-у')))
async def get_stats(message: Message, options: Tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Stats') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(hints.Stats.slots.value[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exists(account, True)
                await message.answer(await _get_formatted_stats(account))
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exists(account)
                await message.answer(await _get_formatted_stats(account))
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('награды',), options=('-п',)))
async def get_claimed_rewards(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.Rewards.slots.value:
        await message.answer(hints.Rewards.slots.value[options[0]])
        return

    async with GenshinDataValidator(message, 'Rewards') as validator:
        account = await get_genshin_account_by_id(message.from_id, False, True, True)
        validator.check_account_exists(account)
        formatted_rewards = await _get_formatted_rewards(account)
        if isinstance(formatted_rewards, tuple):
            formatted_rewards, icon = formatted_rewards
            icon = await download(icon, FILECACHE, f"id{message.from_id}_reward", 'png')
            attachment = await upload(bp.api, 'photo_messages', icon)
            os.remove(icon)
        else:
            attachment = None
        await message.answer(formatted_rewards, attachment)


@bp.on.message(CommandRule(('пром',), options=('-п',)))
async def activate_redeem_code(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.RedeemCode.slots.value:
        await message.answer(hints.RedeemCode.slots.value[options[0]])
        return

    async with RedeemCodeValidator(message, 'Redeem') as validator:
        account = await get_genshin_account_by_id(message.from_id, True, True, True, True)
        validator.check_account_exists(account)
        codes = message.text.lstrip('!пром').strip().split()
        validator.check_redeem_specified(codes)
        await message.answer(await _get_formatted_redeem_codes(account, codes))


@bp.on.chat_message(CommandRule(('резинноут',), options=('-п', '-выкл', '-вкл')))
async def manage_resin_notifications(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.ResinNotifications.slots.value and len(options) == 1:
        await message.answer(hints.ResinNotifications.slots.value[options[0]])
        return
    async with ResinNotifyValidator(message) as validator:
        await validator.check_account_linked(message.from_id)
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
                await validator.check_notifications_enabled(message.from_id, message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(f"""
                        UPDATE users_in_chats SET resin_notifications = false 
                        WHERE user_id = {message.from_id} AND chat_id = {message.peer_id};
                    """)
                await message.answer('Автоматическое напоминание потратить смолу теперь выключено!')
            case ('-вкл',):
                await validator.check_notifications_disabled(message.from_id, message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(f"""
                        UPDATE users_in_chats SET resin_notifications = true 
                        WHERE user_id = {message.from_id} AND chat_id = {message.peer_id};
                    """)
                await message.answer('Автоматическое напоминание потратить смолу теперь включено!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('дневник',), options=('-п', '-у')))
async def get_traveler_diary(message: Message, options: Tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Diary') as validator:
        match options:
            case ('-[error]', ) | ('-п', ):
                await message.answer(hints.Diary.slots.value[options[0]])
            case ('-у', ):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, False, True, True)
                validator.check_account_exists(account, True)
                await message.answer(await _get_formatted_diary(account))
            case ('-[default]', ):
                account = await get_genshin_account_by_id(message.from_id, False, True, True)
                validator.check_account_exists(account)
                await message.answer(await _get_formatted_diary(account))
            case _:
                raise IncompatibleOptions(options)
