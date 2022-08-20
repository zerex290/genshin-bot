from typing import Literal

from PIL import Image, ImageDraw


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

    :param obj: image object which will be processed
    :param rad: round radius in pixels
    :return: image object with rounded corners
    """
    width, height = obj.size
    alpha = Image.new('L', (width, height), 255)
    ellipse = Image.new('L', (rad * 2, rad * 2), 0)
    ImageDraw.Draw(ellipse).ellipse((0, 0, rad * 2, rad * 2), 255)
    #: Ellipse crop request two points with coordinates x0, y0, x1, y1;
    #: Scope of crop will be inside of rectangle with this coordinates
    alpha.paste(ellipse.crop((0, 0, rad, rad)), (0, 0))  #: left-top corner
    alpha.paste(ellipse.crop((0, rad, rad, rad * 2)), (0, height - rad))  #: left-bottom corner
    alpha.paste(ellipse.crop((rad, 0, rad * 2, rad)), (width - rad, 0))  #: right-top corner
    alpha.paste(ellipse.crop((rad, rad, rad * 2, rad * 2)), (width - rad, height - rad))  #: right-bottom corner
    obj.putalpha(alpha)
    return obj
