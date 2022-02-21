import traceback
import threading
from time import sleep
from socket import timeout
from urllib3.exceptions import ReadTimeoutError

from requests.exceptions import ReadTimeout, ConnectionError
from vk_api.exceptions import ApiError

import vkontakte
from constants import Uncategorized
import genshin
import initial
import private
from templates.bot import Commands, PayloadTypes


class Bot:
    def __init__(self, auth_type):
        self.vk = vkontakte.Vk(
            app_id=private.Vk.USER_APP_ID, auth_type=auth_type, scope=private.Vk.USER_SCOPE,
            group_id=private.Vk.GROUP_ID, group_token=private.Vk.GROUP_TOKEN,
            user_token=private.Vk.USER_TOKEN, client_secret=private.Vk.USER_CLIENT_SECRET
        )
        self.genshin = genshin.Genshin()
        self.init = initial.Initial()

    def execute(self, user_id: int, raw: str) -> str or None:
        admins = [191901652, 687594282]
        if user_id in admins:
            try:
                exec(raw)
                return {'message': 'Команда успешно выполнена.'}
            except Exception:
                return {'message': traceback.format_exc()}
        else:
            return {'message': 'У вас недостаточно прав для выполнения данной команды!'}

    @staticmethod
    def guess_command(commands, trigger: str):
        trigger_conv = ''.join([Uncategorized.KEYBOARD.get(s, s) for s in trigger])
        coincidences = [com for com in commands if len(com) >= len(trigger_conv)]
        percentage = {len(set(cds).intersection(set(trigger_conv))) / len(cds): cds for cds in coincidences}
        best = max(percentage) if percentage else None
        return {'percentage': best, 'implied': percentage.get(best), 'is_equal': percentage.get(best) == trigger}


def user_thread():
    while True:
        bot = Bot('user')
        try:
            bot.init.make_post(bot, donut=False)
            bot.init.make_post(bot, donut=True)
            sleep(7200)
        except (ReadTimeout, ReadTimeoutError, timeout, ConnectionError):
            sleep(2)


def main_thread():
    while True:
        bot = Bot('group')
        try:
            for event in bot.vk.get_longpoll_server(bot.vk.group, private.Vk.GROUP_ID).listen():
                if event.type == bot.vk.event_type.MESSAGE_NEW:
                    bot.vk.messages.components(event)
                    trigger = bot.vk.messages.trigger.lower()
                    chat_id = bot.vk.messages.chat_id

                    bot.genshin.hoyolab.load_accounts()
                    bot.vk.chats.load()
                    bot.init.usercoms.load()

                    bot.vk.chats.refresh_chat_members(bot, chat_id)
                    bot.vk.chats.refresh_chats(bot, chat_id)

                    if (bot.vk.messages.prefix
                            and (trigger in bot.init.usercoms.commands.get(chat_id, {}).get('commands', {}))):
                        threading.Thread(target=bot.init.usercoms.send, args=(bot, chat_id, trigger)).start()

                    with Commands(bot) as commands:
                        guess = bot.guess_command(commands, trigger)
                        if bot.vk.messages.prefix and trigger in commands:
                            def execute():
                                bot.vk.messages.send_(chat_id, **commands[trigger]['func'](**commands[trigger]['args']))
                            threading.Thread(target=execute, name=trigger).start()
                        elif bot.vk.messages.prefix and 0.75 <= guess['percentage'] and not guess['is_equal']:
                            bot.vk.messages.send_(chat_id, f"Возможно, вы имели ввиду <<!{guess['implied']}>>?")

                elif (event.type == bot.vk.event_type.MESSAGE_EVENT
                      and event.obj['user_id'] == event.obj.payload['user_id']):
                    with PayloadTypes(bot, event) as responses:
                        def execute():
                            payload_type = event.obj.payload['type']
                            bot.vk.messages.edit_(
                                event.obj['peer_id'], event.obj['conversation_message_id'],
                                **responses[payload_type]['func'](**responses[payload_type]['args'])
                            )

                        threading.Thread(target=execute, name='ГДБ').start()
        except (ReadTimeout, ReadTimeoutError, timeout, ConnectionError):
            sleep(2)
        except ApiError:
            pass
        except Exception:
            bot.vk.messages.send_(2000000004, f"{traceback.format_exc()[:4096]}")


def resin_thread():
    while True:
        bot = Bot('group')
        try:
            bot.genshin.hoyolab.notify_about_resin(bot)
        except (ReadTimeout, ReadTimeoutError, timeout, ConnectionError):
            sleep(2)


def daily_rewards_thread():
    while True:
        bot = Bot('group')
        try:
            bot.genshin.hoyolab.claim_daily_rewards(bot)
        except (ReadTimeout, ReadTimeoutError, timeout, ConnectionError):
            sleep(2)


if __name__ == '__main__':
    main = threading.Thread(target=main_thread, name='Основной поток')
    user = threading.Thread(target=user_thread, name='Вторичный поток')
    resin = threading.Thread(target=resin_thread, name='Оповещение на смолу')
    daily = threading.Thread(target=daily_rewards_thread, name='Сбор логин-бонуса')

    for thread in (main, user, resin, daily):
        thread.start()
