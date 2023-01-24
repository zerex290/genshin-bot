import os
from random import randint
from typing import Literal

from PIL import Image, ImageFont, ImageDraw

from . import FONT, get_centered_position, get_scaled_size, round_corners
from ..utils.files import download
from ..models.honeyimpact.characters import Ascension, AscensionMaterial
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


def _draw_character_text(draw: ImageDraw.ImageDraw, character: str, width: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    draw.text((width // 2, 5), character, (255, 255, 255), font, 'ma')


async def _process_character(character: str, icon: str) -> Image.Image:
    icon = await download(icon, force=False)
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'ascension', 'character_back.png')) as template,
        Image.open(icon) as icon,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'ascension', 'character_front.png')) as front
    ):
        icon = round_corners(icon.resize(get_scaled_size('w', template.width, icon.size), Image.ANTIALIAS), 20)
        template.alpha_composite(icon, (0, template.height - icon.height))
        _draw_character_text(ImageDraw.Draw(front), character, front.width)
        template.alpha_composite(front, (0, template.height - front.height - 20))
        return template


def _draw_material_text(draw: ImageDraw.ImageDraw, quantity: int, width: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    draw.text((width // 2, 0), str(quantity), (255, 255, 255), font, 'ma')


async def _process_material(material: AscensionMaterial) -> Image.Image:
    icon = await download(material.icon, force=False)
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'ascension', 'material_back.png')) as template,
        Image.open(icon) as icon,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'ascension', 'material_front.png')) as front
    ):
        if icon.width > icon.height:
            icon = round_corners(icon.resize(get_scaled_size('w', template.width, icon.size), Image.ANTIALIAS), 15)
        else:
            icon = round_corners(icon.resize(get_scaled_size('h', template.width, icon.size), Image.ANTIALIAS), 15)
        template.alpha_composite(icon, get_centered_position(template.size, icon.size))
        _draw_material_text(ImageDraw.Draw(front), material.quantity, template.width)
        template.alpha_composite(front, (0, template.height - front.height - 15))
        return template


async def _paste_materials(
        template: Image.Image,
        material_type: Literal['lvl', 'talent'],
        materials: list[AscensionMaterial]
) -> None:
    w0, h0 = (225, 79) if material_type == 'lvl' else (550, 79)
    for i, m in enumerate(materials):
        material = await _process_material(m)
        indent_x = (5 + material.width)*(i if i < 3 else i % 3)
        indent_y = (5 + material.height)*(i//3)
        template.alpha_composite(material, (w0 + indent_x, h0 + indent_y))


async def get_ascension_image(character: str, ascension: Ascension) -> str:
    path = os.path.join(FILECACHE, f"ascension_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'ascension', 'ascension.png')) as template:
        template.alpha_composite(await _process_character(character, ascension.gacha_icon), (34, 34))
        await _paste_materials(template, 'lvl', ascension.lvl)
        await _paste_materials(template, 'talent', ascension.talents)
        template.save(path)
    return path
