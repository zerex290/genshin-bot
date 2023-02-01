import datetime
import os
import re

from vkbottle.bot import BotLabeler, Message

from .. import Options
from ..utils import PostgresConnection, get_custom_commands, get_current_timestamp
from ..utils.files import download, upload
from ..utils.postgres import has_postgres_data
from ..rules import CommandRule, CustomCommandRule
from ..errors import IncompatibleOptions
from ..manuals import customcommands as man
from ..templates import customcommands as tpl
from ..models import customcommands as mdl
from ..validators.customcommands import *


bl = BotLabeler()


class CommandMixin:
    message: Message

    async def get_document_id(self, cmd_name: str) -> str:
        doc_ids = []
        for a in self.message.attachments:
            doc = a.doc
            if not doc:
                continue
            title = f"{cmd_name}.{doc.ext}"
            doc = await download(doc.url, name=doc.title, ext=doc.ext)
            doc_id = await upload(self.message.ctx_api, 'document_messages', title, doc, peer_id=self.message.peer_id)
            os.remove(doc)
            if doc_id is not None:
                doc_ids.append(doc_id)
        return ','.join(doc_ids)

    async def get_audio_id(self) -> str:
        audio_ids = []
        for attachment in self.message.attachments:
            if not attachment.audio:
                continue
            audio_ids.append(f"audio{attachment.audio.owner_id}_{attachment.audio.id}")
        return ','.join(audio_ids)

    async def get_photo_id(self, cmd_name: str) -> str:
        photo_ids = []
        for attachment in self.message.attachments:
            if not attachment.photo:
                continue
            urls = {size.height * size.width: size.url for size in attachment.photo.sizes}
            photo = await download(urls[max(urls)], name=f"{cmd_name}_{self.message.peer_id}", ext='jpg')
            photo_id = await upload(self.message.ctx_api, 'photo_messages', photo)
            os.remove(photo)
            if photo_id is not None:
                photo_ids.append(photo_id.rsplit('_', maxsplit=1)[0])
        return ','.join(photo_ids)


class CommandList:
    def __init__(self, chat_id: int) -> None:
        self.chat_id = chat_id

    async def get(self) -> str:
        cmds = await get_custom_commands(self.chat_id)
        if not cmds:
            return 'В данном чате еще не создано ни одной команды!'
        else:
            return 'Список пользовательских команд:\n' + '\n'.join(f"!!{cmd.name}" for cmd in cmds)

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


class Command(CommandMixin):
    def __init__(self, message: Message, command: mdl.CustomCommand, validator: CommandValidator):
        self.message = message
        self.command = command
        self.validator = validator

    async def get(self) -> None:
        attachments = []
        if self.command.document_id:
            attachments.append(self.command.document_id)
        if self.command.audio_id:
            attachments.append(self.command.audio_id)
        if self.command.photo_id:
            attachments.append(self.command.photo_id)
        await self.message.answer(self.command.message, ','.join(attachments))
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE custom_commands SET times_used = times_used + 1 
                WHERE chat_id = {self.command.chat_id} AND name = $1;
            """, self.command.name)

    async def get_information(self) -> None:
        users = await self.message.ctx_api.users.get(
            [self.command.creator_id, self.command.editor_id], fields=['domain']
        )
        if len(users) == 1 and self.command.creator_id == self.command.editor_id:
            creator, editor = (users[0], users[0])
        elif len(users) == 2:
            creator, editor = users
        else:
            creator, editor = (users[0], None)

        await self.message.answer(tpl.format_information(self.command, creator, editor))

    async def edit(self) -> None:
        await self.validator.check_availability(self.message.ctx_api, self.command.chat_id, self.message.from_id)
        msg = re.sub(fr"^!!{self.command.name}\s?|~~ред", '', self.message.text)
        doc_id = await self.get_document_id(self.command.name)
        audio_id = await self.get_audio_id()
        photo_id = await self.get_photo_id(self.command.name)
        self.validator.check_additions_specified([msg, doc_id, audio_id, photo_id])
        msg = msg or self.command.message
        doc_id = doc_id or self.command.document_id
        audio_id = audio_id or self.command.audio_id
        photo_id = photo_id or self.command.photo_id
        self.validator.check_addition_quantity(doc_id, audio_id, photo_id)
        date_edited = get_current_timestamp(3)
        editor_id = self.message.from_id
        await self._update_database(msg, doc_id, audio_id, photo_id, date_edited, editor_id)

    async def _update_database(
            self, msg: str, doc_id: str, audio_id: str, photo_id: str, date_edited: datetime.datetime, editor_id: int
    ) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE custom_commands 
                SET message = $1, document_id = '{doc_id}', audio_id = '{audio_id}', photo_id = '{photo_id}', 
                    edits_num = edits_num + 1, date_edited = '{date_edited}', editor_id = {editor_id} 
                WHERE name = $2 AND chat_id = {self.command.chat_id};
            """, msg, self.command.name)


