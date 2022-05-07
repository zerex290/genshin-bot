"""
DATABASE_ADDRESS: postgres://user:password@host:port/database?option=value
"""

import os


DATABASE_ADDRESS: str = os.getenv('DATABASE_ADDRESS', 'NO_POSTGRES')
