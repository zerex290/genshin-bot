import os


TOKEN: str = os.getenv('GROUP_TOKEN', 'NO_GROUP_TOKEN')
ID: int = int(os.getenv('GROUP_ID', '0'))
SHORTNAME: str = os.getenv('SHORTNAME', 'NO_SHORTNAME')
