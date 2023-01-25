import os


cwd: str = os.getcwd()

BOOKS: str = os.path.join(cwd, 'books', 'books.png')
BOSS_MATERIALS = os.path.join(cwd, 'boss_materials', 'materials.png')
DATABASE_APPEARANCE: str = os.path.join(cwd, 'db_appearance')
FILECACHE: str = os.path.join(cwd, 'cache')
LOGS: str = os.path.join(cwd, 'logs')
IMAGE_PROCESSING: str = os.path.join(cwd, 'image_processing')
