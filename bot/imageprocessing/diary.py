import os
from random import randint
from collections.abc import Sequence

from PIL import Image, ImageFont, ImageDraw
from genshin.models import Diary, DayDiaryData, MonthDiaryData, DiaryActionCategory
from vkbottle_types.objects import UsersUserFull

from . import round_corners, FONT
from ..types.genshin import DiaryCategory
from ..utils.files import download
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


def _draw_user_nickname(draw: ImageDraw.ImageDraw, nickname: str) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 14)
    draw.text((385, 89), nickname, (255, 255, 255), font, 'ma')


def _draw_daily_stat_text(draw: ImageDraw.ImageDraw, data: DayDiaryData) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    draw.text((326, 168), str(data.current_mora), (255, 255, 255), font, 'ma')
    draw.text((464, 168), str(data.current_primogems), (255, 255, 255), font, 'ma')


def _draw_monthly_stat_text(draw: ImageDraw.ImageDraw, data: MonthDiaryData) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    draw.text((326, 263), str(data.current_mora), (255, 255, 255), font, 'ma')
    draw.text((464, 263), str(data.current_primogems), (255, 255, 255), font, 'ma')


def _draw_categories_text(draw: ImageDraw.ImageDraw, categories: Sequence[DiaryActionCategory]) -> None:
    amount_font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 28)
    percentage_font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 12)
    positions = {
        c.value: ((34 + 48 + (96+5)*i, 378), (34 + 48 + (96+5)*i, 356))
        for i, c in enumerate(DiaryCategory)
    }
    for c in categories:
        name = DiaryCategory[c.name.replace(' ', '_').upper()].value
        print(positions[name])
        draw.text(positions[name][0], str(c.amount), (255, 255, 255), amount_font, 'ma')
        draw.text(positions[name][1], f"{c.percentage}%", (255, 255, 255), percentage_font, 'ma')


async def _process_user_avatar(avatar_url: str, b_size: int) -> Image.Image:
    avatar_path = await download(avatar_url, name=f"avatar_{randint(0, 10000)}", ext='png')
    with Image.open(avatar_path) as avatar:
        os.remove(avatar_path)
        avatar = round_corners(avatar, avatar.width // 2).resize((100 - b_size, 100 - b_size), Image.ANTIALIAS)
        return avatar


async def _paste_user_avatar(template: Image.Image, avatar_url: str) -> Image.Image:
    b_size = 15
    avatar = await _process_user_avatar(avatar_url, b_size)
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'diary', 'avatar_front.png')) as front:
        template.paste(avatar, (335 + (b_size//2), 8 + (b_size//2)), mask=avatar)
        template.alpha_composite(front, (334, 83))
        return template


async def get_diary_image(diary: Diary, user: UsersUserFull) -> str:
    path = os.path.join(FILECACHE, f"diary_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'diary', 'diary.png')) as template:
        draw = ImageDraw.Draw(template)
        await _paste_user_avatar(template, user.photo_200)
        _draw_user_nickname(draw, diary.nickname)
        _draw_daily_stat_text(draw, diary.day_data)
        _draw_monthly_stat_text(draw, diary.data)
        _draw_categories_text(draw, diary.data.categories)
        template.save(path)
    return path
