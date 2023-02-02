from typing import Optional

from ...models.honeyimpact import domains


def format_information(domain: Optional[domains.Information]) -> str:
    if domain is None:
        return 'Информация пока отсутствует!'

    return (
        f"🖼Основная информация:\n"
        f"⚔Подземелье: {domain.name}\n"
        f"⚙Тип: {domain.type}\n"
        f"📖Описание: {domain.description}"
    )
