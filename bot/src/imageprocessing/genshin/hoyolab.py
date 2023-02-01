import os
from typing import Optional
from re import sub
from random import randint
from collections.abc import Sequence

from PIL import Image, ImageFont, ImageDraw
from genshin.models import Notes, Expedition  #: For notes
from genshin.models import PartialGenshinUserStats, PartialCharacter, Exploration, Offering  #: For stats
from genshin.models import ClaimedDailyReward  #: For rewards
from genshin.models import Diary  #: For diary
from genshin.models import SpiralAbyss, Chamber  #: for spiral abyss
from vkbottle_types.objects import UsersUserFull


from .. import FONT, round_image, resize, align_center, get_template_path
from ...types.genshin import TeapotComfortName, Character, Region, ExplorationOffering, DiaryCategory
from ...utils import get_current_timestamp
from ...utils.files import download
from ...config.dependencies.paths import FILECACHE


__all__ = (
    'NotesImageGenerator',
    'StatsImageGenerator',
    'RewardsImageGenerator',
    'DiaryImageGenerator',
    'AbyssImageGenerator'
)


class NotesImageGenerator:
    def __init__(self, notes: Notes, user: UsersUserFull) -> None:
        self.notes = notes
        self.user = user

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"notes_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'notes', 'notes')) as template:
            draw = ImageDraw.Draw(template)

            self._draw_resin_text(draw),
            self._draw_dailies_text(draw),
            self._draw_discounts_text(draw),
            self._draw_teapot_text(draw),
            self._draw_transformer_text(draw)
            self._draw_expedition_length_text(draw)
            await self._paste_expeditions(template)
            await self._paste_user_avatar(template)

            indent_y = 15 if self.notes.expeditions else 9
            template.crop((0, 0, template.width, 330 + 69*len(self.notes.expeditions) + indent_y)).save(path)
        return path

    def _draw_resin_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        resin = f"{self.notes.current_resin}/{self.notes.max_resin}"
        h, s = divmod(int(self.notes.remaining_resin_recovery_time.total_seconds()), 3600)
        m, _ = divmod(s, 60)
        rec_time = f"{h}ч {m}мин"
        draw.text((207, 75), resin, (255, 255, 255), font, 'ma')
        draw.text((339, 75), rec_time, (255, 255, 255), font, 'ma')

    def _draw_dailies_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        dailies = f"{self.notes.completed_commissions}/{self.notes.max_commissions}"
        rewards = 'Собраны' if self.notes.claimed_commission_reward else 'Не собраны'
        draw.text((633, 75), dailies, (255, 255, 255), font, 'ma')
        draw.text((765, 75), rewards, (255, 255, 255), font, 'ma')

    def _draw_discounts_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        discounts = f"{self.notes.remaining_resin_discounts} / {self.notes.max_resin_discounts}"
        draw.text((172, 174), discounts, (255, 255, 255), font, 'ma')
        #: 172 = 34 + 117 = base.h_indent + text_holder.width//2

    def _draw_teapot_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        coins = f"{self.notes.current_realm_currency}/{self.notes.max_realm_currency}"
        h, s = divmod(int(self.notes.remaining_realm_currency_recovery_time.total_seconds()), 3600)
        m, _ = divmod(s, 60)
        rec_time = f"{h}ч {m}мин"
        draw.text((419, 174), coins, (255, 255, 255), font, 'ma')
        #: 419 = 332 + 36 + 51 =
        #: = text_holder.h_indent + (svg.h_indent + svg.width) + ((text_holder.width//2 - svg.width) // 2)
        draw.text((551, 174), rec_time, (255, 255, 255), font, 'ma')
        #: 551 = 332 + 276 - 57 =
        #: = text_holder.h_indent + text_holder.width - ((text_holder.width//2 - svg.width) // 2)

    def _draw_transformer_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        rec_time = self.notes.remaining_transformer_recovery_time
        if rec_time is None:
            rec_time = 'Данные не получены'
        else:
            h, s = divmod(int(rec_time.total_seconds()), 3600)
            m, _ = divmod(s, 60)
            rec_time = f"{h}ч {m}мин"
        draw.text((768, 174), rec_time, (255, 255, 255), font, 'ma')

    def _draw_expedition_length_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 18)
        expeditions = str(len(self.notes.expeditions))
        draw.text((630, 269), expeditions, (255, 255, 255), font, 'ma')

    @staticmethod
    def _draw_expedition_text(draw: ImageDraw.ImageDraw, expedition: Expedition) -> None:
        font = ImageFont.truetype(FONT, 18)
        character = Character[expedition.character.name.upper().replace(' ', '_')].value
        h, s = divmod(int(expedition.remaining_time.total_seconds()), 3600)
        m, _ = divmod(s, 60)
        rec_time = f"{h}ч {m}мин"
        draw.text((172, 14), character, (255, 255, 255), font, 'ma')
        draw.text((383, 14), rec_time, (255, 255, 255), font, 'ma')

    async def _process_expedition(self, expedition: Expedition) -> Image.Image:
        icon_path = await download(expedition.character.icon, force=False)
        with (
            Image.open(get_template_path(__file__, 'notes', 'expedition')) as template,
            Image.open(icon_path) as icon
        ):
            icon = resize(icon, (50, 50))
            template.alpha_composite(round_image(icon, icon.width // 2), (0, 0))
            self._draw_expedition_text(ImageDraw.Draw(template), expedition)
            return template

    async def _paste_expeditions(self, template: Image.Image) -> None:
        for i, e in enumerate(self.notes.expeditions):
            expedition = await self._process_expedition(e)
            template.alpha_composite(expedition, (238, 330 + 69*i))
            #: 330 + 69*i = text_holder.v_indent + (text_holder.height + 19)*i

    async def _process_user_avatar(self, b_size: int) -> Image.Image:
        avatar_path = await download(self.user.photo_200, name=f"avatar_{randint(0, 10000)}", ext='png')
        with Image.open(avatar_path) as avatar:
            os.remove(avatar_path)
            return resize(round_image(avatar, avatar.width // 2), (100 - b_size, 100 - b_size))

    async def _paste_user_avatar(self, template: Image.Image) -> None:
        b_size = 15
        avatar = await self._process_user_avatar(b_size)
        template.paste(avatar, (420 + b_size//2, 34 + b_size//2), mask=avatar)


class StatsImageGenerator:
    def __init__(self, stats: PartialGenshinUserStats, user: UsersUserFull) -> None:
        self.stats = stats
        self.user = user
        self._cpx_h = 586  #: character container vertical indent

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"stats_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'stats', 'stats')) as template:
            draw = ImageDraw.Draw(template)
            await self._paste_user_avatar(template)
            self._draw_summary_text(draw)
            self._draw_teapot_text(draw)
            self._draw_characters_header_text(draw)
            await self._paste_characters(template)
            self._cpx_h += 25
            await self._paste_explorations(template)
            template.crop((0, 0, template.width, self._cpx_h)).save(path)
        return path

    def _draw_user_avatar_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 20)  #: for level
        draw.text((82, 5), str(self.stats.info.level), (255, 255, 255), font, 'ma')
        font = ImageFont.truetype(FONT, 14)  #: for nickname
        draw.text((50, 80), self.stats.info.nickname, (255, 255, 255), font, 'ma')

    async def _process_user_avatar(self, b_size: int) -> Image.Image:
        avatar_path = await download(self.user.photo_200, name=f"avatar_{randint(0, 10000)}", ext='png')
        with (
            Image.open(get_template_path(__file__, 'stats', 'avatar_back')) as template,
            Image.open(avatar_path) as avatar,
            Image.open(get_template_path(__file__, 'stats', 'avatar_front')) as front
        ):
            os.remove(avatar_path)
            w = template.width
            align_center(template, resize(round_image(avatar, avatar.width // 2), (w - b_size, w - b_size)))
            template.alpha_composite(front, (0, 0))
            self._draw_user_avatar_text(ImageDraw.Draw(template))
            return template

    async def _paste_user_avatar(self, template: Image.Image) -> None:
        avatar = await self._process_user_avatar(15)
        template.alpha_composite(avatar, (34, 34))

    def _draw_summary_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 28)
        s = self.stats.stats
        positions = [
            s.days_active, s.achievements, s.unlocked_waypoints, s.unlocked_domains, s.spiral_abyss,
            s.characters, s.anemoculi, s.geoculi, s.electroculi, s.dendroculi,
            s.common_chests, s.exquisite_chests, s.precious_chests, s.luxurious_chests, s.remarkable_chests,
        ]
        for i, p in enumerate(positions):
            indent_x = (144+7) * (i if i < 5 else i % 5)
            indent_y = (100+8) * (i//5)
            draw.text((303 - 4 + indent_x, 34 + 20 + indent_y), str(p), font=font, fill=(255, 255, 255), anchor='ra')

    def _draw_teapot_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 28)
        teapot = self.stats.teapot
        if teapot is None:
            draw.text((471, 380), 'Не открыт', (255, 255, 255), font, 'ma')
            return None
        comfort_name = TeapotComfortName[sub(r'[\s-]', '_', teapot.comfort_name).upper()].value
        draw.text((89, 380), comfort_name, (255, 255, 255), font)
        bottom_positions = [
            teapot.level, teapot.comfort, teapot.items, teapot.visitors
        ]
        for i, p in enumerate(bottom_positions):
            indent_x = (213+7) * i
            draw.text((34 + 213//2 + indent_x, 419), str(p), (255, 255, 255), font, 'ma')

    def _draw_characters_header_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 28)
        five_star = []
        four_star = []
        max_friendship = []
        for c in self.stats.characters:
            five_star.append(c) if c.rarity == 5 else four_star.append(c)
            if c.friendship == 10:
                max_friendship.append(c)
        draw.text((177, 522), str(len(five_star)), (255, 255, 255), font, 'ma')
        draw.text((470, 522), str(len(four_star)), (255, 255, 255), font, 'ma')
        draw.text((764, 522), str(len(max_friendship)), (255, 255, 255), font, 'ma')

    @staticmethod
    def _draw_character_text(draw: ImageDraw.ImageDraw, character: PartialCharacter) -> None:
        """Figma sizes + 2px to each width and height"""
        font = ImageFont.truetype(FONT, 12)
        lvl = str(character.level)
        name = Character[character.name.replace(' ', '_').upper()].value
        friendship = str(character.friendship)
        constellation = str(character.constellation)
        draw.text((29, 19), lvl, (255, 255, 255), font, 'ma')
        draw.text((124, 10), name, (255, 255, 255), font, 'ma')
        draw.text((188, 1), friendship, (255, 255, 255), font)
        draw.text((188, 20), constellation, (255, 255, 255), font)

    async def _process_character(self, character: PartialCharacter) -> Image.Image:
        icon = await download(character.icon, force=False)
        if character.element:
            element = character.element.lower()
        else:
            element = 'none'
        with (
            Image.open(get_template_path(__file__, 'stats', 'character')) as template,
            Image.open(icon) as icon,
            Image.open(get_template_path(__file__, 'stats', 'character_lvl')) as lvl,
            Image.open(get_template_path(__file__, 'stats', element)) as element,
            Image.open(get_template_path(__file__, 'stats', f"{character.rarity}_star")) as stars
        ):
            h = template.height
            icon = resize(round_image(icon, icon.width // 2), (h, h))
            template.alpha_composite(icon, (0, 0))
            template.alpha_composite(lvl, (18, 18))
            element = resize(element, (26, 26))
            template.alpha_composite(element, (38, 4))
            template.alpha_composite(stars, (63, 24))  #: figma sizes - 3px from w, h
            self._draw_character_text(ImageDraw.Draw(template), character)
            return template

    async def _paste_characters(self, template: Image.Image) -> None:
        gap = 4
        w, h = 0, 0
        for i, c in enumerate(self.stats.characters):
            character = await self._process_character(c)
            w, h = character.size
            distance = (941 - 68 - w*gap) // 3
            if i > 0:
                self._cpx_h += (h + gap) * ((i % 4) == 0)
            template.alpha_composite(character, (34 + (w+distance) * (i % 4), self._cpx_h))
        self._cpx_h += h

    @staticmethod
    def _draw_exploration_text(draw: ImageDraw.ImageDraw, exploration: Exploration) -> None:
        font = ImageFont.truetype(FONT, 12)
        name = Region[sub(r"'s|:|-", '', exploration.name).replace(' ', '_').upper()].value
        draw.text((51, 85), f"{exploration.explored}%", (255, 255, 255), font, 'ma')
        draw.text((192, 2), name, (255, 255, 255), font, 'ma')

    @staticmethod
    def _draw_offerings_text(draw: ImageDraw.ImageDraw, offerings: Sequence[Offering]) -> None:
        font = ImageFont.truetype(FONT, 10)
        for i, o in enumerate(offerings):
            indent_y = (20+4) * i
            name = ExplorationOffering[sub(r"'s|:|-", '', o.name).replace(' ', '_').upper()].value
            draw.text((120, 42 + indent_y), name, (255, 255, 255), font)
            draw.text((270, 42 + indent_y), str(o.level), (255, 255, 255), font, 'ma')

    async def _process_offerings(self, template: Image.Image, offerings: Sequence[Offering]) -> None:
        for i, o in enumerate(offerings):
            if o.icon:
                icon = await download(o.icon, force=False)
            else:
                icon = get_template_path(__file__, 'stats', 'reputation')
            with Image.open(icon) as icon:
                icon = resize(icon.convert('RGBA'), (20, 20))
                template.alpha_composite(icon, (100, 38 + (20+4)*i))
        self._draw_offerings_text(ImageDraw.Draw(template), offerings)

    async def _process_exploration(self, exploration: Exploration) -> Image.Image:
        icon = await download(exploration.icon, force=False)
        with (
            Image.open(get_template_path(__file__, 'stats', 'exploration')) as template,
            Image.open(icon) as icon,
            Image.open(get_template_path(__file__, 'stats', 'exploration_lvl')) as lvl
        ):
            h = template.height
            icon = resize(icon, (h, h))
            template.alpha_composite(icon, (0, 0))
            template.alpha_composite(lvl, (20, 85))
            self._draw_exploration_text(ImageDraw.Draw(template), exploration)
            await self._process_offerings(template, exploration.offerings)
            return template

    async def _paste_explorations(self, template: Image.Image) -> None:
        gap_y = 4
        w, h = 0, 0
        for i, e in enumerate([e for e in self.stats.explorations if e.name]):
            exploration = await self._process_exploration(e)
            w, h = exploration.size
            gap_x = (941 - 68 - w*3) // 2  #: 941 is main template width, 68=34*2 are base indentations
            if i > 0:
                self._cpx_h += (h + gap_y) * ((i % 3) == 0)
            template.alpha_composite(exploration, (34 + (285+gap_x) * (i % 3), self._cpx_h))
        self._cpx_h += h + 34


class RewardsImageGenerator:
    def __init__(self, rewards: Sequence[ClaimedDailyReward]) -> None:
        self.rewards = rewards

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"rewards_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'rewards', 'rewards')) as template:
            self._draw_rewards_text(ImageDraw.Draw(template))
            await self._paste_last_reward(template)
            template.save(path)
        return path

    def _draw_rewards_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 18)
        current_month = get_current_timestamp(8).month  #: UTC+8 is login bonus offset on Europe
        current_month_rewards = [r for r in self.rewards if r.time.month == current_month]
        draw.text((378, 48), str(len(self.rewards)), (255, 255, 255), font, 'ma')
        draw.text((378, 106), str(len(current_month_rewards)), (255, 255, 255), font, 'ma')

    async def _process_last_reward(self, b_size: int) -> Image.Image:
        icon_path = await download(self.rewards[0].icon)
        with Image.open(icon_path) as icon:
            os.remove(icon_path)
            return resize(icon, (215 - b_size, 215 - b_size)).convert('RGBA')

    async def _paste_last_reward(self, template: Image.Image) -> None:
        b_size = 15
        last_reward = await self._process_last_reward(b_size)
        template.alpha_composite(last_reward, (128 + b_size//2,  238 + b_size//2))


class DiaryImageGenerator:
    def __init__(self, diary: Diary, user: UsersUserFull) -> None:
        self.diary = diary
        self.user = user

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"diary_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'diary', 'diary')) as template:
            draw = ImageDraw.Draw(template)
            await self._paste_user_avatar(template)
            self._draw_user_nickname(draw)
            self._draw_daily_stat_text(draw)
            self._draw_monthly_stat_text(draw)
            self._draw_categories_text(draw)
            template.save(path)
        return path

    async def _process_user_avatar(self, b_size: int) -> Image.Image:
        avatar_path = await download(self.user.photo_200, name=f"avatar_{randint(0, 10000)}", ext='png')
        with Image.open(avatar_path) as avatar:
            os.remove(avatar_path)
            avatar = round_image(avatar, avatar.width // 2).resize((100 - b_size, 100 - b_size), Image.ANTIALIAS)
            return resize(round_image(avatar, avatar.width // 2), (100 - b_size, 100 - b_size))

    async def _paste_user_avatar(self, template: Image.Image) -> Image.Image:
        b_size = 15
        avatar = await self._process_user_avatar(b_size)
        with Image.open(get_template_path(__file__, 'diary', 'avatar_front')) as front:
            template.paste(avatar, (335 + (b_size//2), 34 + (b_size//2)), mask=avatar)
            template.alpha_composite(front, (335, 112))
            return template

    def _draw_user_nickname(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 14)
        draw.text((385, 115), self.diary.nickname, (255, 255, 255), font, 'ma')

    def _draw_daily_stat_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((326, 194), str(self.diary.day_data.current_mora), (255, 255, 255), font, 'ma')
        draw.text((464, 194), str(self.diary.day_data.current_primogems), (255, 255, 255), font, 'ma')

    def _draw_monthly_stat_text(self, draw: ImageDraw.ImageDraw) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((326, 289), str(self.diary.data.current_mora), (255, 255, 255), font, 'ma')
        draw.text((464, 289), str(self.diary.data.current_primogems), (255, 255, 255), font, 'ma')

    def _draw_categories_text(self, draw: ImageDraw.ImageDraw) -> None:
        amount_font = ImageFont.truetype(FONT, 28)
        percentage_font = ImageFont.truetype(FONT, 12)
        positions = {
            c.value: ((34 + 48 + (96+5)*i, 404), (34 + 48 + (96+5)*i, 382))
            for i, c in enumerate(DiaryCategory)
        }
        for c in self.diary.data.categories:
            name = DiaryCategory[c.name.replace(' ', '_').upper()].value
            draw.text(positions[name][0], str(c.amount), (255, 255, 255), amount_font, 'ma')
            draw.text(positions[name][1], f"{c.percentage}%", (255, 255, 255), percentage_font, 'ma')


class AbyssImageGenerator:
    def __init__(self, abyss: SpiralAbyss) -> None:
        self.abyss = abyss
        self._c_num = 0

    async def generate(self) -> str:
        path = os.path.join(FILECACHE, f"abyss_{randint(0, 10000)}.png")
        with Image.open(get_template_path(__file__, 'abyss', 'abyss')) as template:
            await self._paste_chambers(template)
            template.save(path)
        return path

    @staticmethod
    def _draw_character_level(draw: ImageDraw.ImageDraw, b_num: int, ch_num: int, lvl: int) -> None:
        font = ImageFont.truetype(FONT, 14)
        x = 80 + 110*(ch_num % 2) + 230*b_num
        y = 221 + 132*(ch_num // 2)
        draw.text((x, y), f"Лвл {lvl}", (255, 255, 255), font, 'ma')

    @staticmethod
    def _process_character(ch_path: str) -> Image.Image:
        with Image.open(ch_path) as icon:
            return round_image(resize(icon, (96, 96)), 10)

    @staticmethod
    def _draw_battle_text(draw: ImageDraw.ImageDraw, b_num: int) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((135 + 230*b_num, 90), f"{b_num + 1} половина", (255, 255, 255), font, 'ma')

    @staticmethod
    def _draw_chamber_text(draw: ImageDraw.ImageDraw, c: Chamber) -> None:
        font = ImageFont.truetype(FONT, 16)
        draw.text((148, 65), f"Зал {c.chamber}", (255, 255, 255), font, anchor='ma')
        draw.text((258, 65), f"{c.stars} из {c.max_stars}", (255, 255, 255), font, anchor='ma')
        draw.text((380, 65), c.battles[0].timestamp.strftime('%d.%m.%Y'), (255, 255, 255), font, anchor='ma')

    @staticmethod
    def _draw_floor_text(draw: ImageDraw.ImageDraw, f_num: int) -> None:
        font = ImageFont.truetype(FONT, 24)
        draw.text((251, 30), f"Этаж {f_num}", (255, 255, 255), font, 'ma')

    async def _process_chamber(
            self, f_num: Optional[int] = None, c: Optional[Chamber] = None, locked: bool = False
    ) -> Image.Image:
        with Image.open(get_template_path(__file__, 'abyss', f"chamber{'_locked' if locked else ''}")) as template:
            if locked:
                return template.copy()
            draw = ImageDraw.Draw(template)
            self._draw_floor_text(draw, f_num)
            self._draw_chamber_text(draw, c)
            for b_num, b in enumerate(c.battles):
                self._draw_battle_text(draw, b_num)
                for ch_num, ch in enumerate(b.characters):
                    character = self._process_character(await download(ch.icon, force=False))
                    half = 230*b_num
                    template.alpha_composite(character, (32 + 110*(ch_num % 2) + half, 118 + 132*(ch_num // 2)))
                    self._draw_character_level(draw, b_num, ch_num, ch.level)
                    with Image.open(get_template_path(__file__, 'abyss', f"{ch.rarity}_star")) as stars:
                        w, h = stars.size
                        template.alpha_composite(
                            stars,
                            (30 + (100 - w)//2 + 110*(ch_num % 2) + half, 214 - h//2 + 132*(ch_num // 2))
                        )
            return template

    async def _paste_chambers(self, template: Image.Image) -> None:
        for f in self.abyss.floors:
            for c in f.chambers:
                chamber = await self._process_chamber(f.floor, c)
                template.alpha_composite(chamber, (500 * (self._c_num // 3), (400 * (self._c_num % 3))))
                self._c_num += 1
        while self._c_num < 12:
            chamber = await self._process_chamber(locked=True)
            template.alpha_composite(chamber, (500 * (self._c_num // 3), 400 * (self._c_num % 3)))
            self._c_num += 1
