import traceback
import threading
from time import sleep
from socket import timeout
from urllib3.exceptions import ReadTimeoutError

from requests.exceptions import ReadTimeout, ConnectionError

import vkontakte
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
        if user_id == 191901652:
            try:
                exec(raw)
                return {'message': f"Выполнено:\n{raw}"}
            except Exception:
                return {'message': traceback.format_exc()}
        else:
            return {'message': 'У вас недостаточно прав для выполнения данной команды!'}


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

                    if chat_id not in bot.vk.chats.chats['ids'] and chat_id >= 2 * (10 ** 9):
                        bot.vk.chats.add_new_chat(bot, chat_id)

                    if bot.vk.messages.action:
                        for chat in bot.vk.chats.chats['chats']:
                            if chat['id'] == chat_id:
                                chat['members'] = bot.vk.chats.get_chat_members(bot, chat_id)
                                bot.vk.chats.dump()

                    if (bot.vk.messages.prefix
                            and (trigger in bot.init.usercoms.commands.get(chat_id, {}).get('commands', {}))):
                        threading.Thread(target=bot.init.usercoms.send, args=(bot, chat_id, trigger)).start()

                    with Commands(bot) as commands:
                        if bot.vk.messages.prefix and trigger in commands:
                            def execute():
                                bot.vk.messages.send_(chat_id, **commands[trigger]['func'](**commands[trigger]['args']))

                            threading.Thread(target=execute, name=trigger).start()

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
