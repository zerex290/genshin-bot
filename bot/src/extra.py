import asyncio
import os
import random
from typing import Optional

from vkbottle import API, Bot, VKAPIError

from genshin.types import Game

from ..parsers import *
from ..utils import PostgresConnection, GenshinClient, json, get_current_timestamp, find_restricted_tags
from ..utils.files import download, upload
from ..utils.genshin import get_genshin_account_by_id
from ..utils.postgres import has_postgres_data
from ..types.sankaku import MediaType, Rating, TagType
from ..templates.artposting import format_post_message, format_post_source
from ..config.dependencies.paths import FILECACHE
from ..config.dependencies.group import ID


__all__ = (
    'parse_genshin_database_objects',
    'collect_login_bonus',
    'notify_about_resin_replenishment',
    'PostUploader'
)


async def parse_genshin_database_objects() -> None:
    loop = asyncio.get_running_loop()
    character = CharacterParser()
    weapon = WeaponParser()
    artifact = ArtifactParser()
    enemy = EnemyParser()
    book = BookParser()
    domain = DomainParser()
    while True:
        await asyncio.gather(
            loop.run_in_executor(None, json.dump, await character.get_characters(), 'characters'),
            loop.run_in_executor(None, json.dump, await weapon.get_weapons(), 'weapons'),
            loop.run_in_executor(None, json.dump, await artifact.get_artifacts(), 'artifacts'),
            loop.run_in_executor(None, json.dump, await enemy.get_enemies(), 'enemies'),
            loop.run_in_executor(None, json.dump, await book.get_books(), 'books'),
            loop.run_in_executor(None, json.dump, await domain.get_domains(), 'domains'),
        )
        await asyncio.sleep(36000)


async def collect_login_bonus() -> None:
    while True:
        time = get_current_timestamp(3)  #: Moscow time offset

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


async def _get_users() -> list[dict[str, str | int]]:
    async with PostgresConnection() as connection:
        users = await connection.fetch('''
            SELECT user_id, chat_id, notification_number, notification_value 
            FROM users_in_chats 
            WHERE resin_notifications = true;
        ''')
        return [dict(user) for user in users]


async def _get_user_resin(account: Optional[dict[str, str | int]]) -> Optional[int]:
    if not account:
        return None
    async with GenshinClient(exc_catch=True, ltuid=account['ltuid'], ltoken=account['ltoken']) as client:
        return (await client.get_genshin_notes(account['uid'])).current_resin


async def _update_notification_number(chat_id: int, user_id: int) -> None:
    async with PostgresConnection() as connection:
        await connection.execute(f"""
            UPDATE users_in_chats SET notification_number = notification_number + 1 
            WHERE chat_id = {chat_id} AND user_id = {user_id};
        """)


async def _reset_notification_number(chat_id: int, user_id: int) -> None:
    async with PostgresConnection() as connection:
        await connection.execute(f"""
            UPDATE users_in_chats SET notification_number = 0 
            WHERE chat_id = {chat_id} AND user_id = {user_id};
        """)


def _compile_message(user: dict[str, str | int], first_name: str, resin: int) -> str:
    cases = {1: 'у', 2: 'ы', 3: 'ы', 4: 'ы'}  #: Used to write word "единица" in right cases
    message = '@id{} ({}), ваша смола достигла отметки в {} единиц{}, поспешите её потратить! ({}/3)'
    message = message.format(
        user['user_id'],
        first_name,
        resin,
        cases.get(resin - 150, ''),
        user['notification_number'] + 1
    )
    return message


async def notify_about_resin_replenishment(bot: Bot) -> None:
    while True:
        for user in await _get_users():
            resin = await _get_user_resin(await get_genshin_account_by_id(user['user_id']))
            if not isinstance(resin, int):
                continue
            if resin >= user['notification_value'] and user['notification_number'] < 3:
                try:
                    first_name = (await bot.api.users.get([user['user_id']]))[0].first_name
                    await bot.api.messages.send(
                        random_id=random.randint(0, 10000),
                        peer_id=user['chat_id'],
                        message=_compile_message(user, first_name, resin)
                    )
                    await _update_notification_number(user['chat_id'], user['user_id'])
                except VKAPIError:
                    pass  #: tba chat remove from users_in_chats
            elif resin >= user['notification_value'] and user['notification_number'] >= 3:
                continue
            elif resin < user['notification_value'] and user['notification_number'] != 0:
                await _reset_notification_number(user['chat_id'], user['user_id'])
        await asyncio.sleep(3600)


class PostUploader:
    THEMATIC: bool = False
    THEMATIC_TAGS: tuple[str, ...] = ()
    MINIMUM_DONUT_FAV_COUNT: int = 500
    MINIMUM_FAV_COUNT: int = 500

    @property
    def tags(self) -> tuple[str, ...]:
        return ('genshin_impact',) if not self.THEMATIC else self.THEMATIC_TAGS

    async def make_post(self, api: API,  donut: bool = False):
        while True:
            parser = SankakuParser(tags=self.tags, rating=Rating.E if donut else Rating.S)
            async for post in parser.iter_posts(self.MINIMUM_DONUT_FAV_COUNT if donut else self.MINIMUM_FAV_COUNT):
                if post.file_mediatype != MediaType.IMAGE:
                    continue
                if donut and find_restricted_tags(post, ('loli', 'shota', 'penis')):
                    continue
                if len([tag for tag in post.tags if tag.type == TagType.CHARACTER]) > 2 and self.THEMATIC:
                    continue
                if await has_postgres_data(f"SELECT * FROM group_posts WHERE sankaku_post_id = {post.id};"):
                    continue
                file = await download(post.file_url, FILECACHE, str(post.id), post.file_suffix)
                if not file:
                    continue
                attachment = await upload(api, 'photo_wall', file)
                if attachment is None:
                    continue
                wall_post = await api.wall.post(
                    owner_id=ID,
                    donut_paid_duration=-1 if donut else None,
                    attachments=[attachment],
                    copyright=format_post_source(post.source) if post.source else None,
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
