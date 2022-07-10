import os
import re
import datetime
from typing import Optional

from vkbottle.bot import Blueprint, Message
from vkbottle_types.objects import MessagesMessageAttachment

from bot.utils import PostgresConnection
from bot.rules import CommandRule, CustomCommandRule
from bot.utils import get_custom_commands, get_current_timestamp
from bot.errors import IncompatibleOptions
from bot.utils.files import download, upload
from bot.utils.postgres import has_postgres_data
from bot.src.manuals import customcommands as man
from bot.config.dependencies.paths import FILECACHE
from bot.src.models.customcommands import CustomCommand
from bot.validators.customcommands import *


bp = Blueprint('UserCommands')


@bp.on.message(CommandRule(['комы'], ['~~п', '~~с', '~~общ', '~~огр'], man.CommandList))
async def view_custom_commands(message: Message, options: list[str]) -> None:
    async with ViewValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        match options:
            case ['~~[default]']:
                commands: list[CustomCommand] = await get_custom_commands(message.peer_id)
                validator.check_commands_created(commands)
                await message.answer(
                    'Список пользовательских команд:\n' + '\n'.join(command.name for command in commands)
                )
            case ['~~с']:
                status = await has_postgres_data(
                        f"SELECT * FROM chats WHERE ffa_commands = true AND chat_id = {message.peer_id};"
                )
                await message.answer(
                    f"В чате манипуляции с пользовательскими командами "
                    f"являются {'общедоступными' if status else 'ограниченными'}!"
                )
            case ['~~общ']:
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_actions_not_public(message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(f"UPDATE chats SET ffa_commands = true WHERE chat_id = {message.peer_id};")
                await message.answer('Манипуляции с пользовательскими командами теперь являются общедоступными!')
            case ['~~огр']:
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_actions_not_restricted(message.peer_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE chats SET ffa_commands = false WHERE chat_id = {message.peer_id};"
                    )
                await message.answer('Манипуляции с пользовательскими командами теперь являются ограниченными!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.chat_message(CustomCommandRule())
async def get_custom_command(message: Message, command: CustomCommand) -> None:
    attachments: list[str] = []
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


@bp.on.message(CommandRule(['делком'], ['~~п'], man.CommandDeletion))
async def delete_custom_command(message: Message) -> None:
    async with DeletionValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        await validator.check_availability(message.peer_id, message.from_id)
        name = re.sub(r'^!делком\s?', '', message.text)
        validator.check_command_specified(name)
        await validator.check_command_exist(name, message.peer_id)
        async with PostgresConnection() as connection:
            await connection.execute(
                f"DELETE FROM custom_commands WHERE name = '{name}' AND chat_id = {message.peer_id};"
            )
        await message.answer(f"Команда '{name}' была успешно удалена!")


async def _get_document_id(
        command_name: str,
        peer_id: int,
        attachments: Optional[list[MessagesMessageAttachment]]
) -> str:
    document_ids: list[str] = []
    for attachment in attachments:
        document = attachment.doc
        if not document:
            continue
        title = f"{command_name}.{document.ext}"
        document = await download(document.url, FILECACHE, f"{command_name}_{peer_id}", document.ext)
        document_id = await upload(bp.api, 'document_messages', title, document, peer_id=peer_id)
        os.remove(document)
        document_ids.append(document_id)
    return ','.join(document_ids)


async def _get_audio_id(attachments: Optional[list[MessagesMessageAttachment]]) -> str:
    audio_ids: list[str] = []
    for attachment in attachments:
        if not attachment.audio:
            continue
        audio_ids.append(f"audio{attachment.audio.owner_id}_{attachment.audio.id}")
    return ','.join(audio_ids)


async def _get_photo_id(command_name: str, peer_id: int, attachments: Optional[list[MessagesMessageAttachment]]) -> str:
    photo_ids: list[str] = []
    for attachment in attachments:
        if not attachment.photo:
            continue
        urls = {size.height * size.width: size.url for size in attachment.photo.sizes}
        photo = await download(urls[max(urls)], FILECACHE, f"{command_name}_{peer_id}", 'jpg')
        photo_id = await upload(bp.api, 'photo_messages', photo)
        os.remove(photo)
        photo_ids.append(photo_id.rsplit('_', maxsplit=1)[0])
    return ','.join(photo_ids)


async def _insert_into_database(
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


@bp.on.message(CommandRule(['аддком'], ['~~п'], man.CommandCreation))
async def add_custom_command(message: Message) -> None:
    async with CreationValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        await validator.check_availability(message.peer_id, message.from_id)
        text = re.sub(r'^!аддком\s?', '', message.text).split(maxsplit=1)
        name = text[0] if text else ''
        validator.check_command_specified(name)
        await validator.check_command_new(name, message.peer_id)
        validator.check_command_not_reserved(name)
        creator_id = message.from_id
        date_added = get_current_timestamp(3)
        times_used = 0
        msg = text[1] if len(text) > 1 else ''
        document_id = await _get_document_id(name, message.peer_id, message.attachments)
        audio_id = await _get_audio_id(message.attachments)
        photo_id = await _get_photo_id(name, message.peer_id, message.attachments)
        validator.check_additions_specified([msg, document_id, audio_id, photo_id])
        await _insert_into_database(
            name, message.peer_id, creator_id, date_added, times_used, msg, document_id, audio_id, photo_id
        )
        await message.answer(f"Команда '{name}' была успешно добавлена!")
