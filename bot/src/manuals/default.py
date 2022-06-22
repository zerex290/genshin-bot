from bot.src.manuals import BaseManual


class Guide(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=komandy
    \r\nОписание: При использовании данной команды бот отправит в чат ссылку на статью со всеми командами, \
    а также предоставит список всех существующих на данный момент команд (без описания).
    \r\nСинтаксис: !команды [опции]
    \r~~п > текущая помощь по команде
    \r\nПодождите, вам всерьез потребовалась справка по этой команде?..
    '''


class Autocorrection(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=avtokorrekt
    \r\nОписание: Бот имеет возможность предугадывания и исправления синтаксиса написанной команды. \
    Поведение команды по умолчанию: отображение текущего статуса автокоррекции команд.
    \r\nПримечание 1: логика предугадывания команд еще сырая, поэтому иногда возможны неочевидные варианты \
    исправления.
    \r\nСинтаксис: !автокоррект [опции]
    \r~~п > текущая помощь по команде
    \r~~вкл > включение автокоррекции команд
    \r~~выкл > выключение автокоррекции команд
    '''


class Choice(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=vyberi
    \r\nОписание: При использовании данной команды бот отправит в чат один из предоставленных ему вариантов выбора.
    \r\nСинтаксис: !выбери [опции] [вариант-1] / [вариант-2] / [вариант-n]
    \r~~п > текущая помощь по команде
    '''


class Converter(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=konvert
    \r\nОписание: При использовании данной команды с прикрепленным текстовым сообщением бот отправит в чат копию \
    текста прикрепленного сообщения с переводом символов английской раскладки на русскую \
    (используется раскладка qwerty/йцукен).
    \r\nСинтаксис: !конверт [опции] [прикрепленное сообщение]
    \r~~п > текущая помощь по команде
    \r~~ра > конвертация с русской раскладки на английскую
    '''


class Timer(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=taymer
    \r\nОписание: При использовании данной команды бот установит таймер на заданное время, по истечении которого \
    отметит вас в чате, где была использована команда.
    \r\nПримечание 1: время можно задавать в часах, минутах и секундах.
    \r\nПримечание 2: можно указать пометку к таймеру, которая будет использована в ответном сообщения  бота \
    по истечению времени таймера.
    \r\nСинтаксис: !таймер [опции] [*ч *м *с] / [пометка]
    \r~~п > текущая помощь по команде
    '''


class Attachments(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=pereshli
    \r\nОписание: При использовании этой команды с прикрепленным изображением бот отправит в чат прикрепленную \
    ранее картинку.
    \r\nПримечание 1: бот не сможет переслать больше 3 изображений за раз. Эти ограничения наложены самим Вконтакте.
    \r\nСинтаксис: !перешли [опции] [изображения]
    \r~~п > текущая помощь по команде
    '''


class RandomTag(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=randomteg
    \r\nОписание: При использовании данной команды бот отправит в чат случайное количество тегов-псевдонимов для \
    поиска при помощи команды «пик».
    \r\nСинтаксис: !рандомтег [опции]
    \r~~п > текущая помощь по команде
    \r~~г > случайные теги из группы "Геншин"
    \r~~ср > случайные теги из группы "Стиль Рисунка"
    \r~~о > случайные теги из группы "Одежда"
    \r~~у > случайные теги из группы "Украшения"
    \r~~э > случайные теги из группы "Эмоции"
    \r~~т > случайные теги из группы "Тело"
    \r~~с > случайные теги из группы "Существа"
    '''


class RandomPicture(BaseManual):
    HELP = '''
    \r\nСсылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=pik
    \r\nОписание: При использовании данной команды бот отправит в чат до 10 изображений по заданным тегам.
    \r\nПримечание 1: изображения берутся с сайта Sankaku Complex.
    \r\nПримечание 2: теги для команды можно получить при помощи команды «рандомтег», либо написав синтаксически \
    корректное название тега напрямую (как они пишутся на сайте Sankaku Complex).
    \r\nПримечание 3: теги чувствительны к регистру.
    \r\nСинтаксис: !пик [опции] [количество изображений] [теги]
    \r~~п > текущая помощь по команде
    '''
