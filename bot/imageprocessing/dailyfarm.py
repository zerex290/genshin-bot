import os
from collections.abc import AsyncIterator
from random import randint

from PIL import Image, ImageFont, ImageDraw

from . import FONT, get_centered_position, get_scaled_size, round_corners
from ..parsers.honeyimpact import DailyFarmParser
from ..utils.files import download
from ..models.honeyimpact.dailyfarm import Material, Consumer, Zone
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


def _draw_weekday_text(draw: ImageDraw.ImageDraw, weekday: int) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 20)
    weekdays = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье')
    draw.text((471, 39), weekdays[weekday], (255, 255, 255), font, 'ma')


async def _process_materials(materials: list[Material], weekday: int) -> AsyncIterator[Image.Image]:
    for material in materials:
        with (
            Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'dailyfarm', 'material.png')) as template,
            Image.open(await download(material.icon, force=False)) as icon
        ):
            if icon.width > icon.height:
                icon = icon.resize(get_scaled_size('w', 44, icon.size), Image.ANTIALIAS)
            else:
                icon = icon.resize(get_scaled_size('h', 44, icon.size), Image.ANTIALIAS)
            template.alpha_composite(icon, get_centered_position(template.size, icon.size))
            yield template


async def _process_zone(zone: Zone, weekday: int) -> Image.Image:
    materials = [m for m in zone.materials if m.weekday == weekday]
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'dailyfarm', 'zone.png')) as template:
        indent_x = (template.width-(44+8)*len(materials)) // 2
        i = 0
        async for material in _process_materials(materials, weekday):
            template.alpha_composite(material, (indent_x + 3 + i*(44+8), -5))
            i += 1
        return template


async def _paste_zone(template: Image.Image, zone: Zone, weekday: int, cpx_h: int) -> None:
    template.alpha_composite(await _process_zone(zone, weekday), (34, cpx_h))


async def _process_consumer(consumer: Consumer) -> Image.Image:
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'dailyfarm', 'consumer.png')) as template,
        Image.open(await download(consumer.icon, force=False)) as icon,
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'dailyfarm', f"{consumer.rarity}_star.png")) as rarity
    ):
        if icon.width > icon.height:
            icon = round_corners(icon.resize(get_scaled_size('w', 100, icon.size), Image.ANTIALIAS), 40)
        else:
            icon = round_corners(icon.resize(get_scaled_size('h', 100, icon.size), Image.ANTIALIAS), 40)
        template.alpha_composite(icon, get_centered_position(template.size, icon.size))
        template.alpha_composite(rarity, (1, 3))
        return template


async def _paste_consumer(template: Image.Image, consumer: Consumer, c_num: int, cpx_h: int):
    indent_x = 35 + 110*(c_num if c_num < 8 else c_num % 8)
    indent_y = cpx_h + 106*(c_num//8)
    template.alpha_composite(await _process_consumer(consumer), (indent_x, indent_y))


async def get_dailyfarm_images(weekdays: list[int]) -> list[str]:
    paths = []
    zones = await DailyFarmParser.get_zones()
    for weekday in weekdays:
        path = os.path.join(FILECACHE, f"dailyfarm_{randint(0, 10000)}.png")
        with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'dailyfarm', 'dailyfarm.png')) as template:
            draw = ImageDraw.Draw(template)
            _draw_weekday_text(draw, weekday)
            cpx_h = 102
            for zone in zones:
                await _paste_zone(template, zone, weekday, cpx_h)
                cpx_h += 44 + 4
                for c_num, consumer in enumerate([c for c in zone.consumers if weekday in c.weekdays and c.rarity > 3]):
                    await _paste_consumer(template, consumer, c_num, cpx_h)
                cpx_h += 4 + 106 + 106*(c_num//8)
            template.crop((0, 0, template.width, cpx_h + 27)).save(path)
            #: I have no idea why 27, but it eventually matches lower border 34 pixels
            paths.append(path)
    return paths
