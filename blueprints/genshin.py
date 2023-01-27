import os
from datetime import datetime

from vkbottle.bot import Blueprint, Message

from . import Options
from bot.rules import CommandRule
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.utils.files import upload
from bot.manuals import genshin as man
from bot.imageprocessing.dailyfarm import get_dailyfarm_images
from bot.config.dependencies.paths import BOSS_MATERIALS, BOOKS


bp = Blueprint('GenshinCommands')


@bp.on.message(
    CommandRule(['фарм'], ['~~п', '~~пн', '~~вт', '~~ср', '~~чт', '~~пт', '~~сб', '~~вс'], man.DailyMaterials)
)
async def get_dailyfarm(message: Message, options: Options) -> None:
    async with BaseValidator(message):
        match options:
            case _ if '~~п' not in options:
                attachments = []
                weekdays = {'~~пн': 0, '~~вт': 1, '~~ср': 2, '~~чт': 3, '~~пт': 4, '~~сб': 5, '~~вс': 6}
                weekdays = [weekdays.get(opt, datetime.now().weekday()) for opt in options]
                materials = await get_dailyfarm_images(weekdays)
                for material_path in materials:
                    attachments.append(await upload(bp.api, 'photo_messages', material_path))
                    os.remove(material_path)
                await message.answer(attachment=','.join(attachments))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['таланты'], ['~~п'], man.BossMaterials))
async def get_boss_materials(message: Message, **_) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOSS_MATERIALS))


@bp.on.message(CommandRule(['книги'], ['~~п'], man.Books))
async def get_books(message: Message, **_) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOOKS))
