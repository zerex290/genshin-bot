import os
import re
from typing import Tuple

from PIL import Image, ImageDraw, ImageChops

from ..config.dependencies.paths import IMAGEPROCESSING


FONT = os.path.join(IMAGEPROCESSING, 'fonts', 'Montserrat-ExtraBold.ttf')  #: Default font for texts


def align_center(bg_im: Image.Image, fg_im: Image.Image) -> None:
    """Place one image over another vertically and horizontally aligned to center."""
    w0, h0 = bg_im.size
    w1, h1 = fg_im.size
    bg_im.alpha_composite(fg_im, (int((w0 - w1) // 2), int((h0 - h1) // 2)))
    return None


def resize(im: Image.Image, new_size: Tuple[int, int]) -> Image.Image:
    """Return resized image with keeping aspect ratio."""
    w0, h0 = im.size
    w1, h1 = new_size
    ratio = min(w1 / w0, h1 / h0)
    return im.resize((int(w0 * ratio), int(h0 * ratio)), Image.ANTIALIAS)


def round_image(im: Image.Image, rad: int) -> Image.Image:
    """Round image corners.

    :param im: Image object which will be processed
    :param rad: Round radius in pixels
    :return: Image object with rounded corners
    """
    width, height = im.size
    crop_paste_coordinates = [
        [(0, 0, rad, rad), (0, 0)],  #: left-top corner
        [(0, rad, rad, rad * 2), (0, height - rad)],  #: left-bottom corner
        [(rad, 0, rad * 2, rad), (width - rad, 0)],  #: right-top corner
        [(rad, rad, rad * 2, rad * 2), (width - rad, height - rad)]  #: right-bottom corner
    ]
    alpha = Image.new('L', (width, height), 255)
    ellipse = Image.new('L', (rad * 2, rad * 2), 0)
    ImageDraw.Draw(ellipse).ellipse((0, 0, rad * 2, rad * 2), 255)
    for crop_xy, paste_xy in crop_paste_coordinates:
        alpha.paste(ellipse.crop(crop_xy), paste_xy)
    obj_channels = im.split()
    if len(obj_channels) == 4:
        alpha = ImageChops.darker(alpha, obj_channels[-1])
    #: Scope inside ellipse filled with white color (255), outside - with black color (0);
    #: Black color in alpha mode - invisible, white - opaque;
    #: method darker() takes the min of the ellipse and original alpha channel (which can be anywhere between 0-255).
    im.putalpha(alpha)
    return im


def get_template_path(filename: str, template_dir: str, template_name: str) -> str:
    """Get desired image template path.

    :param filename: __file__ of module, where function is used
    :param template_dir: Directory where template is located
    :param template_name: Template name
    :return: Full path to template
    """
    suffix = '' if re.search(r'\.\w+$', template_name) else '.png'
    return os.path.join(
        IMAGEPROCESSING,
        re.sub(r'\S+imageprocessing\S|.py$', '', filename),
        template_dir,
        f"{template_name}{suffix}"
    )
