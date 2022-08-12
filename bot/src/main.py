import asyncio

from vkbottle import load_blueprints_from_package

from ..config import Bot
from ..middlewares import *
from ..src.extra import *
from ..utils.files import write_logs

bot = Bot()
post_uploader = PostUploader(bot.user)
resin_notifier = ResinNotifier(bot.group)


@bot.group.error_handler.register_undefined_error_handler
async def log_undefined_errors(error: Exception) -> None:
    await write_logs(error)


@bot.group.error_handler.catch
async def main() -> None:
    for bp in load_blueprints_from_package('blueprints'):
        bp.load(bot.group)
    bot.group.labeler.message_view.register_middleware(GroupFilterMiddleware)
    bot.group.labeler.message_view.register_middleware(UserRegisterMiddleware)
    bot.group.labeler.message_view.register_middleware(ChatRegisterMiddleware)
    bot.group.labeler.message_view.register_middleware(ChatUserUpdateMiddleware)
    bot.group.labeler.message_view.register_middleware(CommandGuesserMiddleware)

    await asyncio.gather(
        bot.group.run_polling(),
        collect_login_bonus(),
        resin_notifier.notify(),
        parse_genshin_database_objects(),
        post_uploader.make_post(donut=True),
        post_uploader.make_post()
    )
    await asyncio.sleep(0)  #: Used to fix RuntimeError...
