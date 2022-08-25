import os
from re import sub
from random import randint
from typing import Optional
from collections.abc import Sequence

from PIL import Image, ImageFont, ImageDraw
from genshin.models import PartialGenshinUserStats, UserInfo, Stats, Teapot, PartialCharacter, Exploration, Offering
from vkbottle_types.objects import UsersUserFull

from . import FONT, round_corners
from ..types.genshin import TeapotComfortNames, Characters, Regions, Offerings
from ..utils.files import download
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


def _draw_summary_text(draw: ImageDraw.ImageDraw, stats: Stats) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 28)
    positions = [
        stats.days_active, stats.achievements, stats.unlocked_waypoints, stats.unlocked_domains, stats.spiral_abyss,
        stats.characters, stats.anemoculi, stats.geoculi, stats.electroculi, '',
        stats.common_chests, stats.exquisite_chests, stats.precious_chests, stats.luxurious_chests, stats.remarkable_chests,
    ]
    for i, p in enumerate(positions):

        indent_x = (144+7) * (i if i < 5 else i % 5)
        indent_y = (100+8) * (i//5)
        draw.text((303 - 4 + indent_x, 34 + 20 + indent_y), str(p), font=font, fill=(255, 255, 255), anchor='ra')


def _draw_teapot_text(draw: ImageDraw.ImageDraw, teapot: Optional[Teapot]) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 28)
    if teapot is None:
        draw.text((471, 380), 'Не открыт', font=font, fill=(255, 255, 255), anchor='ma')
        return None
    comfort_name = TeapotComfortNames[sub(r'[\s-]', '_', teapot.comfort_name).upper()].value
    draw.text((89, 380), comfort_name, font=font, fill=(255, 255, 255))
    bottom_positions = [
        teapot.level, teapot.comfort, teapot.items, teapot.visitors
    ]
    for i, p in enumerate(bottom_positions):
        indent_x = (213+7) * i
        draw.text((34 + 213//2 + indent_x, 419), str(p), font=font, fill=(255, 255, 255), anchor='ma')


def _draw_characters_header_text(draw: ImageDraw.ImageDraw, characters: Sequence[PartialCharacter]) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 28)
    five_star = []
    four_star = []
    max_friendship = []
    for c in characters:
        five_star.append(c) if c.rarity == 5 else four_star.append(c)
        if c.friendship == 10:
            max_friendship.append(c)
    draw.text((177, 522), str(len(five_star)), font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((470, 522), str(len(four_star)), font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((764, 522), str(len(max_friendship)), font=font, fill=(255, 255, 255), anchor='ma')


def _draw_character_text(draw: ImageDraw.ImageDraw, character: PartialCharacter) -> None:
    """Figma sizes + 2px to each width and height"""
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 12)
    lvl = str(character.level)
    name = Characters[character.name.replace(' ', '_').upper()].value
    friendship = str(character.friendship)
    constellation = str(character.constellation)
    draw.text((30, 21), lvl, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((125, 12), name, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((190, 3), friendship, font=font, fill=(255, 255, 255))
    draw.text((190, 20), constellation, font=font, fill=(255, 255, 255))


async def _process_character(character: PartialCharacter) -> Image.Image:
    icon = await download(character.icon, force=False)
    if character.element:
        element = character.element.lower()
    else:
        element = 'none'
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'character.png')) as template,
        Image.open(icon) as icon,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'character_lvl.png')) as lvl,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', f"{element}.png")) as element,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', f"{character.rarity}_star.png")) as rarity
    ):
        icon = round_corners(icon, icon.width // 2).resize((34, 34), Image.ANTIALIAS)
        template.alpha_composite(icon, (2, 2))
        template.alpha_composite(lvl, (19, 19))  #: figma sizes + 1px to w/h
        element = element.resize((26, 26), Image.ANTIALIAS)
        template.alpha_composite(element, (40, 6))  #: figma sizes + 2px to w/h
        template.alpha_composite(rarity, (65, 26))  #: figma sizes - 1px from w/h
        _draw_character_text(ImageDraw.Draw(template), character)
        return template


async def _paste_characters(template: Image.Image, characters: Sequence[PartialCharacter]) -> None:
    for i, c in enumerate(characters):
        character = await _process_character(c)
        indent_x = (213+7) * (i if i < 4 else i % 4)
        indent_y = (34+4) * (i//4)
        template.alpha_composite(character, (32 + indent_x, 584 + indent_y))  #: figma sizes - 2px from w/h


def _draw_exploration_text(draw: ImageDraw.ImageDraw, exploration: Exploration) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 12)
    name = Regions[sub(r"'s|:|-", '', exploration.name).replace(' ', '_').upper()].value
    draw.text((50, 85), f"{exploration.explored}%", (255, 255, 255), font, 'ma')
    draw.text((192, 2), name, (255, 255, 255), font, 'ma')


def _draw_offerings_text(draw: ImageDraw.ImageDraw, offerings: Sequence[Offering]) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 10)
    for i, o in enumerate(offerings):
        indent_y = (20+4) * i
        name = Offerings[sub(r"'s|:|-", '', o.name).replace(' ', '_').upper()].value
        draw.text((120, 42 + indent_y), name, (255, 255, 255), font)
        draw.text((270, 42 + indent_y), str(o.level), (255, 255, 255), font, 'ma')


