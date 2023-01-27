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
* **PIL**

## Installation
> A few words about dependencies:
> 1. <code>Vk</code>: bot requires as group as user for proper work
> 2. <code>Postgresql</code>: bot requires postgresql database to store information
> 3. <code>Work Directory</code>: bot requires access to specific directories which contains images or logs; 
can be downloaded from [YandexDisk](https://disk.yandex.ru/d/LPnj__Hr9pK8NA)

 1. Clone git repository to chosen directory:
<code> git clone https://github.com/zerex290/genshin-bot </code>
 2. Install requirements: <code>pip install -r requirements.txt</code>
 3. Set environmental variables necessary for work:
    * **ADMINS**: <code>str</code> - admin ids separated by commas
    * **GROUP_TOKEN**: <code>str</code> - your group api access key
    * **GROUP_ID**: <code>int</code> - your group id *(e.g. -123456789)*
    * **SHORTNAME**: <code>str</code> - your group shortname *(e.g. @my_group)*
    * **USER_TOKEN**: <code>str</code> - token from vk standalone app
    * **USER_ID**: <code>int</code> - id of user on which standalone app was registered
    * **DATABASE_ADDRESS**: <code>str</code> - address of your database for asyncpg
*(e.g. postgres://user:pass@host:port/database)*
 4. Download **Work Directory**
 5. Extract **Work Directory** into current folder: <code>tar -xf environment.zip </code>
 6. Run secondary script which will create postgresql tables: <code> python create_pg_tables.py </code>
 7. Run main script: <code>python -m bot</code>
