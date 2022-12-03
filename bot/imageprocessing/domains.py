import os
from random import randint

from PIL import Image, ImageFont, ImageDraw

from . import FONT, get_scaled_size, get_centered_position, round_corners
from ..utils.files import download
from ..config.dependencies.paths import IMAGE_PROCESSING, FILECACHE


def _process_icon(icon_path: str) -> Image.Image:
    """Pastes monster or drop icon to the image template and returns it.
    Values explanations:
        - 35 -> optimal width to resize monster or drop icon relative to the image template

    :param icon_path: Path to monster or icon
    :return: Image object with monster or drop icon pasted over the image template
    """
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'domains', 'icon.png')) as template,
        Image.open(icon_path) as icon
    ):
        icon = icon.resize(get_scaled_size('h', 35, icon.size))
        template.paste(icon, get_centered_position(template.size, icon.size), mask=icon)
        return template


def _process_text(text: str) -> Image.Image:
    """Pastes text at image template and returns it.
    Values explanations:
        - 26 -> optimal font size of the text
        - 130 -> center of the image template
        - 4 -> optimal value to center text by height with 'mt' anchor

    :param text: Text to paste
    :return: Image object with text pasted over the image template
    """
    font = ImageFont.truetype(os.path.join(IMAGE_PROCESSING, 'fonts', FONT), 26)  # 26 is optimal font size
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'domains', 'text.png')) as template:
        draw = ImageDraw.Draw(template)
        draw.text((130, 4), text, font=font, fill=(255, 255, 255), anchor='mt')
        return template


def _process_cover(cover_path: str) -> Image.Image:
    """Pastes domain cover at the image template and returns it.
    Values explanations:
        - 139 -> optimal width to resize domain icon relative to the image template
        - 8 -> optimal radius to round domain cover corners
        - 3 -> optimal width position of the domain icon relative to the image template
        - 2 -> optimal  height position of the domain icon relative to the image template

    :param cover_path: Path to domain cover
    :return: Image object with domain cover pasted over the image template
    """
    with (
        Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'domains', 'cover.png')) as template,
        Image.open(cover_path) as cover
    ):
        cover = cover.resize(get_scaled_size('w', 139, cover.size))
        cover = round_corners(cover, 8)
        template.paste(cover, (3, 2), mask=cover)
        return template


def _calc_icon_pos(
        pos: int,
        idt: int,
        icon_size: tuple[int, int],
        cpx_w: int,
        cpx_h: int
) -> tuple[int, int]:
    """Calculates position of xy coordinates of the certain icon.

    :param pos: Position of icon in the sequence
    :param idt: Horizontal indent applied for each icon
    :param icon_size: Width and height of the icon
    :param cpx_w: Complex width value; should contain text width
    :param cpx_h: Complex height value; should contain as cover and text heights as indentations between them and
    background border
    :return: Two-element tuple with xy coordinates
    """
    iw, ih = icon_size
    ipr = cpx_w // iw  #: quantity of icons per row
    icon_w = idt + (cpx_w-iw*ipr)//2 + iw*(pos if pos < ipr else pos % ipr)
    icon_h = cpx_h + (pos//ipr)*ih
    return icon_w, icon_h


def _calc_crop_box(
        idt: int,
        cpx_w: int,
        cpx_h: int,
        icon_size: tuple[int, int],
        icon_q: int
) -> tuple[int, int, int, int]:
    """Calculates coordinates of rectangle which will be cropped from image.

    :param idt: Indentation between objects
    :param cpx_w: Complex width value; should contain text width
    :param cpx_h: Complex height value; should contain as cover and text heights as indentations between them and
    background border
    :param icon_size: Width and height of the icon with monster or drop inside it
    :param icon_q: Quantity of icons pasted to the image template
    :return: Four-element tuple with x0, y0, x1, y1 coordinates of rectangle which will define new image scope
    """
    icon_h, icon_w = icon_size
    w0, h0 = 0, 0
    w1 = cpx_w*2 + idt*3
    h1 = cpx_h + idt + icon_h*(icon_q//(cpx_w//icon_w) + (1 if icon_q % (cpx_w//icon_w) != 0 else 0))
    return w0, h0, w1, h1


async def get_domain_image(cover_url: str, monsters: list[str], rewards: list[str]) -> str:
    """Process domain image template, save it and return its path

    :param cover_url: Link to image of domain cover
    :param monsters: List of urls of each monster
    :param rewards: List of urls of each reward
    :return: Path to saved image
    """
    cover = _process_cover(await download(cover_url, force=False))
    texts = [_process_text(t) for t in ('Дроп', 'Противники')]
    monsters = [_process_icon(await download(m, force=False)) for m in monsters]
    rewards = [_process_icon(await download(r, force=False)) for r in rewards]

    path = os.path.join(FILECACHE, f"domain_{randint(0, 10000)}.png")
    with Image.open(os.path.join(IMAGE_PROCESSING, 'templates', 'domains', 'domains.png')) as template:
        idt = 8  #: indentation between objects in pixels
        cpx_w = texts[0].width
        cpx_h = cover.height + texts[0].height + idt*3
        template.paste(cover, (idt + (cpx_w+idt//2) - cover.width//2, idt), mask=cover)
        for i, t in enumerate(texts):
            template.paste(t, (idt + (t.width+idt)*i, cover.height + idt*2), mask=t)
        for i, d in enumerate(rewards):
            template.paste(d, _calc_icon_pos(i, idt, d.size, cpx_w, cpx_h), mask=d)
        for i, m in enumerate(monsters):
            template.paste(m, _calc_icon_pos(i, cpx_w + idt*2, m.size, cpx_w, cpx_h), mask=m)
        template = template.crop(_calc_crop_box(idt, cpx_w, cpx_h, rewards[0].size, max(len(rewards), len(monsters))))
        template.save(path)
    return path
