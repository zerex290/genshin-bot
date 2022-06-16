import re
from typing import Dict, Tuple
from itertools import groupby

from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules import ABCRule

from bot.utils import get_custom_commands
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
            commands: Tuple[str, ...],
            prefix: str = '!',
            options: Tuple[str, ...] = tuple(),
    ) -> None:
        self.commands = commands
        self.prefix = prefix
        self.options = options

    async def check(self, event: Message) -> bool | Dict[str, Tuple[str, ...]]:
        for command in self.commands:
            if not event.text.lower().startswith(self.prefix + command):
                continue
            if event.text.lower() == self.prefix + command:
                return {'options': ('-[default]',)}
            options = tuple([option.lstrip() for option in re.findall(r'\s-\S+', event.text)])
            if options:
                filtered_options = set(options)
                if not filtered_options.issubset(self.options):
                    return {'options': ('-[error]',)}
                elif filtered_options.issubset(self.options):
                    return {'options': tuple([opt for opt, _ in groupby(options)])}
            elif not options:
                return {'options': ('-[default]',)}
        return False


class AdminRule(ABCRule[Message]):
    def __init__(
            self,
            commands: Tuple[str, ...] = ('exec', 'execpg'),
            prefix: str = '!',
            admins: Tuple[int, ...] = ()
    ) -> None:
        self.commands = commands
        self.prefix = prefix
        self.admins = admins

    async def check(self, event: Message) -> bool | Dict[str, bool]:
        if not any([event.text.lower().startswith(self.prefix + command) for command in self.commands]):
            return False
        if event.from_id not in self.admins:
            await event.answer('У вас недостаточно прав для использования данной команды!')
            return False
        return {'postgres': True if event.text.lower().startswith(f"{self.prefix}execpg") else False}


class CustomCommandRule(ABCRule[Message]):
    def __init__(self, prefix: str = '!!') -> None:
        self.prefix = prefix

    async def check(self, event: Message) -> bool | Dict[str, CustomCommand]:
        if not event.text.startswith(self.prefix):
            return False
        custom_commands: list[CustomCommand] = await get_custom_commands(event.peer_id)
        if not custom_commands:
            return False
        requested_command = event.text.partition(' ')[0].lstrip(self.prefix)
        if requested_command not in custom_commands:
            return False
        return {'command': [command for command in custom_commands if command.name == requested_command][0]}


class EventRule(ABCRule[MessageEvent]):
    def __init__(self, payload_type: Tuple[str, ...]) -> None:
        self.payload_types = payload_type

    async def check(self, event: MessageEvent) -> Dict[str, dict] | bool:
        if event.payload['type'] not in self.payload_types:
            return False
        if not event.payload['user_id'] == event.user_id:
            return False
        return {'payload': event.payload}
