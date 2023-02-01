from .genshinbot import bot
from ..extra import PostManager, ResinNotifier


__all__ = (
    'bot',
    'post_manager',
    'resin_notifier'
)


post_manager = PostManager(bot.user.api)
resin_notifier = ResinNotifier(bot.group.api)
