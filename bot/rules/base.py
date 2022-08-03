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
                    if not len(self.options) > 1:
                        return True
                    return {'options': ['~~[default]']}
                case _ if incorrect_options:
                    await event.answer(
                        self.manual.with_incorrect_options(incorrect_options)
                    )
                case _ if not incorrect_options:
                    return {'options': options}
        return False


class AdminRule(ABCRule[Message]):
    DENY_MSG = 'У вас недостаточно прав для использования данной команды!'

    def __init__(
            self,
            command: str,
            admins: list[int],
            prefix: str = '!',
    ) -> None:
        self.command = command
        self.admins = admins
        self.prefix = prefix

    async def check(self, event: Message) -> bool:
        if not event.text.lower().startswith(self.prefix + self.command):
            return False
        if event.from_id not in self.admins:
            await event.answer(self.DENY_MSG)
            return False
        return True


class CustomCommandRule(ABCRule[Message]):
    def __init__(self, prefix: str = '!!') -> None:
        self.prefix = prefix

    async def check(self, event: Message) -> bool | dict[str, CustomCommand]:
        if not event.text.startswith(self.prefix):
            return False
        cmds = await get_custom_commands(event.peer_id)
        if not cmds:
            return False
        request_cmd = event.text.partition(' ')[0].lstrip(self.prefix)
        if request_cmd not in [cmd.name for cmd in cmds]:
            return False
        return {'command': [cmd for cmd in cmds if cmd.name == request_cmd][0]}


class EventRule(ABCRule[MessageEvent]):
    def __init__(self, payload_type: list[str]) -> None:
        self.payload_types = payload_type

    async def check(self, event: MessageEvent) -> dict[str, dict] | bool:
        if event.payload['type'] not in self.payload_types:
            return False
        if not event.payload['user_id'] == event.user_id:
            return False
        return {'payload': event.payload}
