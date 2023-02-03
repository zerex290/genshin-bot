import asyncio

from .config import *
from .extra import refresh_cookies, collect_login_bonus, cache_genshindb_objects


async def main() -> None:
    bot.load_labelers().register_middlewares()
    await asyncio.gather(
        bot.group.run_polling(),
        refresh_cookies(),
        collect_login_bonus(),
        resin_notifier.notify(),
        cache_genshindb_objects(),
        post_manager.make_post(donut=True),
        post_manager.make_post()
    )
    await asyncio.sleep(0)  #: Used to fix RuntimeError...
