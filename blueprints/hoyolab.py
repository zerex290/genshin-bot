import asyncio
import os
from random import randint

from vkbottle.bot import Blueprint, Message

from genshin.types import Game
from genshin.errors import GenshinException, InvalidCookies

import bot.src.templates as tpl
from bot.errors import IncompatibleOptions
from bot.rules import CommandRule
from bot.utils import PostgresConnection, GenshinClient
from bot.utils.files import download, upload
from bot.utils.genshin import get_genshin_account_by_id
from bot.imageprocessing.abyss import get_abyss_image
from bot.src.manuals import hoyolab as man
from bot.validators.hoyolab import *
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('HoYoLabCommands')


async def _get_formatted_notes(account: dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            notes = await client.get_genshin_notes(account['uid'])
            return tpl.hoyolab.format_notes(notes)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_stats(account: dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            stats = await client.get_partial_genshin_user(account['uid'])
            return tpl.hoyolab.format_stats(stats)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_rewards(account: dict[str, str | int]) -> tuple[str, str] | str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            rewards = await client.claimed_rewards(game=Game.GENSHIN.value)
            icon = await download(rewards[0].icon, FILECACHE, f"reward_{randint(0, 10000)}", 'png')
            attachment = await upload(bp.api, 'photo_messages', icon)
            os.remove(icon)
            return tpl.hoyolab.format_daily_rewards(rewards), attachment
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше не действительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_redeem_codes(account: dict[str, str | int], codes: list[str]) -> str:
    async with GenshinClient(account_id=account['ltuid'], cookie_token=account['cookie_token']) as client:
        response: list[str] = []
        for code in codes:
            try:
                await client.redeem_code(code, account['uid'])
                response.append(f"Успешно активирован промокод {code}!")
            except InvalidCookies:
                return 'Ошибка: указанные игровые данные больше недействительны!'
            except GenshinException as e:
                response.append(f"Ошибка активации промокода {code}: {e}")
            if len(codes) > 1:
                await asyncio.sleep(5)  #: required cooldown time to successfully activate redeem codes
        return '\n'.join(response)


async def _get_formatted_diary(account: dict[str, str | int]) -> str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            diary = await client.get_diary()
            return tpl.hoyolab.format_traveler_diary(diary)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


async def _get_formatted_abyss(account: dict[str, str | int], validator: SpiralAbyssValidator) -> tuple[str, str] | str:
    async with GenshinClient(ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        try:
            abyss = await client.get_genshin_spiral_abyss(account['uid'])
            validator.check_abyss_unlocked(abyss.unlocked)
            abyss_image = await get_abyss_image(abyss)
            attachment = await upload(bp.api, 'photo_messages', abyss_image)
            os.remove(abyss_image)
            return tpl.hoyolab.format_spiral_abyss(abyss), attachment
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as e:
            return f"Необработанная ошибка: {e}\nПросьба сообщить о ней в личные сообщения группы!"


@bp.on.message(CommandRule(('линк',), options=('-п',)))
async def link_genshin_account(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.AccountLink.options:
        await message.answer(man.AccountLink.options[options[0]])
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
async def unlink_genshin_account(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.AccountUnlink.options:
        await message.answer(man.AccountUnlink.options[options[0]])
        return

    async with AccountUnlinkValidator(message) as validator:
        await validator.check_account_linked(message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"DELETE FROM genshin_accounts WHERE user_id = {message.from_id};")
        await message.answer('Ваш игровой аккаунт был успешно отвязан!')


@bp.on.message(CommandRule(('заметки',), options=('-п', '-у')))
async def get_notes(message: Message, options: tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Notes') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.Notes.options[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await _get_formatted_notes(account))
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                await message.answer(await _get_formatted_notes(account))
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('статы',), options=('-п', '-у')))
async def get_stats(message: Message, options: tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Stats') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.Stats.options[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await _get_formatted_stats(account))
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                await message.answer(await _get_formatted_stats(account))
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('награды',), options=('-п',)))
async def get_rewards(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.Rewards.options:
        await message.answer(man.Rewards.options[options[0]])
        return

    async with GenshinDataValidator(message, 'Rewards') as validator:
        account = await get_genshin_account_by_id(message.from_id, False, True, True)
        validator.check_account_exist(account)
        formatted_rewards = await _get_formatted_rewards(account)
        if isinstance(formatted_rewards, tuple):
            formatted_rewards, attachment = formatted_rewards
        else:
            attachment = None
        await message.answer(formatted_rewards, attachment)


@bp.on.message(CommandRule(('пром',), options=('-п',)))
async def redeem_code(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.RedeemCode.options:
        await message.answer(man.RedeemCode.options[options[0]])
        return

    async with CodeValidator(message, 'Redeem') as validator:
        account = await get_genshin_account_by_id(message.from_id, True, True, True, True)
        validator.check_account_exist(account)
        codes = message.text.lstrip('!пром').strip().split()
        validator.check_code_specified(codes)
        await message.answer(await _get_formatted_redeem_codes(account, codes))


@bp.on.message(CommandRule(('резинноут',), options=('-п', '-выкл', '-вкл')))
async def manage_resin_notifications(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.ResinNotifications.options and len(options) == 1:
        await message.answer(man.ResinNotifications.options[options[0]])
        return

    async with ResinNotifyValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
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
async def get_traveler_diary(message: Message, options: tuple[str, ...]) -> None:
    async with GenshinDataValidator(message, 'Diary') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.Diary.options[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, False, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await _get_formatted_diary(account))
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, False, True, True)
                validator.check_account_exist(account)
                await message.answer(await _get_formatted_diary(account))
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('бездна',), options=('-п', '-у')))
async def get_spiral_abyss(message: Message, options: tuple[str, ...]) -> None:
    async with SpiralAbyssValidator(message, 'SpiralAbyss') as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.SpiralAbyss.options[options[0]])
            case ('-у',):
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)

                formatted_abyss = await _get_formatted_abyss(account, validator)
                if isinstance(formatted_abyss, tuple):
                    formatted_abyss, attachment = formatted_abyss
                else:
                    attachment = None
                await message.answer(formatted_abyss, attachment)
            case ('-[default]',):
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                formatted_abyss = await _get_formatted_abyss(account, validator)
                if isinstance(formatted_abyss, tuple):
                    formatted_abyss, attachment = formatted_abyss
                else:
                    attachment = None
                await message.answer(formatted_abyss, attachment)
            case _:
                raise IncompatibleOptions(options)
