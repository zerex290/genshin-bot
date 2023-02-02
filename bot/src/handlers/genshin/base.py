import os
from datetime import datetime

from vkbottle.bot import BotLabeler, Message

from bot.src import Options
from bot.src.config import bot
from bot.src.rules import CommandRule
from bot.src.errors import IncompatibleOptions
from bot.src.validators import BaseValidator
from bot.src.utils.files import upload
from bot.src.manuals import genshin as man
from bot.src.parsers.honeyimpact import DailyFarmParser, TalentBookParser, BossMaterialParser
from bot.src.imageprocessing.genshin.base import *


bl = BotLabeler()


@bl.message(CommandRule(['фарм'], ['~~п', '~~пн', '~~вт', '~~ср', '~~чт', '~~пт', '~~сб', '~~вс'], man.DailyMaterials))
async def get_dailyfarm(message: Message, options: Options) -> None:
    async with BaseValidator(message):
        match options:
            case _ if '~~п' not in options:
                attachments = []
                weekdays = {'~~пн': 0, '~~вт': 1, '~~ср': 2, '~~чт': 3, '~~пт': 4, '~~сб': 5, '~~вс': 6}
                weekdays = [weekdays.get(opt, datetime.now().weekday()) for opt in options]
                materials = await DailyFarmImageGenerator(weekdays, await DailyFarmParser.get_zones()).generate()
                for material in materials:
                    attachments.append(await upload(bot.group.api, 'photo_messages', material))
                    os.remove(material)
                await message.answer(attachment=','.join(attachments))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


@bl.message(CommandRule(['таланты'], ['~~п'], man.BossMaterials))
async def get_boss_materials(message: Message, **_) -> None:
    boss_materials = await BossMaterialImageGenerator(BossMaterialParser.get_related_bosses()).generate()
    attachment = await upload(bot.group.api, 'photo_messages', boss_materials)
    os.remove(boss_materials)
    await message.answer(attachment=attachment)


@bl.message(CommandRule(['книги'], ['~~п'], man.Books))
async def get_talent_books(message: Message, **_) -> None:
    talent_books = await TalentBookImageGenerator(await TalentBookParser.get_related_talent_books()).generate()
    attachment = await upload(bot.group.api, 'photo_messages', talent_books)
    os.remove(talent_books)
    await message.answer(attachment=attachment)
