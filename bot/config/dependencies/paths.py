"""
ASCENSION: path to folder that contains character ascension pictures
BOOKS: path to certain book picture
BOSS_MATERIALS: path to certain boss materials picture
MATERIALS: path to folder that contains accessible materials for each day of week
DATABASE_APPEARANCE: path to folder that contains database menu appearance files
DUNGEONS: path to certain dungeons picture
FILECACHE: path to folder which will contain files some amount of time
LOGS: path to folder which will contain logs

All pictures must be '*.png'
"""

import os


ASCENSION: str = os.getenv('ASCENSION', 'NO_ASCENSION')
BOOKS: str = os.getenv('BOOKS', 'NO_BOOKS')
BOSS_MATERIALS = os.getenv('BOSS_MATERIALS', 'NO_BOSS_MATERIALS')
DAILY_MATERIALS: str = os.getenv('DAILY_MATERIALS', 'NO_DAILY_MATERIALS')
DATABASE_APPEARANCE: str = os.getenv('DATABASE_APPEARANCE', 'NO_DATABASE_APPEARANCE')
DUNGEONS: str = os.getenv('DUNGEONS', 'NO_DUNGEONS')
FILECACHE: str = os.getenv('FILECACHE')
USER_COMMANDS: str = os.getenv('USER_COMMANDS')
LOGS: str = os.getenv('LOGS')
