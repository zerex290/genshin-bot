import os
from collections.abc import AsyncIterator
from random import randint
from typing import Optional

from PIL import Image, ImageFont, ImageDraw

from .. import FONT, align_center, resize, round_image, get_template_path
from ...types.uncategorized import Weekday
from ...parsers.honeyimpact import DailyFarmParser, TalentBookParser, BossMaterialParser
from ...utils.files import download
from ...models.honeyimpact.dailyfarm import Material, Consumer, Zone
from ...models.honeyimpact.talentbooks import TalentBook
from ...models.honeyimpact.bossmaterials import Boss
from ...config.dependencies.paths import FILECACHE


__all__ = (
    'DailyFarmImageGenerator',
    'TalentBookImageGenerator',
    'BossMaterialImageGenerator'
)


class DailyFarmImageGenerator:
    def __init__(self, weekdays: list[int]) -> None:
        self.weekdays = weekdays
        self._cpx_h = 102  #: zone.indent_v = 102

    async def generate(self) -> list[str]:
        paths = []
        zones = await DailyFarmParser.get_zones()
        for weekday in self.weekdays:
            path = os.path.join(FILECACHE, f"dailyfarm_{randint(0, 10000)}.png")
            with Image.open(get_template_path(__file__, 'dailyfarm', 'dailyfarm')) as template:
                draw = ImageDraw.Draw(template)
                self._draw_weekday_text(draw, weekday)
                for zone in zones:
                    await self._paste_zone(template, zone, weekday)
                    self._cpx_h += 48  #: 48 = 44 + 4 = zone.height + const
                    for c_num, c in enumerate([c for c in zone.consumers if weekday in c.weekdays and c.rarity > 3]):
                        await self._paste_consumer(template, c, c_num)
                    self._cpx_h += 110 + 110*(c_num // 8)  #: 110 = consumer.height + consumer.indent_h
                template.crop((0, 0, template.width, self._cpx_h + 24)).save(path)
                paths.append(path)
                self._cpx_h = 102
        return paths

    @staticmethod
    def _draw_weekday_text(draw: ImageDraw.ImageDraw, weekday: int) -> None:
        font = ImageFont.truetype(FONT, 20)
        weekdays = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье')
        draw.text((471, 39), weekdays[weekday], (255, 255, 255), font, 'ma')

    @staticmethod
    async def _process_materials(materials: list[Material]) -> AsyncIterator[tuple[int, Image.Image]]:
        for i, material in enumerate(materials):
            with (
                Image.open(get_template_path(__file__, 'dailyfarm', 'material')) as template,
                Image.open(await download(material.icon, force=False)) as icon
            ):
                align_center(template, resize(icon, template.size))
                yield i, template

    async def _process_zone(self, zone: Zone, weekday: int) -> Image.Image:
        materials = [m for m in zone.materials if m.weekday == weekday]
        with Image.open(get_template_path(__file__, 'dailyfarm', 'zone')) as template:
            w = template.width
            async for i, material in self._process_materials(materials):
                indent_x = material.width + 8
                template.alpha_composite(material, ((w - indent_x*len(materials))//2 + i*indent_x, 0))
            return template

    async def _paste_zone(self, template: Image.Image, zone: Zone, weekday: int) -> None:
        template.alpha_composite(await self._process_zone(zone, weekday), (34, self._cpx_h))

    @staticmethod
    async def _process_consumer(consumer: Consumer) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'dailyfarm', 'consumer')) as template,
            Image.open(await download(consumer.icon, force=False)) as icon,
            Image.open(get_template_path(__file__, 'dailyfarm', f"{consumer.rarity}_star")) as stars
        ):
            align_center(template, round_image(resize(icon, template.size), 40))
            template.alpha_composite(stars, (0, 0))
            return template

    async def _paste_consumer(self, template: Image.Image, consumer: Consumer, c_num: int) -> None:
        c = await self._process_consumer(consumer)
        w, h = c.size
        indent = 10
        template.alpha_composite(c, (34 + (w + indent)*(c_num % 8), self._cpx_h + (h + indent)*(c_num // 8)))


class TalentBookImageGenerator:
    def __init__(self) -> None:
        self._indent_x = 0
        self._cpx_h = [97, 97, 97]
        self._row = 0
        self.talent_books: Optional[list[TalentBook]] = None

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"talentbooks_{randint(0, 10000)}.png")
        self.talent_books = await TalentBookParser.get_related_talent_books()
        with Image.open(get_template_path(__file__, 'talentbooks', 'talentbooks')) as template:
            for book in self.talent_books:
                if Weekday.MONDAY in book.weekdays:
                    self._row = 0
                    self._indent_x = 34
                elif Weekday.TUESDAY in book.weekdays:
                    self._row = 1
                    self._indent_x = 594
                else:
                    self._row = 2
                    self._indent_x = 1154
                await self._paste_talent_book_info(template, book)
            template.crop((0, 0, template.width, max(self._cpx_h))).save(path)
        return path

    async def _paste_talent_book_info(self, template: Image.Image, b: TalentBook) -> None:
        """Paste talent book icon with its consumers."""
        book = self._process_talent_book(await download(b.icon, force=False))
        template.alpha_composite(book, (self._indent_x, self._cpx_h[self._row]))
        await self._paste_characters(template, b, book.width)
        self._cpx_h[self._row] += book.height + (24 if b != self.talent_books[-1] else 34)

    @staticmethod
    def _process_talent_book(book_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'talentbooks', 'book')) as template,
            Image.open(book_path) as book
        ):

            align_center(template, round_image(resize(book, template.size), 20))
            return template

    async def _paste_characters(self, template: Image.Image, b: TalentBook, b_width: int) -> None:
        gap = 8
        for ch_num, icon in enumerate(b.used_by):
            character = self._process_character(await download(icon, force=False))
            x = self._indent_x + b_width + gap + (character.width + gap)*(ch_num // 2)
            y = self._cpx_h[self._row] + (character.height + gap)*(ch_num % 2)
            template.alpha_composite(character, (x, y))

    @staticmethod
    def _process_character(character_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'talentbooks', 'character')) as template,
            Image.open(character_path) as character
        ):
            align_center(template, round_image(resize(character, template.size), 15))
            return template


