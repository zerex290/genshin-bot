import re
from typing import Union, Tuple, Type, List, Dict

from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules import ABCRule

from .. import Options, Payload
from ..utils import get_custom_commands
from ..manuals import BaseManual
from ..models.customcommands import CustomCommand


__all__ = (
    'CommandRule',
    'AdminRule',
    'CustomCommandRule',
    'EventRule'
)


class RuleMixin:
    options: Options

    def get_options(self, text: str) -> Tuple[List[str], List[str]]:
        options = []
        for opt in re.findall(r'\s~~\w+', text):
            opt = opt.lstrip()
            if opt not in options:
                options.append(opt)
        incorrect_options = [opt for opt in options if opt not in self.options]
        return options, incorrect_options


class CommandRule(ABCRule[Message], RuleMixin):
    def __init__(self, commands: List[str], options: Options, manual: Type[BaseManual], prefix: str = '!') -> None:
        self.commands = commands
        self.options = options
        self.manual = manual
        self.prefix = prefix

    async def check(self, event: Message) ->Union[bool, Dict[str, Options]]:
        for command in self.commands:
            if not event.text.lower().startswith(self.prefix + command):
                continue
            options, incorrect_options = self.get_options(event.text)
            if options == ['~~п']:
                await event.answer(self.manual.HELP)
            elif not options:
                return {'options': ['~~[default]']}
            elif incorrect_options:
                await event.answer(
                    self.manual.with_incorrect_options(incorrect_options)
                )
            elif not incorrect_options:
                return {'options': options}
        return False


class AdminRule(ABCRule[Message]):
    DENY_MSG = 'У вас недостаточно прав для использования данной команды!'

    def __init__(
            self,
            command: str,
            admins: List[int],
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


class CustomCommandRule(ABCRule[Message], RuleMixin):
    def __init__(self, options: Options, manual: Type[BaseManual], prefix: str = '!!') -> None:
        self.options = options
        self.manual = manual
        self.prefix = prefix

    async def check(self, event: Message) -> Union[bool, Dict[str, Union[CustomCommand, Options]]]:
        if not event.text.startswith(self.prefix):
            return False
        cmds = await get_custom_commands(event.peer_id)
        if not cmds:
            return False
        command = re.match(fr"{self.prefix}\S+", event.text)
        if command is None:
            return False
        command = command[0].lstrip(self.prefix)
        if command not in [cmd.name for cmd in cmds]:
            return False
        options, incorrect_options = self.get_options(event.text)
        if options == ['~~п']:
            await event.answer(self.manual.HELP)
        elif not options:
            return {'command': [cmd for cmd in cmds if cmd.name == command][0], 'options': ['~~[default]']}
        elif incorrect_options:
            await event.answer(
                self.manual.with_incorrect_options(incorrect_options)
            )
        elif not incorrect_options:
            return {'command': [cmd for cmd in cmds if cmd.name == command][0], 'options': options}


class EventRule(ABCRule[MessageEvent]):
    def __init__(self, handler: type, payload_types: List[str], is_public: bool = False) -> None:
        self.handler = handler.__name__
        self.payload_types = payload_types
        self.is_public = is_public

    async def check(self, event: MessageEvent) -> Union[Dict[str, Payload], bool]:
        if event.payload['handler'] != self.handler:
            return False
        if event.payload['type'] not in self.payload_types:
            return False
        if not event.payload['user_id'] == event.user_id and not self.is_public:
            return False
        return {'payload': event.payload}
