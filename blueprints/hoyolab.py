import asyncio
import os
from random import randint
from typing import TypeAlias

from vkbottle.bot import Blueprint, Message

from genshin.types import Game
from genshin.errors import GenshinException, InvalidCookies

import bot.src.templates as tpl
from . import Options
from bot.errors import IncompatibleOptions
from bot.rules import CommandRule
from bot.utils import PostgresConnection, GenshinClient
from bot.utils.files import download, upload
from bot.utils.genshin import get_genshin_account_by_id, catch_hoyolab_errors
from bot.imageprocessing.abyss import get_abyss_image
from bot.src.manuals import hoyolab as man
from bot.validators.hoyolab import *
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('HoYoLabCommands')


GenshinAccount: TypeAlias = dict[str, str | int]


class HoYoLAB:
    def __init__(self, account: GenshinAccount) -> None:
        self.account = account


class Notes(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> str:
        async with GenshinClient(ltuid=self.account['ltuid'], ltoken=self.account['ltoken']) as client:
            return tpl.hoyolab.format_notes(await client.get_genshin_notes(self.account['uid']))


class Stats(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> str:
        async with GenshinClient(ltuid=self.account['ltuid'], ltoken=self.account['ltoken']) as client:
            return tpl.hoyolab.format_stats(await client.get_partial_genshin_user(self.account['uid']))


class Rewards(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> tuple[str, str]:
        async with GenshinClient(ltuid=self.account['ltuid'], ltoken=self.account['ltoken']) as client:
            rewards = await client.claimed_rewards(game=Game.GENSHIN.value)
            icon = await download(rewards[0].icon, FILECACHE, f"reward_{randint(0, 10000)}", 'png')
            attachment = await upload(bp.api, 'photo_messages', icon)
            os.remove(icon)
            return tpl.hoyolab.format_daily_rewards(rewards), attachment


class Codes(HoYoLAB):
    def __init__(self, account: GenshinAccount, codes: list[str]) -> None:
        super().__init__(account)
        self.codes = codes

    async def redeem(self) -> str:
        async with GenshinClient(account_id=self.account['ltuid'], cookie_token=self.account['cookie_token']) as client:
            response = []
            for code in self.codes:
                try:
                    await client.redeem_code(code, self.account['uid'])
                    response.append(f"Успешно активирован промокод {code}!")
                except InvalidCookies:
                    return 'Ошибка: указанные игровые данные больше недействительны!'
                except GenshinException as e:
                    response.append(f"Ошибка активации промокода {code}: {e}")
                if len(self.codes) > 1:
                    await asyncio.sleep(5)  #: required cooldown time to successfully activate redeem codes
            return '\n'.join(response)


class Diary(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> str:
        async with GenshinClient(ltuid=self.account['ltuid'], ltoken=self.account['ltoken']) as client:
            return tpl.hoyolab.format_traveler_diary(await client.get_diary(self.account['uid']))


class ResinNotifications:
    def __init__(self, message: Message) -> None:
        self.message = message

    async def get_status(self) -> str:
        async with PostgresConnection() as connection:
            data = dict(await connection.fetchrow(f"""
                SELECT resin_notifications, notification_value 
                FROM users_in_chats 
                WHERE user_id = {self.message.from_id} AND chat_id = {self.message.peer_id};
            """))
            status, value = data['resin_notifications'], data['notification_value']
            return (
                f"В текущем чате у вас {'включены' if status else 'выключены'} "
                f"упоминания о трате смолы! "
                f"{'Минимально необходимое для упоминаний значение равно {}.'.format(value) if status else ''}"
            )

    async def set_notification_minimum(self, value: int) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE users_in_chats SET notification_value = {value} 
                WHERE user_id = {self.message.from_id} AND chat_id = {self.message.peer_id};
            """)

    async def turn_on(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE users_in_chats SET resin_notifications = true 
                WHERE user_id = {self.message.from_id} AND chat_id = {self.message.peer_id};
            """)

    async def turn_off(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE users_in_chats SET resin_notifications = false 
                WHERE user_id = {self.message.from_id} AND chat_id = {self.message.peer_id};
            """)


class SpiralAbyss(HoYoLAB):
    def __init__(self, account: GenshinAccount, validator: SpiralAbyssValidator) -> None:
        super().__init__(account)
        self.validator = validator

    @catch_hoyolab_errors
    async def get(self) -> tuple[str, str]:
        async with GenshinClient(ltuid=self.account['ltuid'], ltoken=self.account['ltoken']) as client:
            abyss = await client.get_genshin_spiral_abyss(self.account['uid'])
            self.validator.check_abyss_unlocked(abyss.unlocked)
            abyss_image = await get_abyss_image(abyss)
            attachment = await upload(bp.api, 'photo_messages', abyss_image)
            os.remove(abyss_image)
            return tpl.hoyolab.format_spiral_abyss(abyss), attachment


@bp.on.message(CommandRule(['линк'], ['~~п'], man.AccountLink))
async def link_genshin_account(message: Message) -> None:
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


@bp.on.message(CommandRule(['анлинк'], ['~~п'], man.AccountUnlink))
async def unlink_genshin_account(message: Message) -> None:
    async with AccountUnlinkValidator(message) as validator:
        await validator.check_account_linked(message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"DELETE FROM genshin_accounts WHERE user_id = {message.from_id};")
        await message.answer('Ваш игровой аккаунт был успешно отвязан!')


@bp.on.message(CommandRule(['заметки'], ['~~п', '~~у'], man.Notes))
async def get_notes(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message, 'Notes') as validator:
        match options:
            case ['~~у']:
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await Notes(account).get())
            case ['~~[default]']:
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                await message.answer(await Notes(account).get())
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['статы'], ['~~п', '~~у'], man.Stats))
async def get_stats(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message, 'Stats') as validator:
        match options:
            case ['~~у']:
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await Stats(account).get())
            case ['~~[default]']:
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                await message.answer(await Stats(account).get())
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['награды'], ['~~п'], man.Rewards))
async def get_rewards(message: Message) -> None:
    async with HoYoLABValidator(message, 'Rewards') as validator:
        account = await get_genshin_account_by_id(message.from_id, False, True, True)
        validator.check_account_exist(account)
        rewards = await Rewards(account).get()
        if isinstance(rewards, tuple):
            rewards, attachment = rewards
        else:
            attachment = None
        await message.answer(rewards, attachment)


@bp.on.message(CommandRule(['пром'], ['~~п'], man.RedeemCode))
async def redeem_code(message: Message) -> None:
    async with CodeValidator(message, 'Redeem') as validator:
        account = await get_genshin_account_by_id(message.from_id, True, True, True, True)
        validator.check_account_exist(account)
        codes = message.text.lstrip('!пром').strip().split()
        validator.check_code_specified(codes)
        await message.answer(await Codes(account, codes).redeem())


@bp.on.message(CommandRule(['резинноут'], ['~~п', '~~выкл', '~~вкл', '~~мин'], man.ResinNotifications))
async def manage_resin_notifications(message: Message, options: Options) -> None:
    async with ResinNotifyValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        await validator.check_account_linked(message.from_id)
        notifications = ResinNotifications(message)
        match options:
            case ['~~[default]']:
                await message.answer(await notifications.get_status())
            case ['~~выкл']:
                await validator.check_notifications_enabled(message.from_id, message.peer_id)
                await notifications.turn_off()
                await message.answer('Автоматическое напоминание потратить смолу теперь выключено!')
            case ['~~вкл']:
                await validator.check_notifications_disabled(message.from_id, message.peer_id)
                await notifications.turn_on()
                await message.answer('Автоматическое напоминание потратить смолу теперь включено!')
            case ['~~мин']:
                value = message.text[message.text.find('~~мин') + 5:].strip()
                validator.check_value_valid(value)
                value = int(value)
                validator.check_value_range(value)
                await notifications.set_notification_minimum(value)
                await message.answer('Успешно установлено новое минимально необходимое для упоминаний значение смолы!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['дневник'], ['~~п', '~~у'], man.Diary))
async def get_traveler_diary(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message, 'Diary') as validator:
        match options:
            case ['~~у']:
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, False, True, True)
                validator.check_account_exist(account, True)
                await message.answer(await Diary(account).get())
            case ['~~[default]']:
                account = await get_genshin_account_by_id(message.from_id, False, True, True)
                validator.check_account_exist(account)
                await message.answer(await Diary(account).get())
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['бездна'], ['~~п', '~~у'], man.SpiralAbyss))
async def get_spiral_abyss(message: Message, options: Options) -> None:
    async with SpiralAbyssValidator(message, 'SpiralAbyss') as validator:
        match options:
            case ['~~у']:
                validator.check_reply_message(message.reply_message)
                account = await get_genshin_account_by_id(message.reply_message.from_id, True, True, True)
                validator.check_account_exist(account, True)
                abyss = await SpiralAbyss(account, validator).get()
                if isinstance(abyss, tuple):
                    abyss, attachment = abyss
                else:
                    attachment = None
                await message.answer(abyss, attachment)
            case ['~~[default]']:
                account = await get_genshin_account_by_id(message.from_id, True, True, True)
                validator.check_account_exist(account)
                abyss = await SpiralAbyss(account, validator).get()
                if isinstance(abyss, tuple):
                    abyss, attachment = abyss
                else:
                    attachment = None
                await message.answer(abyss, attachment)
            case _:
                raise IncompatibleOptions(options)
