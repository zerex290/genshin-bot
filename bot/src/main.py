import asyncio

from .config import *
from .extra import refresh_cookies, collect_login_bonus, cache_genshindb_objects
from .utils.files import write_logs


@bot.group.error_handler.register_undefined_error_handler
async def log_undefined_errors(error: Exception) -> None:
    await write_logs(error)


@bot.group.error_handler.catch
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