class CommandCreation(CommandMixin):
    def __init__(self, message: Message, validator: CreationValidator) -> None:
        self.message = message
        self.validator = validator

    async def create(self) -> str:
        self.validator.check_chat_allowed(self.message.peer_id)
        await self.validator.check_availability(self.message.ctx_api, self.message.peer_id, self.message.from_id)
        text = re.sub(r'^!аддком\s?', '', self.message.text).split(maxsplit=1)
        cmd_name = text[0] if text else ''
        self.validator.check_command_specified(cmd_name)
        await self.validator.check_command_new(cmd_name, self.message.peer_id)
        msg = text[1] if len(text) > 1 else ''
        doc_id = await self.get_document_id(cmd_name)
        audio_id = await self.get_audio_id()
        photo_id = await self.get_photo_id(cmd_name)
        self.validator.check_additions_specified([msg, doc_id, audio_id, photo_id])
        self.validator.check_addition_quantity(doc_id, audio_id, photo_id)
        await self._add_to_database(cmd_name, msg, doc_id, audio_id, photo_id)
        return cmd_name

    async def _add_to_database(self, cmd_name: str, msg: str, doc_id: str, audio_id: str, photo_id: str) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO custom_commands (name, chat_id, creator_id, message, document_id, audio_id, photo_id) 
                VALUES ($1, {self.message.peer_id}, {self.message.from_id}, $2, '{doc_id}', '{audio_id}', '{photo_id}');
            """, cmd_name, msg)


@bl.message(CommandRule(['комы'], ['~~п', '~~с', '~~общ', '~~огр'], man.CommandList))
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


@bl.chat_message(CustomCommandRule(['~~п', '~~инфо', '~~ред'], man.Command))
async def get_custom_command(message: Message, command: mdl.CustomCommand, options: Options) -> None:
    async with CommandValidator(message) as validator:
        custom_command = Command(message, command, validator)
        match options:
            case ['~~[default]']:
                await custom_command.get()
            case ['~~инфо']:
                await custom_command.get_information()
            case ['~~ред']:
                await custom_command.edit()
                await message.answer(f"Успешно отредактирована команда '{command.name}'!")
            case _:
                raise IncompatibleOptions(options)


@bl.message(CommandRule(['делком'], ['~~п'], man.CommandDeletion))
async def delete_custom_command(message: Message, **_) -> None:
    async with DeletionValidator(message) as validator:
        validator.check_chat_allowed(message.peer_id)
        await validator.check_availability(message.ctx_api, message.peer_id, message.from_id)
        name = re.sub(r'^!делком\s?', '', message.text)
        validator.check_command_specified(name)
        await validator.check_command_exist(name, message.peer_id)
        async with PostgresConnection() as connection:
            await connection.execute(
                f"DELETE FROM custom_commands WHERE name = $1 AND chat_id = {message.peer_id};",
                name
            )
        await message.answer(f"Команда '{name}' была успешно удалена!")


@bl.message(CommandRule(['аддком'], ['~~п'], man.CommandCreation))
async def add_custom_command(message: Message, **_) -> None:
    async with CreationValidator(message) as validator:
        cmd = await CommandCreation(message, validator).create()
        await message.answer(f"Команда '{cmd}' была успешно добавлена!")
