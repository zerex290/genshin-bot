import asyncio
import os
import re
from typing import Optional, Tuple, Union, List

from vkbottle.bot import BotLabeler, Message
from vkbottle_types.objects import UsersUserFull

import genshin

from bot.src import Options, templates as tpl
from bot.src.config import bot
from bot.src.errors import IncompatibleOptions
from bot.src.rules import CommandRule
from bot.src.utils import PostgresConnection, GenshinClient
from bot.src.utils.files import download, upload
from bot.src.utils.genshin import get_genshin_account_by_id, catch_hoyolab_errors
from bot.src.models.hoyolab import GenshinAccount
from bot.src.imageprocessing.genshin.hoyolab import *
from bot.src.manuals import hoyolab as man
from bot.src.validators.hoyolab import *


bl = BotLabeler()


class HoYoLAB:
    def __init__(self, account: GenshinAccount, user: Optional[UsersUserFull] = None) -> None:
        self.account = account
        self.user = user

    @classmethod
    async def switch_to_short_display(cls, user_id: int):
        async with PostgresConnection() as connection:
            await connection.execute(
                f"UPDATE users SET {cls.__name__.lower()} = 'short' WHERE user_id = {user_id};"
            )

    @classmethod
    async def switch_to_long_display(cls, user_id: int):
        async with PostgresConnection() as connection:
            await connection.execute(
                f"UPDATE users SET {cls.__name__.lower()} = 'long' WHERE user_id = {user_id};"
            )


