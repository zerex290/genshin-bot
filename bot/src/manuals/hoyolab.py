from bot.src.manuals import BaseManual


class AccountLink(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=link
    \r\nОписание: Данная команда позволяет привязать свой игровой аккаунт к базе данных бота. \
    Требуемые данные: [ltoken], [ltuid], [cookie_token], [uid]
    \r\nПримечание 1: после привязки бот автоматически будет собирать логин-бонус для вашего аккаунта на \
    сайте HoYoLab. Происходить это будет раз в 8 часов вечера по Московскому времени.
    \r\nПримечание 2: если после привязки аккаунта вы решите сменить свои внутриигровые данные, то процесс \
    регистрации придется проводить по новой, т.к. при их смене ваши cookie обновятся.
    \r\nСинтаксис: !линк [опции] [данные=значение]
    \r~~п > текущая помощь по команде
    '''


class AccountUnlink(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=anlink
    \r\nОписание: Данная команда позволяет отвязать свой игровой аккаунт от базы данных бота.
    \r\nСинтаксис: !анлинк [опции]
    \r~~п > текущая помощь по команде
    '''


class Notes(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=zametki
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с вашими заметками \
    путешественника в реальном времени.
    \r\nПримечание 1: при использовании опции «-у» вместе с прикрепленным сообщением другого игрока, данные \
    которого привязаны к базе данных бота, имеется возможность посмотреть его игровые заметки.
    \r\nСинтаксис: !заметки [опции]
    \r~~п > текущая помощь по команде
    \r~~у [ответ на сообщение другого игрока] > просмотр заметок другого путешественника
    '''


class Stats(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=staty
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с вашей внутриигровой \
    статистикой.
    \r\nПримечание 1: при использовании опции «-у» вместе с прикрепленным сообщением другого игрока, данные \
    которого привязаны к базе данных бота, имеется возможность посмотреть его внутриигровую статистику.
    \r\nСинтаксис: !статы [опции]
    \r~~п > текущая помощь по команде
    \r~~у [ответ на сообщение другого игрока] > просмотр внутриигровой статистики другого путешественника
    '''


class Rewards(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=nagrady
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с информацией о ваших \
    ежедневных отметках на сайте HoYoLAB.
    \r\nСинтаксис: !награды [опции]
    \r~~п > текущая помощь по команде
    '''


class RedeemCode(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: hhttps://vk.com/@bot_genshin-commands?anchor=prom
    \r\nОписание: При использовании данной команды бот активирует на вашем игровом аккаунте указанные в сообщении \
    промокоды.
    \r\nПримечание 1: промокоды вводятся через пробел.
    \r\nПримечание 2: обработка команды может занимать время, т.к. после каждого введенного промокода боту \
    требуется подождать 5 секунд, прежде чем вводить новый.
    \r\n!пром [опции] [промокод-1] [промокод-2] [промокод-n]
    \r~~п > текущая помощь по команде
    '''


class ResinNotifications(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=rezinnout
    \r\nОписание: Бот имеет возможность отмечать в чате пользователя, значение смолы которого достигло или \
    превысило 150 единиц. По умолчанию эта команда показывает, включены ли такие упоминания ботом пользователя в \
    текущем чате.
    \r\nПримечание 1: при использовании опций имеется возможность включать или выключать упоминания вас ботом.
    \r\nПримечание 2: интервал между отметками пользователя в чате составляет 1 час.
    \r\nПримечание 3: бот совершает 3 последовательных отметки пользователя, значение смолы которого достигло или \
    превысило 150 единиц. Если после 3 отметок подряд значения смолы так и не опустилось ниже 150, то бот \
    прекращает упоминать в чате пользователя до момента, пока пользователь не зайдет в игру и не потратит смолу.
    \r\nСинтаксис: !резинноут [опции]
    \r~~п > текущая помощь по команде
    \r~~выкл > выключение функции отметки пользователя в чате
    \r~~вкл > включение функции отметки пользователя в чате
    '''


class Diary(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=dnevnik
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с информацией о вашем дневнике \
    путешественника.
    \r\nПримечание 1: при использовании опции «-у» вместе с прикрепленным сообщением другого игрока, \
    данные которого привязаны к базе данных бота, имеется возможность посмотреть его дневник путешественника.
    \r\nСинтаксис: !дневник [опции]
    \r~~п > текущая помощь по команде
    \r~~у [ответ на сообщение другого игрока] > просмотр дневника другого путешественника
    '''


class SpiralAbyss(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=bezdna
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с информацией о вашем прогрессе \
    витой бездны (9-12 этажи).
    \r\nПримечание 1: при использовании опции «-у» вместе с прикрепленным сообщением другого игрока, \
    данные которого привязаны к базе данных бота, имеется возможность посмотреть его прогресс витой бездны.
    \r\nСинтаксис: !бездна [опции]
    \r~~п > текущая помощь по команде
    \r~~у [ответ на сообщение другого игрока] > просмотр прогресса витой бездны другого путешественника
    '''