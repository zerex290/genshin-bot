import os
from random import randint
from collections.abc import Sequence

from PIL import Image, ImageFont, ImageDraw
from genshin.models import ClaimedDailyReward

from . import FONT
from ..utils import get_current_timestamp
from ..utils.files import download
from ..config.dependencies.paths import FILECACHE, IMAGE_PROCESSING


def _draw_rewards_text(draw: ImageDraw.ImageDraw, rewards: Sequence[ClaimedDailyReward]) -> None:
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 18)
    current_month = get_current_timestamp(8).month  #: UTC+8 is login bonus offset on Europe
    current_month_rewards = [r for r in rewards if r.time.month == current_month]
    draw.text((378, 48), str(len(rewards)), (255, 255, 255), font, 'ma')
    draw.text((378, 106), str(len(current_month_rewards)), (255, 255, 255), font, 'ma')


async def _process_last_reward(reward_url: str, b_size: int) -> Image.Image:
    icon_path = await download(reward_url)
    with Image.open(icon_path) as icon:
        os.remove(icon_path)
        icon = icon.resize((215 - b_size, 215 - b_size), Image.ANTIALIAS).convert('RGBA')
        return icon


async def _paste_last_reward(template: Image.Image, reward_url: str) -> None:
    b_size = 15
    last_reward = await _process_last_reward(reward_url, b_size)
    template.alpha_composite(last_reward, (128 + b_size//2,  238 + b_size//2))


async def get_rewards_image(rewards: Sequence[ClaimedDailyReward]) -> str:
    path = os.path.join(FILECACHE, f"rewards_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'rewards', 'rewards.png')) as template:
        _draw_rewards_text(ImageDraw.Draw(template), rewards)
        await _paste_last_reward(template, rewards[0].icon)
        template.save(path)
    return path
