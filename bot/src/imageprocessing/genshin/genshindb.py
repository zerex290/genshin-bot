import os
import re
from random import randint
from typing import Literal, List, Dict

from PIL import Image, ImageFont, ImageDraw
from vkbottle_types.objects import GroupsGroupFull

from .. import FONT, align_center, resize, round_image, get_template_path
from ...utils.files import download
from ...models import honeyimpact as mdl
from ...config.dependencies.paths import FILECACHE


__all__ = (
    'MenuImageGenerator',
    'SectionImageGenerator',
    'ObjectImageGenerator',
    'AscensionImageGenerator',
    'DomainImageGenerator',
    'WeaponProgressionImageGenerator',
    'EnemyDropImageGenerator',
    'EnemyProgressionImageGenerator'
)


class ImageGeneratorMixin:
    page_num: int

    @staticmethod
    def _draw_header_text(draw: ImageDraw.ImageDraw, text: str, indent_x: int) -> None:
        font = ImageFont.truetype(FONT, 24)
        text = f"{text[:19]}..." if len(text) > 21 else text
        draw.text((indent_x - font.getsize(text)[0]//2, 39), text, (255, 255, 255), font)

    def _draw_page_text(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        font = ImageFont.truetype(FONT, 28)
        page_num = str(self.page_num)
        draw.text((width - 44//2, 2), page_num, (255, 255, 255), font, 'ma')

    def _paste_page(self, template: Image.Image) -> None:
        with Image.open(get_template_path(__file__, 'genshindb', 'page')) as page:
            self._draw_page_text(ImageDraw.Draw(page), page.width)
            template.alpha_composite(page, (470, 34))


class MenuImageGenerator(ImageGeneratorMixin):
    def __init__(self, categories: List[str], group: GroupsGroupFull) -> None:
        self.categories = categories
        self.group = group

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"menu_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'genshindb', 'genshindb')) as template:
            self._draw_header_text(ImageDraw.Draw(template), 'Меню', template.width // 2)
            template.alpha_composite(await self._process_group_avatar(), (144, 126))
            self._paste_categories(template)
            template.save(path)
        return path

    async def _process_group_avatar(self) -> Image.Image:
        avatar_path = await download(self.group.photo_200, name=f"group_avatar_{randint(0, 10000)}", ext='png')
        with (
            Image.open(get_template_path(__file__, 'genshindb', 'avatar')) as template,
            Image.open(avatar_path) as avatar
        ):
            os.remove(avatar_path)

            alpha = Image.new('L', avatar.size, 0)
            ImageDraw.Draw(alpha).ellipse((2, 2, alpha.width - 2, alpha.height - 2), 255)
            avatar = resize(avatar, (template.width - 20, template.height - 20))
            avatar = round_image(avatar, avatar.width // 2)
            avatar.putalpha(alpha.resize(avatar.size))
            align_center(template, avatar)
            return template

    @staticmethod
    def _draw_category_text(draw: ImageDraw.ImageDraw, category: str, width: int) -> None:
        font = ImageFont.truetype(FONT, 14)
        draw.text((width // 2, 16), category, (255, 255, 255), font, 'ma')

    def _paste_categories(self, template: Image.Image) -> None:
        for i, c in enumerate(self.categories):
            with Image.open(get_template_path(__file__, 'genshindb', 'category')) as category:
                self._draw_category_text(ImageDraw.Draw(category), c, category.width)
                indent_x = (category.width + 6) * (i % 2)  #: 2 categories in row
                indent_y = (category.height + 6) * (i // 2)
                template.alpha_composite(category, (348 + indent_x, 147 + indent_y))


class SectionImageGenerator(ImageGeneratorMixin):
    def __init__(self, section_paths: List[str], page_num: int, category: str) -> None:
        self.section_paths = section_paths
        self.page_num = page_num
        self.category = category

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"section_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'genshindb', 'genshindb')) as template:
            self._draw_header_text(ImageDraw.Draw(template), self.category, 144 + 326//2)
            self._paste_page(template)
            self._paste_sections(template)
            template.save(path)
        return path

    @staticmethod
    def _process_section(section: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'genshindb', 'section')) as template,
            Image.open(get_template_path(__file__, 'genshindb', section)) as section
        ):
            s_w, s_h = section.size
            if s_w > s_h:
                box = (0 + s_w//2 - s_h//2, 0, 0 + s_w//2 + s_h//2, s_h)
            else:
                box = (0, 0 + s_h//2 - s_w//2, s_w, 0 + s_h//2 + s_w//2)
            section = round_image(resize(section.crop(box), (template.width - 6, template.height - 6)), 10)
            align_center(template, section)
            return template

    def _paste_sections(self, template: Image.Image) -> None:
        for i, s in enumerate(self.section_paths):
            section = self._process_section(s)
            indent_x = (section.width + 8) * (i % 2)  #: 2 categories in row
            indent_y = (section.height + 8) * (i // 2)
            template.alpha_composite(section, (275 + indent_x, 80 + indent_y))


class ObjectImageGenerator(ImageGeneratorMixin):
    def __init__(self, object_urls: List[str], page_num: int, section: str) -> None:
        self.object_urls = object_urls
        self.page_num = page_num
        self.section = section

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"object_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'genshindb', 'genshindb')) as template:
            self._draw_header_text(ImageDraw.Draw(template), self.section, 144 + 326//2)
            self._paste_page(template)
            await self._paste_objects(template)
            template.save(path)
        return path

    @staticmethod
    async def _process_object(object_url: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'genshindb', 'object')) as template,
            Image.open(await download(object_url, force=False)) as obj
        ):
            s_w, s_h = obj.size
            if s_w > s_h:
                box = (0 + s_w//2 - s_h//2, 0, 0 + s_w//2 + s_h//2, s_h)
            else:
                box = (0, 0 + s_h//2 - s_w//2, s_w, 0 + s_h//2 + s_w//2)
            obj = round_image(resize(obj.crop(box), (template.width - 6, template.height - 6)), 10)
            align_center(template, obj)
            return template

    async def _paste_objects(self, template: Image.Image) -> None:
        for i, o in enumerate(self.object_urls):
            obj = await self._process_object(o)
            indent_x = (obj.width + 8) * (i % 2)  #: 2 categories in row
            indent_y = (obj.height + 8) * (i // 2)
            template.alpha_composite(obj, (250 + indent_x, 80 + indent_y))


class AscensionImageGenerator:
    def __init__(self, character: str, ascension: mdl.characters.Ascension) -> None:
        self.character = character
        self.ascension = ascension

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"ascension_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'ascension', 'ascension')) as template:
            template.alpha_composite(await self._process_character(), (34, 34))
            await self._paste_materials(template, 'lvl', self.ascension.lvl)
            await self._paste_materials(template, 'talent', self.ascension.talents)
            template.save(path)
        return path

    def _draw_character_text(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((width // 2, 5), self.character, (255, 255, 255), font, 'ma')

    async def _process_character(self) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'ascension', 'character_back')) as template,
            Image.open(await download(self.ascension.gacha_icon, force=False)) as icon,
            Image.open(get_template_path(__file__, 'ascension', 'character_front')) as front
        ):
            icon = round_image(resize(icon, template.size), 20)
            template.alpha_composite(icon, (0, template.height - icon.height))
            self._draw_character_text(ImageDraw.Draw(front), front.width)
            template.alpha_composite(front, (0, template.height - front.height - 20))
            return template

    @staticmethod
    def _draw_material_text(draw: ImageDraw.ImageDraw, quantity: int, width: int) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((width // 2, 0), str(quantity), (255, 255, 255), font, 'ma')

    async def _process_material(self, material: mdl.characters.AscensionMaterial) -> Image.Image:
        icon = await download(material.icon, force=False)
        with (
            Image.open(get_template_path(__file__, 'ascension', 'material_back')) as template,
            Image.open(icon) as icon,
            Image.open(get_template_path(__file__, 'ascension', 'material_front')) as front
        ):
            align_center(template, round_image(resize(icon, template.size), 15))
            self._draw_material_text(ImageDraw.Draw(front), material.quantity, template.width)
            template.alpha_composite(front, (0, template.height - front.height - 15))
            return template

    async def _paste_materials(
            self,
            template: Image.Image,
            material_type: Literal['lvl', 'talent'],
            materials: List[mdl.characters.AscensionMaterial]
    ) -> None:
        w0, h0 = (225, 79) if material_type == 'lvl' else (550, 79)
        for i, m in enumerate(materials):
            material = await self._process_material(m)
            indent_x = (5 + material.width)*(i % 3)
            indent_y = (5 + material.height)*(i // 3)
            template.alpha_composite(material, (w0 + indent_x, h0 + indent_y))


class DomainImageGenerator:
    def __init__(self, cover_url: str, monsters: List[str], rewards: List[str]) -> None:
        self.cover_url = cover_url
        self.monsters = monsters
        self.rewards = rewards
        self._cpx_h = 246  #: distance from bg top to material top at first row

    async def generate(self) -> str:
        gap = 6

        path = os.path.join(FILECACHE, f"domain_{randint(0, 10000)}.png")
        with (
            Image.open(get_template_path(__file__, 'domains', 'domains')) as template,
            Image.open(await download(self.cover_url, force=False)) as cover
        ):
            b_size = 4
            cover = resize(cover, (316 - b_size*2, 316 - b_size*2))
            cover = resize(cover, (316 - b_size*2, 316 - b_size*2))
            template.alpha_composite(round_image(cover, 20), (187 + b_size, 34 + b_size // 2))
            rewards = [await self._process_icon(icon) for icon in self.rewards]
            monsters = [await self._process_icon(icon) for icon in self.monsters]
            self._paste_icons(template, rewards, 34, gap)
            self._paste_icons(template, monsters, 350, gap)
            mul = max(len(rewards), len(monsters))
            icon_h = rewards[0].height + gap
            self._cpx_h += icon_h*(mul // 6) + icon_h*((mul % 6) > 0) + (34 - gap)
            template.crop((0, 0, template.width, self._cpx_h)).save(path)
        return path

    @staticmethod
    async def _process_icon(icon: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'domains', 'icon')) as template,
            Image.open(await download(icon, force=False)) as icon
        ):
            b_size = 2
            icon = round_image(resize(icon, (template.width - b_size*2, template.height - b_size*2)), 5)
            align_center(template, icon)
            return template

    def _paste_icons(self, template: Image.Image, icons: List[Image.Image], indent_w: int, gap: int) -> None:
        for i, icon in enumerate(icons):
            x = indent_w + (icon.width + gap)*(i % 6)
            y = self._cpx_h + (icon.height + gap)*(i // 6)
            template.alpha_composite(icon, (x, y))


class WeaponProgressionImageGenerator:
    def __init__(self, weapon_icon: str, progression: List[mdl.weapons.Progression]) -> None:
        self.weapon_icon = weapon_icon
        self.progression = progression
        self._cpx_h = 34

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"weaponprog_{randint(0, 10000)}.png")
        gap = 8
        with Image.open(get_template_path(__file__, 'weaponprog', 'weaponprog')) as template:
            weapon = self._process_weapon(await download(self.weapon_icon, force=False))
            template.alpha_composite(weapon, (428, self._cpx_h))
            self._cpx_h += 160 + gap
            for p in self.progression:
                progrow = self._process_progrow(p)
                template.alpha_composite(progrow, (34, self._cpx_h))
                self._cpx_h += progrow.height + gap
            template.save(path)
        return path

    @staticmethod
    def _process_weapon(weapon_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'weaponprog', 'weapon')) as template,
            Image.open(weapon_path) as weapon
        ):
            w, h = template.size
            align_center(template, round_image(resize(weapon, (w - 12, h - 12)), 20))
            return template

    def _process_progrow(self, p: mdl.weapons.Progression) -> Image.Image:
        with Image.open(get_template_path(__file__, 'weaponprog', 'progrow')) as progrow:
            self._draw_progrow_text(ImageDraw.Draw(progrow), p)
            return progrow

    @staticmethod
    def _draw_progrow_text(draw: ImageDraw.ImageDraw, p: mdl.weapons.Progression) -> None:
        font = ImageFont.truetype(FONT, 30)
        draw.text((42, 0), p.level, (255, 255, 255), font)
        draw.text((198, 0), p.primary_stat_value, (255, 255, 255), font)
        draw.text((384, 0), f"{p.secondary_stat_title}: {p.secondary_stat_value}", (255, 255, 255), font)


class EnemyDropImageGenerator:
    def __init__(self, enemy_icon: str, drop: Dict[str, str]) -> None:
        self.enemy_icon = enemy_icon
        self.drop = drop
        self._cpx_w = [306, 306, 306, 306]

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"enemydrop_{randint(0, 10000)}.png")
        with (
            Image.open(get_template_path(__file__, 'enemydrop', 'enemydrop')) as template,
            Image.open(await download(self.enemy_icon, force=False)) as enemy
        ):
            template.alpha_composite(round_image(resize(enemy, (256, 256)), 20), (34, 34))
            await self._paste_drop(template)
            template.crop((0, 0, max(self._cpx_w), template.height)).save(path)
            return path

    async def _paste_drop(self, template: Image.Image) -> None:
        gap = 8
        items = list(self.drop.values())
        if not items:
            self._cpx_w[0] += 34 - gap*2
            return None
        for d_num, d in enumerate(items):
            drop = self._process_drop(await download(d, force=False))
            row = d_num % 4
            y = 34 + (drop.height + gap)*row
            template.alpha_composite(drop, (self._cpx_w[row], y))
            self._cpx_w[row] += drop.width + (gap if d != items[-1] else 34)

    @staticmethod
    def _process_drop(drop_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'enemydrop', 'drop')) as template,
            Image.open(drop_path) as drop
        ):
            align_center(template, round_image(resize(drop, template.size), 10))
            return template


class EnemyProgressionImageGenerator:
    def __init__(self, enemy_icon: str, progression: List[mdl.enemies.Progression]) -> None:
        self.enemy_icon = enemy_icon
        self.progression = progression
        self._cpx_h = [34, 34]

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"enemyprog_{randint(0, 10000)}.png")
        gap = 8
        with Image.open(get_template_path(__file__, 'enemyprog', 'enemyprog')) as template:
            for p_num, p in enumerate(self.progression):
                col = p_num // 10
                progrow = self._process_progrow(await download(self.enemy_icon, force=False), p)
                template.alpha_composite(progrow, (34 + (progrow.width + gap*3)*col, self._cpx_h[col]))
                self._cpx_h[p_num // 10] += progrow.height + gap
            template.save(path)
        return path

    def _process_progrow(self, enemy_path: str, p: mdl.enemies.Progression) -> Image.Image:
        with Image.open(get_template_path(__file__, 'enemyprog', 'progrow')) as template:
            enemy = self._process_enemy(enemy_path)
            template.alpha_composite(enemy, (0, 0))
            self._draw_progrow_text(ImageDraw.Draw(template), p, enemy.width, template.height // 3)
            return template

    @staticmethod
    def _draw_progrow_text(
            draw: ImageDraw.ImageDraw, p: mdl.enemies.Progression, enemy_width: int, row_height: int
    ) -> None:
        font = ImageFont.truetype(FONT, 92)
        draw.text((enemy_width + 4, 0), p.level, (255, 255, 255), font)
        font = ImageFont.truetype(FONT, 30)
        for v_num, v in enumerate(list(p.__dict__.values())[1:]):
            x_pos = [362, 591, 830, 1084]
            v = str(round(int(re.match(r'\d+', str(v))[0])))
            draw.text((x_pos[v_num // 3], row_height * (v_num % 3)), v, (255, 255, 255), font)

    @staticmethod
    def _process_enemy(enemy_path: str) -> Image.Image:
        with (
            Image.open(get_template_path(__file__, 'enemyprog', 'enemy')) as template,
            Image.open(enemy_path) as enemy
        ):
            align_center(template, round_image(resize(enemy, template.size), 10))
            return template
