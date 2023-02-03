import traceback
import os
from datetime import datetime
from typing import Optional, Literal, TypeAlias
from json.decoder import JSONDecodeError

import aiohttp
import aiofiles

from vkbottle import API, VKAPIError
from vkbottle import PhotoMessageUploader, DocMessagesUploader, PhotoWallUploader, DocWallUploader, VideoUploader

from ..utils import catch_aiohttp_errors
from ..config.genshinbot import error_handler
from ..config.dependencies.paths import FILECACHE, LOGS


UploaderType: TypeAlias = Literal['photo_messages', 'document_messages', 'photo_wall', 'document_wall', 'video']


@catch_aiohttp_errors
async def download(
        url: str,
        directory: str = FILECACHE,
        name: Optional[str] = None,
        ext: Optional[str] = None,
        force: bool = True
) -> Optional[str]:
    """

    :param url: Link to file
    :param directory: Path to directory where file could be saved
    :param name: Optional file name
    :param ext: Optional file extension
    :param force: Re-download file or not if it already exists in given directory
    :return:
    """
    if name is None or ext is None:
        name, ext = url.rsplit('/', maxsplit=1)[1].split('.')
    path = os.path.join(directory, f"{name}.{ext}")
    if not force and os.path.exists(path):
        return path
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.ok:
                async with aiofiles.open(path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(1024):
                        await file.write(chunk) if chunk else await file.write(b'')
                return path


async def upload(
        api: API,
        uploader_type: UploaderType,
        *args,
        **kwargs
) -> Optional[str]:
    uploaders = {
        'photo_messages': PhotoMessageUploader(api).upload,
        'document_messages': DocMessagesUploader(api).upload,
        'photo_wall': PhotoWallUploader(api).upload,
        'document_wall': DocWallUploader(api).upload,
        'video': VideoUploader(api).upload
    }
    attachment = None
    while attachment is None:
        try:
            attachment = await uploaders[uploader_type](*args, **kwargs)
        except JSONDecodeError:
            continue
        except VKAPIError[100]:  #: Uploader errors
            break
    return attachment


@error_handler.register_undefined_error_handler
async def write_logs(error: Exception) -> None:
    dt = datetime.now()
    async with aiofiles.open(f"{LOGS}{os.sep}{dt.strftime('%B %Y')}.txt", 'a', encoding='utf-8') as log:
        exc_type = error.__class__.__name__
        await log.write(f"{dt.strftime('%d %B %Y - %H:%M:%S')}: {exc_type}\n{traceback.format_exc()}\n{'-'*79}\n\n")
