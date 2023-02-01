from .admin import bl as admin_labeler
from .customcommands import bl as customcommands_labeler
from .default import default_labeler
from .genshin import genshin_labeler


__all__ = (
    'admin_labeler',
    'customcommands_labeler',
    'default_labeler',
    'genshin_labeler',
)
