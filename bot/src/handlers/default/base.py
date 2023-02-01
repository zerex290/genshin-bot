import random
import re
from typing import Optional
from asyncio import sleep

from vkbottle.bot import BotLabeler, Message

from bot.src import Options
from bot.src.rules import CommandRule
from bot.src.utils import PostgresConnection
from bot.src.utils.postgres import has_postgres_data
from bot.src.constants import keyboard, commands, tags as t
from bot.src.errors import IncompatibleOptions
from bot.src.validators import BaseValidator
from bot.src.validators.default import *
from bot.src.manuals import default as man


bl = BotLabeler()


class Autocorrection:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    async def get_status(self) -> str:
        status = await has_postgres_data(
            f"SELECT * FROM users WHERE user_id = {self.user_id} AND autocorrect = true;"
        )
        return f"У вас {'включена' if status else 'выключена'} автокоррекция команд!"

    async def turn_off(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(
                f"UPDATE users SET autocorrect = false WHERE user_id = {self.user_id};"
            )

    async def turn_on(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(
                f"UPDATE users SET autocorrect = true WHERE user_id = {self.user_id};"
            )


class Timer:
    def __init__(self, message: Message, validator: TimerValidator) -> None:
        self.message = message
        self.validator = validator

    async def set(self) -> None:
        text = self.message.text.removeprefix('!таймер')
        self.validator.check_timer_specified(text)
        time, note = (text.split('/')[0], text.split('/')[1]) if text.find('/') != -1 else (text, '')
        countdown = self._evaluate_time(time.lower())
        self.validator.check_timer_syntax(countdown)
        await self.message.answer('Таймер установлен!')
        await sleep(countdown)
        await self.message.answer(await self._compile_message(note))

    @staticmethod
    def _evaluate_time(time: str) -> Optional[int]:
        try:
            time = re.sub('[xч]', '*3600+', re.sub('[vм]', '*60+', re.sub('[cс]', '*1+', time))).strip().rpartition('+')
            countdown = eval(time[0])
        except (SyntaxError, NameError):
            countdown = None
        return countdown

    async def _compile_message(self, note: str) -> str:
        return (
            f"@id{self.message.from_id} ({(await self.message.get_user()).first_name}), время прошло! "
            f"{'Пометка: ' + note if note else ''}"
        )


class RandomTag:
    @staticmethod
    def get_all_tags() -> dict[str, str]:
        all_tags = {}
        all_tags.update(t.GENSHIN_IMPACT)
        all_tags.update(t.ART_STYLE)
        all_tags.update(t.CLOTHING)
        all_tags.update(t.JEWELRY)
        all_tags.update(t.EMOTIONS)
        all_tags.update(t.BODY)
        all_tags.update(t.CREATURES)
        return all_tags

    @staticmethod
    def get_all_tags_by_groups(options: Options) -> dict[str, str]:
        gathered_tags = {}
        tag_groups = {
            '~~г': t.GENSHIN_IMPACT,
            '~~ср': t.ART_STYLE,
            '~~о': t.CLOTHING,
            '~~у': t.JEWELRY,
            '~~э': t.EMOTIONS,
            '~~т': t.BODY,
            '~~с': t.CREATURES
        }
        for option in options:
            tag_group = tag_groups[option]
            for tag in tag_group:
                gathered_tags[tag] = tag_group[tag]
        return gathered_tags

    @staticmethod
    def get_randomized_tags(tags: dict[str, str]) -> str:
        randomized_tags = []
        for _ in range(0, random.randint(1, len(tags) // 2)):
            if not tags:
                continue
            tag = random.choice(tuple(tags))
            randomized_tags.append(tag)
            del tags[tag]
        return ' | '.join(randomized_tags)


@bl.message(CommandRule(['команды'], ['~~п'], man.Guide))
async def get_commands_article(message: Message, **_) -> None:
    msg = [
        'Статья с подробным описанием всех команд: vk.com/@bot_genshin-commands',
        '\nОсновные команды:', '\n'.join(f"!{c}" for c in commands.MAIN),
        '\nКоманды по Геншину:', '\n'.join(f"!{c}" for c in commands.GENSHIN),
        '\nПользовательские команды:', '\n'.join(f"!{c}" for c in commands.CUSTOM), '!!<<триггер>>'
    ]
    await message.answer('\n'.join(msg))


@bl.message(CommandRule(['автокоррект'], ['~~п', '~~выкл', '~~вкл'], man.Autocorrection))
async def manage_syntax_autocorrection(message: Message, options: Options) -> None:
    async with AutocorrectionValidator(message) as validator:
        autocorrection = Autocorrection(message.from_id)
        match options:
            case ['~~[default]']:
                await message.answer(await autocorrection.get_status())
            case ['~~выкл']:
                await validator.check_autocorrection_enabled(message.from_id)
                await autocorrection.turn_off()
                await message.answer('Автокоррекция команд теперь выключена!')
            case ['~~вкл']:
                await validator.check_autocorrection_disabled(message.from_id)
                await autocorrection.turn_on()
                await message.answer('Автокоррекция команд теперь включена!')
            case _:
                raise IncompatibleOptions(options)


@bl.message(CommandRule(['выбери'], ['~~п'], man.Choice))
async def choose(message: Message, **_) -> None:
    async with ChoiceValidator(message) as validator:
        options = re.sub(r'^!выбери\s?', '', message.text).split('/') if message.text.find('/') != -1 else []
        validator.check_options_specified(options)
        validator.check_options_syntax(options)
        await message.answer(random.choice(options))


@bl.message(CommandRule(['конверт'], ['~~п'], man.Converter))
async def convert(message: Message, **_) -> None:
    async with ConvertValidator(message) as validator:
        validator.check_reply_message(message.reply_message)
        validator.check_reply_message_text(message.reply_message.text)
        converted = ''.join(
            keyboard.CYRILLIC.get(s, keyboard.LATIN.get(s, s))
            if ord(s) < 128
            else keyboard.LATIN.get(s, keyboard.CYRILLIC.get(s, s))
            for s in message.reply_message.text
        )
        await message.answer(converted)


@bl.message(CommandRule(['таймер'], ['~~п'], man.Timer))
async def set_timer(message: Message, **_) -> None:
    async with TimerValidator(message) as validator:
        await Timer(message, validator).set()


@bl.message(CommandRule(['перешли'], ['~~п'], man.Attachments))
async def forward_attachments(message: Message, **_) -> None:
    async with AttachmentForwardValidator(message) as validator:
        attachments = message.attachments
        validator.check_attachments(attachments)
        response = [f"photo{a.photo.owner_id}_{a.photo.id}_{a.photo.access_key}" for a in attachments if a.photo]
        validator.check_attachment_response(response)
        await message.answer(attachment=','.join(response))


@bl.message(CommandRule(['рандомтег'], ['~~п', '~~г', '~~ср', '~~о', '~~у', '~~э', '~~т', '~~с'], man.RandomTag))
async def get_random_tags(message: Message, options: Options) -> None:
    async with BaseValidator(message):
        match options:
            case ['~~[default]']:
                await message.answer(RandomTag.get_randomized_tags(RandomTag.get_all_tags()))
            case _ if '~~п' not in options:
                await message.answer(RandomTag.get_randomized_tags(RandomTag.get_all_tags_by_groups(options)))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)
