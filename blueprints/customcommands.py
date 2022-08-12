import os
import re
import datetime

from vkbottle.bot import Blueprint, Message

from . import Options
from bot.utils import PostgresConnection
from bot.rules import CommandRule, CustomCommandRule
from bot.utils import get_custom_commands, get_current_timestamp
from bot.errors import IncompatibleOptions
from bot.utils.files import download, upload
from bot.utils.postgres import has_postgres_data
from bot.manuals import customcommands as man
from bot.config.dependencies.paths import FILECACHE
from bot.models.customcommands import CustomCommand
from bot.validators.customcommands import *


bp = Blueprint('UserCommands')


class CommandList:
    def __init__(self, chat_id: int) -> None:
        self.chat_id = chat_id

    async def get(self) -> str:
        cmds = await get_custom_commands(self.chat_id)
        if not cmds:
            return 'В данном чате еще не создано ни одной команды!'
        else:
            return 'Список пользовательских команд:\n' + '\n'.join(cmd.name for cmd in cmds)

    async def get_status(self) -> str:
        status = await has_postgres_data(
            f"SELECT * FROM chats WHERE ffa_commands = true AND chat_id = {self.chat_id};"
        )
        return (
            f"В чате манипуляции с пользовательскими командами "
            f"являются {'общедоступными' if status else 'ограниченными'}!"
        )

    async def make_public(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"UPDATE chats SET ffa_commands = true WHERE chat_id = {self.chat_id};")

    async def make_restricted(self) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"UPDATE chats SET ffa_commands = false WHERE chat_id = {self.chat_id};")


class CommandCreation:
    def __init__(self, message: Message, validator: CreationValidator) -> None:
        self.message = message
        self.validator = validator

    async def _get_document_id(self, cmd_name: str) -> str:
        document_ids = []
        for a in self.message.attachments:
            document = a.doc
            if not document:
                continue
            title = f"{cmd_name}.{document.ext}"
            document = await download(document.url, FILECACHE, f"{cmd_name}{self.message.peer_id}", document.ext)
            document_id = await upload(bp.api, 'document_messages', title, document, peer_id=self.message.peer_id)
            os.remove(document)
            if document_id is not None:
                document_ids.append(document_id)
        return ','.join(document_ids)

    async def _get_audio_id(self) -> str:
        audio_ids = []
        for attachment in self.message.attachments:
            if not attachment.audio:
                continue
            audio_ids.append(f"audio{attachment.audio.owner_id}_{attachment.audio.id}")
        return ','.join(audio_ids)

    async def _get_photo_id(self, cmd_name: str) -> str:
        photo_ids = []
        for attachment in self.message.attachments:
            if not attachment.photo:
                continue
            urls = {size.height * size.width: size.url for size in attachment.photo.sizes}
            photo = await download(urls[max(urls)], FILECACHE, f"{cmd_name}_{self.message.peer_id}", 'jpg')
            photo_id = await upload(bp.api, 'photo_messages', photo)
            os.remove(photo)
            if photo_id is not None:
                photo_ids.append(photo_id.rsplit('_', maxsplit=1)[0])
        return ','.join(photo_ids)

    async def _add_to_database(
            self, cmd_name: str, date_added: datetime.datetime,
            msg: str, doc_id: str, audio_id: str, photo_id: str
    ) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO custom_commands VALUES (
                    '{cmd_name}', {self.message.peer_id}, {self.message.from_id}, '{date_added}', 
                    0, '{msg}', '{doc_id}', '{audio_id}', '{photo_id}'
                );
            """)

    async def create(self) -> str:
        self.validator.check_chat_allowed(self.message.peer_id)
        await self.validator.check_availability(self.message.peer_id, self.message.from_id)
        text = re.sub(r'^!аддком\s?', '', self.message.text).split(maxsplit=1)
        cmd_name = text[0] if text else ''
        self.validator.check_command_specified(cmd_name)
        await self.validator.check_command_new(cmd_name, self.message.peer_id)
        self.validator.check_command_not_reserved(cmd_name)
        date_added = get_current_timestamp(3)
        msg = text[1] if len(text) > 1 else ''
        doc_id = await self._get_document_id(cmd_name)
        audio_id = await self._get_audio_id()
        photo_id = await self._get_photo_id(cmd_name)
        self.validator.check_additions_specified([msg, doc_id, audio_id, photo_id])
        await self._add_to_database(cmd_name, date_added, msg, doc_id, audio_id, photo_id)
        return cmd_name


@bp.on.message(CommandRule(['комы'], ['~~п', '~~с', '~~общ', '~~огр'], man.CommandList))
async def view_custom_commands(message: Message, options: Options) -> None:
    async with ViewValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        commands = CommandList(message.peer_id)
        match options:
            case ['~~[default]']:
                await message.answer(await commands.get())
            case ['~~с']:
                await message.answer(await commands.get_status())
            case ['~~общ']:
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_actions_restricted(message.peer_id)
                await commands.make_public()
                await message.answer('Манипуляции с пользовательскими командами теперь являются общедоступными!')
            case ['~~огр']:
                await validator.check_privileges(message.ctx_api, message.peer_id, message.from_id)
                await validator.check_actions_public(message.peer_id)
                await commands.make_restricted()
                await message.answer('Манипуляции с пользовательскими командами теперь являются ограниченными!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.chat_message(CustomCommandRule())
async def get_custom_command(message: Message, command: CustomCommand) -> None:
    attachments = []
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


@bp.on.message(CommandRule(['аддком'], ['~~п'], man.CommandCreation))
async def add_custom_command(message: Message) -> None:
    async with CreationValidator(message) as validator:
        cmd = await CommandCreation(message, validator).create()
        await message.answer(f"Команда '{cmd}' была успешно добавлена!")
