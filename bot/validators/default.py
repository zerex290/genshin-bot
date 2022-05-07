from typing import List, Tuple

from bot.errors.default import *


__all__ = ('RandomPictureValidator',)


class RandomPictureValidator:
    @staticmethod
    def check_quantity_specified(query: List[str]) -> None:
        if not query or not query[0].isdigit():
            raise QuantityNotSpecifiedError

    @staticmethod
    def check_quantity_overflowed(quantity: int) -> None:
        if quantity > 10:
            raise QuantityOverflowError

    @staticmethod
    def check_tags_overflowed(tags: Tuple[str, ...]) -> None:
        if len(tags) > 3:
            raise TagOverflowError