class Notes(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> Union[Tuple[str, str], str]:
        async with GenshinClient(self.account) as client:
            notes = await client.get_genshin_notes()
            async with PostgresConnection() as connection:
                display = dict(
                    await connection.fetchrow(f"SELECT notes FROM users WHERE user_id = {self.user.id};")
                )['notes']
            info = tpl.hoyolab.format_notes(notes, self.user, display)
            if display == 'short':
                notes_image = await NotesImageGenerator(notes, self.user).generate()
                attachment = await upload(bot.group.api, 'photo_messages', notes_image)
                os.remove(notes_image)
                return info, attachment
            else:
                return info


class Stats(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> Union[Tuple[str, str], str]:
        async with GenshinClient(self.account) as client:
            stats = await client.get_partial_genshin_user(self.account.uid)
            async with PostgresConnection() as connection:
                display = dict(
                    await connection.fetchrow(f"SELECT stats FROM users WHERE user_id = {self.user.id};")
                )['stats']
            info = tpl.hoyolab.format_stats(stats, self.user, display)
            if display == 'short':
                stats_image = await StatsImageGenerator(stats, self.user).generate()
                attachment = await upload(bot.group.api, 'photo_messages', stats_image)
                os.remove(stats_image)
                return info, attachment
            else:
                return info


class Rewards(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> Tuple[str, str]:
        async with GenshinClient(self.account) as client:
            rewards = await client.claimed_rewards()
            async with PostgresConnection() as connection:
                display = dict(
                    await connection.fetchrow(f"SELECT rewards FROM users WHERE user_id = {self.user.id};")
                )['rewards']
            if display == 'short':
                rewards_image = await RewardsImageGenerator(rewards).generate()
            else:
                rewards_image = await download(rewards[0].icon)
            attachment = await upload(bot.group.api, 'photo_messages', rewards_image)
            os.remove(rewards_image)
            return tpl.hoyolab.format_daily_rewards(rewards, self.user, display), attachment


class Codes(HoYoLAB):
    def __init__(self, account: GenshinAccount, user: Optional[UsersUserFull] = None, *, codes: List[str]) -> None:
        super().__init__(account, user)
        self.codes = codes

    @classmethod
    async def switch_to_short_display(cls, user_id: int):
        raise AttributeError('This method is unavailable!')

    @classmethod
    async def switch_to_long_display(cls, user_id: int):
        raise AttributeError('This method is unavailable!')

    async def redeem(self) -> str:
        async with GenshinClient(self.account) as client:
            response = []
            for code in self.codes:
                response.append(await self._redeem(client, code))
                if len(self.codes) > 1:
                    await asyncio.sleep(5)  #: required cooldown time to successfully activate redeem codes
            return '\n'.join(response)

    @staticmethod
    @catch_hoyolab_errors
    async def _redeem(client: genshin.Client, code: str) -> str:
        await client.redeem_code(code)
        return f"Успешно активирован промокод {code}!"


class Diary(HoYoLAB):
    @catch_hoyolab_errors
    async def get(self) -> Union[Tuple[str, str], str]:
        async with GenshinClient(self.account) as client:
            diary = await client.get_diary()
            async with PostgresConnection() as connection:
                display = dict(
                    await connection.fetchrow(f"SELECT diary FROM users WHERE user_id = {self.user.id};")
                )['diary']
            info = tpl.hoyolab.format_traveler_diary(diary, self.user, display)
            if display == 'short':
                diary_image = await DiaryImageGenerator(diary, self.user).generate()
                attachment = await upload(bot.group.api, 'photo_messages', diary_image)
                os.remove(diary_image)
                return info, attachment
            else:
                return info


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
    def __init__(
            self,
            account: GenshinAccount,
            user: Optional[UsersUserFull] = None,
            *,
            validator: SpiralAbyssValidator
    ) -> None:
        super().__init__(account, user)
        self.validator = validator

    @classmethod
    async def switch_to_short_display(cls, user_id: int):
        raise AttributeError('This method is unavailable!')

    @classmethod
    async def switch_to_long_display(cls, user_id: int):
        raise AttributeError('This method is unavailable!')

    @catch_hoyolab_errors
    async def get(self) -> Tuple[str, str]:
        async with GenshinClient(self.account) as client:
            abyss = await client.get_genshin_spiral_abyss(self.account.uid)
            self.validator.check_abyss_unlocked(abyss.unlocked)
            abyss_image = await AbyssImageGenerator(abyss).generate()
            attachment = await upload(bot.group.api, 'photo_messages', abyss_image)
            os.remove(abyss_image)
            return tpl.hoyolab.format_spiral_abyss(abyss), attachment


@bl.message(CommandRule(['линк'], ['~~п'], man.AccountLink))
async def link_genshin_account(message: Message, **_) -> None:
    async with AccountLinkValidator(message) as validator:
        await validator.check_account_new(message.from_id)
        cookies = re.sub('^!линк', '', message.text).strip().split()
        validator.check_cookie_amount(cookies)
        validator.check_cookie_syntax(cookies)
        cookies = {c.lower().split('=')[0]: c.split('=')[1] for c in cookies}
        cookies['uid'] = int(cookies['uid'])
        cookies['ltuid'] = int(cookies['ltuid'])
        account = GenshinAccount(message.from_id, **cookies)
        await validator.check_cookies_valid(account)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO genshin_accounts (user_id, uid, ltuid, ltoken, cookie_token) 
                VALUES ({message.from_id}, $1, $2, $3, $4);
            """, cookies['uid'], cookies['ltuid'], cookies['ltoken'], cookies['cookie_token'])
        await message.answer('Привязка вашего аккаунта прошла успешно!')


@bl.message(CommandRule(['анлинк'], ['~~п'], man.AccountUnlink))
async def unlink_genshin_account(message: Message, **_) -> None:
    async with AccountUnlinkValidator(message) as validator:
        await validator.check_account_linked(message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"DELETE FROM genshin_accounts WHERE user_id = {message.from_id};")
        await message.answer('Ваш игровой аккаунт был успешно отвязан!')


@bl.message(CommandRule(['заметки'], ['~~п', '~~о'], man.Notes))
async def get_notes(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message) as validator:
        if options == ['~~о']:
            d_types = {'текст': 'long', 'пик': 'short'}
            display = message.text[message.text.find('~~о') + 3:].strip().lower()
            display = d_types.get(display, display)
            validator.check_display_type_correct(display)
            if display == 'short':
                await validator.check_display_long(Notes.__name__.lower(), message.from_id)
                await Notes.switch_to_short_display(message.from_id)
            else:
                await validator.check_display_short(Notes.__name__.lower(), message.from_id)
                await Notes.switch_to_long_display(message.from_id)
            await message.answer('Способ отображения пользовательских заметок был успешно изменен!')
        elif options == ['~~[default]']:
            for_other_user = message.reply_message is not None
            msg = message.reply_message or message
            account = await get_genshin_account_by_id(msg.from_id)
            validator.check_account_exist(account, for_other_user)
            user = await msg.get_user(fields='photo_200')
            notes = await Notes(account, user).get()
            if isinstance(notes, tuple):
                notes, attachment = notes
            else:
                attachment = None
            await message.answer(notes, attachment)
        else:
            raise IncompatibleOptions(options)


@bl.message(CommandRule(['статы'], ['~~п', '~~о'], man.Stats))
async def get_stats(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message) as validator:
        if options == ['~~о']:
            d_types = {'текст': 'long', 'пик': 'short'}
            display = message.text[message.text.find('~~о') + 3:].strip().lower()
            display = d_types.get(display, display)
            validator.check_display_type_correct(display)
            if display == 'short':
                await validator.check_display_long(Stats.__name__.lower(), message.from_id)
                await Stats.switch_to_short_display(message.from_id)
            else:
                await validator.check_display_short(Stats.__name__.lower(), message.from_id)
                await Stats.switch_to_long_display(message.from_id)
            await message.answer('Способ отображения пользовательской статистики был успешно изменен!')
        elif options == ['~~[default]']:
            for_other_user = message.reply_message is not None
            msg = message.reply_message or message
            account = await get_genshin_account_by_id(msg.from_id)
            validator.check_account_exist(account, for_other_user)
            user = await msg.get_user(fields='photo_200')
            stats = await Stats(account, user).get()
            if isinstance(stats, tuple):
                stats, attachment = stats
            else:
                attachment = None
            await message.answer(stats, attachment)
        else:
            raise IncompatibleOptions(options)


@bl.message(CommandRule(['награды'], ['~~п', '~~о'], man.Rewards))
async def get_rewards(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message) as validator:
        if options == ['~~о']:
            d_types = {'текст': 'long', 'пик': 'short'}
            display = message.text[message.text.find('~~о') + 3:].strip().lower()
            display = d_types.get(display, display)
            validator.check_display_type_correct(display)
            if display == 'short':
                await validator.check_display_long(Rewards.__name__.lower(), message.from_id)
                await Rewards.switch_to_short_display(message.from_id)
            else:
                await validator.check_display_short(Rewards.__name__.lower(), message.from_id)
                await Rewards.switch_to_long_display(message.from_id)
            await message.answer('Способ отображения пользовательских наград был успешно изменен!')
        elif options == ['~~[default]']:
            for_other_user = message.reply_message is not None
            msg = message.reply_message or message
            account = await get_genshin_account_by_id(msg.from_id)
            validator.check_account_exist(account, for_other_user)
            user = await msg.get_user(fields='photo_200')
            rewards = await Rewards(account, user).get()
            if isinstance(rewards, tuple):
                rewards, attachment = rewards
            else:
                attachment = None
            await message.answer(rewards, attachment)
        else:
            raise IncompatibleOptions(options)


@bl.message(CommandRule(['пром'], ['~~п'], man.Codes))
async def redeem_code(message: Message, **_) -> None:
    async with CodeValidator(message) as validator:
        for_other_user = message.reply_message is not None
        msg = message.reply_message or message
        account = await get_genshin_account_by_id(msg.from_id)
        validator.check_account_exist(account, for_other_user)
        codes = re.sub('^!пром', '', message.text).strip().split()
        validator.check_code_specified(codes)
        await message.answer(await Codes(account, codes=codes).redeem())


@bl.message(CommandRule(['резинноут'], ['~~п', '~~выкл', '~~вкл', '~~мин'], man.ResinNotifications))
async def manage_resin_notifications(message: Message, options: Options) -> None:
    async with ResinNotifyValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        await validator.check_account_linked(message.from_id)
        notifications = ResinNotifications(message)
        if options == ['~~[default]']:
            await message.answer(await notifications.get_status())
        elif options == ['~~выкл']:
            await validator.check_notifications_enabled(message.from_id, message.peer_id)
            await notifications.turn_off()
            await message.answer('Автоматическое напоминание потратить смолу теперь выключено!')
        elif options == ['~~вкл']:
            await validator.check_notifications_disabled(message.from_id, message.peer_id)
            await notifications.turn_on()
            await message.answer('Автоматическое напоминание потратить смолу теперь включено!')
        elif options == ['~~мин']:
            value = message.text[message.text.find('~~мин') + 5:].strip()
            validator.check_value_valid(value)
            value = int(value)
            validator.check_value_range(value)
            await notifications.set_notification_minimum(value)
            await message.answer('Успешно установлено новое минимально необходимое для упоминаний значение смолы!')
        else:
            raise IncompatibleOptions(options)


@bl.message(CommandRule(['дневник'], ['~~п', '~~о'], man.Diary))
async def get_traveler_diary(message: Message, options: Options) -> None:
    async with HoYoLABValidator(message) as validator:
        if options == ['~~о']:
            d_types = {'текст': 'long', 'пик': 'short'}
            display = message.text[message.text.find('~~о') + 3:].strip().lower()
            display = d_types.get(display, display)
            validator.check_display_type_correct(display)
            if display == 'short':
                await validator.check_display_long(Diary.__name__.lower(), message.from_id)
                await Diary.switch_to_short_display(message.from_id)
            else:
                await validator.check_display_short(Diary.__name__.lower(), message.from_id)
                await Diary.switch_to_long_display(message.from_id)
            await message.answer('Способ отображения пользовательского дневника был успешно изменен!')
        elif options == ['~~[default]']:
            for_other_user = message.reply_message is not None
            msg = message.reply_message or message
            account = await get_genshin_account_by_id(msg.from_id)
            validator.check_account_exist(account, for_other_user)
            user = await msg.get_user(fields='photo_200')
            diary = await Diary(account, user).get()
            if isinstance(diary, tuple):
                diary, attachment = diary
            else:
                attachment = None
            await message.answer(diary, attachment)
        else:
            raise IncompatibleOptions(options)


@bl.message(CommandRule(['бездна'], ['~~п'], man.SpiralAbyss))
async def get_spiral_abyss(message: Message, **_) -> None:
    async with SpiralAbyssValidator(message) as validator:
        for_other_user = message.reply_message is not None
        msg = message.reply_message or message
        account = await get_genshin_account_by_id(msg.from_id)
        validator.check_account_exist(account, for_other_user)
        abyss = await SpiralAbyss(account, validator=validator).get()
        if isinstance(abyss, tuple):
            abyss, attachment = abyss
        else:
            attachment = None
        await message.answer(abyss, attachment)
