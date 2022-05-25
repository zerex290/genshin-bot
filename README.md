# genshin-bot
> An **asynchronous** bot for [Vk](https://vk.com) with genshin related features and postgresql database
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
> For properly work you need both group and user api.
> Also you need to create postgresql database.  
> 
> Group api is easy to get. Same situation with database creation.  
> User api can be obtained from registering any standalone vk app
> and then giving it permissions. After that you can get user token.

 1. Clone git repository to chosen directory
 2. Set necessary for work environmental variables:
    * **GROUP_TOKEN**: <code>str</code> - your group api access key
    * **GROUP_ID**: <code>int</code> - your group id
    * **SHORTNAME**: <code>str</code> - your group shortname *(e.g. @my_group)*
    * **USER_TOKEN**: <code>str</code> - token from vk standalone app
    * **USER_ID**: <code>int</code> - id of user on which standalone app was registered
    * **DATABASE_ADDRESS**: <code>str</code> - address of your database for asyncpg
*(e.g. postgres://user:pass@host:port/database)*
    * ~~**ASCENSION**~~
    * ~~**BOOKS**~~
    * ~~**BOSS_MATERIALS**~~
    * ~~**DAILY_MATERIALS**~~
    * ~~**DATABASE_APPEARANCE**~~
    * ~~**DUNGEONS**~~
    * **FILECACHE**: <code>str</code> - path to directory that will contain temporary file cache
    * **LOGS**: <code>str</code> - path to directory that will contain logs
 3. Run **create_pg_tables.py**

> After all conditions are met, just write <code>python -m bot</code> in the console.

