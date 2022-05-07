from enum import Enum


class Rating(Enum):
    U = ''
    S = 'rating:safe'
    Q = 'rating:questionable'
    E = 'rating:explicit'


class Order(Enum):
    POPULAR = 'order:popularity'
    RANDOM = 'order:random'
    DATE = 'order:date'
    QUALITY = 'order:quality'


class TagType(Enum):
    ARTIST = 1
    COPYRIGHT = 3
    CHARACTER = 4
    GENERAL = 0

    MEDIUM = 8
    META = 9
    GENRE = 5
    STUDIO = 2


class MediaType(Enum):
    IMAGE = 'image'
    VIDEO = 'video'
