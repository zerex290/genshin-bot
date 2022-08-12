import traceback
from os import sep
from datetime import datetime
from typing import Optional, Literal, TypeAlias
from json.decoder import JSONDecodeError

import aiohttp
import aiofiles

from vkbottle import API, VKAPIError
from vkbottle import PhotoMessageUploader, DocMessagesUploader, PhotoWallUploader, DocWallUploader, VideoUploader

from ..utils import catch_aiohttp_errors
from ..config.dependencies.paths import LOGS


UploaderType: TypeAlias = Literal['photo_messages', 'document_messages', 'photo_wall', 'document_wall', 'video']


@catch_aiohttp_errors
async def download(url: str, download_path: str, filename: str, suffix: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.ok:
                async with aiofiles.open(download_path + sep + filename + '.' + suffix, 'wb') as file:
                    async for chunk in response.content.iter_chunked(1024):
                        await file.write(chunk) if chunk else await file.write(b'')
                return download_path + sep + filename + '.' + suffix


async def upload(
        api: API,
        uploader_type: UploaderType,
        *args,
        **kwargs
) -> Optional[str]:
    uploader_types = {
        'photo_messages': PhotoMessageUploader(api).upload,
        'document_messages': DocMessagesUploader(api).upload,
        'photo_wall': PhotoWallUploader(api).upload,
        'document_wall': DocWallUploader(api).upload,
        'video': VideoUploader(api).upload
    }
    attachment = None
    while attachment is None:
        try:
            attachment = await uploader_types[uploader_type](*args, **kwargs)
        except JSONDecodeError:
            continue
        except VKAPIError[100]:  #: Uploader errors
            break
    return attachment


async def write_logs(error: Exception) -> None:
    dt = datetime.now()
    async with aiofiles.open(f"{LOGS}{sep}{dt.strftime('%B %Y')}.txt", 'a', encoding='utf-8') as log:
        exc_type = error.__class__.__name__
        await log.write(f"{dt.strftime('%d %B %Y - %H:%M:%S')}: {exc_type}\n{traceback.format_exc()}\n{'-'*79}\n\n")
