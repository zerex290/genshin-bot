import re
from typing import Type

from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules import ABCRule

from bot.utils import get_custom_commands
from bot.src.manuals import BaseManual
from bot.src.models.customcommands import CustomCommand


__all__ = (
    'CommandRule',
    'AdminRule',
    'CustomCommandRule',
    'EventRule'
)


class CommandRule(ABCRule[Message]):
    def __init__(
            self,
            commands: list[str],
            options: list[str],
            manual: Type[BaseManual],
            prefix: str = '!'
    ) -> None:
        self.commands = commands
        self.options = options
        self.manual = manual
        self.prefix = prefix

    def _get_options(self, text: str) -> tuple[list[str], list[str]]:
        options = []
        for opt in re.findall(r'\s~~\w+', text):
            opt = opt.lstrip()
            if opt not in options:
                options.append(opt)
        incorrect_options = [opt for opt in options if opt not in self.options]
        return options, incorrect_options

    async def check(self, event: Message) -> bool | dict[str, list[str]]:
        for command in self.commands:
            if not event.text.lower().startswith(self.prefix + command):
                continue
            options, incorrect_options = self._get_options(event.text)
            match options:
                case ['~~п']:
                    await event.answer(self.manual.HELP)
                case []:
                    return {'options': ['~~[default]']} if len(self.options) > 1 else True
                case _ if incorrect_options:
                    await event.answer(self.manual.with_incorrect_options(incorrect_options))
                case _ if not incorrect_options:
                    return {'options': options}
        return False


class AdminRule(ABCRule[Message]):
    def __init__(
            self,
            commands: tuple[str, ...] = ('exec', 'execpg'),
            prefix: str = '!',
            admins: tuple[int, ...] = ()
    ) -> None:
        self.commands = commands
        self.prefix = prefix
        self.admins = admins

    async def check(self, event: Message) -> bool | dict[str, bool]:
        if not any([event.text.lower().startswith(self.prefix + command) for command in self.commands]):
            return False
        if event.from_id not in self.admins:
            await event.answer('У вас недостаточно прав для использования данной команды!')
            return False
        return {'postgres': True if event.text.lower().startswith(f"{self.prefix}execpg") else False}


class CustomCommandRule(ABCRule[Message]):
    def __init__(self, prefix: str = '!!') -> None:
        self.prefix = prefix

    async def check(self, event: Message) -> bool | dict[str, CustomCommand]:
        if not event.text.startswith(self.prefix):
            return False
        custom_commands: list[CustomCommand] = await get_custom_commands(event.peer_id)
        if not custom_commands:
            return False
        requested_command = event.text.partition(' ')[0].lstrip(self.prefix)
        if requested_command not in [command.name for command in custom_commands]:
            return False
        return {'command': [command for command in custom_commands if command.name == requested_command][0]}


class EventRule(ABCRule[MessageEvent]):
    def __init__(self, payload_type: tuple[str, ...]) -> None:
        self.payload_types = payload_type

    async def check(self, event: MessageEvent) -> dict[str, dict] | bool:
        if event.payload['type'] not in self.payload_types:
            return False
        if not event.payload['user_id'] == event.user_id:
            return False
        return {'payload': event.payload}
