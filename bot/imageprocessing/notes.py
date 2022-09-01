import os
from random import randint

from PIL import Image, ImageFont, ImageDraw
from genshin.models import Notes, Expedition
from vkbottle_types.objects import UsersUserFull

from . import FONT, round_corners
from ..types.genshin import Character
from ..utils.files import download
from ..config.dependencies.paths import IMAGE_PROCESSING, FILECACHE


def _draw_resin_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws text containing resin information of user.

    Values explanations:
        - 198 -> complex horizontal text position; counts by addition of 119+69+10,
          where 119 is distance between left corner and text template,
          69 is text template width divided by 4, 10 is custom indent
        - 336 -> complex horizontal text position; counts by addition of 119+138+69+10,
          where 119 is distance between left corner and text template, 138 is text template width divided by 2,
          69 is text template width divided by 4, 10 is custom indent
        - 49 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    resin = f"{notes.current_resin}/{notes.max_resin}"
    h, s = divmod(int(notes.remaining_resin_recovery_time.total_seconds()), 3600)
    m, _ = divmod(s, 60)
    rec_time = f"{h}ч {m}мин"
    draw.text((198, 49), resin, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((336, 49), rec_time, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_dailies_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws text containing daily commissions information of user.

    Values explanations:
        - 624 -> complex horizontal text position; counts by addition of 545+69+10,
          where 545 is distance between left corner and text template,
          69 is text template width divided by 4, 10 is custom indent
        - 762 -> complex horizontal text position; counts by addition of 545+138+69+10,
          where 545 is distance between left corner and text template,
          138 is text template width divided by 2,
          69 is text template width divided by 4, 10 is custom indent
        - 49 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    dailies = f"{notes.completed_commissions}/{notes.max_commissions}"
    rewards = 'Собраны' if notes.claimed_commission_reward else 'Не собраны'
    draw.text((624, 49), dailies, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((762, 49), rewards, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_discounts_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws text containing boss discounts information of user.

    Values explanations:
        - 172 -> complex horizontal text position; counts by addition of 34+138,
          where 34 is distance between left corner and text template
          and 138 is text template width divided by 2
        - 149 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    discounts = f"{notes.remaining_resin_discounts} / {notes.max_resin_discounts}"
    draw.text((172, 149), discounts, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_teapot_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws text containing teapot information of user.

    Values explanations:
        - 420 -> complex horizontal text position; counts by addition of 332+69+19,
          where 332 is distance between left corner and text template,
          69 is text template width divided by 4, 19 is custom indent
        - 549 -> complex horizontal text position; counts by addition of 332+138+69+10,
          where 332 is distance between left corner and text template,
          138 is text template width divided by 2,
          69 is text template width divided by 4, 10 is custom indent
        - 149 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    coins = f"{notes.current_realm_currency}/{notes.max_realm_currency}"
    h, s = divmod(int(notes.remaining_realm_currency_recovery_time.total_seconds()), 3600)
    m, _ = divmod(s, 60)
    rec_time = f"{h}ч {m}мин"
    draw.text((420, 149), coins, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((549, 149), rec_time, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_transformer_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws text containing parametric transformer information of user.

    Values explanations:
        - 767 -> complex horizontal text position; counts by addition of 629+138,
          where 629 is distance between left corner and text template
          and 138 is text template width divided by 2
        - 149 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 16)
    rec_time = notes.remaining_transformer_recovery_time
    if rec_time is None:
        rec_time = 'Данные не получены'
    else:
        h, s = divmod(int(rec_time.total_seconds()), 3600)
        m, _ = divmod(s, 60)
        rec_time = f"{h}ч {m}мин"
    draw.text((767, 149), rec_time, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_expedition_length_text(draw: ImageDraw.ImageDraw, notes: Notes) -> None:
    """Draws expedition header text.

    Values explanations:
        - 629 -> complex horizontal text position; counts by addition of 604+25,
          where 604 is distance between left corner and text template
          and 25 is text template width divided by 2
        - 243 -> vertical text position

    :param draw: An image to draw in
    :param notes: Real time notes data of certain user
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 18)
    expeditions = str(len(notes.expeditions))
    draw.text((629, 243), expeditions, font=font, fill=(255, 255, 255), anchor='ma')


def _draw_expedition_text(draw: ImageDraw.ImageDraw, expedition: Expedition) -> None:
    """Draws text containing certain expedition information.

    Values explanations:
        - 172 -> complex horizontal text position; counts by addition of 50+25+97,
          where 50 is width of character icon template,
          25 is indent between character icon template and text template,
          97 is text template width divided by 4
        - 376 -> complex horizontal text position; counts by addition of 50+25+194+97+10,
          where 50 is width of character icon template,
          25 is indent between character icon template and text template,
          194 is text template width divided by 2, 97 is text template width divided by 4,
          10 is custom indent
        - 14 -> vertical text position

    :param draw: An image to draw in
    :param expedition: One of the real time notes expeditions
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 18)
    character = Character[expedition.character.name.upper().replace(' ', '_')].value
    h, s = divmod(int(expedition.remaining_time.total_seconds()), 3600)
    m, _ = divmod(s, 60)
    rec_time = f"{h}ч {m}мин"
    draw.text((172, 14), character, font=font, fill=(255, 255, 255), anchor='ma')
    draw.text((376, 14), rec_time, font=font, fill=(255, 255, 255), anchor='ma')


async def _process_expedition(expedition: Expedition) -> Image.Image:
    """Pastes expedition character and text to image template and returns it.

    Values explanations:
        - 50 -> width and height of character icon template

    :param expedition: One of the real time notes expeditions
    :return: Image object with expedition character and text pasted over the image template
    """
    icon_path = await download(expedition.character.icon, force=False)
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'notes', 'expedition.png')) as template,
        Image.open(icon_path) as icon
    ):
        icon = round_corners(icon, icon.width // 2).resize((50, 50), Image.ANTIALIAS)
        template.alpha_composite(icon, (0, 0))
        _draw_expedition_text(ImageDraw.Draw(template), expedition)
        return template


async def _paste_expeditions(template: Image.Image, notes: Notes) -> None:
    """Iter through user expeditions and add processed expedition image to the image template.

    Width calculations:
        - 237 -> distance between left corner and expedition template

    Height calculations:
        - 307 -> distance between top corner and expedition template
        - 75 -> indent between expedition templates

    :param template: Template of the background image
    :param notes: Real time notes data of certain user
    """
    for i, e in enumerate(notes.expeditions):
        expedition = await _process_expedition(e)
        template.alpha_composite(expedition, (237, 307 + 75*i))


async def _process_user_avatar(avatar_url: str, b_size: int) -> Image.Image:
    """Download user avatar, round its corners and resize it to avatar template size.

    :param avatar_url: Link to user avatar image
    :param b_size: Preferable border size of processed user avatar image
    :return: Processed user avatar image
    """
    avatar_path = await download(avatar_url, name=f"avatar_{randint(0, 10000)}", ext='png')
    with Image.open(avatar_path) as avatar:
        os.remove(avatar_path)
        avatar = round_corners(avatar, avatar.width // 2).resize((100 - b_size, 100 - b_size), Image.ANTIALIAS)
        return avatar


async def _paste_user_avatar(template: Image.Image, avatar_url: str) -> None:
    """Pastes user avatar to the image template.

    Values explanations:
        - 420 -> distance between left corner and avatar template
        - 8 -> vertical avatar template position

    :param template: Template of the background image
    :param avatar_url: Link to user avatar image
    """
    b_size = 15
    avatar = await _process_user_avatar(avatar_url, b_size)
    template.paste(avatar, (420 + b_size//2, 8 + b_size//2), mask=avatar)


def _crop_notes_image(template: Image.Image, expedition_q: int) -> Image.Image:
    """Crops notes image to new height depending on expedition quantity.

    :param template: Template of the background image
    :param expedition_q: User expedition quantity
    :return: Cropped copy of the image template
    """
    return template.crop((0, 0, template.width, 307 + 75*expedition_q + 9))


async def get_notes_image(notes: Notes, user: UsersUserFull) -> str:
    """Process notes image template, save it and return its path.

    :param notes: Real time notes data of certain user
    :param user: Vk data of user who made request
    :return: Path to saved image
    """
    path = os.path.join(FILECACHE, f"notes_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'notes', 'notes.png')) as template:
        draw = ImageDraw.Draw(template)
        _draw_resin_text(draw, notes)
        _draw_dailies_text(draw, notes)
        _draw_discounts_text(draw, notes)
        _draw_teapot_text(draw, notes)
        _draw_transformer_text(draw, notes)
        _draw_expedition_length_text(draw, notes)
        await _paste_expeditions(template, notes)
        await _paste_user_avatar(template, user.photo_200)
        template = _crop_notes_image(template, len(notes.expeditions))
        template.save(path)
    return path
