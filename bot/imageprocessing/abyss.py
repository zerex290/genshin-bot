"""Module for building a spiral abyss image with data of certain user"""

import os
from random import randint
from typing import Sequence

from PIL import Image, ImageFont, ImageDraw
from genshin.models import SpiralAbyss, Floor, Chamber, Battle, AbyssCharacter

from bot.imageprocessing import FONT, cache_icon
from bot.config.dependencies.paths import IMAGE_PROCESSING, FILECACHE


def _draw_floor_text(draw: ImageDraw.ImageDraw, floor_number: int, floor: Floor, chamber_number: int) -> None:
    """Draws text of the certain floor to the image template

    Width calculations:
        - 250 -> indent of floor text box center
        - 500 -> indent between floors

    Height calculations:
        - 9 -> indent of floor text box
        - 400 -> indent between chambers

    :param draw: An image to draw in
    :param floor_number: Number of floor in the sequence
    :param floor: One of last four floors in the certain spiral abyss
    :param chamber_number: Number of chamber in the sequence
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 26)
    draw.text(
        (250 + 500*floor_number, 9 + 400*chamber_number),
        'Этаж {}'.format(floor.floor),
        font=font,
        fill=(255, 255, 255),
        anchor='mt'
    )


def _draw_chamber_text(draw: ImageDraw.ImageDraw, floor_number: int, chamber_number: int, chamber: Chamber) -> None:
    """Draws text of the certain chamber to the image template

    Width calculations:
        - 250 -> indent of chamber text box center
        - 500 -> indent between floors

    Height calculations:
        - 50 -> indent of chamber text box
        - 400 -> indent between chambers

    :param draw: An image to draw in
    :param floor_number: Number of floor in the sequence
    :param chamber_number: Number of chamber in the sequence
    :param chamber: One of the three chambers at the certain floor
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 18)
    draw.text(
        (250 + 500*floor_number, 50 + 400*chamber_number),
        'Зал {} | {}/{}* | {}'
        .format(chamber.chamber, chamber.stars, chamber.max_stars, chamber.battles[0].timestamp.strftime('%d.%m.%Y')),
        font=font,
        fill=(255, 255, 255),
        anchor='mt'
    )


def _draw_half_text(
        draw: ImageDraw.ImageDraw,
        floor_number: int,
        chamber_number: int,
        battle_number: int,
        battle: Battle
) -> None:
    """Draws text of the certain battle-half to the image template

    Width calculations:
        - 132.5 -> indent of first-half text box center
        - 235 -> indent between centers of first-half and second-half text boxes
        - 500 -> indent between floors

    Height calculations:
        - 91 -> indent of battle-half text box
        - 400 -> indent between chambers

    :param draw: An image to draw in
    :param floor_number: Number of floor in the sequence
    :param chamber_number: Number of chamber in the sequence
    :param battle_number: Number of battle in the sequence
    :param battle: One of the two battles at the certain chamber
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 20)
    draw.text(
        (132.5 + 235*battle_number + 500*floor_number, 91 + 400*chamber_number),
        '{} половина'.format(battle.half),
        font=font,
        fill=(255, 255, 255),
        anchor='mt'
    )


def _paste_character(
        template: Image.Image,
        floor_number: int,
        chamber_number: int,
        battle_number: int,
        character_number: int,
        character: AbyssCharacter
) -> None:
    """Pastes certain character to the image template.

    Width calculations:
        - 500 -> indent between floors
        - 235 -> value calculated by subtraction of
    indent of first character's icon box (32) from indent of second character's icon box (267)
        - 96 -> optimal width coordinate to resize base 256x256 character icons

    Height calculations:
        - 400 -> indent between chambers
        - 218 -> indent of first/second character's icon box
        - 346 -> indent of third/fourth character's icon box
        - 96 -> optimal height coordinate to resize base 256x256 character icons

    :param template: Template of the background image
    :param floor_number: Number of floor in the sequence
    :param chamber_number: Number of chamber in the sequence
    :param battle_number: Number of battle in the sequence
    :param character_number: Number of character in the sequence
    :param character: One of the four spiral abyss characters used at certain half of battle
    """
    with Image.open(os.path.join(FILECACHE, character.icon.rsplit('/', maxsplit=1)[1])) as icon:
        icon = icon.resize((96, 96))
        ident_x = 32 if character_number % 2 == 0 else 137
        ident_y = 218 - icon.height if character_number < 2 else 346 - icon.height
        template.paste(
            icon,
            (500*floor_number + 235*battle_number + ident_x, 400*chamber_number + ident_y),
            mask=icon
        )


def _draw_character_level(
    draw: ImageDraw.ImageDraw,
    floor_number: int,
    chamber_number: int,
    battle_number: int,
    character_number: int,
    character: AbyssCharacter
) -> None:
    """Draws text of level of the certain character

    Width calculations:
        - 500 -> indent between floors
        - 235 -> value calculated by subtraction of
    indent of first character's icon box (32) from indent of second character's icon box (267)
        - 80 -> indent of first/second character's icon box center
        - 185 -> indent of second/fourth character's icon box center

    Height calculations:
        - 400 -> indent between chambers
        - 226 -> indent of first/second character's level text box
        - 354 -> indent of third/fourth character's level text box

    :param draw: An image to draw in
    :param floor_number: Number of floor in the sequence
    :param chamber_number: Number of chamber in the sequence
    :param battle_number: Number of battle in the sequence
    :param character_number: Number of character in the sequence
    :param character: One of the four spiral abyss characters used at certain half of battle
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 18)
    ident_x = 80 if character_number % 2 == 0 else 185
    ident_y = 226 if character_number < 2 else 354
    draw.text(
        (500*floor_number + 235*battle_number + ident_x, 400*chamber_number + ident_y),
        'Лвл {}'.format(character.level),
        font=font,
        fill=(255, 255, 255),
        anchor='mt'
    )


