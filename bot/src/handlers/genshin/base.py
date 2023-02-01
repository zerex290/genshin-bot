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
                materials = await DailyFarmImageGenerator(weekdays).generate()
                for material_path in materials:
                    attachments.append(await upload(bot.group.api, 'photo_messages', material_path))
                    os.remove(material_path)
                await message.answer(attachment=','.join(attachments))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


@bl.message(CommandRule(['таланты'], ['~~п'], man.BossMaterials))
async def get_boss_materials(message: Message, **_) -> None:
    materials_path = await BossMaterialImageGenerator().generate()
    attachment = await upload(bot.group.api, 'photo_messages', materials_path)
    os.remove(materials_path)
    await message.answer(attachment=attachment)


@bl.message(CommandRule(['книги'], ['~~п'], man.Books))
async def get_talent_books(message: Message, **_) -> None:
    books_path = await TalentBookImageGenerator().generate()
    attachment = await upload(bot.group.api, 'photo_messages', books_path)
    os.remove(books_path)
    await message.answer(attachment=attachment)
