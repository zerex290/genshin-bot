import os
from typing import List


ADMINS: List[int] = [int(admin_id) for admin_id in os.getenv("ADMINS").split(",")]
