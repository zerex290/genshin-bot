import os
from random import randint

from PIL import Image, ImageFont, ImageDraw
from vkbottle_types.objects import GroupsGroupFull

from . import FONT, get_centered_position, round_corners
from ..utils.files import download
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


__all__ = (
    'get_menu_image',
    'get_section_image',
    'get_object_image'
)


def _draw_header_text(draw: ImageDraw.ImageDraw, text: str, indent_x: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 24)
    text = f"{text[:19]}..." if len(text) > 21 else text
    draw.text((indent_x - font.getsize(text)[0]//2, 39), text, (255, 255, 255), font)


def _draw_page_text(draw: ImageDraw.ImageDraw, page_num: int, width: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 28)
    page_num = str(page_num)
    draw.text((width - 44//2, 2), page_num, (255, 255, 255), font, 'ma')


def _paste_page(template: Image.Image, page_num: int) -> None:
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'page.png')) as page:
        _draw_page_text(ImageDraw.Draw(page), page_num, page.width)
        template.alpha_composite(page, (470, 34))


def _draw_category_text(draw: ImageDraw.ImageDraw, category: str, width: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 14)
    draw.text((width // 2, 16), category, (255, 255, 255), font, 'ma')


def _paste_categories(template: Image.Image, categories: list[str]) -> None:
    for i, c in enumerate(categories):
        with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'category.png')) as category:
            _draw_category_text(ImageDraw.Draw(category), c, category.width)
            indent_x = (category.width + 6) * (i % 2)  #: 2 categories in row
            indent_y = (category.height + 6) * (i // 2)
            template.alpha_composite(category, (348 + indent_x, 147 + indent_y))


async def _process_group_avatar(avatar_url: str) -> Image.Image:
    avatar_path = await download(avatar_url, name=f"group_avatar_{randint(0, 10000)}", ext='png')
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'avatar.png')) as template,
        Image.open(avatar_path) as avatar
    ):
        os.remove(avatar_path)

        alpha = Image.new('L', avatar.size, 0)
        ImageDraw.Draw(alpha).ellipse((2, 2, alpha.width - 2, alpha.height - 2), 255)
        avatar = (
            round_corners(avatar, avatar.width // 2)
            .resize((template.width - 20, template.height - 20), Image.ANTIALIAS)  #: Outer border 10px
        )
        avatar.putalpha(alpha.resize(avatar.size, Image.ANTIALIAS))
        template.alpha_composite(avatar, get_centered_position(template.size, avatar.size))
        return template


def _process_section(section_path: str) -> Image.Image:
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'section.png')) as template,
        Image.open(section_path) as section
    ):
        s_w, s_h = section.size
        if s_w > s_h:
            box = (0 + s_w//2 - s_h//2, 0, 0 + s_w//2 + s_h//2, s_h)
        else:
            box = (0, 0 + s_h//2 - s_w//2, s_w, 0 + s_h//2 + s_w//2)
        section = round_corners(
            section.crop(box).resize((template.width - 6, template.height - 6), Image.ANTIALIAS), 10
        )
        template.alpha_composite(section, get_centered_position(template.size, section.size))
        return template


def _paste_sections(template: Image.Image, section_paths: list[str]) -> None:
    for i, s in enumerate(section_paths):
        section = _process_section(s)
        indent_x = (section.width + 8) * (i % 2)  #: 2 categories in row
        indent_y = (section.height + 8) * (i // 2)
        template.alpha_composite(section, (275 + indent_x, 80 + indent_y))


async def _process_object(object_url: str) -> Image.Image:
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'object.png')) as template,
        Image.open(await download(object_url, force=False)) as obj
    ):
        s_w, s_h = obj.size
        if s_w > s_h:
            box = (0 + s_w//2 - s_h//2, 0, 0 + s_w//2 + s_h//2, s_h)
        else:
            box = (0, 0 + s_h//2 - s_w//2, s_w, 0 + s_h//2 + s_w//2)
        obj = round_corners(obj.crop(box).resize((template.width - 6, template.height - 6), Image.ANTIALIAS), 10)
        template.alpha_composite(obj, get_centered_position(template.size, obj.size))
        return template


async def _paste_objects(template: Image.Image, object_urls: list[str]) -> None:
    for i, o in enumerate(object_urls):
        obj = await _process_object(o)
        indent_x = (obj.width + 8) * (i % 2)  #: 2 categories in row
        indent_y = (obj.height + 8) * (i // 2)
        template.alpha_composite(obj, (250 + indent_x, 80 + indent_y))


async def get_menu_image(group: GroupsGroupFull, categories: list[str]) -> str:
    path = os.path.join(FILECACHE, f"menu_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'genshindb.png')) as template:
        _draw_header_text(ImageDraw.Draw(template), 'Меню', template.width // 2)
        template.alpha_composite(await _process_group_avatar(group.photo_200), (144, 126))
        _paste_categories(template, categories)
        template.save(path)
    return path


def get_section_image(section_paths: list[str], page_num: int, category: str) -> str:
    path = os.path.join(FILECACHE, f"section_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'genshindb.png')) as template:
        _draw_header_text(ImageDraw.Draw(template), category, 144 + 326//2)
        _paste_page(template, page_num)
        _paste_sections(template, section_paths)
        template.save(path)
    return path


async def get_object_image(object_urls: list[str], page_num: int, section: str) -> str:
    path = os.path.join(FILECACHE, f"object_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'genshindb', 'genshindb.png')) as template:
        _draw_header_text(ImageDraw.Draw(template), section, 144 + 326//2)
        _paste_page(template, page_num)
        await _paste_objects(template, object_urls)
        template.save(path)
    return path
