import datetime
from typing import Dict, List, Tuple, Optional, AsyncGenerator

import aiohttp

from fake_useragent import UserAgent
from fake_useragent.errors import FakeUserAgentError

from bot.config import sankaku
from bot.utils import get_tz, catch_aiohttp_errors
from bot.src.types.sankaku import Rating, Order, TagType
from bot.src.models.sankaku import Post, Author, Tag


__all__ = ('SankakuParser',)


class SankakuParser:
    def __init__(
            self,
            rating: Rating = Rating.S,
            order: Order = Order.RANDOM,
            tags: Tuple[str, ...] = ()
    ) -> None:
        self._url = sankaku.URL
        self._headers = sankaku.HEADERS
        self._attributes = sankaku.ATTRIBUTES

        self._rating = rating.value
        self._order = order.value
        self._tags = (*tags, self._rating, self._order)

    def _set_headers(self) -> Dict[str, str]:
        headers = self._headers.copy()
        try:
            useragent = UserAgent()
            headers['user_agent'] = useragent.random
        except FakeUserAgentError:
            pass
        return headers

    def _set_attributes(self, next_: str) -> Dict[str, str]:
        attributes = self._attributes.copy()
        attributes['tags'] += ' '.join(self._tags)
        attributes['next'] = next_
        return attributes

    @catch_aiohttp_errors
    async def _get_json(self, next_: str) -> Tuple[List[Dict[str, str | int]], Optional[str]]:
        headers = self._set_headers()
        attributes = self._set_attributes(next_)
        async with aiohttp.ClientSession() as session:
            async with session.get(self._url, headers=headers, params=attributes) as page:
                json = await page.json()
                data = json.get('data', [])
                meta_next = json.get('meta', {}).get('next')
                return data, meta_next

    @staticmethod
    def _compile_author(post: dict) -> Author:
        author = post['author']
        author['avatar_rating'] = Rating[author['avatar_rating'].upper() if author['avatar_rating'] else 'U']
        return Author(**author)

    @staticmethod
    def _compile_tags(post: dict) -> List[Tag]:
        tags = []
        post_tags = post['tags']
        for tag in post_tags:
            tag['rating'] = Rating[tag['rating'].upper() if tag['rating'] else 'U']
            tag['type'] = TagType(tag['type'])
            tags.append(Tag(**tag))
        return tags

    def _compile_post(self, post: dict) -> Post:
        post['author'] = self._compile_author(post)
        post['tags'] = self._compile_tags(post)
        post['rating'] = Rating[post['rating'].upper() if post['rating'] else 'U']

        timestamp = datetime.datetime.fromtimestamp(post['created_at']['s'], get_tz(3))
        post['created_at'] = timestamp

        return Post(**post)

    async def _iter_pages(self) -> AsyncGenerator:
        next_ = ''
        while next_ is not None:
            page_data = await self._get_json(next_)
            page, next_ = page_data if len(page_data) == 2 else ([], None)
            yield page

    async def iter_posts(self, minimum_fav_count: int = 0) -> AsyncGenerator:
        async for page in self._iter_pages():
            for post in page:
                if not post['file_url']:
                    continue
                if post['fav_count'] < minimum_fav_count:
                    continue
                yield self._compile_post(post)