class BossMaterialImageGenerator:
    def __init__(self):
        self._indent_x = 0
        self._cpx_h = 34
        self.bosses: Optional[list[Boss]] = None

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"bossmaterials_{randint(0, 10000)}.png")
        gap = 8
        self.bosses = BossMaterialParser.get_related_bosses()
        with Image.open(get_template_path(__file__, 'bossmaterials', 'bossmaterials')) as template:
            for boss in self.bosses:
                await self._paste_boss_info(template, boss, gap)
                self._cpx_h += (gap * 3 if boss != self.bosses[-1] else 34)
            template.crop((0, 0, template.width, self._cpx_h)).save(path)
        return path

    async def _paste_boss_info(self, template: Image.Image, b: Boss, gap: int) -> None:
        """Paste boss with its materials and characters."""
        boss = self._process_boss(await download(b.icon, force=False))
        template.alpha_composite(boss, (34, self._cpx_h))
        for m in b.materials:
            self._indent_x = 34 + boss.width + gap*2
            material = self._process_boss_material(await download(m.icon, force=False))
            template.alpha_composite(material, (self._indent_x, self._cpx_h))
            self._indent_x += material.width + gap
            await self._paste_characters(template, m.used_by, gap)
            self._cpx_h += material.height + (gap if m != b.materials[-1] else 0)

    @staticmethod
    def _process_boss(boss_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'bossmaterials', 'boss')) as template,
            Image.open(boss_path) as boss
        ):
            align_center(template, round_image(resize(boss, template.size), 20))
            return template

    @staticmethod
    def _process_boss_material(material_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'bossmaterials', 'material')) as template,
            Image.open(material_path) as material
        ):
            align_center(template, round_image(resize(material, template.size), 10))
            return template

    async def _paste_characters(self, template: Image.Image, icons: list[str], gap: int) -> None:
        for icon in icons:
            character = self._process_character(await download(icon, force=False))
            template.alpha_composite(character, (self._indent_x, self._cpx_h))
            self._indent_x += character.width + gap

    @staticmethod
    def _process_character(character_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'bossmaterials', 'character')) as template,
            Image.open(character_path) as character
        ):
            align_center(template, round_image(resize(character, template.size), 10))
            return template