async def _process_offerings(template: Image.Image, offerings: Sequence[Offering]) -> None:
    for i, o in enumerate(offerings):
        if o.icon:
            icon = await download(o.icon, force=False)
        else:
            icon = os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'reputation.png')
        with Image.open(icon) as icon:
            icon = icon.convert('RGBA').resize((20, 20), Image.ANTIALIAS)
            template.alpha_composite(icon, (100, 38 + (20+4)*i))
    _draw_offerings_text(ImageDraw.Draw(template), offerings)


async def _process_exploration(exploration: Exploration) -> Image.Image:
    icon = await download(exploration.icon, force=False)
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'exploration.png')) as template,
        Image.open(icon) as icon,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'exploration_lvl.png')) as lvl
    ):
        icon = icon.resize((100, 100), Image.ANTIALIAS)
        template.alpha_composite(icon, (0, 0))
        template.alpha_composite(lvl, (16, 80))
        _draw_exploration_text(ImageDraw.Draw(template), exploration)
        await _process_offerings(template, exploration.offerings)
        return template


async def _paste_explorations(template: Image.Image, explorations: Sequence[Exploration], v_indent: int) -> None:
    for i, e in enumerate([e for e in explorations if e.name]):
        exploration = await _process_exploration(e)
        indent_x = (285+9) * (i if i < 3 else i % 3)
        indent_y = (100+4) * (i//3)
        template.alpha_composite(exploration, (34 + indent_x, v_indent + indent_y))


def _draw_user_avatar_text(draw: ImageDraw.ImageDraw, info: UserInfo) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 20)  #: for level
    draw.text((82, 5), str(info.level), font=font, fill=(255, 255, 255), anchor='ma')
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 14)  #: for nickname
    draw.text((50, 80), info.nickname, font=font, fill=(255, 255, 255), anchor='ma')


async def _process_user_avatar(info: UserInfo, avatar_url: str, b_size: int) -> Image.Image:
    avatar_path = await download(avatar_url, name=f"avatar_{randint(0, 10000)}", ext='png')
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'avatar_back.png')) as template,
        Image.open(avatar_path) as avatar,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'avatar_front.png')) as front
    ):
        os.remove(avatar_path)
        avatar = round_corners(avatar, avatar.width // 2).resize((100 - b_size, 100 - b_size), Image.ANTIALIAS)
        template.paste(avatar, (b_size // 2, b_size // 2), mask=avatar)
        template.alpha_composite(front, (-1, 0))
        _draw_user_avatar_text(ImageDraw.Draw(template), info)
        return template


async def _paste_user_avatar(template: Image.Image, info: UserInfo, avatar_url: str) -> None:
    avatar = await _process_user_avatar(info, avatar_url, 15)
    template.alpha_composite(avatar, (34, 34))


async def get_stats_image(stats: PartialGenshinUserStats, user: UsersUserFull) -> str:
    path = os.path.join(FILECACHE, f"stats_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'stats', 'stats.png')) as template:
        draw = ImageDraw.Draw(template)
        await _paste_user_avatar(template, stats.info, user.photo_200)
        _draw_summary_text(draw, stats.stats)
        _draw_teapot_text(draw, stats.teapot)
        _draw_characters_header_text(draw, stats.characters)
        await _paste_characters(template, stats.characters)
        v_indent = 586 + (34+4)*(len(stats.characters)//4 + 1 if len(stats.characters) % 4 != 0 else 0) + 25
        await _paste_explorations(template, stats.explorations, v_indent)
        v_indent += (100+4)*(len(stats.explorations)//3 + 1 if len(stats.explorations) % 3 != 0 else 0) + 34
        template = template.crop((0, 0, template.width, v_indent))
        template.save(path)
    return path
