import datetime
from typing import Dict, List, Tuple, AsyncGenerator

import aiohttp

from fake_useragent import UserAgent
from fake_useragent.errors import FakeUserAgentError

from bot.config import sankaku
from bot.utils import get_tz
from bot.src.types.sankaku import Rating, Order, TagType
from bot.src.models.sankaku import Post, Author, Tag


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
        self._tags = tags

    def _set_headers(self) -> Dict[str, str]:
        headers = self._headers.copy()
        try:
            useragent = UserAgent()
            headers['user_agent'] = useragent.random
        except FakeUserAgentError:
            pass
        return headers

    async def _get_json(self, next_: str) -> Tuple[Dict[str, str | int], str] | Tuple[dict, None]:
        headers = self._set_headers()
        attrs = self._attributes.copy()
        attrs['tags'] += ' '.join(self._tags + (self._rating,) + (self._order,))
        attrs['next'] = next_

        async with aiohttp.ClientSession() as session:
            async with session.get(self._url, headers=headers, params=attrs) as page:
                json = await page.json()
                if not json.get('success', True):
                    return {}, None
                return json['data'], json['meta']['next']

    @staticmethod
    def _get_author(post: dict) -> Author:
        author = post['author']
        author['avatar_rating'] = Rating[author['avatar_rating'].upper() if author['avatar_rating'] else 'U']
        return Author(**author)

    @staticmethod
    def _get_tags(post: dict) -> List[Tag]:
        tags = []
        post_tags = post['tags']
        for tag in post_tags:
            tag['rating'] = Rating[tag['rating'].upper() if tag['rating'] else 'U']
            tag['type'] = TagType(tag['type'])
            tags.append(Tag(**tag))
        return tags

    def _compile_post(self, post: dict) -> Post:
        post['author'] = self._get_author(post)
        post['tags'] = self._get_tags(post)
        post['rating'] = Rating[post['rating'].upper() if post['rating'] else 'U']

        timestamp = datetime.datetime.fromtimestamp(post['created_at']['s'], get_tz(3))
        post['created_at'] = timestamp

        return Post(**post)

    async def _iter_pages(self) -> AsyncGenerator:
        next_ = ''
        while next_ is not None:
            page, next_ = await self._get_json(next_)
            yield page

    async def iter_posts(self, minimum_fav_count: int = 0) -> AsyncGenerator:
        async for page in self._iter_pages():
            for post in page:
                if not post['file_url']:
                    continue
                if post['fav_count'] < minimum_fav_count:
                    continue
                yield self._compile_post(post)
