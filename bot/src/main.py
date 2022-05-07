import asyncio

from vkbottle import load_blueprints_from_package

from bot.config import Bot
from bot.middlewares import GroupFilterMiddleware, CustomCommandsMiddleware
from bot.middlewares import UserRegisterMiddleware, ChatRegisterMiddleware, ChatUsersUpdateMiddleware
from bot.middlewares import MessageLogMiddleware
from bot.src.extra import collect_login_bonus, notify_about_resin_replenishment, parse_genshin_db_objects, PostUploader
from bot.utils.files import write_logs

bot = Bot()
post_uploader = PostUploader()


@bot.group.error_handler.register_undefined_error_handler
async def log_undefined_errors(error: BaseException) -> None:
    await write_logs(None, None, True, error)


@bot.group.error_handler.catch
async def main() -> None:
    for bp in load_blueprints_from_package('blueprints'):
        bp.load(bot.group)
    bot.group.labeler.message_view.register_middleware(GroupFilterMiddleware)
    bot.group.labeler.message_view.register_middleware(CustomCommandsMiddleware)
    bot.group.labeler.message_view.register_middleware(UserRegisterMiddleware)
    bot.group.labeler.message_view.register_middleware(ChatRegisterMiddleware)
    bot.group.labeler.message_view.register_middleware(ChatUsersUpdateMiddleware)
    bot.group.labeler.message_view.register_middleware(MessageLogMiddleware)

    await asyncio.gather(
        bot.group.run_polling(),
        collect_login_bonus(),
        notify_about_resin_replenishment(bot.group),
        parse_genshin_db_objects(),
        # post_uploader.make_post(bot.user.api, donut=True),
        # post_uploader.make_post(bot.user.api)
    )
    await asyncio.sleep(0)  #: Used to fix RuntimeError...
