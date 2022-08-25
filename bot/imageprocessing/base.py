from typing import Literal

from PIL import Image, ImageDraw, ImageChops


FONT = 'Montserrat-ExtraBold.ttf'  #: Default font for texts


def get_centered_position(bg_size: tuple[float, float], obj_size: tuple[float, float]) -> tuple[float, float]:
    """Return xy coordinates to center one image over another.

    :param bg_size: Tuple with xy coordinates of the background
    :param obj_size: Tuple with xy coordinates of the object
    :return: Tuple with xy coordinates of object which should be pasted into center of given background
    """
    return (bg_size[0] - obj_size[0]) // 2, (bg_size[1] - obj_size[1]) // 2


def get_scaled_size(scale_by: Literal['w', 'h'], new_val: int, obj_width: int, obj_height: int) -> tuple[int, int]:
    """Return resized image width and height with saved proportions.

    :param scale_by: Desired scaling; can be by width 'w' or by height 'h'
    :param new_val: Desired width or height of the resized image
    :param obj_width: Actual width of the image
    :param obj_height: Actual height of the image
    :return: Tuple with resized width and height
    """
    match scale_by:
        case 'w':
            return new_val, int(new_val / (obj_width/obj_height))
        case 'h':
            return int(new_val / (obj_height/obj_width)), new_val


def round_corners(obj: Image.Image, rad: int) -> Image.Image:
    """Round image corners.

    :param obj: Image object which will be processed
    :param rad: Round radius in pixels
    :return: Image object with rounded corners
    """
    width, height = obj.size
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
    obj_channels = obj.split()
    if len(obj_channels) == 4:
        alpha = ImageChops.darker(alpha, obj_channels[-1])
    #: Scope inside ellipse filled with white color (255), outside - with black color (0);
    #: Black color in alpha mode - invisible, white - opaque;
    #: method darker() takes the min of the ellipse and original alpha channel (which can be anywhere between 0-255).
    obj.putalpha(alpha)
    return obj
