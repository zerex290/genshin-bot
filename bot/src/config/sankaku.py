URL: str = 'https://capi-v2.sankakucomplex.com/posts/keyset'

HEADERS: dict = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/94.0.4606.85 YaBrowser/21.11.0.1996 Yowser/2.5 Safari/537.36',
    'accept': 'application/vnd.sankaku.api+json;v=2',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru,en',
    'content-type': 'application/json; charset=utf-8',
}

ATTRIBUTES: dict = {
    'lang': 'en',
    'default_threshold': '1',
    'hide_posts_in_books': 'in-larger-tags',
    'limit': '100',
    'tags': '',
    'next': ''
}
