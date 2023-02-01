from .base import bl as _base_labeler
from .randompicture import bl as _randompicture_labeler


__all__ = ('default_labeler',)


_base_labeler.load(_randompicture_labeler)
default_labeler = _base_labeler
