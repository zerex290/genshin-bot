import os
from datetime import datetime

from vkbottle.bot import Blueprint, Message

from . import Options
from bot.rules import CommandRule
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.utils.files import upload
from bot.src.manuals import genshin as man
from bot.config.dependencies.paths import DAILY_MATERIALS, BOSS_MATERIALS, BOOKS


bp = Blueprint('GenshinCommands')


@bp.on.message(
    CommandRule(['фарм'], ['~~п', '~~пн', '~~вт', '~~ср', '~~чт', '~~пт', '~~сб', '~~вс'], man.DailyMaterials)
)
async def get_daily_materials(message: Message, options: Options) -> None:
    async with BaseValidator(message):
        match options:
            case _ if '~~п' not in options:
                attachments = []
                days = {'~~пн': 0, '~~вт': 1, '~~ср': 2, '~~чт': 3, '~~пт': 4, '~~сб': 5, '~~вс': 6}
                for opt in options:
                    attachment = f"{days.get(opt, datetime.now().weekday())}.png"
                    attachments.append(
                        await upload(bp.api, 'photo_messages', os.path.join(DAILY_MATERIALS, attachment))
                    )
                await message.answer(attachment=','.join(attachments))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['таланты'], ['~~п'], man.BossMaterials))
async def get_boss_materials(message: Message) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOSS_MATERIALS))


@bp.on.message(CommandRule(['книги'], ['~~п'], man.Books))
async def get_books(message: Message) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOOKS))
