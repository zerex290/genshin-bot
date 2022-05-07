import datetime
import asyncio
import os
import random
from typing import List, Dict, Tuple, Optional

from vkbottle import API, Bot

from genshin.types import Game

from bot.parsers import SankakuParser, CharacterParser, WeaponParser, ArtifactParser, EnemyParser, BookParser
from bot.utils import PostgresConnection, GenshinClient, json
from bot.utils.files import download, upload
from bot.utils.genshin import get_genshin_account_by_id
from bot.utils.postgres import has_postgres_data
from bot.src.types.sankaku import MediaType, Rating
from bot.src.templates.artposting import format_post_message, format_source
from bot.config.dependencies.paths import FILECACHE
from bot.config.dependencies.group import ID


async def parse_genshin_db_objects() -> None:
    loop = asyncio.get_running_loop()
    character = CharacterParser()
    weapon = WeaponParser()
    artifact = ArtifactParser()
    enemy = EnemyParser()
    book = BookParser()
    while True:
        await asyncio.gather(
            loop.run_in_executor(None, json.dump, await character.get_characters(), 'characters'),
            loop.run_in_executor(None, json.dump, await weapon.get_weapons(), 'weapons'),
            loop.run_in_executor(None, json.dump, await artifact.get_artifacts(), 'artifacts'),
            loop.run_in_executor(None, json.dump, await enemy.get_enemies(), 'enemies'),
            loop.run_in_executor(None, json.dump, await book.get_books(), 'books'),
        )
        await asyncio.sleep(36000)


async def collect_login_bonus() -> None:
    while True:
        tz_offset = datetime.timedelta(hours=3)  #: Moscow time offset
        tz = datetime.timezone(tz_offset)
        time = datetime.datetime.now(tz=tz)

        if time.hour < 20:
            await asyncio.sleep((20 - time.hour)*3600 - time.minute*60)
        elif time.hour > 20:
            await asyncio.sleep((24 - time.hour + 20)*3600 - time.minute*60)
        else:
            accounts = []
            async with PostgresConnection() as connection:
                for account in await connection.fetch('SELECT uid, ltuid, ltoken FROM genshin_accounts;'):
                    accounts.append(dict(account))
            for account in accounts:
                async with GenshinClient(exc_catch=True, **account) as client:
                    await client.claim_daily_reward(game=Game.GENSHIN.value)
            await asyncio.sleep(24*3600 - time.minute*60)


async def _get_users() -> List[Dict[str, str | int]]:
    async with PostgresConnection() as connection:
        users = await connection.fetch('''
            SELECT first_name, uic.user_id, chat_id FROM users u JOIN users_in_chats uic 
            ON u.user_id = uic.user_id 
            WHERE uic.resin_notifications = true;
        ''')
        return [dict(user) for user in users]


async def _get_user_resin(account: Dict[str, str | int]) -> Optional[int]:
    async with GenshinClient(exc_catch=True, ltuid=account['ltuid'], ltoken=account['ltoken'] + 'f') as client:
        return (await client.get_genshin_notes(account['uid'])).current_resin


async def notify_about_resin_replenishment(bot: Bot) -> None:
    endings = {1: 'у', 2: 'ы', 3: 'ы', 4: 'ы'}  #: Used to write word "единица" in right cases
    while True:
        for user in await _get_users():
            resin = await _get_user_resin(await get_genshin_account_by_id(user['user_id'], True, True, True))
            if isinstance(resin, int) and resin >= 150:
                await bot.api.messages.send(
                    random_id=random.randint(0, 1000),
                    peer_id=user['chat_id'],
                    message=f"@id{user['user_id']} ({user['first_name']}), ваша смола достигла отметки в "
                            f"{resin} единиц{endings.get(resin - 150, '')}, поспешите её потратить!"
                )
        await asyncio.sleep(1800)


class PostUploader:
    THEMATIC: bool = False
    THEMATIC_TAGS: Tuple[str, ...] = ()
    MINIMUM_DONUT_FAV_COUNT = 500
    MINIMUM_FAV_COUNT = 0

    def _get_tags(self, donut: bool) -> Tuple[str, ...]:
        if not self.__class__.THEMATIC:
            tags = ('genshin_impact', '-loli') if donut else ('genshin_impact',)
        else:
            tags = (*self.__class__.THEMATIC_TAGS, '-loli') if donut else self.__class__.THEMATIC_TAGS
        return tags

    async def make_post(self, api: API,  donut: bool = False):
        while True:
            parser = SankakuParser(tags=self._get_tags(donut), rating=Rating.Q if donut else Rating.S)
            async for post in parser.iter_posts(
                    self.__class__.MINIMUM_DONUT_FAV_COUNT if donut else self.__class__.MINIMUM_FAV_COUNT
            ):
                if post.file_mediatype == MediaType.VIDEO:
                    continue
                if await has_postgres_data(f"SELECT * FROM group_posts WHERE sankaku_post_id = {post.id};"):
                    continue
                file = await download(post.file_url, FILECACHE, str(post.id), post.file_suffix)
                if not file:
                    continue
                attachment = await upload(api, 'photo_wall', file)
                wall_post = await api.wall.post(
                    owner_id=ID,
                    donut_paid_duration=-1 if donut else None,
                    attachments=[attachment],
                    copyright=format_source(post.source) if post.source else None,
                    message=format_post_message(donut, post.tags)
                )
                async with PostgresConnection() as connection:
                    await connection.execute(f"""
                        INSERT INTO group_posts VALUES (
                            {wall_post.post_id}, {post.id}, 'photo', {'true' if donut else 'false'}
                        );
                    """)
                os.remove(file)
                break
            await asyncio.sleep(7200)
