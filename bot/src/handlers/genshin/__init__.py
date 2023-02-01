from .base import bl as _base_labeler
from .genshindb import bl as _genshindb_labeler
from .hoyolab import bl as _hoyolab_labeler


__all__ = ('genshin_labeler',)


_base_labeler.load(_genshindb_labeler)
_base_labeler.load(_hoyolab_labeler)
genshin_labeler = _base_labeler
