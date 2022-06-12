"""
ASCENSION: path to folder that contains character ascension pictures
BOOKS: path to certain book picture
BOSS_MATERIALS: path to certain boss materials picture
DAILY_MATERIALS: path to folder that contains accessible materials for each day of week
DATABASE_APPEARANCE: path to folder that contains database menu appearance files
DUNGEONS: path to certain dungeons picture
FILECACHE: path to folder which will contain files some amount of time
LOGS: path to folder which will contain logs
"""

import os


cwd: str = os.getcwd()  #: get current working directory

ASCENSION: str = f"{cwd}{os.sep}ascension"
BOOKS: str = f"{cwd}{os.sep}books{os.sep}books.png"
BOSS_MATERIALS = f"{cwd}{os.sep}boss_materials{os.sep}materials.png"
DAILY_MATERIALS: str = f"{cwd}{os.sep}daily_farm{os.sep}"
DATABASE_APPEARANCE: str = f"{cwd}{os.sep}db_appearance"
DUNGEONS: str = f"{cwd}{os.sep}dungeons{os.sep}dungeons.png"
FILECACHE: str = f"{cwd}{os.sep}cache"
LOGS: str = f"{cwd}{os.sep}logs"
IMAGE_PROCESSING: str = f"{cwd}{os.sep}image_processing"
