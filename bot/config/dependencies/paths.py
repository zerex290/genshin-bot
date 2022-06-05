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


os.chdir(f".{os.sep}..{os.sep}..{os.sep}..{os.sep}")  #: change current directory to root directory of bot
root_dir: str = os.getcwd()

ASCENSION: str = f"{root_dir}{os.sep}ascension"
BOOKS: str = f"{root_dir}{os.sep}books{os.sep}books.png"
BOSS_MATERIALS = f"{root_dir}{os.sep}boss_materials{os.sep}materials.png"
DAILY_MATERIALS: str = f"{root_dir}{os.sep}daily_farm{os.sep}"
DATABASE_APPEARANCE: str = f"{root_dir}{os.sep}db_appearance"
DUNGEONS: str = f"{root_dir}{os.sep}dungeons{os.sep}dungeons.png"
FILECACHE: str = f"{root_dir}{os.sep}cache"
LOGS: str = f"{root_dir}{os.sep}logs"
