import os
import datetime
from typing import Tuple, List, Optional

from vkbottle.bot import Blueprint, Message
from vkbottle_types.objects import MessagesMessageAttachment

from bot.utils import PostgresConnection
from bot.rules import CommandRule, CustomCommandRule
from bot.utils import get_custom_commands, get_current_timestamp
from bot.errors import IncompatibleOptions
from bot.utils.files import download, upload
from bot.utils.postgres import has_postgres_data
from bot.src.types.help import customcommands as hints
from bot.config.dependencies.paths import USER_COMMANDS
from bot.src.models.customcommands import CustomCommand, ChatCustomCommands
from bot.validators.customcommands import *


bp = Blueprint('UserCommands')


@bp.on.chat_message(CommandRule(('комы',), options=('-п', '-с', '-общ', '-огр')))
async def view_custom_commands(message: Message, options: Tuple[str, ...]) -> None:
    async with ViewValidator(message) as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(hints.CommandList.slots.value[options[0]])
            case ('-[default]',):
                custom_commands: ChatCustomCommands = await get_custom_commands(message.peer_id)
                validator.check_created(custom_commands)
                await message.answer(
                    'Список пользовательских команд:\n' + '\n'.join(command.name for command in custom_commands)
                )
            case ('-с',):
                if not await has_postgres_data(
                        f"SELECT * FROM chats WHERE ffa_commands = true AND chat_id = {message.peer_id};"
                ):
                    await message.answer('В чате манипуляции с пользовательскими командами являются ограниченными!')
                else:
                    await message.answer('В чате манипуляции с пользовательскими командами являются общедоступными!')
            case ('-общ', '-огр') | ('-огр', '-общ'):
                raise IncompatibleOptions(options)
            case ('-общ',):
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_not_public(message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(f"UPDATE chats SET ffa_commands = true WHERE chat_id = {message.peer_id};")
                await message.answer('Манипуляции с пользовательскими командами теперь являются общедоступными!')
            case ('-огр',):
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_not_restricted(message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE chats SET ffa_commands = false WHERE chat_id = {message.peer_id};"
                    )
                await message.answer('Манипуляции с пользовательскими командами теперь являются ограниченными!')


@bp.on.chat_message(CustomCommandRule())
async def send_custom_command(message: Message, command: CustomCommand) -> None:
    attachments: List[str] = []
    if command.document_id:
        attachments.append(command.document_id)
    if command.audio_id:
        attachments.append(command.audio_id)
    if command.photo_id:
        attachments.append(command.photo_id)
    await message.answer(command.message, ','.join(attachments))
    async with PostgresConnection() as connection:
        await connection.execute(f"""
        UPDATE custom_commands SET times_used = times_used + 1 
        WHERE chat_id = {message.peer_id} AND name = '{command.name}';
        """)


@bp.on.chat_message(CommandRule(('делком',), options=('-п',)))
async def delete_custom_command(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.CommandDeletion.slots.value:
        await message.answer(hints.CommandDeletion.slots.value[options[0]])
        return None

    name = message.text.lstrip('!делком').strip()
    async with DeletionValidator(message) as validator:
        await validator.check_availability(message.peer_id, message.from_id)
        validator.check_command_specified(name)
        await validator.check_command_exists(name, message.peer_id)
        async with PostgresConnection() as connection:
            await connection.execute(
                f"DELETE FROM custom_commands WHERE name = '{name}' AND chat_id = {message.peer_id};"
            )
        for file in os.listdir(f"{USER_COMMANDS}{os.sep}{message.peer_id}{os.sep}"):
            if file.startswith(f"{name}.jpg"):
                os.remove(f"{USER_COMMANDS}{os.sep}{message.peer_id}{os.sep}{name}.jpg")
        await message.answer(f"Команда '{name}' была успешно удалена!")


async def _get_document_id(command_name: str, peer_id: int, attachments: Optional[MessagesMessageAttachment]) -> str:
    for attachment in attachments:
        document = attachment.doc
        if not document:
            continue
        title = f"{command_name}.{document.ext}"
        path = await download(document.url, f"{USER_COMMANDS}{os.sep}{peer_id}{os.sep}", command_name, document.ext)
        document_id = await upload(bp.api, 'document_messages', title, path, peer_id=peer_id)
        os.remove(path)
        return document_id
    return ''


async def _get_audio_id(attachments: Optional[MessagesMessageAttachment]) -> str:
    for attachment in attachments:
        if not attachment.audio:
            continue
        return f"audio{attachment.audio.owner_id}_{attachment.audio.id}"
    return ''


async def _get_photo_id(command_name: str, peer_id: int, attachments: Optional[MessagesMessageAttachment]) -> str:
    for attachment in attachments:
        if not attachment.photo:
            continue
        urls = {size.height * size.width: size.url for size in attachment.photo.sizes}
        path = await download(urls[max(urls)], f"{USER_COMMANDS}{os.sep}{peer_id}{os.sep}", command_name, 'jpg')
        photo_id = await upload(bp.api, 'photo_messages', path)
        return '_'.join(photo_id.split('_')[:-1])
    return ''


async def _insert(
        name: str,
        chat_id: int,
        creator_id: int,
        date_added: datetime.datetime,
        times_used: int,
        message: str,
        document_id: str,
        audio_id: str,
        photo_id: str
) -> None:
    async with PostgresConnection() as connection:
        await connection.execute(f"""
            INSERT INTO custom_commands VALUES (
                '{name}', {chat_id}, {creator_id}, '{date_added}', 
                {times_used}, '{message}', '{document_id}', '{audio_id}', '{photo_id}'
            );
        """)


@bp.on.chat_message(CommandRule(('аддком',), options=('-п',)))
async def add_custom_command(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.CommandDeletion.slots.value:
        await message.answer(hints.CommandCreation.slots.value[options[0]])
        return None

    query = message.text.lstrip('!аддком').split()
    async with CreationValidator(message) as validator:
        await validator.check_availability(message.peer_id, message.from_id)
        name = query[0] if query else ''
        validator.check_command_specified(name)
        await validator.check_command_new(name, message.peer_id)
        validator.check_command_not_reserved(name)
        creator_id = message.from_id
        date_added = get_current_timestamp(3)
        times_used = 0
        msg = ' '.join(query[1:]) if len(query) > 1 else ''
        document_id = await _get_document_id(name, message.peer_id, message.attachments)
        audio_id = await _get_audio_id(message.attachments)
        photo_id = await _get_photo_id(name, message.peer_id, message.attachments)
        validator.check_additions_specified([msg, document_id, audio_id, photo_id])
        await _insert(name, message.peer_id, creator_id, date_added, times_used, msg, document_id, audio_id, photo_id)
        await message.answer(f"Команда '{name}' была успешно добавлена!")
