import traceback
from os import sep
from datetime import datetime
from typing import Optional
from asyncio.exceptions import TimeoutError
from json.decoder import JSONDecodeError

import aiohttp
import aiofiles
from aiohttp.client_exceptions import ClientPayloadError

from vkbottle import API
from vkbottle import PhotoMessageUploader, DocMessagesUploader, PhotoWallUploader, DocWallUploader, VideoUploader

from bot.config.dependencies.paths import LOGS


async def download(url: str, download_path: str, filename: str, suffix: str) -> str | bool:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as query:
            if not query.ok:
                return False
            async with aiofiles.open(download_path + sep + filename + '.' + suffix, 'wb') as file:
                try:
                    async for chunk in query.content.iter_chunked(1024):
                        await file.write(chunk) if chunk else await file.write(b'')
                except (ClientPayloadError, TimeoutError):
                    return False
    return download_path + sep + filename + '.' + suffix


async def upload(api: API, uploader_type: str, *args, **kwargs) -> Optional[str]:
    """
    :param api: Bot or User api
    :param uploader_type: Can be "photo_messages", "document_messages", "photo_wall", "document_wall" or "video".
    :param args: Positional arguments for vkbottle uploaders
    :return: Formatted attachment string or None
    """
    uploader_types = {
        'photo_messages': PhotoMessageUploader(api).upload,
        'document_messages': DocMessagesUploader(api).upload,
        'photo_wall': PhotoWallUploader(api).upload,
        'document_wall': DocWallUploader(api).upload,
        'video': VideoUploader(api).upload
    }
    attachment = None
    while not attachment:
        try:
            attachment = await uploader_types[uploader_type](*args, **kwargs)
        except JSONDecodeError:
            continue
    return attachment


async def write_logs(event, handlers, is_error: bool = False, error: Optional[BaseException] = None) -> None:
    dt = datetime.now()
    async with aiofiles.open(f"{LOGS}{sep}{dt.strftime('%B %Y')}.txt", 'a', encoding='utf-8') as log:
        if not is_error:
            await log.write(
                f"{dt.strftime('%d.%m.%y - %H:%M:%S')}: {handlers[0]}\n"
                f"Chat id: {event.peer_id}\n"
                f"User id: {event.from_id}\n"
                f"Message: {event.text}\n"
                f"Attachments ({len(event.attachments)}): {[a.type.value for a in event.attachments]}\n\n"
            )
        else:
            await log.write(
                f"{dt.strftime('%d.%m.%y - %H:%M:%S')}: {error.__class__.__name__}\n"
                f"{traceback.format_exc()}\n\n"
            )
