# Внимание

*Данный репозиторий был заброшен и более не поддерживается*.

---

# genshin-bot

*Асинхронный* бот для [VK](https://vk.com/bot_genshin) по игре Genshin Impact.

## Особенности

- Интерактивная база данных по Genshin Impact прямо внутри бота;
- Возможность поиска артов через сайт [SankakuComplex](https://beta.sankakucomplex.com);
- Автоматическая публикация постов с артами по Genshin Impact в группу;
- Поддержка PostgreSQL для хранения данных бота;
- Логирование возможных ошибок при работе;
- Генерация изображений из шаблонов;
- Возможность добавления собственных команд без необходимости модифицировать код;
- Возможность прямого взаимодействия с ботом и системой через команду `!exec`.

---

Описание команд бота (с примерами): https://vk.com/@bot_genshin-commands

---

## Зависимости

- Python 3.8+
- PostgreSQL
- aiohttp
- aiofiles
- vkbottle
- asyncpg
- genshin
- lxml
- PIL
- sankaku

## Установка

Необходимо клонировать гит-репозиторий в любую папку:

```commandline
git clone https://github.com/zerex290/genshin-bot
```

После этого нужно установить зависимости из файла `requirements.txt`:

```commandline
pip install -r requirements.txt
```

**Для корректной работы боту необходимо:**

1. Установить необходимые переменные окружения.
2. Создать и инициализировать базу данных.
3. Сконфигурировать рабочее пространство бота.

### Установка переменных окружения

Необходимо установить следующие переменные окружения:

- ADMINS: `str` - ID администраторов бота (разделенные запятыми);
- GROUP_TOKEN: `str` - API-ключ группы, от лица которой будет работать бот;
- GROUP_ID: `int` - ID группы, от лица которой будет работать бот (например, -123456789);
- SHORTNAME: `str` - короткое имя группы, от лица которой будет работать бот (например, @mygroup);
- USER_TOKEN: `str` - API-ключ приложения ВК (для автоматизации публикации постов в группу);
- USER_ID: `id` - ID пользователя-владельца ВК приложения (и от имени которого будут публиковаться посты);
- DATABASE_ADDRESS: `str` - адрес базы данных для asyncpg (например, postgres://user:pass@host:port/dbname).

### Создание и инициализация базы данных

Для того чтобы создать базу данных, необходимо во время сеанса `psql` написать:

```sql
CREATE DATABASE dbname;
```

После создания базы данных ее нужно проинициализировать:

```commandline
python initdb.py
```

### Конфигурирование рабочего пространства

Для конфигурации необходимо скачать архив с файлами с [ЯндексДиск](https://disk.yandex.ru/d/LPnj__Hr9pK8NA).
Архив необходимо скачивать в ту же директорию, в которую был клонирован репозиторий.

После этого необходимо распаковать его:

```commandline
tar -xf environment.zip 
```

## Запуск бота

Для того чтобы запустить бота на локальном устройстве или удаленном сервере,
необходимо написать:

```commandline
python -m bot
```

## Дополнительная информация

Все шаблоны, используемые для генерации изображений, можно получить, клонировав
на собственный аккаунт проект в [Figma](https://www.figma.com/file/egZKJ5MaYPjLvnuLPslHXv/GenshinBot?type=design&node-id=0%3A1&t=4lkET2JluNKpRvXJ-1).