import re
from typing import List

from bot.src.models.sankaku import TagType, Tag
from bot.config.dependencies.group import SHORTNAME


def _prettify_tag(tag: str) -> str:
    tag = re.sub(r'[!@#№$%^&*-+:;"\'{}\[\]<,>.?/\\|]', '', tag)
    return tag[:tag.find('_(')] if tag.find('_(') != -1 else tag


def format_post_message(donut: bool, tags: List[Tag]) -> str:
    match donut:
        case True:
            character = [_prettify_tag(tag.name_en) for tag in tags if tag.type == TagType.CHARACTER]
            copyright_ = [_prettify_tag(tag.name_en) for tag in tags if tag.type == TagType.COPYRIGHT]
            artist = [tag.name_en for tag in tags if tag.type == TagType.ARTIST]
            general = ['\n' + _prettify_tag(tag.name_en) for tag in tags if tag.type == TagType.GENERAL]
            formatted_post_message = (
                f"Art\n"
                f"Копирайт: {', '.join(copyright_)}\n"
                f"Художники: {', '.join(artist)}\n"
                f"Персонажи: {', '.join(character)}\n\n"
                f"Дополнительные теги:{''.join(general)}"
            )
            return formatted_post_message
        case False:
            character = [f"#{_prettify_tag(tag.name_en)}{SHORTNAME}" for tag in tags if tag.type == TagType.CHARACTER]
            copyright_ = [f"#{_prettify_tag(tag.name_en)}{SHORTNAME}" for tag in tags if tag.type == TagType.COPYRIGHT]
            artist = [f"#{_prettify_tag(tag.name_en)}{SHORTNAME}" for tag in tags if tag.type == TagType.ARTIST]

            formatted_post_message = (
                f"#Art{SHORTNAME}\n"
                f"Копирайт: {', '.join(copyright_)}\n"
                f"Художники: {', '.join(artist)}\n"
                f"Персонажи: {', '.join(character)}"
            )
            return formatted_post_message


def format_source(source: str) -> str:
    if source.find('i.pximg.net') != 1:
        pixiv_id = source.rsplit('/', maxsplit=1)[-1].split('_')[0]
        return f"https://www.pixiv.net/en/artworks/{pixiv_id}"
    return source
