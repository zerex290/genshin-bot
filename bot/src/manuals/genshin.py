from bot.src.manuals import BaseManual


class DailyMaterials(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=farm
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с изображением тех персонажей и \
    оружия, ресурсы для возвышения которых доступны на сегодняшний день.
    \r\nПримечание 1: при использовании опций отправляются изображения согласно использованным опциям.
    \r\nПримечание 2: опции можно комбинировать.
    \r\nСинтаксис: !фарм [опции]
    \r~~п > текущая помощь по команде
    \r~~пн > материалы для возвышения на понедельник
    \r~~вт > материалы для возвышения на вторник
    \r~~ср > материалы для возвышения на среду
    \r~~чт > материалы для возвышения на четверг
    \r~~пт > материалы для возвышения на пятницу
    \r~~сб > материалы для возвышения на субботу
    \r~~вс > материалы для возвышения на воскресенье
    '''


class AscensionMaterials(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=farm
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с изображением материалов \
    возвышения определенного персонажа.
    \r\nСинтаксис: !ресы [опции] [имя персонажа]
    \r~~п > текущая помощь по команде
    '''


class BossMaterials(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=talanty
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с изображением материалов \
    боссов, используемых определенными персонажами.
    \r\nСинтаксис: !таланты [опции]
    \r~~п > текущая помощь по команде
    '''


class Books(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=knigi
    \r\nОписание: При использовании данной команды бот отправляет в чат сообщение с изображением таблицы формата \
    «дни недели-доступные для фарма книги».
    \r\nСинтаксис: !книги [опции]
    \r~~п > текущая помощь по команде
    '''
