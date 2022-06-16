# genshin-bot
> **Asynchronous** bot for [Vk](https://vk.com/bot_genshin) with genshin related features and postgresql database
> implementation.

## Requirements
* **python 3.10+**
* **aiohttp**
* **aiofiles**
* **vkbottle**
* **asyncpg**
* **genshin**
* **lxml**

## Installation
> A few words about dependencies:
> 1. <code>Vk</code>: bot require as group as user for proper work
> 2. <code>Postgresql</code>: bot require postgresql database to store information
> 3. <code>Work Directory</code>: bot require access to specific directories which contains images or logs; 
can be downloaded from [YandexDisk](https://disk.yandex.ru/d/LPnj__Hr9pK8NA)

 1. Clone git repository to chosen directory:
<code> git clone https://github.com/zerex290/genshin-bot </code>
 2. Set environmental variables necessary for work:
    * **GROUP_TOKEN**: <code>str</code> - your group api access key
    * **GROUP_ID**: <code>int</code> - your group id *(e.g. -123456789)*
    * **SHORTNAME**: <code>str</code> - your group shortname *(e.g. @my_group)*
    * **USER_TOKEN**: <code>str</code> - token from vk standalone app
    * **USER_ID**: <code>int</code> - id of user on which standalone app was registered
    * **DATABASE_ADDRESS**: <code>str</code> - address of your database for asyncpg
*(e.g. postgres://user:pass@host:port/database)*
 3. Extract **Work Directory** into current folder: <code>tar -xf environment.zip </code>
 4. Run secondary script which will create postgresql tables: <code> ./create_pg_tables.py </code>
 5. Run main script: <code>python -m bot</code>
