FONT = 'Montserrat-ExtraBold.ttf'  #: Default font for texts


def get_centered_position(bg_size: tuple[float, float], obj_size: tuple[float, float]) -> tuple[float, float]:
    """Returns tuple with xy coordinates of object which should be pasted into center of given background

    :param bg_size: Tuple with xy coordinates of the background
    :param obj_size: Tuple with xy coordinates of the object
    :return: None
    """
    return (bg_size[0] - obj_size[0]) / 2, (bg_size[1] - obj_size[1]) / 2