def _paste_character_stars(
    template: Image.Image,
    floor_number: int,
    chamber_number: int,
    battle_number: int,
    character_number: int,
    character: AbyssCharacter
) -> None:
    """Pastes a certain character rarity stars to the image template

    Width calculations:
        - 500 -> indent between floors
        - 235 -> value calculated by subtraction of
    indent of first character's icon box (32) from indent of second character's icon box (267)
        - 32 -> indent of first/third character's icon box
        - 137 -> indent of second/fourth character's icon box
        - 96 -> character icon box width without its borders

    Height calculations:
        - 400 -> indent between chambers
        - 218 -> indent of first/second character's icon box
        - 346 -> indent of third/fourth character's icon box

    :param template: Template of the background image
    :param floor_number:  Number of floor in the sequence
    :param chamber_number:  Number of chamber in the sequence
    :param battle_number:  Number of battle in the sequence
    :param character_number:  Number of character in the sequence
    :param character:  One of the four spiral abyss characters used at certain half of battle
    """
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'abyss', 'star.png')) as star:
        ident_x = 32 if character_number % 2 == 0 else 137
        ident_y = 218 - star.height//2 if character_number < 2 else 346 - star.height//2
        for s in range(character.rarity):
            template.paste(
                star,
                (500*floor_number + 235*battle_number + ident_x + 96//character.rarity*s, 400*chamber_number + ident_y),
                mask=star
            )


async def _process_image_parts(template: Image.Image, floors: Sequence[Floor]) -> None:
    """Iter through spiral abyss floors and add element to the image template

    :param template: Template of the background image
    :param floors: Sequence with spiral abyss floors
    """
    draw = ImageDraw.Draw(template)
    for f_num, f in enumerate(floors):
        for c_num, c in enumerate(f.chambers):
            _draw_floor_text(draw, f_num, f, c_num)
            _draw_chamber_text(draw, f_num, c_num, c)
            for b_num, b in enumerate(c.battles):
                _draw_half_text(draw, f_num, c_num, b_num, b)
                for ch_num, ch in enumerate(b.characters):
                    await cache_icon(ch.icon)
                    _paste_character(template, f_num, c_num, b_num, ch_num, ch)
                    _draw_character_level(draw, f_num, c_num, b_num, ch_num, ch)
                    _paste_character_stars(template, f_num, c_num, b_num, ch_num, ch)


async def get_abyss_image(abyss: SpiralAbyss) -> str:
    """Process abyss image template, save it and return its path

    :param abyss: Spiral abyss data of certain user
    :return: Path to saved image
    """
    path = os.path.join(FILECACHE, f"abyss_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'abyss', 'abyss.png')) as template:
        await _process_image_parts(template, abyss.floors)
        template.save(path)
    return path
