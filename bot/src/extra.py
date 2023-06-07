import asyncio
import os
import random
from typing import Optional, Union, Dict, List

from vkbottle import API, VKAPIError

from sankaku import SankakuClient
from sankaku.types import PostOrder, Rating, FileType, TagType

from .parsers import *
from .utils import PostgresConnection, GenshinClient, json, get_current_timestamp, cycle
from .utils.files import download, upload
from .utils.genshin import get_genshin_account_by_id
from .utils.postgres import has_postgres_data
from .templates.artposting import format_post_message, format_post_source
from .models.hoyolab import GenshinAccount
from .config.genshinbot import error_handler
from .config.dependencies.group import ID


__all__ = (
    'ResinNotifier',
    'PostManager',
    'cache_genshindb_objects',
    'collect_login_bonus',
)


class ResinNotifier:
    def __init__(self, api: API) -> None:
        self.api = api

    @cycle(hours=1)
    @error_handler.catch
    async def notify(self) -> None:
        for user in await self._get_users():
            resin = await self._get_user_resin(await get_genshin_account_by_id(user['user_id']))
            if not isinstance(resin, int):
                continue
            if resin >= user['notification_value'] and user['notification_number'] < 3:
                try:
                    first_name = (await self.api.users.get([user['user_id']]))[0].first_name
                    await self.api.messages.send(
                        random_id=random.randint(0, 10000),
                        peer_id=user['chat_id'],
                        message=self._compile_message(user, first_name, resin)
                    )
                    await self._update_notification_number(user['chat_id'], user['user_id'])
                except VKAPIError:
                    pass  #: tba chat remove from users_in_chats
            elif resin >= user['notification_value'] and user['notification_number'] >= 3:
                continue
            elif resin < user['notification_value'] and user['notification_number'] != 0:
                await self._reset_notification_number(user['chat_id'], user['user_id'])

    @staticmethod
    async def _get_users() -> List[Dict[str, Union[str, int]]]:
        async with PostgresConnection() as connection:
            users = await connection.fetch('''
                SELECT user_id, chat_id, notification_number, notification_value 
                FROM users_in_chats 
                WHERE resin_notifications = true;
            ''')
            return [dict(user) for user in users]

    @staticmethod
    async def _get_user_resin(account: Optional[GenshinAccount]) -> Optional[int]:
        if not account:
            return None
        async with GenshinClient(account, exc_catch=True) as client:
            return (await client.get_genshin_notes()).current_resin

    @staticmethod
    async def _update_notification_number(chat_id: int, user_id: int) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE users_in_chats SET notification_number = notification_number + 1 
                WHERE chat_id = {chat_id} AND user_id = {user_id};
            """)

    @staticmethod
    async def _reset_notification_number(chat_id: int, user_id: int) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                UPDATE users_in_chats SET notification_number = 0 
                WHERE chat_id = {chat_id} AND user_id = {user_id};
            """)

    @staticmethod
    def _compile_message(user: Dict[str, Union[str, int]], first_name: str, resin: int) -> str:
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


class PostManager:
    THEMATIC: bool = False
    THEMATIC_TAGS: List[str] = []
    MINIMUM_DONUT_FAV_COUNT: int = 500
    MINIMUM_FAV_COUNT: int = 500

    def __init__(self, api: API) -> None:
        self.api = api

    @cycle(hours=2)
    @error_handler.catch
    async def make_post(self, donut: bool = False):
        async for post in SankakuClient().browse_posts(
            order=PostOrder.RANDOM,
            rating=Rating.EXPLICIT if donut else Rating.SAFE,
            tags=self.THEMATIC_TAGS if self.THEMATIC else ["genshin_impact"]
        ):
            if post.file_type is not FileType.IMAGE:
                continue
            if len([tag for tag in post.tags if tag.type is TagType.CHARACTER]) > 2 and self.THEMATIC:
                continue
            if await has_postgres_data(f"SELECT * FROM group_posts WHERE sankaku_post_id = {post.id};"):
                continue
            file = await download(post.file_url, name=str(post.id), ext=post.extension)
            if not file:
                continue
            attachment = await upload(self.api, 'photo_wall', file)
            if attachment is None:
                continue
            wall_post = await self.api.wall.post(
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


@cycle(hours=12)
@error_handler.catch
async def cache_genshindb_objects() -> None:
    json.dump(await CharacterParser.get_characters(), 'characters')
    json.dump(await WeaponParser.get_weapons(), 'weapons')
    json.dump(await ArtifactParser.get_artifacts(), 'artifacts')
    json.dump(await EnemyParser.get_enemies(), 'enemies')
    json.dump(await BookParser.get_books(), 'books')
    json.dump(await DomainParser.get_domains(), 'domains')
    json.dump(await TalentBookParser.get_talent_books(), 'talentbooks')
    json.dump(await BossMaterialParser.get_boss_materials(), 'bossmaterials')


@cycle()
@error_handler.catch
async def collect_login_bonus() -> None:
    time = get_current_timestamp(3)  #: Moscow time offset

    if time.hour < 20:
        await asyncio.sleep((20 - time.hour)*3600 - time.minute*60)
    elif time.hour > 20:
        await asyncio.sleep((24 - time.hour + 20)*3600 - time.minute*60)
    else:
        accounts = []
        async with PostgresConnection() as connection:
            for account in await connection.fetch('SELECT * FROM genshin_accounts;'):
                accounts.append(GenshinAccount(**dict(account)))
        for account in accounts:
            async with GenshinClient(account, exc_catch=True) as client:
                await client.claim_daily_reward(reward=False)
        await asyncio.sleep(24*3600 - time.minute*60)
